from __future__ import annotations

import asyncio
import logging
import threading
import traceback
from datetime import date, datetime, timedelta
from math import isfinite, sqrt
from typing import Any, Optional
from uuid import uuid4

_logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

if __package__:
    from ...backtest.engine_router import EngineRouter
    from ...backtest.engine_router import EngineTypeError
    from ...backtest.local_engine import ApiDataProvider
    from ...backtest.local_engine import LocalBacktestEngine
    from ...backtest.local_engine import LocalBacktestParams
    from ...backtest.local_engine import LocalBacktestReport
    from ...backtest.runner import BacktestJobInput
    from ...backtest.runner import OnlineBacktestRunner
    from ...backtest.result_builder import BacktestReport
    from ...core.settings import get_settings
    from .support import ACTIVE_STATUSES
    from .support import append_event_log
    from .support import append_system_log
    from .support import build_strategy_execution_profile
    from .support import build_result_summary
    from .support import get_compat_state
    from .support import get_strategy_record
    from .support import latest_result_for_strategy
    from .support import list_results_sorted
    from .support import normalize_contract_symbol
    from .support import resolve_result_report_file
else:
    from backtest.engine_router import EngineRouter
    from backtest.engine_router import EngineTypeError
    from backtest.local_engine import ApiDataProvider
    from backtest.local_engine import LocalBacktestEngine
    from backtest.local_engine import LocalBacktestParams
    from backtest.local_engine import LocalBacktestReport
    from backtest.result_builder import BacktestReport
    from backtest.runner import BacktestJobInput
    from backtest.runner import OnlineBacktestRunner
    from core.settings import get_settings
    from support import ACTIVE_STATUSES
    from support import append_event_log
    from support import append_system_log
    from support import build_strategy_execution_profile
    from support import build_result_summary
    from support import get_compat_state
    from support import get_strategy_record
    from support import latest_result_for_strategy
    from support import list_results_sorted
    from support import normalize_contract_symbol
    from support import resolve_result_report_file

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Serialize background backtest executions — TqSdk does not support
# multiple concurrent API sessions in one process.
_backtest_execution_lock = threading.Lock()
_engine_router = EngineRouter()


class BacktestRunPayload(BaseModel):
    strategy_id: Optional[str] = None
    strategy_name: Optional[str] = None
    name: Optional[str] = None
    engine_type: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    symbols: list[str] = Field(default_factory=list)
    contract: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    initialCapital: Optional[float] = None
    initial_capital: Optional[float] = None
    slippage_per_unit: Optional[float] = None
    commission_per_lot_round_turn: Optional[float] = None


class BacktestAdjustPayload(BaseModel):
    task_id: Optional[str] = None
    id: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    start: Optional[str] = None
    end: Optional[str] = None
    symbols: list[str] = Field(default_factory=list)


class BatchDeletePayload(BaseModel):
    ids: list[str] = Field(default_factory=list)


def _now_ts() -> int:
    return int(datetime.now().timestamp())


def _parse_date(value: Optional[str], fallback: date) -> date:
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return fallback


def _resolve_strategy_name(payload: BacktestRunPayload) -> str:
    for value in (payload.strategy_id, payload.strategy_name, payload.name):
        if value and value.strip():
            return value.strip()
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="strategy_id is required")


def _resolve_initial_capital(
    payload: BacktestRunPayload,
    strategy_record: Optional[dict[str, Any]] = None,
) -> float:
    for value in (payload.initialCapital, payload.initial_capital):
        if value is not None:
            return float(value)
    if strategy_record is not None:
        capital_params = strategy_record.get("capital_params", {})
        if not isinstance(capital_params, dict):
            capital_params = {}
        initial_capital = capital_params.get("initial_capital")
        if initial_capital is not None:
            return float(initial_capital)
    return 500000.0


def _compat_seed(text: str) -> int:
    return max(1, sum(ord(char) for char in text))


def _result_or_404(state: dict[str, Any], task_id: str) -> dict[str, Any]:
    result = state["results"].get(task_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest result not found")
    return result


def _require_strategy_record(state: dict[str, Any], strategy_name: str) -> dict[str, Any]:
    strategy_record = get_strategy_record(state, strategy_name)
    if strategy_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_name} not found. Please import the strategy YAML first.",
        )
    return strategy_record


def _derive_symbols(
    payload: BacktestRunPayload,
    strategy_record: Optional[dict[str, Any]],
) -> list[str]:
    symbols = [symbol for symbol in payload.symbols if symbol]
    if payload.contract:
        symbols.insert(0, payload.contract)
    if not symbols and strategy_record is not None:
        symbols.extend(strategy_record.get("symbols", []))
    if not symbols:
        symbols.append("SHFE.rb2505")

    deduped: list[str] = []
    seen = set()
    for symbol in symbols:
        normalized_symbol = normalize_contract_symbol(symbol)
        if normalized_symbol not in seen:
            seen.add(normalized_symbol)
            deduped.append(normalized_symbol)
    return deduped


def _build_result_execution_profile(strategy_record: Optional[dict[str, Any]]) -> dict[str, Any]:
    base_profile = build_strategy_execution_profile(strategy_record or {})
    executed_reason = "当前 /api/backtest/* 结果仍由兼容层路由生成，未直接调用 services/backtest/src/backtest/runner.py 正式引擎。"
    return {
        **base_profile,
        "executed_mode": "compatibility_preview",
        "executed_label": "兼容预览",
        "executed_formal": False,
        "can_execute_formal": bool(base_profile.get("formal_supported")),
        "executed_reason": executed_reason,
        "evidence": [
            executed_reason,
            *list(base_profile.get("evidence", [])),
        ],
    }


def _build_submitted_tqsdk_execution_profile(strategy_record: Optional[dict[str, Any]]) -> dict[str, Any]:
    base_profile = build_strategy_execution_profile(strategy_record or {})
    executed_reason = "当前任务已提交到 TqSdk 正式引擎，正在异步执行。"
    return {
        **base_profile,
        "engine_type": "tqsdk",
        "executed_mode": "tqsdk",
        "executed_label": "TqSdk 在线回测",
        "executed_formal": True,
        "can_execute_formal": True,
        "executed_reason": executed_reason,
        "evidence": [
            executed_reason,
            *list(base_profile.get("evidence", [])),
        ],
    }


def _coerce_timeframe_minutes(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        minutes = int(value)
        return minutes if minutes > 0 else None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return None
        multiplier = 1
        if normalized.endswith("m"):
            normalized = normalized[:-1].strip()
        elif normalized.endswith("h"):
            normalized = normalized[:-1].strip()
            multiplier = 60
        elif normalized.endswith("d"):
            normalized = normalized[:-1].strip()
            multiplier = 1440
        if normalized.isdigit():
            minutes = int(normalized) * multiplier
            return minutes if minutes > 0 else None
    return None


def _resolve_local_timeframe_minutes(
    payload: BacktestRunPayload,
    strategy_record: dict[str, Any],
) -> int:
    strategy_params = strategy_record.get("params", {})
    if not isinstance(strategy_params, dict):
        strategy_params = {}
    strategy_payload = strategy_record.get("strategy", {})
    if not isinstance(strategy_payload, dict):
        strategy_payload = {}

    candidates = [
        payload.params.get("timeframe_minutes"),
        payload.params.get("timeframe"),
        strategy_params.get("timeframe_minutes"),
        strategy_params.get("timeframe"),
        strategy_payload.get("timeframe_minutes"),
        strategy_payload.get("timeframe"),
    ]
    for candidate in candidates:
        timeframe_minutes = _coerce_timeframe_minutes(candidate)
        if timeframe_minutes is not None:
            return timeframe_minutes
    return 60


def _resolve_runtime_cost(
    explicit_value: Optional[float],
    strategy_record: dict[str, Any],
    *keys: str,
) -> float:
    if explicit_value is not None:
        return float(explicit_value)

    for section_name in ("transaction_costs", "capital_params"):
        section = strategy_record.get(section_name)
        if not isinstance(section, dict):
            continue
        for key in keys:
            candidate = section.get(key)
            if candidate is None:
                continue
            try:
                return float(candidate)
            except (TypeError, ValueError):
                continue
    return 0.0


def _normalize_risk_ratio(value: Any, *, initial_capital: float) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric < 0:
        return None
    if numeric > 1.0 and initial_capital > 0:
        return round(numeric / initial_capital, 6)
    return numeric


def _resolve_local_risk_limits(
    strategy_record: dict[str, Any],
    initial_capital: float,
) -> dict[str, float]:
    max_drawdown: Optional[float] = None
    daily_loss_limit: Optional[float] = None

    for section_name in ("risk", "risk_control"):
        section = strategy_record.get(section_name)
        if not isinstance(section, dict):
            continue

        if max_drawdown is None:
            for key in ("max_drawdown", "max_drawdown_pct"):
                if key in section:
                    max_drawdown = _normalize_risk_ratio(section.get(key), initial_capital=initial_capital)
                    break

        if daily_loss_limit is None:
            if "daily_loss_limit" in section:
                daily_loss_limit = _normalize_risk_ratio(
                    section.get("daily_loss_limit"),
                    initial_capital=initial_capital,
                )
            elif "daily_loss_limit_pct" in section:
                daily_loss_limit = _normalize_risk_ratio(
                    section.get("daily_loss_limit_pct"),
                    initial_capital=initial_capital,
                )
            elif "daily_loss_limit_yuan" in section:
                daily_loss_limit = _normalize_risk_ratio(
                    section.get("daily_loss_limit_yuan"),
                    initial_capital=initial_capital,
                )

    return {
        "max_drawdown": max_drawdown if max_drawdown is not None else 1.0,
        "daily_loss_limit": daily_loss_limit if daily_loss_limit is not None else 1.0,
    }


def _should_require_formal_or_fail(execution_profile: dict[str, Any]) -> bool:
    template_id = str(execution_profile.get("template_id") or "").strip()
    registered_templates = set(execution_profile.get("formal_engine", {}).get("registered_templates") or [])
    return bool(template_id) and template_id in registered_templates and not bool(execution_profile.get("formal_supported"))


def _reject_runtime_overrides_for_formal(payload: BacktestRunPayload) -> None:
    if payload.params:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="正式回测不接受 runtime params 覆盖。请先修改 YAML 并重新导入，系统不会在执行前静默改写策略参数。",
        )


def _get_formal_runner(request: Request) -> Any:
    runner = getattr(request.app.state, "backtest_formal_runner", None)
    if runner is None:
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        runner = OnlineBacktestRunner(settings=get_settings())
        setattr(request.app.state, "backtest_formal_runner", runner)
    return runner


def _parse_timeframe_number(timeframe: Optional[str]) -> Any:
    if not timeframe:
        return "unknown"
    normalized = str(timeframe).strip().lower()
    if normalized.endswith("m"):
        number = normalized[:-1].strip()
        if number.isdigit():
            return int(number)
    return timeframe


def _build_formal_tqsdk_stat(report: BacktestReport) -> dict[str, Any]:
    return {
        "symbol": report.symbol,
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "timeframe": _parse_timeframe_number(report.timeframe),
        "init_balance": round(report.initial_capital, 2),
        "balance": round(report.final_equity, 2),
        "trading_days": max(len(report.equity_curve) - 1, 0),
        "open_times": report.total_trades,
        "close_times": report.total_trades,
        "profit_volumes": max(0, int(round(report.performance_metrics.win_rate * report.total_trades))),
        "loss_volumes": max(
            0,
            report.total_trades - int(round(report.performance_metrics.win_rate * report.total_trades)),
        ),
    }


def _build_formal_result_execution_profile(
    strategy_record: Optional[dict[str, Any]],
    report: BacktestReport,
) -> dict[str, Any]:
    base_profile = build_strategy_execution_profile(strategy_record or {})
    executed_reason = "当前结果由 services/backtest/src/backtest/runner.py 正式引擎生成。"
    if report.status != "completed" and report.failure_reason:
        executed_reason = f"正式引擎已执行，但结果状态为 {report.status}: {report.failure_reason}"
    return {
        **base_profile,
        "mode": "formal",
        "label": "正式回测",
        "engine_type": "tqsdk",
        "formal_supported": True,
        "executed_mode": "tqsdk",
        "executed_label": "TqSdk 在线回测",
        "executed_formal": True,
        "can_execute_formal": True,
        "executed_reason": executed_reason,
        "evidence": [
            executed_reason,
            f"formal_status={report.status}",
            f"formal_report_path={report.report_path}",
            *list(base_profile.get("evidence", [])),
        ],
    }


def _build_local_result_execution_profile(
    strategy_record: Optional[dict[str, Any]],
    report: LocalBacktestReport,
) -> dict[str, Any]:
    base_profile = build_strategy_execution_profile(strategy_record or {})
    executed_reason = "当前结果由 LocalBacktestEngine 经 EngineRouter 生成。"
    if report.summary.get("status") != "completed":
        executed_reason = f"LocalBacktestEngine 已执行，但结果状态为 {report.summary.get('status')}。"
    return {
        **base_profile,
        "mode": "local",
        "label": "本地回测",
        "engine_type": "local",
        "executed_mode": "local",
        "executed_label": "Local 本地回测",
        "executed_formal": False,
        "can_execute_formal": bool(base_profile.get("formal_supported")),
        "executed_reason": executed_reason,
        "evidence": [
            executed_reason,
            f"local_status={report.summary.get('status')}",
            *list(base_profile.get("evidence", [])),
        ],
    }


def _annualized_return_pct(
    initial_capital: float,
    final_equity: float,
    start_date: date,
    end_date: date,
) -> float:
    if initial_capital <= 0:
        return 0.0
    total_days = max((end_date - start_date).days, 1)
    return ((final_equity / initial_capital) ** (365.0 / total_days) - 1.0) * 100.0


def _build_local_result_record(
    payload: BacktestRunPayload,
    *,
    strategy_name: str,
    strategy_record: dict[str, Any],
    report: LocalBacktestReport,
    symbols: list[str],
    contract: str,
) -> dict[str, Any]:
    report_payload = report.to_dict()
    execution_profile = _build_local_result_execution_profile(strategy_record, report)
    payload_strategy = dict(strategy_record.get("strategy", {}))
    payload_strategy["id"] = strategy_name
    payload_strategy["execution_profile"] = execution_profile

    job_payload = report_payload.get("job", {})
    summary_payload = report_payload.get("summary", {})
    transaction_costs = report_payload.get("transaction_costs", {})
    artifacts = report_payload.get("artifacts", {})
    local_trades = list(artifacts.get("trades") or []) if isinstance(artifacts, dict) else []
    requested_symbol = str(job_payload.get("requested_symbol") or contract)
    executed_data_symbol = str(job_payload.get("executed_data_symbol") or contract)
    source_kind = str(job_payload.get("source_kind") or "mock")
    initial_capital = float(job_payload.get("initial_capital") or _resolve_initial_capital(payload, strategy_record))
    final_equity = float(summary_payload.get("final_equity") or initial_capital)
    start_date = _parse_date(str(job_payload.get("start_date") or payload.start), date(2024, 1, 2))
    end_date = _parse_date(str(job_payload.get("end_date") or payload.end), date(2024, 12, 31))
    total_return = ((final_equity - initial_capital) / initial_capital * 100.0) if initial_capital else 0.0
    annual_return = _annualized_return_pct(initial_capital, final_equity, start_date, end_date)

    winners = [float(trade.get("pnl", 0.0)) for trade in local_trades if float(trade.get("pnl", 0.0)) > 0.0]
    losers = [abs(float(trade.get("pnl", 0.0))) for trade in local_trades if float(trade.get("pnl", 0.0)) < 0.0]
    profit_loss_ratio = 0.0
    if winners and losers:
        profit_loss_ratio = (sum(winners) / len(winners)) / (sum(losers) / len(losers))

    result_record = {
        "id": str(job_payload.get("job_id") or uuid4()),
        "task_id": str(job_payload.get("job_id") or uuid4()),
        "name": strategy_name,
        "strategy": strategy_name,
        "status": str(summary_payload.get("status") or "completed"),
        "payload": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "symbols": symbols,
            "contract": requested_symbol,
            "engine_type": "local",
            "requested_symbol": requested_symbol,
            "executed_data_symbol": executed_data_symbol,
            "source_kind": source_kind,
            "params": payload.params or strategy_record.get("params", {}),
            "strategy": payload_strategy,
            "signal": strategy_record.get("signal", {}),
            "risk": strategy_record.get("risk") or strategy_record.get("risk_control", {}),
            "timeframe": job_payload.get("timeframe"),
            "template_id": payload_strategy.get("template_id"),
        },
        "contracts": symbols,
        "submitted_at": _now_ts(),
        "progress": 100,
        "current_date": end_date.isoformat(),
        "trades": local_trades,
        "equity_curve": list(artifacts.get("equity_curve") or []) if isinstance(artifacts, dict) else [],
        "error_message": None,
        "source": "local_backtest_engine",
        "requested_symbol": requested_symbol,
        "executed_data_symbol": executed_data_symbol,
        "source_kind": source_kind,
        "report_path": None,
        "execution_profile": execution_profile,
        "duration_seconds": 0,
        "completion_logged": True,
        "report_summary": dict(summary_payload),
        "formal_report": report_payload,
        "formal_notes": list(report.notes),
        "risk_summary": {
            "event_count": len(report.risk_events),
            "events": list(report.risk_events),
        },
        "transaction_costs": dict(transaction_costs),
        "transaction_cost_summary": {
            "total_cost": transaction_costs.get("total_cost"),
            "slippage_per_unit": transaction_costs.get("slippage_per_unit"),
            "commission_per_lot_round_turn": transaction_costs.get("commission_per_lot_round_turn"),
            "total_commission_estimated": round(
                sum(float(t.get("total_cost") or 0.0) for t in local_trades), 2
            ) if local_trades else 0.0,
            "total_slippage_estimated": round(
                float(transaction_costs.get("slippage_per_unit") or 0.0)
                * 2.0
                * sum(int(t.get("quantity") or 1) for t in local_trades),
                2,
            ) if local_trades else 0.0,
        },
        "template_id": payload_strategy.get("template_id"),
        "timeframe": job_payload.get("timeframe"),
        "totalReturn": round(total_return, 2),
        "annualReturn": round(annual_return, 2),
        "maxDrawdown": round(float(summary_payload.get("max_drawdown") or 0.0) * 100.0, 2),
        "sharpeRatio": round(float(summary_payload.get("sharpe") or 0.0), 2),
        "winRate": round(float(summary_payload.get("win_rate") or 0.0) * 100.0, 1),
        "profitLossRatio": round(profit_loss_ratio, 2),
        "totalTrades": int(summary_payload.get("total_trades") or 0),
        "total_trades": int(summary_payload.get("total_trades") or 0),
        "initialCapital": round(initial_capital, 2),
        "finalCapital": round(final_equity, 2),
    }
    result_record["result"] = {
        "totalReturn": result_record["totalReturn"],
        "annualReturn": result_record["annualReturn"],
        "maxDrawdown": result_record["maxDrawdown"],
        "sharpeRatio": result_record["sharpeRatio"],
        "winRate": result_record["winRate"],
        "profitLossRatio": result_record["profitLossRatio"],
        "totalTrades": result_record["totalTrades"],
    }
    result_record["tqsdk_stat"] = {
        "symbol": executed_data_symbol,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timeframe": _parse_timeframe_number(job_payload.get("timeframe")),
        "init_balance": round(initial_capital, 2),
        "balance": round(final_equity, 2),
        "trading_days": len(result_record["equity_curve"]),
        "open_times": result_record["totalTrades"],
        "close_times": result_record["totalTrades"],
        "profit_volumes": len(winners),
        "loss_volumes": len(losers),
    }
    return result_record


def _coerce_profit_factor(value: float) -> Optional[float]:
    if not isfinite(value):
        return None
    return round(value, 2)


def _build_formal_result_record(
    payload: BacktestRunPayload,
    *,
    strategy_name: str,
    strategy_record: dict[str, Any],
    report: BacktestReport,
    symbols: list[str],
    contract: str,
) -> dict[str, Any]:
    report_payload = report.to_dict()
    execution_profile = _build_formal_result_execution_profile(strategy_record, report)
    payload_strategy = dict(strategy_record.get("strategy", {}))
    payload_strategy["id"] = strategy_name
    payload_strategy["execution_profile"] = execution_profile

    total_return = round(report.performance_metrics.total_return * 100.0, 2)
    annual_return = round(report.performance_metrics.annualized_return * 100.0, 2)
    max_drawdown = round(report.performance_metrics.max_drawdown * 100.0, 2)
    win_rate = round(report.performance_metrics.win_rate * 100.0, 1)
    profit_factor = _coerce_profit_factor(report.performance_metrics.profit_factor)

    result_record = {
        "id": report.job_id,
        "task_id": report.job_id,
        "name": strategy_name,
        "strategy": strategy_name,
        "status": report.status,
        "payload": {
            "start": report.start_date.isoformat(),
            "end": report.end_date.isoformat(),
            "symbols": symbols,
            "contract": contract,
            "engine_type": "tqsdk",
            "params": payload.params or {},
            "strategy": payload_strategy,
            "signal": strategy_record.get("signal", {}),
            "risk": strategy_record.get("risk", {}),
            "timeframe": report.timeframe,
            "template_id": report.strategy_template_id,
        },
        "contracts": symbols,
        "submitted_at": _now_ts(),
        "progress": 100,
        "current_date": report.end_date.isoformat(),
        "trades": list(report.trades),
        "equity_curve": report_payload.get("equity_curve", []),
        "error_message": report.failure_reason,
        "source": "tqsdk_formal_engine",
        "report_path": report.report_path,
        "execution_profile": execution_profile,
        "duration_seconds": 0,
        "completion_logged": True,
        "report_summary": report.report_summary,
        "formal_report": report_payload,
        "formal_notes": list(report.notes),
        "risk_summary": report_payload.get("risk_summary", {}),
        "transaction_costs": report_payload.get("transaction_costs", {}),
        "transaction_cost_summary": report_payload.get("transaction_cost_summary", {}),
        "template_id": report.strategy_template_id,
        "timeframe": report.timeframe,
        "totalReturn": total_return,
        "annualReturn": annual_return,
        "maxDrawdown": max_drawdown,
        "sharpeRatio": round(report.performance_metrics.sharpe_ratio, 2),
        "winRate": win_rate,
        "profitLossRatio": profit_factor,
        "totalTrades": report.total_trades,
        "total_trades": report.total_trades,
        "initialCapital": round(report.initial_capital, 2),
        "finalCapital": round(report.final_equity, 2),
    }
    result_record["result"] = {
        "totalReturn": result_record["totalReturn"],
        "annualReturn": result_record["annualReturn"],
        "maxDrawdown": result_record["maxDrawdown"],
        "sharpeRatio": result_record["sharpeRatio"],
        "winRate": result_record["winRate"],
        "profitLossRatio": result_record["profitLossRatio"],
        "totalTrades": result_record["totalTrades"],
    }
    result_record["tqsdk_stat"] = _build_formal_tqsdk_stat(report)
    return result_record


def _build_trades(
    strategy_name: str,
    contract: str,
    start_date: date,
    end_date: date,
    seed: int,
) -> list[dict[str, Any]]:
    total_trades = 18 + seed % 13
    span_days = max((end_date - start_date).days, total_trades)
    trades: list[dict[str, Any]] = []

    for index in range(total_trades):
        step_day = max(1, int((index + 1) * span_days / total_trades))
        trade_date = start_date + timedelta(days=min(span_days, step_day))
        direction = "buy" if index % 2 == 0 else "sell"
        offset = "open" if index % 2 == 0 else "close"
        volume = 1 + (index + seed) % 3
        base_profit = 1850.0 + (seed % 9) * 125.0 + (index % 5) * 110.0
        is_win = (index + seed) % 5 in {0, 1, 3}
        commission = round(8.0 + (index % 4) * 1.5, 2)
        profit = round(base_profit - commission, 2) if is_win else round(-(base_profit * 0.72) - commission, 2)
        price = round(3500.0 + (seed % 180) + index * 7.5, 2)
        trades.append(
            {
                "symbol": contract,
                "date": trade_date.isoformat(),
                "direction": direction,
                "offset": offset,
                "price": price,
                "volume": volume,
                "profit": profit,
                "commission": commission,
                "strategy": strategy_name,
            }
        )
    return trades


def _build_equity_curve(
    trades: list[dict[str, Any]],
    initial_capital: float,
    start_date: date,
) -> list[dict[str, Any]]:
    equity = round(initial_capital, 2)
    curve = [
        {
            "date": start_date.isoformat(),
            "timestamp": start_date.isoformat(),
            "nav": equity,
            "equity": equity,
            "value": equity,
        }
    ]

    for trade in trades:
        equity = round(equity + float(trade["profit"]), 2)
        curve.append(
            {
                "date": trade["date"],
                "timestamp": trade["date"],
                "nav": equity,
                "equity": equity,
                "value": equity,
            }
        )
    return curve


def _compute_metrics(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    initial_capital: float,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    first_value = float(equity_curve[0]["nav"])
    final_value = float(equity_curve[-1]["nav"])
    total_return = ((final_value - first_value) / first_value * 100.0) if first_value else 0.0
    total_days = max((end_date - start_date).days, 1)

    if first_value > 0:
        annual_return = ((final_value / first_value) ** (365.0 / total_days) - 1.0) * 100.0
    else:
        annual_return = 0.0

    peak = first_value
    max_drawdown = 0.0
    step_returns: list[float] = []
    previous_value = first_value
    for point in equity_curve[1:]:
        value = float(point["nav"])
        peak = max(peak, value)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - value) / peak * 100.0)
        if previous_value > 0:
            step_returns.append((value - previous_value) / previous_value)
        previous_value = value

    sharpe_ratio = 0.0
    if len(step_returns) > 1:
        mean_return = sum(step_returns) / len(step_returns)
        variance = sum((value - mean_return) ** 2 for value in step_returns) / (len(step_returns) - 1)
        std_dev = sqrt(variance) if variance > 0 else 0.0
        if std_dev > 0:
            sharpe_ratio = mean_return / std_dev * sqrt(252.0)

    closed_trades = [trade for trade in trades if trade.get("profit") is not None]
    wins = [float(trade["profit"]) for trade in closed_trades if float(trade["profit"]) > 0]
    losses = [abs(float(trade["profit"])) for trade in closed_trades if float(trade["profit"]) < 0]
    win_rate = (len(wins) / len(closed_trades) * 100.0) if closed_trades else 0.0
    profit_loss_ratio = (sum(wins) / len(wins)) / (sum(losses) / len(losses)) if wins and losses else 0.0

    return {
        "totalReturn": round(total_return, 2),
        "annualReturn": round(annual_return, 2),
        "maxDrawdown": round(max_drawdown, 2),
        "sharpeRatio": round(sharpe_ratio, 2),
        "winRate": round(win_rate, 1),
        "profitLossRatio": round(profit_loss_ratio, 2),
        "totalTrades": len(closed_trades),
        "total_trades": len(closed_trades),
        "initialCapital": round(initial_capital, 2),
        "finalCapital": round(final_value, 2),
    }


def _build_tqsdk_stat(
    start_date: date,
    end_date: date,
    contract: str,
    initial_capital: float,
    final_capital: float,
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
) -> dict[str, Any]:
    winning_trades = sum(1 for trade in trades if float(trade.get("profit", 0.0)) > 0)
    losing_trades = sum(1 for trade in trades if float(trade.get("profit", 0.0)) < 0)
    return {
        "symbol": contract,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timeframe": 5,
        "init_balance": round(initial_capital, 2),
        "balance": round(final_capital, 2),
        "trading_days": len(equity_curve),
        "open_times": (len(trades) + 1) // 2,
        "close_times": len(trades) // 2,
        "profit_volumes": winning_trades,
        "loss_volumes": losing_trades,
    }


def _build_result_record(
    state: dict[str, Any],
    payload: BacktestRunPayload,
    *,
    strategy_name: str,
    strategy_record: dict[str, Any],
    adjusted_from: Optional[str] = None,
) -> dict[str, Any]:
    execution_profile = _build_result_execution_profile(strategy_record)
    symbols = _derive_symbols(payload, strategy_record)
    contract = payload.contract or symbols[0]
    start_date = _parse_date(payload.start, date(2024, 1, 2))
    end_date = _parse_date(payload.end, date(2024, 12, 31))
    initial_capital = _resolve_initial_capital(payload)
    seed = _compat_seed(f"{strategy_name}:{contract}:{adjusted_from or 'base'}:{len(state['results'])}")

    trades = _build_trades(strategy_name, contract, start_date, end_date, seed)
    equity_curve = _build_equity_curve(trades, initial_capital, start_date)
    metrics = _compute_metrics(equity_curve, trades, initial_capital, start_date, end_date)
    task_id = str(uuid4())
    submitted_at = _now_ts()
    payload_params = payload.params or strategy_record.get("params", {})
    payload_strategy = dict(strategy_record.get("strategy", {}))
    payload_strategy["id"] = strategy_name

    result_record = {
        "id": task_id,
        "task_id": task_id,
        "name": strategy_name,
        "strategy": strategy_name,
        "status": "submitted",
        "payload": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "symbols": symbols,
            "contract": contract,
            "params": payload_params,
            "strategy": payload_strategy,
        },
        "contracts": symbols,
        "submitted_at": submitted_at,
        "progress": 0,
        "current_date": start_date.isoformat(),
        "trades": trades,
        "equity_curve": equity_curve,
        "error_message": None,
        "source": "service_local_compatibility",
        "report_path": None,
        "execution_profile": execution_profile,
        "adjusted_from": adjusted_from,
        "duration_seconds": max(8, min(18, 6 + max((end_date - start_date).days, 1) // 30)),
        "completion_logged": False,
        **metrics,
    }
    result_record["result"] = {
        "totalReturn": result_record["totalReturn"],
        "annualReturn": result_record["annualReturn"],
        "maxDrawdown": result_record["maxDrawdown"],
        "sharpeRatio": result_record["sharpeRatio"],
        "winRate": result_record["winRate"],
        "profitLossRatio": result_record["profitLossRatio"],
        "totalTrades": result_record["totalTrades"],
    }
    result_record["tqsdk_stat"] = _build_tqsdk_stat(
        start_date,
        end_date,
        contract,
        result_record["initialCapital"],
        result_record["finalCapital"],
        trades,
        equity_curve,
    )
    return result_record


def _update_strategy_status(state: dict[str, Any], strategy_name: str, status_value: str) -> None:
    strategy_record = get_strategy_record(state, strategy_name)
    if strategy_record is None:
        return
    strategy_record["status"] = status_value
    strategy_record["updated_at"] = _now_ts()


def _resolve_progress_date(start_date: date, end_date: date, progress: int) -> str:
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    span_days = max((end_date - start_date).days, 0)
    offset_days = min(span_days, max(0, round(span_days * progress / 100)))
    return (start_date + timedelta(days=offset_days)).isoformat()


def _refresh_result_state(state: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    status_value = str(result.get("status") or "")
    if status_value in {"completed", "done", "failed", "cancelled", "strategy_input_required"}:
        return result

    is_async_formal = result.get("source") == "tqsdk_formal_engine"

    payload = result.get("payload", {})
    start_date = _parse_date(payload.get("start"), date(2024, 1, 2))
    end_date = _parse_date(payload.get("end"), start_date)
    submitted_at = int(result.get("submitted_at") or _now_ts())
    duration_seconds = max(1, int(result.get("duration_seconds") or 8))
    elapsed_seconds = max(0, _now_ts() - submitted_at)
    progress_value = min(100, int(elapsed_seconds * 100 / duration_seconds))
    strategy_name = str(result.get("strategy") or result.get("name") or "")

    if is_async_formal:
        # Async formal engine: cap progress at 95%, let the background thread
        # set "completed" with real data when the backtest actually finishes.
        progress_value = min(95, progress_value)
        result["status"] = "submitted" if elapsed_seconds < 2 else "running"
        result["progress"] = max(1, progress_value)
        result["current_date"] = _resolve_progress_date(start_date, end_date, int(result["progress"]))
        if strategy_name:
            _update_strategy_status(state, strategy_name, str(result["status"]))
        return result

    if progress_value >= 100:
        result["status"] = "completed"
        result["progress"] = 100
        result["current_date"] = end_date.isoformat()
        if strategy_name:
            _update_strategy_status(state, strategy_name, "completed")
        if not result.get("completion_logged"):
            append_event_log(
                state,
                strategy=strategy_name,
                action="本地兼容回测完成",
                contract=result.get("payload", {}).get("contract"),
                result=f"{result['totalReturn']:+.2f}%",
            )
            append_system_log(state, f"compatibility result {result['id']} completed")
            result["completion_logged"] = True
        return result

    result["status"] = "submitted" if elapsed_seconds < 2 else "running"
    result["progress"] = max(1, progress_value)
    result["current_date"] = _resolve_progress_date(start_date, end_date, int(result["progress"]))
    if strategy_name:
        _update_strategy_status(state, strategy_name, str(result["status"]))
    return result


def _refresh_all_results(state: dict[str, Any]) -> None:
    for result in state["results"].values():
        _refresh_result_state(state, result)


def _store_result(state: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    state["results"][result["id"]] = result
    strategy_name = str(result["strategy"])
    strategy_record = get_strategy_record(state, strategy_name)
    if strategy_record is not None:
        strategy_record["status"] = result["status"]
        strategy_record["updated_at"] = _now_ts()

    append_event_log(
        state,
        strategy=strategy_name,
        action="提交本地兼容回测",
        contract=result["payload"].get("contract"),
    )
    append_system_log(
        state,
        f"service-local compatibility result submitted for {strategy_name} ({result['id']})",
    )
    return result


def _store_formal_result(state: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    state["results"][result["id"]] = result
    strategy_name = str(result["strategy"])
    strategy_record = get_strategy_record(state, strategy_name)
    if strategy_record is not None:
        strategy_record["status"] = result["status"]
        strategy_record["updated_at"] = _now_ts()

    append_event_log(
        state,
        strategy=strategy_name,
        action="执行正式回测",
        contract=result["payload"].get("contract"),
        result=(
            f"{result['totalReturn']:+.2f}%"
            if result.get("status") == "completed"
            else str(result.get("status"))
        ),
    )
    append_system_log(
        state,
        f"formal result stored for {strategy_name} ({result['id']}, status={result['status']})",
    )
    return result


def _store_local_result(state: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    state["results"][result["id"]] = result
    strategy_name = str(result["strategy"])
    strategy_record = get_strategy_record(state, strategy_name)
    if strategy_record is not None:
        strategy_record["status"] = result["status"]
        strategy_record["updated_at"] = _now_ts()

    append_event_log(
        state,
        strategy=strategy_name,
        action="执行本地回测",
        contract=result["payload"].get("contract"),
        result=f"{result['totalReturn']:+.2f}%",
    )
    append_system_log(
        state,
        f"local result stored for {strategy_name} ({result['id']}, status={result['status']})",
    )
    return result


@router.get("/summary")
def get_summary(request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    strategies = list(state["strategies"].values())
    results = list_results_sorted(state)

    running_count = sum(1 for result in results if result.get("status") in ACTIVE_STATUSES)
    archived_count = sum(
        1
        for result in results
        if result.get("status") in {"completed", "failed", "cancelled", "strategy_input_required"}
    )
    standby_count = 0
    for strategy in strategies:
        latest = latest_result_for_strategy(state, str(strategy.get("name", "")))
        if latest is None or latest.get("status") == "local":
            standby_count += 1

    return {
        "running_count": running_count,
        "standby_count": standby_count,
        "archived_count": archived_count,
        "logs": list(state["event_logs"]),
        "market_time": "service-local compatibility snapshot",
    }


@router.get("/results")
def get_results(request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    return [build_result_summary(result) for result in list_results_sorted(state)]


def _run_backtest_background(
    state: dict[str, Any],
    runner: "OnlineBacktestRunner",
    job_input: "BacktestJobInput",
    payload: BacktestRunPayload,
    strategy_name: str,
    strategy_record: dict[str, Any],
    symbols: list[str],
    contract: str,
    job_id: str,
) -> None:
    """Background worker: execute formal backtest and update result in state."""
    try:
        with _backtest_execution_lock:
            report = runner.run_job_sync(job_input)
        full_result = _build_formal_result_record(
            payload,
            strategy_name=strategy_name,
            strategy_record=strategy_record,
            report=report,
            symbols=symbols,
            contract=contract,
        )
        # Update the placeholder record in-place so the same id is kept
        state["results"][job_id] = full_result
        sr = get_strategy_record(state, strategy_name)
        if sr is not None:
            sr["status"] = full_result.get("status", "completed")
            sr["updated_at"] = _now_ts()
        append_event_log(
            state,
            strategy=strategy_name,
            action="正式回测完成（异步）",
            contract=contract,
            result=f"{full_result.get('totalReturn', 0):+.2f}%",
        )
        append_system_log(state, f"async formal backtest completed for {strategy_name} ({job_id})")
        _logger.info("async backtest completed: %s %s", strategy_name, job_id)
    except Exception:
        tb = traceback.format_exc()
        _logger.error("async backtest failed: %s %s\n%s", strategy_name, job_id, tb)
        placeholder = state["results"].get(job_id)
        if placeholder is not None:
            placeholder["status"] = "failed"
            placeholder["progress"] = 0
            placeholder["error_message"] = f"回测执行异常: {tb[:500]}"
        sr = get_strategy_record(state, strategy_name)
        if sr is not None:
            sr["status"] = "failed"
            sr["updated_at"] = _now_ts()
        append_event_log(
            state,
            strategy=strategy_name,
            action="正式回测失败（异步）",
            contract=contract,
        )
        append_system_log(state, f"async formal backtest FAILED for {strategy_name} ({job_id}): {tb[:200]}")


@router.post("/run", status_code=status.HTTP_201_CREATED)
def run_backtest(payload: BacktestRunPayload, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    strategy_name = _resolve_strategy_name(payload)
    strategy_record = _require_strategy_record(state, strategy_name)
    try:
        resolved_engine_type = _engine_router.validate_engine_type(payload.engine_type)
    except EngineTypeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # 若请求 tqsdk 但 auth 未配置，或策略不满足 formal_supported，自动降级到 local 引擎
    engine_downgrade_reason: str | None = None
    if resolved_engine_type == "tqsdk":
        settings = get_settings()
        tqsdk_available = bool(settings.tqsdk_auth_username and settings.tqsdk_auth_password)
        execution_profile_check = build_strategy_execution_profile(strategy_record)
        if not tqsdk_available:
            engine_downgrade_reason = "TqSdk 账号未配置（缺少 TQSDK_AUTH_USERNAME / TQSDK_AUTH_PASSWORD），已自动切换到本地回测"
            resolved_engine_type = "local"
        elif not execution_profile_check.get("formal_supported"):
            engine_downgrade_reason = "策略模板不支持 TqSdk 在线回测（formal_supported=False），已自动切换到本地回测"
            resolved_engine_type = "local"
        if engine_downgrade_reason:
            _logger.info(
                "tqsdk engine requested but not available (auth=%s, formal_supported=%s);"
                " auto-downgrading to local for %s",
                tqsdk_available,
                execution_profile_check.get("formal_supported") if not engine_downgrade_reason or "账号" not in engine_downgrade_reason else False,
                strategy_name,
            )

    if resolved_engine_type == "local":
        symbols = _derive_symbols(payload, strategy_record)
        contract = payload.contract or symbols[0]
        initial_capital = _resolve_initial_capital(payload, strategy_record)
        local_risk_limits = _resolve_local_risk_limits(strategy_record, initial_capital)
        local_router = EngineRouter(
            local_engine=LocalBacktestEngine(
                data_provider=ApiDataProvider(get_settings().data_api_url)
            )
        )

        try:
            local_report = local_router.route_local(
                LocalBacktestParams(
                    job_id=str(uuid4()),
                    strategy_id=strategy_name,
                    symbols=symbols,
                    requested_symbol=contract,
                    strategy_yaml_filename=(
                        str(strategy_record.get("strategy_yaml_filename")).strip()
                        if strategy_record.get("strategy_yaml_filename")
                        else None
                    ),
                    start_date=_parse_date(payload.start, date(2024, 1, 2)),
                    end_date=_parse_date(payload.end, date(2024, 12, 31)),
                    initial_capital=initial_capital,
                    timeframe_minutes=_resolve_local_timeframe_minutes(payload, strategy_record),
                    slippage_per_unit=_resolve_runtime_cost(
                        payload.slippage_per_unit,
                        strategy_record,
                        "slippage_per_unit",
                        "slippage",
                    ),
                    commission_per_lot_round_turn=_resolve_runtime_cost(
                        payload.commission_per_lot_round_turn,
                        strategy_record,
                        "commission_per_lot_round_turn",
                        "commission",
                    ),
                    max_drawdown=local_risk_limits["max_drawdown"],
                    daily_loss_limit=local_risk_limits["daily_loss_limit"],
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

        local_result = _store_local_result(
            state,
            _build_local_result_record(
                payload,
                strategy_name=strategy_name,
                strategy_record=strategy_record,
                report=local_report,
                symbols=symbols,
                contract=contract,
            ),
        )
        return {
            "task_id": local_result["id"],
            "engine_type": "local",
            "engine_downgrade_reason": engine_downgrade_reason,
            "transaction_cost_summary": local_result.get("transaction_cost_summary", {}),
            **build_result_summary(local_result),
        }

    execution_profile = build_strategy_execution_profile(strategy_record)

    if execution_profile.get("formal_supported"):
        _reject_runtime_overrides_for_formal(payload)
        symbols = _derive_symbols(payload, strategy_record)
        contract = payload.contract or symbols[0]
        job_id = str(uuid4())

        start_date = _parse_date(payload.start, date(2024, 1, 2))
        end_date = _parse_date(payload.end, date(2024, 12, 31))
        initial_capital = _resolve_initial_capital(payload, strategy_record)

        job_input = BacktestJobInput(
            job_id=job_id,
            strategy_template_id=str(execution_profile.get("template_id") or strategy_record.get("strategy", {}).get("template_id")),
            strategy_yaml_filename=str(strategy_record.get("strategy_yaml_filename") or strategy_name),
            symbol=contract,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            transaction_costs_override={
                k: v for k, v in {
                    "slippage_per_unit": payload.slippage_per_unit,
                    "commission_per_lot_round_turn": payload.commission_per_lot_round_turn,
                }.items() if v is not None
            } or None,
        )

        # Build placeholder result record for async progress tracking
        payload_strategy = dict(strategy_record.get("strategy", {}))
        payload_strategy["id"] = strategy_name
        placeholder_execution_profile = _build_submitted_tqsdk_execution_profile(strategy_record)
        payload_strategy["execution_profile"] = placeholder_execution_profile

        placeholder = {
            "id": job_id,
            "task_id": job_id,
            "name": strategy_name,
            "strategy": strategy_name,
            "status": "running",
            "payload": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "symbols": symbols,
                "contract": contract,
                "engine_type": "tqsdk",
                "params": payload.params or {},
                "strategy": payload_strategy,
                "signal": strategy_record.get("signal", {}),
                "risk": strategy_record.get("risk", {}),
            },
            "contracts": symbols,
            "submitted_at": _now_ts(),
            "progress": 1,
            "current_date": start_date.isoformat(),
            "duration_seconds": 240,  # estimated backtest duration for progress bar
            "trades": [],
            "equity_curve": [],
            "error_message": None,
            "source": "tqsdk_formal_engine",
            "totalReturn": 0,
            "annualReturn": 0,
            "maxDrawdown": 0,
            "sharpeRatio": 0,
            "winRate": 0,
            "profitLossRatio": 0,
            "totalTrades": 0,
            "total_trades": 0,
            "initialCapital": round(initial_capital, 2),
            "finalCapital": round(initial_capital, 2),
            "result": {},
            "execution_profile": placeholder_execution_profile,
        }
        state["results"][job_id] = placeholder

        sr = get_strategy_record(state, strategy_name)
        if sr is not None:
            sr["status"] = "running"
            sr["updated_at"] = _now_ts()

        append_event_log(
            state,
            strategy=strategy_name,
            action="提交正式回测（异步）",
            contract=contract,
        )
        append_system_log(state, f"async formal backtest submitted for {strategy_name} ({job_id})")

        # Get the runner before launching the thread (bound to request)
        runner = _get_formal_runner(request)

        thread = threading.Thread(
            target=_run_backtest_background,
            args=(state, runner, job_input, payload, strategy_name, strategy_record, symbols, contract, job_id),
            daemon=True,
            name=f"backtest-{job_id[:8]}",
        )
        thread.start()

        return {
            "task_id": job_id,
            "engine_type": "tqsdk",
            "status": "running",
            "progress": 1,
            "strategy": strategy_name,
        }

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "compatibility_mode_disabled",
            "message": "兼容模式已关闭，仅支持正式回测。请确保策略 YAML 包含有效的 template_id，并已完成 TQSDK 认证。",
            "reason": str(execution_profile.get("reason") or "策略未满足正式回测要求"),
            "formal_supported": False,
            "formal_parser_error": execution_profile.get("formal_parser_error"),
            "hint": "请检查：① strategy YAML 是否包含 template_id 字段 ② 环境变量 TQSDK_AUTH_USERNAME / TQSDK_AUTH_PASSWORD 是否已配置",
        },
    )


@router.get("/results/{task_id}")
def get_result_by_id(task_id: str, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    return dict(_result_or_404(state, task_id))


@router.post("/adjust", status_code=status.HTTP_201_CREATED)
def adjust_backtest(payload: BacktestAdjustPayload, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    original_id = payload.task_id or payload.id
    if not original_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="task_id is required")

    original = _result_or_404(state, original_id)
    strategy_name = str(original.get("strategy") or "")
    strategy_record = _require_strategy_record(state, strategy_name)
    execution_profile = build_strategy_execution_profile(strategy_record)

    if not execution_profile.get("formal_supported"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "compatibility_mode_disabled",
                "message": "兼容模式已关闭，参数调整后的再次回测需要正式引擎支持。请先确保策略满足正式回测条件。",
                "reason": str(execution_profile.get("reason") or "策略未满足正式回测要求"),
            },
        )

    symbols = _derive_symbols(
        BacktestRunPayload(
            strategy_id=strategy_name,
            start=payload.start or original.get("payload", {}).get("start"),
            end=payload.end or original.get("payload", {}).get("end"),
            symbols=payload.symbols or original.get("payload", {}).get("symbols", []),
            contract=original.get("payload", {}).get("contract"),
        ),
        strategy_record,
    )
    contract = original.get("payload", {}).get("contract") or symbols[0]
    job_id = str(uuid4())
    report = _get_formal_runner(request).run_job_sync(
        BacktestJobInput(
            job_id=job_id,
            strategy_template_id=str(execution_profile.get("template_id") or strategy_record.get("strategy", {}).get("template_id")),
            strategy_yaml_filename=str(strategy_record.get("strategy_yaml_filename") or strategy_name),
            symbol=contract,
            start_date=_parse_date(payload.start or original.get("payload", {}).get("start"), date(2024, 1, 2)),
            end_date=_parse_date(payload.end or original.get("payload", {}).get("end"), date(2024, 12, 31)),
            initial_capital=_resolve_initial_capital(
                BacktestRunPayload(initialCapital=original.get("initialCapital")),
                strategy_record,
            ),
        )
    )
    run_payload = BacktestRunPayload(
        strategy_id=strategy_name,
        start=payload.start or original.get("payload", {}).get("start"),
        end=payload.end or original.get("payload", {}).get("end"),
        symbols=payload.symbols or original.get("payload", {}).get("symbols", []),
        contract=contract,
        initialCapital=original.get("initialCapital"),
    )
    result = _store_formal_result(
        state,
        _build_formal_result_record(
            run_payload,
            strategy_name=strategy_name,
            strategy_record=strategy_record,
            report=report,
            symbols=symbols,
            contract=contract,
        ),
    )
    append_event_log(
        state,
        strategy=strategy_name,
        action="调整参数后重新提交正式回测",
        contract=result["payload"].get("contract"),
    )
    return {
        "task_id": result["id"],
        **build_result_summary(result),
    }


@router.get("/history/{strategy_id}")
def get_history(strategy_id: str, request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    history = [
        build_result_summary(result)
        for result in list_results_sorted(state)
        if result.get("strategy") == strategy_id
        or result.get("payload", {}).get("strategy", {}).get("id") == strategy_id
    ]
    return history


@router.get("/results/{task_id}/equity")
def get_result_equity(task_id: str, request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    return list(_result_or_404(state, task_id).get("equity_curve", []))


def _expand_local_engine_trades(result: dict[str, Any], trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将 local_engine 的一对一成交记录（entry+exit 配对）展开为 CTP 风格的开仓/平仓两行格式。"""
    if not trades:
        return trades
    # 仅对 local_engine 产出的配对格式做展开（判断特征字段）
    if "entry_price" not in trades[0]:
        return trades
    symbol = str(
        result.get("executed_data_symbol")
        or (result.get("contracts") or [""])[0]
        or ""
    )
    tx_costs = result.get("transaction_costs") or {}
    slippage_per_unit = float(tx_costs.get("slippage_per_unit") or 0.0)
    expanded: list[dict[str, Any]] = []
    for trade in trades:
        side = str(trade.get("side") or "long")
        qty = int(trade.get("quantity") or 1)
        entry_price = trade.get("entry_price")
        exit_price = trade.get("exit_price")
        entry_time = str(trade.get("entry_time") or "")
        exit_time = str(trade.get("exit_time") or trade.get("close_time") or "")
        pnl = trade.get("pnl")
        total_cost = float(trade.get("total_cost") or 0.0)
        commission_each = round(total_cost / 2.0, 2)
        slip = round(slippage_per_unit * qty, 2) if slippage_per_unit > 0 else None
        is_buy_open = side == "long"
        # 开仓行
        expanded.append({
            "date": entry_time[:10] if entry_time else "",
            "symbol": symbol,
            "direction": "BUY" if is_buy_open else "SELL",
            "offset": "OPEN",
            "price": entry_price,
            "volume": qty,
            "commission": commission_each,
            "slippage": slip,
            "profit": None,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "exit_reason": trade.get("exit_reason"),
            "pnl": None,
        })
        # 平仓行
        expanded.append({
            "date": exit_time[:10] if exit_time else "",
            "symbol": symbol,
            "direction": "SELL" if is_buy_open else "BUY",
            "offset": "CLOSE",
            "price": exit_price,
            "volume": qty,
            "commission": commission_each,
            "slippage": slip,
            "profit": pnl,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "exit_reason": trade.get("exit_reason"),
            "pnl": pnl,
        })
    return expanded


@router.get("/results/{task_id}/trades")
def get_result_trades(task_id: str, request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    result = _result_or_404(state, task_id)
    trades = list(result.get("trades", []))
    return _expand_local_engine_trades(result, trades)


@router.get("/results/{task_id}/report")
def get_result_report(task_id: str, request: Request) -> Response:
    import json as _json
    import math as _math

    def _safe_json_dumps(obj: Any) -> str:
        def _sanitize(o: Any) -> Any:
            if isinstance(o, float):
                return None if not _math.isfinite(o) else o
            if isinstance(o, dict):
                return {k: _sanitize(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_sanitize(v) for v in o]
            return o
        return _json.dumps(_sanitize(obj), ensure_ascii=False, indent=2)

    state = get_compat_state(request)
    _refresh_all_results(state)
    result = _result_or_404(state, task_id)
    report_path = str(result.get("report_path") or "").strip()

    # Try file first
    if report_path:
        try:
            absolute_path = resolve_result_report_file(report_path)
            if absolute_path.exists():
                return FileResponse(
                    absolute_path,
                    media_type="application/json",
                    filename=f"{task_id}.report.json",
                )
        except ValueError:
            pass

    # Fall back to in-memory formal_report (when result dir is unavailable)
    formal_report = result.get("formal_report")
    if formal_report:
        content = _safe_json_dumps(formal_report)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{task_id}.report.json"'},
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest report not found")


@router.get("/progress/{task_id}")
def get_progress(task_id: str, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    result = _result_or_404(state, task_id)
    return {
        "task_id": task_id,
        "status": result.get("status"),
        "progress": result.get("progress", 100),
        "current_date": result.get("current_date"),
    }


@router.post("/cancel/{task_id}")
def cancel_backtest(task_id: str, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    result = _result_or_404(state, task_id)
    if result.get("status") in ACTIVE_STATUSES:
        result["status"] = "cancelled"
        result["progress"] = min(99, result.get("progress", 0))
        _update_strategy_status(state, str(result.get("strategy") or result.get("name") or ""), "cancelled")
        append_event_log(
            state,
            strategy=str(result.get("strategy")),
            action="取消回测任务",
            contract=result.get("payload", {}).get("contract"),
        )
        append_system_log(state, f"result {task_id} cancelled in compatibility layer", level="WARNING")
    return {
        "task_id": task_id,
        "status": result.get("status"),
        "progress": result.get("progress", 100),
    }


@router.get("/equity-curve")
def get_latest_equity_curve(request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    _refresh_all_results(state)
    latest = next((result for result in list_results_sorted(state) if result.get("status") == "completed"), None)
    if latest is None:
        return []
    return list(latest.get("equity_curve", []))


@router.delete("/results/batch")
def delete_results_batch(payload: BatchDeletePayload, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    deleted_ids: list[str] = []
    for task_id in payload.ids:
        if task_id in state["results"]:
            deleted_ids.append(task_id)
            state["results"].pop(task_id, None)

    if deleted_ids:
        append_system_log(state, f"deleted {len(deleted_ids)} compatibility results in batch")
    return {
        "deleted_ids": deleted_ids,
        "deleted_count": len(deleted_ids),
    }
