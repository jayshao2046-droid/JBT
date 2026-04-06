"""TASK-0018 批次 C — local 自建回测引擎

基于本地数据源的逐 bar 撮合仿真回测，作为 engine_type=local 的核心执行路径。

数据供给通过 DataProvider 协议抽象：
  - MVP 阶段使用 MockDataProvider（内嵌正弦波 OHLCV，无需外部文件）。
  - 批次 B / D 可替换为 HDF5Provider 或 ApiDataProvider，无需修改引擎核心逻辑。

报告产出符合合约 formal_report_v1 schema（见 shared/contracts/backtest/api.md §6.2.3）。
"""
from __future__ import annotations

import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from .risk_engine import RiskEngine, RiskParams
except ImportError:
    from risk_engine import RiskEngine, RiskParams  # type: ignore[no-redef]


# ─────────────────────────────────────────────────────────────────────────────
# DataProvider 抽象（预留接口，用于批次 B 对接）
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Bar:
    """单根 K 线（时间升序）。"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class DataProvider(ABC):
    """
    数据供给接口抽象，隔离实际数据源（本地 HDF5、内存 mock、或 data-service API）。

    实现者必须保证返回列表按 timestamp 升序排列。
    """

    @abstractmethod
    def load_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 60,
    ) -> List[Bar]:
        """返回指定区间内的 K 线列表（按时间升序）。"""
        raise NotImplementedError


class MockDataProvider(DataProvider):
    """
    MVP 内嵌 mock 数据源：用正弦波生成 OHLCV，无需外部文件。

    生成规则：
      - 基准价格 = 10000.0
      - 价格振荡 += 300 * sin(i * 0.05)
      - 振幅与成交量用辅助正弦函数注入随机感
    """

    def load_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 60,
    ) -> List[Bar]:
        bars: List[Bar] = []
        current = datetime(
            start_date.year, start_date.month, start_date.day,
            9, 0, 0, tzinfo=timezone.utc,
        )
        end_dt = datetime(
            end_date.year, end_date.month, end_date.day,
            15, 0, 0, tzinfo=timezone.utc,
        )
        step = timedelta(minutes=max(1, timeframe_minutes))
        base_price = 10000.0
        i = 0
        while current < end_dt:
            mid = base_price + 300.0 * math.sin(i * 0.05)
            amplitude = abs(50.0 * math.sin(i * 0.3 + 1.0))
            open_ = mid + amplitude * math.cos(i * 0.17)
            close = mid + 20.0 * math.cos(i * 0.07)
            high = max(open_, close) + amplitude
            low = min(open_, close) - amplitude
            volume = 1000.0 + 500.0 * abs(math.sin(i * 0.1))
            bars.append(Bar(
                timestamp=current,
                open=round(open_, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close, 2),
                volume=round(volume, 2),
            ))
            current += step
            i += 1
        return bars


# ─────────────────────────────────────────────────────────────────────────────
# 任务参数
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LocalBacktestParams:
    """local 引擎任务参数（最小集合：symbols / start_date / end_date / initial_capital）。"""
    job_id: str
    symbols: List[str]
    start_date: date
    end_date: date
    initial_capital: float
    timeframe_minutes: int = field(default=60)
    slippage_per_unit: float = field(default=0.0)
    commission_per_lot_round_turn: float = field(default=0.0)
    strategy_id: str = field(default="unknown")
    max_drawdown: float = field(default=1.0)
    """最大回撤风控上限（比例）。>= 1.0 表示禁用。"""
    daily_loss_limit: float = field(default=1.0)
    """日亏损风控上限（相对初始资金比例）。>= 1.0 表示禁用。"""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LocalBacktestParams":
        def _coerce_date(v: Any, label: str) -> date:
            if isinstance(v, date):
                return v
            if isinstance(v, str):
                return date.fromisoformat(v)
            raise ValueError(f"{label} must be a date or ISO date string")

        symbols_raw = d.get("symbols") or []
        if isinstance(symbols_raw, str):
            symbols_raw = [symbols_raw]
        symbols_raw = list(symbols_raw)
        if not symbols_raw:
            raise ValueError("symbols must be a non-empty list")

        return cls(
            job_id=str(d.get("job_id") or uuid.uuid4()),
            symbols=symbols_raw,
            start_date=_coerce_date(d.get("start_date"), "start_date"),
            end_date=_coerce_date(d.get("end_date"), "end_date"),
            initial_capital=float(d.get("initial_capital", 1_000_000.0)),
            timeframe_minutes=int(d.get("timeframe_minutes", 60)),
            slippage_per_unit=float(d.get("slippage_per_unit", 0.0)),
            commission_per_lot_round_turn=float(d.get("commission_per_lot_round_turn", 0.0)),
            strategy_id=str(d.get("strategy_id") or "unknown"),
            max_drawdown=float(d.get("max_drawdown", 1.0)),
            daily_loss_limit=float(d.get("daily_loss_limit", 1.0)),
        )


# ─────────────────────────────────────────────────────────────────────────────
# 报告对象（formal_report_v1 语义）
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LocalBacktestReport:
    """
    符合 formal_report_v1 schema 的本地回测报告对象。
    字段定义见 shared/contracts/backtest/api.md §6.2.3。
    """
    schema_version: str
    report_id: str
    generated_at: str
    job: Dict[str, Any]
    summary: Dict[str, Any]
    transaction_costs: Dict[str, Any]
    risk_events: List[Dict[str, Any]]
    artifacts: Dict[str, Any]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "job": self.job,
            "summary": self.summary,
            "transaction_costs": self.transaction_costs,
            "risk_events": self.risk_events,
            "artifacts": self.artifacts,
            "notes": self.notes,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 最小撮合引擎
# ─────────────────────────────────────────────────────────────────────────────

class LocalBacktestEngine:
    """
    local 引擎：基于本地数据源（DataProvider）的逐 bar 撮合仿真。

    MVP 策略：EMA(5) 上穿 EMA(20) 开多，下穿平仓（一次只持 1 手）。
    数据源通过 DataProvider 协议抽象，默认使用 MockDataProvider。
    报告产出符合 formal_report_v1 schema。
    """

    def __init__(self, data_provider: Optional[DataProvider] = None) -> None:
        self._data_provider = data_provider or MockDataProvider()

    def run(self, params: LocalBacktestParams) -> LocalBacktestReport:
        """执行本地回测，返回 LocalBacktestReport。"""
        if params.end_date < params.start_date:
            raise ValueError("end_date must be >= start_date")
        if not params.symbols:
            raise ValueError("symbols must be non-empty")

        symbol = params.symbols[0]
        bars = self._data_provider.load_bars(
            symbol=symbol,
            start_date=params.start_date,
            end_date=params.end_date,
            timeframe_minutes=params.timeframe_minutes,
        )

        equity, trades, risk_events, notes = self._simulate(bars, params)

        final_equity = equity[-1] if equity else params.initial_capital
        pnl = final_equity - params.initial_capital
        max_dd = self._calc_max_drawdown(equity)
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get("pnl", 0.0) > 0)
        win_rate = wins / total_trades if total_trades else 0.0
        sharpe = self._calc_sharpe(equity)
        total_cost = sum(
            params.commission_per_lot_round_turn + params.slippage_per_unit * 2.0
            for _ in trades
        )

        # 序列化 equity_curve（符合 formal_report_v1 §6.2.3）
        peak_eq = params.initial_capital
        equity_curve_data: List[Dict[str, Any]] = []
        for bar, eq_val in zip(bars, equity):
            if eq_val > peak_eq:
                peak_eq = eq_val
            dd = (peak_eq - eq_val) / peak_eq if peak_eq > 0.0 else 0.0
            equity_curve_data.append({
                "bar_time": bar.timestamp.isoformat(),
                "equity": round(eq_val, 2),
                "drawdown": round(dd, 6),
            })

        now_str = datetime.now(tz=timezone.utc).isoformat()
        return LocalBacktestReport(
            schema_version="formal_report_v1",
            report_id=f"rpt-{uuid.uuid4().hex[:12]}",
            generated_at=now_str,
            job={
                "job_id": params.job_id,
                "engine_type": "local",
                "strategy_id": params.strategy_id,
                "symbol": symbol,
                "timeframe": f"{params.timeframe_minutes}m",
                "start_date": params.start_date.isoformat(),
                "end_date": params.end_date.isoformat(),
                "initial_capital": params.initial_capital,
            },
            summary={
                "status": "completed",
                "total_trades": total_trades,
                "final_equity": round(final_equity, 2),
                "max_drawdown": round(max_dd, 6),
                "pnl": round(pnl, 2),
                "win_rate": round(win_rate, 4),
                "sharpe": round(sharpe, 4),
            },
            transaction_costs={
                "slippage_per_unit": params.slippage_per_unit,
                "commission_per_lot_round_turn": params.commission_per_lot_round_turn,
                "total_cost": round(total_cost, 2),
            },
            risk_events=risk_events,
            artifacts={
                "equity_curve": equity_curve_data,
                "trades": None,
                "positions": None,
            },
            notes=notes,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _simulate(
        self,
        bars: List[Bar],
        params: LocalBacktestParams,
    ) -> Tuple[List[float], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """
        MVP 最小撮合：EMA(5) 上穿 EMA(20) 开多，下穿平仓。
        使用简单移动平均近似 EMA（MVP 阶段已满足闭环验收）。
        """
        equity_curve: List[float] = []
        trades: List[Dict[str, Any]] = []
        notes: List[str] = [
            "local_engine=MVP",
            "strategy=sma_crossover(fast=5,slow=20)",
        ]

        short_w = 5
        long_w = 20

        if len(bars) < long_w + 1:
            notes.append("insufficient_bars_for_crossover")
            return [params.initial_capital], trades, [], notes

        risk_engine = RiskEngine(
            job_id=params.job_id,
            initial_capital=params.initial_capital,
            params=RiskParams(
                max_drawdown=params.max_drawdown,
                daily_loss_limit=params.daily_loss_limit,
            ),
        )

        capital = params.initial_capital
        position = 0       # +1=多头持仓, 0=空仓
        entry_price = 0.0
        peak_equity = capital

        for i, bar in enumerate(bars):
            if i < long_w:
                equity_curve.append(capital)
                risk_engine.check(bar.timestamp, capital)
                continue

            # 当前 bar 与前一根 bar 的均线
            short_now = sum(b.close for b in bars[i - short_w + 1: i + 1]) / short_w
            long_now = sum(b.close for b in bars[i - long_w + 1: i + 1]) / long_w
            short_prev = sum(b.close for b in bars[i - short_w: i]) / short_w
            long_prev = sum(b.close for b in bars[i - long_w: i]) / long_w

            cross_up = (short_prev <= long_prev) and (short_now > long_now)
            cross_dn = (short_prev >= long_prev) and (short_now < long_now)

            if position == 0 and cross_up and risk_engine.open_allowed:
                # 开多：收盘价 + 滑点（仅风控未触发时允许开仓）
                fill_price = bar.close + params.slippage_per_unit
                entry_price = fill_price
                position = 1
                capital -= params.commission_per_lot_round_turn / 2.0

            elif position == 1 and cross_dn:
                # 平多：收盘价 - 滑点
                fill_price = bar.close - params.slippage_per_unit
                gross_pnl = fill_price - entry_price
                net_pnl = gross_pnl - params.commission_per_lot_round_turn / 2.0
                capital += net_pnl
                trades.append({
                    "entry_price": round(entry_price, 4),
                    "exit_price": round(fill_price, 4),
                    "pnl": round(net_pnl, 2),
                    "close_time": bar.timestamp.isoformat(),
                })
                position = 0
                entry_price = 0.0

            # 按市价计算当前权益（持仓时按 close 浮动盈亏）
            mark_equity = capital + (bar.close - entry_price if position == 1 else 0.0)
            if mark_equity > peak_equity:
                peak_equity = mark_equity
            equity_curve.append(mark_equity)
            risk_engine.check(bar.timestamp, mark_equity)

        # 收盘若仍有持仓则按最后一根 bar 强平（MVP 简化）
        if position == 1 and bars:
            last_bar = bars[-1]
            fill_price = last_bar.close - params.slippage_per_unit
            net_pnl = fill_price - entry_price - params.commission_per_lot_round_turn / 2.0
            capital += net_pnl
            trades.append({
                "entry_price": round(entry_price, 4),
                "exit_price": round(fill_price, 4),
                "pnl": round(net_pnl, 2),
                "close_time": last_bar.timestamp.isoformat(),
                "note": "forced_close_at_end",
            })
            if equity_curve:
                equity_curve[-1] = capital

        return equity_curve, trades, risk_engine.risk_events, notes

    @staticmethod
    def _calc_max_drawdown(equity: List[float]) -> float:
        peak = -math.inf
        max_dd = 0.0
        for v in equity:
            if v > peak:
                peak = v
            if peak > 0:
                dd = (peak - v) / peak
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    @staticmethod
    def _calc_sharpe(equity: List[float]) -> float:
        if len(equity) < 2:
            return 0.0
        returns = []
        for i in range(1, len(equity)):
            prev = equity[i - 1]
            if prev > 0:
                returns.append((equity[i] - prev) / prev)
        if not returns:
            return 0.0
        n = len(returns)
        mean_r = sum(returns) / n
        variance = sum((r - mean_r) ** 2 for r in returns) / max(n - 1, 1)
        std_r = math.sqrt(variance)
        if std_r == 0.0:
            return 0.0
        # 年化（假设每个 bar 约为 1 个交易时段单位）
        return round(mean_r / std_r * math.sqrt(252), 4)
