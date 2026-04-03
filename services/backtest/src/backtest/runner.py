from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

try:
    from ..core.settings import Settings, get_settings
    from .result_builder import BacktestJobSnapshot, BacktestReport, BacktestResultBuilder
    from .session import BacktestSessionConfigError, TqSdkSessionManager
    from .strategy_base import (
        StrategyConfigError,
        StrategyDefinition,
        StrategyInputRequiredError,
        StrategyRuntimeContext,
        StrategyTemplateRegistry,
        strategy_registry,
    )
except ImportError:
    from core.settings import Settings, get_settings
    from result_builder import BacktestJobSnapshot, BacktestReport, BacktestResultBuilder
    from session import BacktestSessionConfigError, TqSdkSessionManager
    from strategy_base import (
        StrategyConfigError,
        StrategyDefinition,
        StrategyInputRequiredError,
        StrategyRuntimeContext,
        StrategyTemplateRegistry,
        strategy_registry,
    )

BacktestRunStatus = Union[str, Any]


class BacktestExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class FrozenFormalBacktestSpec:
    strategy_template_id: str
    symbol: str
    timeframe_minutes: int
    start_date: date
    end_date: date
    initial_capital: float
    slippage_per_unit: float
    commission_per_lot_round_turn: float


FIRST_REAL_FC_224_SPEC = FrozenFormalBacktestSpec(
    strategy_template_id="FC-224_v3_intraday_trend_cf605_5m",
    symbol="CZCE.CF605",
    timeframe_minutes=5,
    start_date=date(2024, 4, 3),
    end_date=date(2026, 4, 3),
    initial_capital=1_000_000.0,
    slippage_per_unit=1.0,
    commission_per_lot_round_turn=8.0,
)


@dataclass(frozen=True)
class BacktestJobInput:
    job_id: str
    strategy_template_id: str
    strategy_yaml_filename: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "BacktestJobInput":
        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a mapping when provided")
        return cls(
            job_id=_as_non_empty_string(payload.get("job_id"), label="job_id"),
            strategy_template_id=_as_non_empty_string(
                payload.get("strategy_template_id"),
                label="strategy_template_id",
            ),
            strategy_yaml_filename=_as_non_empty_string(
                payload.get("strategy_yaml_filename"),
                label="strategy_yaml_filename",
            ),
            symbol=_as_non_empty_string(payload.get("symbol"), label="symbol"),
            start_date=_coerce_date(payload.get("start_date"), label="start_date"),
            end_date=_coerce_date(payload.get("end_date"), label="end_date"),
            initial_capital=float(payload.get("initial_capital", 0.0)),
            metadata={str(key): value for key, value in metadata.items()},
        )

    @classmethod
    def build_fc_224_formal_run(
        cls,
        *,
        job_id: str,
        strategy_yaml_filename: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> "BacktestJobInput":
        return cls(
            job_id=job_id,
            strategy_template_id=FIRST_REAL_FC_224_SPEC.strategy_template_id,
            strategy_yaml_filename=strategy_yaml_filename,
            symbol=FIRST_REAL_FC_224_SPEC.symbol,
            start_date=FIRST_REAL_FC_224_SPEC.start_date,
            end_date=FIRST_REAL_FC_224_SPEC.end_date,
            initial_capital=FIRST_REAL_FC_224_SPEC.initial_capital,
            metadata={str(key): value for key, value in (metadata or {}).items()},
        )


@dataclass
class BacktestRunRecord:
    job: BacktestJobInput
    status: str = "pending"
    submitted_at: datetime = field(default_factory=lambda: datetime.now().astimezone())
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report: Optional[BacktestReport] = None
    error_message: Optional[str] = None


class OnlineBacktestRunner:
    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        session_manager: Optional[TqSdkSessionManager] = None,
        result_builder: Optional[BacktestResultBuilder] = None,
        template_registry: Optional[StrategyTemplateRegistry] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._session_manager = session_manager or TqSdkSessionManager(settings=self._settings)
        self._result_builder = result_builder or BacktestResultBuilder(
            result_root=self._settings.backtest_result_dir,
        )
        self._template_registry = template_registry or strategy_registry
        self._records: Dict[str, BacktestRunRecord] = {}
        self._tasks: Dict[str, asyncio.Task[BacktestRunRecord]] = {}
        self._semaphore = asyncio.Semaphore(max(1, self._settings.backtest_max_concurrent))

    async def submit(self, job_input: Union[BacktestJobInput, Mapping[str, Any]]) -> BacktestRunRecord:
        job = self._normalize_job_input(job_input)
        existing_task = self._tasks.get(job.job_id)
        if existing_task is not None and not existing_task.done():
            raise BacktestExecutionError(f"job {job.job_id} is already running")

        record = BacktestRunRecord(job=job)
        self._records[job.job_id] = record
        task = asyncio.create_task(self._execute(record))
        self._tasks[job.job_id] = task
        return record

    async def wait_for_job(self, job_id: str) -> BacktestRunRecord:
        if job_id not in self._tasks:
            raise BacktestExecutionError(f"job {job_id} was not submitted")
        return await self._tasks[job_id]

    def get_record(self, job_id: str) -> Optional[BacktestRunRecord]:
        return self._records.get(job_id)

    def run_job_sync(self, job_input: Union[BacktestJobInput, Mapping[str, Any]]) -> BacktestReport:
        job = self._normalize_job_input(job_input)
        snapshot = self._build_snapshot(job)
        strategy_definition: Optional[StrategyDefinition] = None

        try:
            strategy_yaml_path = self._resolve_strategy_yaml_path(job)
            strategy_definition = StrategyDefinition.load(
                strategy_yaml_path,
                expected_template_id=job.strategy_template_id,
            )
            self._validate_frozen_first_real_backtest(job, strategy_definition)
            transaction_costs = self._read_transaction_costs(strategy_definition)
            template_cls = self._template_registry.resolve(strategy_definition.template_id)
            session_config = self._session_manager.build_config_from_job(job)
            with self._session_manager.open_session(session_config) as session:
                apply_transaction_costs = getattr(self._session_manager, "apply_transaction_costs", None)
                transaction_cost_notes = []
                if callable(apply_transaction_costs):
                    transaction_cost_notes = list(
                        apply_transaction_costs(
                            session,
                            symbol=job.symbol,
                            transaction_costs=transaction_costs,
                        )
                    )
                runtime_context = StrategyRuntimeContext(
                    job_id=job.job_id,
                    symbol=job.symbol,
                    initial_capital=job.initial_capital,
                    strategy_config=strategy_definition,
                    settings=self._settings,
                    session=session,
                    submitted_at=datetime.now().astimezone(),
                )
                strategy = template_cls(runtime_context)
                artifacts = strategy.run()
                artifacts.notes.extend(transaction_cost_notes)
            report = self._result_builder.build(snapshot, strategy_definition, artifacts)
        except StrategyInputRequiredError as exc:
            report = self._result_builder.build_strategy_input_required(
                snapshot,
                reason=str(exc),
                strategy_definition=strategy_definition,
            )
        except (BacktestSessionConfigError, StrategyConfigError, ValueError) as exc:
            report = self._result_builder.build_failed(
                snapshot,
                reason=str(exc),
                strategy_definition=strategy_definition,
            )
        except Exception as exc:
            report = self._result_builder.build_failed(
                snapshot,
                reason=f"Backtest execution failed: {exc}",
                strategy_definition=strategy_definition,
            )
        return self._finalize_report(snapshot, strategy_definition, report)

    async def _execute(self, record: BacktestRunRecord) -> BacktestRunRecord:
        async with self._semaphore:
            record.status = "running"
            record.started_at = datetime.now().astimezone()
            report = await asyncio.to_thread(self.run_job_sync, record.job)
            record.report = report
            record.status = report.status
            record.completed_at = report.completed_at
            record.error_message = report.failure_reason
            return record

    def _normalize_job_input(
        self,
        job_input: Union[BacktestJobInput, Mapping[str, Any]],
    ) -> BacktestJobInput:
        if isinstance(job_input, BacktestJobInput):
            return job_input
        return BacktestJobInput.from_mapping(job_input)

    def _build_snapshot(self, job: BacktestJobInput) -> BacktestJobSnapshot:
        return BacktestJobSnapshot(
            job_id=job.job_id,
            strategy_template_id=job.strategy_template_id,
            strategy_yaml_filename=job.strategy_yaml_filename,
            symbol=job.symbol,
            start_date=job.start_date,
            end_date=job.end_date,
            initial_capital=job.initial_capital,
        )

    def _finalize_report(
        self,
        snapshot: BacktestJobSnapshot,
        strategy_definition: Optional[StrategyDefinition],
        report: BacktestReport,
    ) -> BacktestReport:
        _ = snapshot
        _ = strategy_definition
        report = self._reject_zero_trade_fc_224_result(report)
        self._result_builder.write_report(report)
        return report

    def _reject_zero_trade_fc_224_result(
        self,
        report: BacktestReport,
    ) -> BacktestReport:
        if report.strategy_template_id != FIRST_REAL_FC_224_SPEC.strategy_template_id:
            return report
        if "execution_loop=wait_update_target_pos" not in report.notes:
            return report
        if report.status != "completed" or report.total_trades > 0:
            return report

        failure_reason = (
            "FC-224 首轮真实回测 completed 且 total_trades=0，判定为策略执行逻辑未闭环，禁止作为正式首轮结果交付"
        )
        report_summary = report.report_summary
        if "status=completed" in report_summary:
            report_summary = report_summary.replace("status=completed", "status=failed", 1)
        else:
            report_summary = f"{report_summary}; status=failed"
        if f"failure_reason={failure_reason}" not in report_summary:
            report_summary = f"{report_summary}; failure_reason={failure_reason}"

        notes = list(report.notes)
        notes.append("formal_result_rejected=true")
        notes.append("formal_result_rejected_reason=execution_loop_not_closed")
        return replace(
            report,
            status="failed",
            failure_reason=failure_reason,
            notes=notes,
            report_summary=report_summary,
        )

    def _validate_frozen_first_real_backtest(
        self,
        job: BacktestJobInput,
        strategy_definition: StrategyDefinition,
    ) -> None:
        if strategy_definition.template_id != FIRST_REAL_FC_224_SPEC.strategy_template_id:
            return

        mismatches = []
        if job.symbol != FIRST_REAL_FC_224_SPEC.symbol:
            mismatches.append(f"symbol must be {FIRST_REAL_FC_224_SPEC.symbol}")
        if job.start_date != FIRST_REAL_FC_224_SPEC.start_date:
            mismatches.append(
                f"start_date must be {FIRST_REAL_FC_224_SPEC.start_date.isoformat()}"
            )
        if job.end_date != FIRST_REAL_FC_224_SPEC.end_date:
            mismatches.append(
                f"end_date must be {FIRST_REAL_FC_224_SPEC.end_date.isoformat()}"
            )
        if not _is_close(job.initial_capital, FIRST_REAL_FC_224_SPEC.initial_capital):
            mismatches.append(
                f"initial_capital must be {FIRST_REAL_FC_224_SPEC.initial_capital:.0f}"
            )
        if strategy_definition.timeframe_minutes != FIRST_REAL_FC_224_SPEC.timeframe_minutes:
            mismatches.append(
                f"timeframe_minutes must be {FIRST_REAL_FC_224_SPEC.timeframe_minutes}"
            )

        transaction_costs = self._read_transaction_costs(strategy_definition)
        if not _is_close(
            transaction_costs["slippage_per_unit"],
            FIRST_REAL_FC_224_SPEC.slippage_per_unit,
        ):
            mismatches.append(
                "transaction_costs.slippage_per_unit must be 1 for the first formal FC-224 backtest"
            )
        if not _is_close(
            transaction_costs["commission_per_lot_round_turn"],
            FIRST_REAL_FC_224_SPEC.commission_per_lot_round_turn,
        ):
            mismatches.append(
                "transaction_costs.commission_per_lot_round_turn must be 8 for the first formal FC-224 backtest"
            )

        if mismatches:
            raise StrategyConfigError("首轮真实回测冻结输入不匹配: " + "; ".join(mismatches))

    def _read_transaction_costs(self, strategy_definition: StrategyDefinition) -> Dict[str, float]:
        transaction_costs = strategy_definition.transaction_costs
        if not transaction_costs:
            raise StrategyConfigError(
                "strategy YAML must contain transaction_costs for formal backtest execution"
            )
        return {
            "slippage_per_unit": _coerce_non_negative_float(
                transaction_costs.get("slippage_per_unit"),
                label="transaction_costs.slippage_per_unit",
            ),
            "commission_per_lot_round_turn": _coerce_non_negative_float(
                transaction_costs.get("commission_per_lot_round_turn"),
                label="transaction_costs.commission_per_lot_round_turn",
            ),
        }

    def _resolve_strategy_yaml_path(self, job: BacktestJobInput) -> Path:
        strategy_root = self._settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
        candidate = (strategy_root / job.strategy_yaml_filename).expanduser().resolve()

        if strategy_root not in candidate.parents and candidate != strategy_root:
            raise StrategyConfigError(
                "strategy_yaml_filename must stay within TQSDK_STRATEGY_YAML_DIR"
            )
        if not candidate.exists():
            raise StrategyInputRequiredError(
                f"策略 YAML 文件 {job.strategy_yaml_filename} 尚未提供，当前已到达需要 Jay.S 提供策略输入的检查点"
            )
        return candidate


def _coerce_date(value: Any, *, label: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{label} must be an ISO date string") from exc
    raise ValueError(f"{label} must be a date")


def _as_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _coerce_non_negative_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be numeric")
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be numeric") from exc
    if coerced < 0:
        raise StrategyConfigError(f"{label} must be greater than or equal to zero")
    return coerced


def _is_close(left: float, right: float, *, tolerance: float = 1e-9) -> bool:
    return abs(left - right) <= tolerance
