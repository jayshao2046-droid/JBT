"""人工手动回测执行器 — TASK-0055 CG2

提供手动提交回测、查看结果、审核确认的完整流程。
审核结果可回写给 decision 端。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ManualBacktestResult:
    """单次手动回测的完整记录。"""

    run_id: str
    strategy_id: str
    status: str  # pending / running / completed / failed
    start_time: str
    end_time: Optional[str] = None
    metrics: dict = field(default_factory=dict)
    approved: Optional[bool] = None  # None=未审核, True=通过, False=拒绝
    reviewer_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ManualRunner:
    """人工手动回测管理器（内存存储）。"""

    def __init__(self, data_service_url: str = "http://localhost:8105") -> None:
        self._results: dict[str, ManualBacktestResult] = {}
        self._data_service_url = data_service_url

    # ── 提交回测 ─────────────────────────────────────────────────────

    def submit(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        params: dict | None = None,
    ) -> ManualBacktestResult:
        """创建并同步执行一次手动回测，返回结果。"""
        run_id = uuid.uuid4().hex[:16]
        now = datetime.now(timezone.utc).isoformat()

        result = ManualBacktestResult(
            run_id=run_id,
            strategy_id=strategy_id,
            status="running",
            start_time=now,
        )
        self._results[run_id] = result

        try:
            metrics = self._execute_backtest(strategy_id, start_date, end_date, params)
            result.status = "completed"
            result.metrics = metrics
        except Exception as exc:
            logger.warning("手动回测执行失败: %s", exc)
            result.status = "failed"
            result.metrics = {"error": str(exc)}

        result.end_time = datetime.now(timezone.utc).isoformat()
        return result

    # ── 查询 ──────────────────────────────────────────────────────────

    def get_result(self, run_id: str) -> ManualBacktestResult | None:
        return self._results.get(run_id)

    def list_results(
        self, strategy_id: str | None = None
    ) -> list[ManualBacktestResult]:
        items = list(self._results.values())
        if strategy_id:
            items = [r for r in items if r.strategy_id == strategy_id]
        return items

    # ── 审核确认 ──────────────────────────────────────────────────────

    def approve(
        self, run_id: str, approved: bool, note: str = ""
    ) -> ManualBacktestResult:
        """对已完成的回测进行审核确认/拒绝。"""
        result = self._results.get(run_id)
        if result is None:
            raise KeyError(f"run_id not found: {run_id}")
        if result.status not in ("completed", "failed"):
            raise ValueError(f"只能审核已完成/失败的回测，当前状态: {result.status}")

        result.approved = approved
        result.reviewer_note = note

        # 异步通知 decision 端
        self._notify_decision(run_id, result.strategy_id, approved)

        return result

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _execute_backtest(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        params: dict | None = None,
    ) -> dict:
        """从 data 服务拉取 bars，用简单均线策略模拟执行，返回 metrics。"""
        short_window = (params or {}).get("short_window", 5)
        long_window = (params or {}).get("long_window", 20)

        # 从 data 服务获取 K 线
        bars = self._fetch_bars(strategy_id, start_date, end_date)

        if len(bars) < long_window:
            return {
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "total_return": 0.0,
                "trades_count": 0,
            }

        # 简单双均线策略模拟
        closes = [b.get("close", b.get("收盘价", 0.0)) for b in bars]
        trades: list[float] = []
        position = 0  # 0=空仓, 1=持仓
        entry_price = 0.0

        for i in range(long_window, len(closes)):
            short_ma = sum(closes[i - short_window : i]) / short_window
            long_ma = sum(closes[i - long_window : i]) / long_window

            if short_ma > long_ma and position == 0:
                position = 1
                entry_price = closes[i]
            elif short_ma < long_ma and position == 1:
                position = 0
                pnl = (closes[i] - entry_price) / entry_price
                trades.append(pnl)

        # 如果最后还持仓，以最后收盘价平仓
        if position == 1 and closes:
            pnl = (closes[-1] - entry_price) / entry_price
            trades.append(pnl)

        total_return = sum(trades) if trades else 0.0
        win_count = sum(1 for t in trades if t > 0)
        win_rate = win_count / len(trades) if trades else 0.0

        # 简化版最大回撤
        equity = [1.0]
        for t in trades:
            equity.append(equity[-1] * (1 + t))
        peak = equity[0]
        max_dd = 0.0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        # 简化版 sharpe
        import statistics

        if len(trades) >= 2:
            avg = statistics.mean(trades)
            std = statistics.stdev(trades)
            sharpe = (avg / std) * (252 ** 0.5) if std > 0 else 0.0
        else:
            sharpe = 0.0

        return {
            "sharpe": round(sharpe, 4),
            "max_drawdown": round(max_dd, 4),
            "win_rate": round(win_rate, 4),
            "total_return": round(total_return, 4),
            "trades_count": len(trades),
        }

    def _fetch_bars(
        self, strategy_id: str, start_date: str, end_date: str
    ) -> list[dict]:
        """从 data service 获取分钟 K 线数据。"""
        url = f"{self._data_service_url}/api/v1/bars"
        try:
            resp = httpx.get(
                url,
                params={
                    "strategy_id": strategy_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("bars", [])
        except Exception as exc:
            logger.warning("从 data 服务获取 bars 失败: %s", exc)
            return []

    def _notify_decision(
        self, run_id: str, strategy_id: str, approved: bool
    ) -> None:
        """异步通知 decision 端审核结果（失败只打 warning 日志不抛异常）。"""
        try:
            httpx.post(
                "http://localhost:8103/api/v1/strategies/approval-callback",
                json={
                    "run_id": run_id,
                    "strategy_id": strategy_id,
                    "approved": approved,
                },
                timeout=10.0,
            )
        except Exception as exc:
            logger.warning("通知 decision 端审核结果失败: %s", exc)
