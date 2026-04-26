"""TASK-0018 批次 C — local 自建回测引擎

基于 DataProvider 的逐 bar 成交仿真回测，作为 engine_type=local 的执行路径。

兼容口径：
    - 未传 strategy_yaml_filename 时，继续保留 MockDataProvider + MVP SMA 路径。
    - 传入 strategy_yaml_filename 时，走 API 真数据 + StrategyDefinition / GenericTemplateConfig
        驱动的本地成交回测。

报告产出符合 formal_report_v1 schema（见 shared/contracts/backtest/api.md §6.2.3）。
"""
from __future__ import annotations

import json
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from ..core.settings import get_settings
    from .factor_registry import factor_registry
    from .generic_strategy import GenericTemplateConfig
    from .generic_strategy import _candidate_signal_state
    from .generic_strategy import _evaluate_factor_formula
    from .generic_strategy import _evaluate_market_filter_conditions
    from .generic_strategy import _evaluate_signal_condition
    from .risk_engine import RiskEngine, RiskParams
    from .strategy_base import StrategyConfigError, StrategyDefinition
except ImportError:
    from core.settings import get_settings  # type: ignore[no-redef]
    from factor_registry import factor_registry  # type: ignore[no-redef]
    from generic_strategy import GenericTemplateConfig  # type: ignore[no-redef]
    from generic_strategy import _candidate_signal_state  # type: ignore[no-redef]
    from generic_strategy import _evaluate_factor_formula  # type: ignore[no-redef]
    from generic_strategy import _evaluate_market_filter_conditions  # type: ignore[no-redef]
    from generic_strategy import _evaluate_signal_condition  # type: ignore[no-redef]
    from risk_engine import RiskEngine, RiskParams  # type: ignore[no-redef]
    from strategy_base import StrategyConfigError, StrategyDefinition  # type: ignore[no-redef]


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
    open_interest: float = 0.0


@dataclass(frozen=True)
class LoadedBars:
    """带数据来源元信息的 K 线加载结果。"""

    requested_symbol: str
    resolved_symbol: str
    source_kind: str
    bars: List[Bar]


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

    def load_bars_with_metadata(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 60,
    ) -> LoadedBars:
        bars = self.load_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe_minutes=timeframe_minutes,
        )
        return LoadedBars(
            requested_symbol=symbol,
            resolved_symbol=symbol,
            source_kind="provider",
            bars=bars,
        )


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
                open_interest=0.0,
            ))
            current += step
            i += 1
        return bars

    def load_bars_with_metadata(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 60,
    ) -> LoadedBars:
        return LoadedBars(
            requested_symbol=symbol,
            resolved_symbol=symbol,
            source_kind="mock",
            bars=self.load_bars(symbol, start_date, end_date, timeframe_minutes),
        )


class ApiDataProvider(DataProvider):
    """通过 data 服务 /api/v1/bars 拉取真实 K 线。"""

    def __init__(self, base_url: str, *, timeout_seconds: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def load_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 60,
    ) -> List[Bar]:
        return self.load_bars_with_metadata(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe_minutes=timeframe_minutes,
        ).bars

    def load_bars_with_metadata(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 60,
    ) -> LoadedBars:
        query = urlencode(
            {
                "symbol": symbol,
                "timeframe_minutes": max(1, int(timeframe_minutes)),
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        )
        request = Request(
            f"{self._base_url}/api/v1/bars?{query}",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - exercised via monkeypatched provider in tests.
            raise ValueError(f"failed to fetch bars from data API: {exc}") from exc

        raw_bars = payload.get("bars") or []
        bars: List[Bar] = []
        for index, raw_bar in enumerate(raw_bars):
            if not isinstance(raw_bar, dict):
                raise ValueError(f"data API bars[{index}] must be a mapping")
            try:
                bars.append(
                    Bar(
                        timestamp=_parse_iso_datetime(raw_bar.get("datetime")),
                        open=float(raw_bar.get("open", 0.0)),
                        high=float(raw_bar.get("high", 0.0)),
                        low=float(raw_bar.get("low", 0.0)),
                        close=float(raw_bar.get("close", 0.0)),
                        volume=float(raw_bar.get("volume", 0.0)),
                        open_interest=float(raw_bar.get("open_interest", 0.0) or 0.0),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid bar payload at index {index}: {exc}") from exc

        return LoadedBars(
            requested_symbol=str(payload.get("requested_symbol") or symbol),
            resolved_symbol=str(payload.get("resolved_symbol") or symbol),
            source_kind=str(payload.get("source_kind") or "api"),
            bars=bars,
        )


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
    requested_symbol: Optional[str] = field(default=None)
    strategy_yaml_filename: Optional[str] = field(default=None)
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
            requested_symbol=str(d.get("requested_symbol") or symbols_raw[0]),
            strategy_yaml_filename=(
                str(d.get("strategy_yaml_filename")).strip()
                if d.get("strategy_yaml_filename")
                else None
            ),
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
        self._data_provider = data_provider
        self._mock_data_provider = MockDataProvider()

    def run(self, params: LocalBacktestParams) -> LocalBacktestReport:
        """执行本地回测，返回 LocalBacktestReport。"""
        if params.end_date < params.start_date:
            raise ValueError("end_date must be >= start_date")
        if not params.symbols:
            raise ValueError("symbols must be non-empty")

        requested_symbol = params.requested_symbol or params.symbols[0]
        bar_batch = self._select_provider(params).load_bars_with_metadata(
            symbol=requested_symbol,
            start_date=params.start_date,
            end_date=params.end_date,
            timeframe_minutes=params.timeframe_minutes,
        )

        if not bar_batch.bars:
            raise ValueError("no bars loaded for local backtest window")

        if params.strategy_yaml_filename:
            report = self._run_generic_strategy(params, bar_batch)
        else:
            report = self._run_mvp_strategy(params, bar_batch)

        return report

    def _run_mvp_strategy(
        self,
        params: LocalBacktestParams,
        bar_batch: LoadedBars,
    ) -> LocalBacktestReport:
        equity, trades, risk_events, notes = self._simulate_mvp(bar_batch.bars, params)
        return self._build_report(
            params=params,
            requested_symbol=bar_batch.requested_symbol,
            executed_data_symbol=bar_batch.resolved_symbol,
            source_kind=bar_batch.source_kind,
            bars=bar_batch.bars,
            equity=equity,
            trades=trades,
            risk_events=risk_events,
            notes=notes,
        )

    def _run_generic_strategy(
        self,
        params: LocalBacktestParams,
        bar_batch: LoadedBars,
    ) -> LocalBacktestReport:
        definition = StrategyDefinition.load(self._resolve_strategy_yaml_path(params.strategy_yaml_filename or ""))
        config = GenericTemplateConfig.from_definition(
            definition,
            requested_symbol=bar_batch.requested_symbol,
        )
        bars = bar_batch.bars
        merged_rows = self._build_generic_rows(bars, config)
        equity, trades, risk_events, notes = self._simulate_generic(
            bars=bars,
            merged_rows=merged_rows,
            params=params,
            config=config,
        )
        return self._build_report(
            params=params,
            requested_symbol=bar_batch.requested_symbol,
            executed_data_symbol=bar_batch.resolved_symbol,
            source_kind=bar_batch.source_kind,
            bars=bars,
            equity=equity,
            trades=trades,
            risk_events=risk_events,
            notes=notes,
        )

    def _build_report(
        self,
        *,
        params: LocalBacktestParams,
        requested_symbol: str,
        executed_data_symbol: str,
        source_kind: str,
        bars: List[Bar],
        equity: List[float],
        trades: List[Dict[str, Any]],
        risk_events: List[Dict[str, Any]],
        notes: List[str],
    ) -> LocalBacktestReport:
        final_equity = equity[-1] if equity else params.initial_capital
        pnl = final_equity - params.initial_capital
        max_dd = self._calc_max_drawdown(equity)
        total_trades = len(trades)
        wins = sum(1 for trade in trades if float(trade.get("pnl", 0.0)) > 0.0)
        win_rate = wins / total_trades if total_trades else 0.0
        sharpe = self._calc_sharpe(equity)
        total_cost = sum(float(trade.get("total_cost", 0.0)) for trade in trades)

        peak_eq = params.initial_capital
        equity_curve_data: List[Dict[str, Any]] = []
        for bar, eq_val in zip(bars, equity):
            if eq_val > peak_eq:
                peak_eq = eq_val
            drawdown = (peak_eq - eq_val) / peak_eq if peak_eq > 0.0 else 0.0
            equity_curve_data.append(
                {
                    "bar_time": bar.timestamp.isoformat(),
                    "equity": round(eq_val, 2),
                    "drawdown": round(drawdown, 6),
                }
            )

        now_str = datetime.now(tz=timezone.utc).isoformat()
        return LocalBacktestReport(
            schema_version="formal_report_v1",
            report_id=f"rpt-{uuid.uuid4().hex[:12]}",
            generated_at=now_str,
            job={
                "job_id": params.job_id,
                "engine_type": "local",
                "strategy_id": params.strategy_id,
                "symbol": requested_symbol,
                "requested_symbol": requested_symbol,
                "executed_data_symbol": executed_data_symbol,
                "source_kind": source_kind,
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
                "trades": trades,
                "positions": None,
            },
            notes=notes,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _simulate_mvp(
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
            return [params.initial_capital for _ in bars] or [params.initial_capital], trades, [], notes

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
                    "side": "long",
                    "quantity": 1,
                    "entry_price": round(entry_price, 4),
                    "exit_price": round(fill_price, 4),
                    "entry_time": bars[i - 1].timestamp.isoformat() if i > 0 else bar.timestamp.isoformat(),
                    "exit_time": bar.timestamp.isoformat(),
                    "pnl": round(net_pnl, 2),
                    "close_time": bar.timestamp.isoformat(),
                    "exit_reason": "signal_flip",
                    "total_cost": round(params.commission_per_lot_round_turn + params.slippage_per_unit * 2.0, 2),
                })
                position = 0
                entry_price = 0.0

            # 按市价计算当前权益（持仓时按 close 浮动盈亏）
            mark_equity = capital + (bar.close - entry_price if position == 1 else 0.0)
            equity_curve.append(mark_equity)
            risk_engine.check(bar.timestamp, mark_equity)

        # 收盘若仍有持仓则按最后一根 bar 强平（MVP 简化）
        if position == 1 and bars:
            last_bar = bars[-1]
            fill_price = last_bar.close - params.slippage_per_unit
            net_pnl = fill_price - entry_price - params.commission_per_lot_round_turn / 2.0
            capital += net_pnl
            trades.append({
                "side": "long",
                "quantity": 1,
                "entry_price": round(entry_price, 4),
                "exit_price": round(fill_price, 4),
                "entry_time": bars[-2].timestamp.isoformat() if len(bars) > 1 else last_bar.timestamp.isoformat(),
                "exit_time": last_bar.timestamp.isoformat(),
                "pnl": round(net_pnl, 2),
                "close_time": last_bar.timestamp.isoformat(),
                "note": "forced_close_at_end",
                "exit_reason": "end_of_backtest",
                "total_cost": round(params.commission_per_lot_round_turn + params.slippage_per_unit * 2.0, 2),
            })
            if equity_curve:
                equity_curve[-1] = capital

        return equity_curve, trades, risk_engine.risk_events, notes

    def _simulate_generic(
        self,
        *,
        bars: List[Bar],
        merged_rows: List[Dict[str, Any]],
        params: LocalBacktestParams,
        config: GenericTemplateConfig,
    ) -> Tuple[List[float], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        notes: List[str] = [
            "local_engine=generic_yaml",
            f"strategy_yaml_filename={params.strategy_yaml_filename}",
        ]
        warmup_bars = self._required_bar_count(config)
        if len(bars) < warmup_bars + 1:
            notes.append("insufficient_bars_for_generic_strategy")
            return [params.initial_capital for _ in bars] or [params.initial_capital], [], [], notes

        signal_states = self._build_signal_states(merged_rows, config)
        risk_engine = RiskEngine(
            job_id=params.job_id,
            initial_capital=params.initial_capital,
            params=RiskParams(
                max_drawdown=config.max_drawdown if config.max_drawdown is not None else params.max_drawdown,
                daily_loss_limit=config.daily_loss_limit if config.daily_loss_limit is not None else params.daily_loss_limit,
            ),
        )

        capital = params.initial_capital
        equity_curve: List[float] = []
        trades: List[Dict[str, Any]] = []
        market_filter_passes = 0
        total_bar_evals = 0
        position: Dict[str, Any] = {
            "side": "flat",
            "quantity": 0,
            "entry_price": 0.0,
            "entry_time": None,
            "entry_date": None,
        }

        for index, bar in enumerate(bars):
            if index == 0 or index < warmup_bars:
                mark_equity = self._mark_equity(capital, position, bar.close, config.contract_size)
                equity_curve.append(mark_equity)
                risk_engine.check(bar.timestamp, mark_equity)
                continue

            signal_row = merged_rows[index - 1]
            desired_state = signal_states[index - 1]
            if signal_row.get("market_filter_passed"):
                market_filter_passes += 1
            total_bar_evals += 1

            entered_this_bar = False
            skip_open = self._is_force_close_bar(bar.timestamp, config)

            if position["side"] != "flat" and skip_open:
                capital = self._close_position(
                    capital=capital,
                    position=position,
                    exit_price=self._fill_price(bar.open, "sell" if position["side"] == "long" else "buy", params.slippage_per_unit, config.price_tick),
                    exit_time=bar.timestamp,
                    exit_reason=self._force_close_reason(bar.timestamp, config),
                    contract_size=config.contract_size,
                    commission_per_lot_round_turn=params.commission_per_lot_round_turn,
                    trades=trades,
                )

            if position["side"] != "flat" and not skip_open:
                if config.no_overnight and position.get("entry_date") is not None and bar.timestamp.date() != position["entry_date"]:
                    capital = self._close_position(
                        capital=capital,
                        position=position,
                        exit_price=self._fill_price(bar.open, "sell" if position["side"] == "long" else "buy", params.slippage_per_unit, config.price_tick),
                        exit_time=bar.timestamp,
                        exit_reason="no_overnight",
                        contract_size=config.contract_size,
                        commission_per_lot_round_turn=params.commission_per_lot_round_turn,
                        trades=trades,
                    )
                    skip_open = True
                elif desired_state != position["side"]:
                    capital = self._close_position(
                        capital=capital,
                        position=position,
                        exit_price=self._fill_price(bar.open, "sell" if position["side"] == "long" else "buy", params.slippage_per_unit, config.price_tick),
                        exit_time=bar.timestamp,
                        exit_reason="signal_flip" if desired_state in {"long", "short"} else "signal_flat",
                        contract_size=config.contract_size,
                        commission_per_lot_round_turn=params.commission_per_lot_round_turn,
                        trades=trades,
                    )

            if position["side"] == "flat" and not skip_open and desired_state in {"long", "short"} and risk_engine.open_allowed:
                quantity = self._resolve_quantity(config, params.initial_capital, bar.open)
                if quantity > 0:
                    position["side"] = desired_state
                    position["quantity"] = quantity
                    position["entry_price"] = self._fill_price(
                        bar.open,
                        "buy" if desired_state == "long" else "sell",
                        params.slippage_per_unit,
                        config.price_tick,
                    )
                    position["entry_time"] = bar.timestamp.isoformat()
                    position["entry_date"] = bar.timestamp.date()
                    entry_commission = quantity * params.commission_per_lot_round_turn / 2.0
                    position["entry_commission"] = round(entry_commission, 2)
                    capital -= entry_commission
                    entered_this_bar = True

            if position["side"] != "flat" and not entered_this_bar:
                atr_value = _optional_float(signal_row.get("atr"))
                intrabar_exit = self._intrabar_exit(
                    position_side=str(position["side"]),
                    entry_price=float(position["entry_price"]),
                    quantity=int(position["quantity"]),
                    atr_value=atr_value,
                    bar=bar,
                    config=config,
                    slippage_per_unit=params.slippage_per_unit,
                )
                if intrabar_exit is not None:
                    capital = self._close_position(
                        capital=capital,
                        position=position,
                        exit_price=intrabar_exit[0],
                        exit_time=bar.timestamp,
                        exit_reason=intrabar_exit[1],
                        contract_size=config.contract_size,
                        commission_per_lot_round_turn=params.commission_per_lot_round_turn,
                        trades=trades,
                    )

            mark_equity = self._mark_equity(capital, position, bar.close, config.contract_size)
            equity_curve.append(mark_equity)
            risk_engine.check(bar.timestamp, mark_equity)

        if position["side"] != "flat" and bars:
            last_bar = bars[-1]
            capital = self._close_position(
                capital=capital,
                position=position,
                exit_price=self._fill_price(last_bar.close, "sell" if position["side"] == "long" else "buy", params.slippage_per_unit, config.price_tick),
                exit_time=last_bar.timestamp,
                exit_reason="end_of_backtest",
                contract_size=config.contract_size,
                commission_per_lot_round_turn=params.commission_per_lot_round_turn,
                trades=trades,
            )
            if equity_curve:
                equity_curve[-1] = capital

        if total_bar_evals > 0:
            notes.append(
                f"market_filter_pass_rate={market_filter_passes}/{total_bar_evals}"
                f"({round(market_filter_passes * 100 / total_bar_evals)}%)"
            )
        return equity_curve, trades, risk_engine.risk_events, notes

    def _build_generic_rows(
        self,
        bars: List[Bar],
        config: GenericTemplateConfig,
    ) -> List[Dict[str, Any]]:
        base_rows = [
            {
                "timestamp": bar.timestamp,
                "datetime": bar.timestamp.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "open_interest": bar.open_interest,
            }
            for bar in bars
        ]
        merged_rows = [dict(row) for row in base_rows]

        for indicator in config.indicators:
            result = factor_registry.calculate(indicator.indicator_type, base_rows, indicator.params)
            for row, indicator_row in zip(merged_rows, result.rows):
                row[indicator.name] = indicator_row.get(indicator.primary_output)
                for key, value in indicator_row.items():
                    if key != "timestamp":
                        row[key] = value

        for row in merged_rows:
            factor_scores: List[float] = []
            weighted_scores: List[float] = []
            factor_map: Dict[str, float] = {}
            environment = dict(row)
            for factor in config.factors:
                if not factor.formula:
                    continue
                value = _evaluate_factor_formula(factor, environment)
                factor_map[factor.factor_name] = value
                factor_scores.append(value)
                weighted_scores.append(value * factor.weight)
                row[factor.factor_name] = value
                environment[factor.factor_name] = value
            row["factor_map"] = factor_map
            row["factor_scores"] = factor_scores
            row["weighted_factor_scores"] = weighted_scores
            row["factor_total_score"] = sum(weighted_scores)
            signal_environment = dict(environment)
            signal_environment["factor_map"] = factor_map
            signal_environment["factor_scores"] = factor_scores
            signal_environment["weighted_factor_scores"] = weighted_scores
            signal_environment["factor_total_score"] = row["factor_total_score"]
            market_filter_passed = _evaluate_market_filter_conditions(
                config.market_filter_conditions,
                signal_environment,
            )
            row["market_filter_passed"] = market_filter_passed
            row["long_signal_candidate"] = _evaluate_signal_condition(
                config.long_condition,
                signal_environment,
            ) and market_filter_passed
            row["short_signal_candidate"] = _evaluate_signal_condition(
                config.short_condition,
                signal_environment,
            ) and market_filter_passed

        return merged_rows

    def _build_signal_states(
        self,
        merged_rows: List[Dict[str, Any]],
        config: GenericTemplateConfig,
    ) -> List[str]:
        states = [_candidate_signal_state(row) for row in merged_rows]
        resolved: List[str] = []
        for index in range(len(states)):
            recent = states[max(0, index - config.confirm_bars + 1) : index + 1]
            if len(recent) < config.confirm_bars:
                resolved.append("flat")
                continue
            if recent[-1] in {"long", "short"} and all(state == recent[-1] for state in recent):
                resolved.append(recent[-1])
            else:
                resolved.append("flat")
        return resolved

    def _required_bar_count(self, config: GenericTemplateConfig) -> int:
        max_period = max((indicator.period_hint for indicator in config.indicators), default=10)
        return max(80, max_period * 4, config.confirm_bars + 10)

    def _resolve_quantity(
        self,
        config: GenericTemplateConfig,
        initial_capital: float,
        reference_price: float,
    ) -> int:
        if config.position_method == "fixed_lots" and config.fixed_lots is not None:
            return max(1, int(config.fixed_lots))
        denominator = max(reference_price * config.contract_size, 1.0)
        raw_quantity = (initial_capital * config.position_ratio) / denominator
        return max(1, int(round(raw_quantity)))

    def _intrabar_exit(
        self,
        *,
        position_side: str,
        entry_price: float,
        quantity: int,
        atr_value: Optional[float],
        bar: Bar,
        config: GenericTemplateConfig,
        slippage_per_unit: float,
    ) -> Optional[Tuple[float, str]]:
        if atr_value is None or atr_value <= 0:
            return None
        if position_side == "long":
            if config.stop_loss_atr is not None:
                stop_price = entry_price - atr_value * config.stop_loss_atr
                if bar.low <= stop_price:
                    return self._fill_price(stop_price, "sell", slippage_per_unit, config.price_tick), "stop_loss_atr"
            if config.take_profit_atr is not None:
                take_price = entry_price + atr_value * config.take_profit_atr
                if bar.high >= take_price:
                    return self._fill_price(take_price, "sell", slippage_per_unit, config.price_tick), "take_profit_atr"
            return None

        if config.stop_loss_atr is not None:
            stop_price = entry_price + atr_value * config.stop_loss_atr
            if bar.high >= stop_price:
                return self._fill_price(stop_price, "buy", slippage_per_unit, config.price_tick), "stop_loss_atr"
        if config.take_profit_atr is not None:
            take_price = entry_price - atr_value * config.take_profit_atr
            if bar.low <= take_price:
                return self._fill_price(take_price, "buy", slippage_per_unit, config.price_tick), "take_profit_atr"
        return None

    def _close_position(
        self,
        *,
        capital: float,
        position: Dict[str, Any],
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
        contract_size: float,
        commission_per_lot_round_turn: float,
        trades: List[Dict[str, Any]],
    ) -> float:
        quantity = int(position.get("quantity") or 0)
        if quantity <= 0 or position.get("side") == "flat":
            return capital
        entry_price = float(position.get("entry_price") or 0.0)
        side = str(position.get("side") or "flat")
        direction = 1.0 if side == "long" else -1.0
        gross_pnl = (exit_price - entry_price) * direction * quantity * contract_size
        exit_commission = quantity * commission_per_lot_round_turn / 2.0
        net_pnl = gross_pnl - exit_commission
        capital += net_pnl
        total_cost = float(position.get("entry_commission") or 0.0) + exit_commission
        trades.append(
            {
                "side": side,
                "quantity": quantity,
                "entry_price": round(entry_price, 4),
                "exit_price": round(exit_price, 4),
                "entry_time": position.get("entry_time"),
                "exit_time": exit_time.isoformat(),
                "close_time": exit_time.isoformat(),
                "pnl": round(net_pnl, 2),
                "gross_pnl": round(gross_pnl, 2),
                "exit_reason": exit_reason,
                "total_cost": round(total_cost, 2),
            }
        )
        position["side"] = "flat"
        position["quantity"] = 0
        position["entry_price"] = 0.0
        position["entry_time"] = None
        position["entry_date"] = None
        position["entry_commission"] = 0.0
        return capital

    def _mark_equity(
        self,
        capital: float,
        position: Dict[str, Any],
        reference_price: float,
        contract_size: float,
    ) -> float:
        if position.get("side") == "flat" or int(position.get("quantity") or 0) <= 0:
            return capital
        quantity = int(position.get("quantity") or 0)
        entry_price = float(position.get("entry_price") or 0.0)
        side = str(position.get("side") or "flat")
        direction = 1.0 if side == "long" else -1.0
        unrealized = (reference_price - entry_price) * direction * quantity * contract_size
        return capital + unrealized

    def _fill_price(
        self,
        price: float,
        side: str,
        slippage_per_unit: float,
        price_tick: float,
    ) -> float:
        adjusted = price + slippage_per_unit if side == "buy" else max(price - slippage_per_unit, 0.0)
        return _round_to_tick(adjusted, price_tick)

    def _is_force_close_bar(self, timestamp: datetime, config: GenericTemplateConfig) -> bool:
        cutoff = self._force_close_cutoff(timestamp, config)
        if cutoff is None:
            return False
        return _local_time(timestamp) >= cutoff

    def _force_close_reason(self, timestamp: datetime, config: GenericTemplateConfig) -> str:
        return "force_close_night" if _local_time(timestamp).hour >= 20 else "force_close_day"

    def _force_close_cutoff(self, timestamp: datetime, config: GenericTemplateConfig) -> Optional[datetime.time]:
        return config.force_close_night if _local_time(timestamp).hour >= 20 else config.force_close_day

    def _resolve_strategy_yaml_path(self, strategy_yaml_filename: str) -> Path:
        settings = get_settings()
        strategy_root = settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
        candidate = (strategy_root / strategy_yaml_filename).resolve()
        if strategy_root not in candidate.parents:
            raise ValueError("strategy_yaml_filename must stay within TQSDK_STRATEGY_YAML_DIR")
        if not candidate.exists():
            raise ValueError(f"strategy YAML not found: {strategy_yaml_filename}")
        return candidate

    def _select_provider(self, params: LocalBacktestParams) -> DataProvider:
        if params.strategy_yaml_filename:
            return self._data_provider or self._mock_data_provider
        return self._mock_data_provider

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


def _parse_iso_datetime(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("bar datetime must be a non-empty ISO string")
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _optional_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _local_time(timestamp: datetime) -> datetime.time:
    if timestamp.tzinfo is None:
        return timestamp.time()
    return timestamp.astimezone(timezone.utc).timetz().replace(tzinfo=None)


def _round_to_tick(value: float, price_tick: float) -> float:
    if price_tick <= 0:
        return round(value, 4)
    scaled = round(value / price_tick) * price_tick
    return round(scaled, 6)
