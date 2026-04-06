"""TASK-0018 批次 D — risk_engine 测试

覆盖场景：
  (1) max_drawdown 规则未触发（净值正常）→ risk_events 为空
  (2) max_drawdown 规则触发 → risk_events 有一条，字段完整
  (3) daily_loss_limit 规则触发 → risk_events 有一条，trigger_reason 正确
  (4) equity_curve 序列化后长度与 bar 数一致
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

# 确保项目根目录在 sys.path（与 test_local_engine.py 保持相同的路径解析方式）
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.risk_engine import RiskEngine, RiskParams
from services.backtest.src.backtest.local_engine import (
    LocalBacktestEngine,
    LocalBacktestParams,
    MockDataProvider,
)


# ── 辅助 ─────────────────────────────────────────────────────────────────────

def _engine(max_drawdown: float = 1.0, daily_loss_limit: float = 1.0, initial_capital: float = 100_000.0) -> RiskEngine:
    return RiskEngine(
        job_id="test-job",
        initial_capital=initial_capital,
        params=RiskParams(max_drawdown=max_drawdown, daily_loss_limit=daily_loss_limit),
    )


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


# ── (1) max_drawdown 规则未触发 ───────────────────────────────────────────────

def test_max_drawdown_not_triggered() -> None:
    """净值回撤低于阈值时 risk_events 为空，open_allowed 为 True。"""
    eng = _engine(max_drawdown=0.05, initial_capital=100_000.0)
    eng.check(_ts("2026-01-02T09:00:00"), 100_000.0)
    eng.check(_ts("2026-01-02T10:00:00"), 99_000.0)   # 回撤 1%
    eng.check(_ts("2026-01-02T11:00:00"), 98_000.0)   # 回撤 2%
    assert eng.risk_events == []
    assert eng.open_allowed is True


# ── (2) max_drawdown 规则触发 ─────────────────────────────────────────────────

def test_max_drawdown_triggered() -> None:
    """净值回撤超过阈值时触发一条 risk_event，所有字段符合 api.md §6.2.2。"""
    eng = _engine(max_drawdown=0.05, initial_capital=100_000.0)
    eng.check(_ts("2026-01-02T09:00:00"), 100_000.0)   # 峰值 = 100 000
    eng.check(_ts("2026-01-02T10:00:00"), 94_000.0)    # 回撤 6% → 触发

    assert len(eng.risk_events) == 1
    evt = eng.risk_events[0]

    # 顶层必需字段
    assert evt["trigger_reason"] == "max_drawdown_limit_breached"
    assert evt["event_type"] == "system_risk"
    assert evt["engine_type"] == "local"
    assert "event_id" in evt
    assert "job_id" in evt
    assert "event_time" in evt

    # threshold 对象
    th = evt["threshold"]
    assert th["name"] == "max_drawdown"
    assert th["operator"] == ">="
    assert th["value"] == pytest.approx(0.05, abs=1e-9)
    assert th["unit"] == "ratio"

    # observed 对象
    ob = evt["observed"]
    assert ob["name"] == "current_drawdown"
    assert ob["value"] == pytest.approx(0.06, abs=1e-5)
    assert ob["unit"] == "ratio"
    assert "sample_time" in ob

    # action 对象
    ac = evt["action"]
    assert ac["decision"] == "stop_open"
    assert ac["status"] == "executed"
    assert "detail" in ac

    # 风控触发后禁止开仓
    assert eng.open_allowed is False

    # 同一条规则不重复触发
    eng.check(_ts("2026-01-02T11:00:00"), 90_000.0)
    assert len(eng.risk_events) == 1


# ── (3) daily_loss_limit 规则触发 ─────────────────────────────────────────────

def test_daily_loss_limit_triggered() -> None:
    """当日亏损超过阈值时触发一条 risk_event，trigger_reason 正确。"""
    eng = _engine(daily_loss_limit=0.05, initial_capital=100_000.0)
    eng.check(_ts("2026-01-02T09:00:00"), 100_000.0)   # 当日起始 = 100 000
    eng.check(_ts("2026-01-02T10:00:00"), 96_000.0)    # 日亏损 4%，未触发
    eng.check(_ts("2026-01-02T11:00:00"), 94_000.0)    # 日亏损 6% → 触发

    assert len(eng.risk_events) == 1
    evt = eng.risk_events[0]
    assert evt["trigger_reason"] == "daily_loss_limit_breached"
    assert evt["threshold"]["name"] == "daily_loss_limit"
    assert evt["threshold"]["value"] == pytest.approx(0.05, abs=1e-9)
    assert evt["observed"]["name"] == "current_daily_loss"
    assert evt["observed"]["value"] == pytest.approx(0.06, abs=1e-5)
    assert eng.open_allowed is False


# ── (4) equity_curve 序列化长度与 bar 数一致 ────────────────────────────────

def test_equity_curve_length_matches_bars() -> None:
    """report.artifacts['equity_curve'] 长度 == 实际加载的 bar 数，且每条含必需字段。"""
    params = LocalBacktestParams(
        job_id="test-curve",
        symbols=["SHFE.rb2501"],
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 6),
        initial_capital=100_000.0,
        timeframe_minutes=60,
    )

    # 直接查询 MockDataProvider 以获得预期 bar 数
    provider = MockDataProvider()
    bars = provider.load_bars(
        symbol="SHFE.rb2501",
        start_date=params.start_date,
        end_date=params.end_date,
        timeframe_minutes=params.timeframe_minutes,
    )

    engine = LocalBacktestEngine(data_provider=provider)
    report = engine.run(params)

    ec = report.artifacts["equity_curve"]
    assert isinstance(ec, list)
    assert len(ec) > 0, "equity_curve 不能为空列表"
    assert len(ec) == len(bars), (
        f"equity_curve 长度 {len(ec)} != bar 数 {len(bars)}"
    )

    # 每条记录的必需字段
    first = ec[0]
    assert "bar_time" in first
    assert "equity" in first
    assert "drawdown" in first
    assert isinstance(first["equity"], float)
    assert isinstance(first["drawdown"], float)


# ── (5) equity_curve 不受 strategy_id 影响，strategy_id 写入 job ─────────────

def test_strategy_id_in_report() -> None:
    """strategy_id 从参数读取写入 job 字段，不传时为 'unknown'。"""
    p1 = LocalBacktestParams(
        job_id="sid-test",
        symbols=["SHFE.rb2501"],
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 4),
        initial_capital=50_000.0,
        strategy_id="FC-224_v3",
    )
    report = LocalBacktestEngine().run(p1)
    assert report.job["strategy_id"] == "FC-224_v3"

    p2 = LocalBacktestParams(
        job_id="sid-test-2",
        symbols=["SHFE.rb2501"],
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 4),
        initial_capital=50_000.0,
    )
    report2 = LocalBacktestEngine().run(p2)
    assert report2.job["strategy_id"] == "unknown"
