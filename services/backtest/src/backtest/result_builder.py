from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from math import inf, sqrt
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

if __package__:
    from .strategy_base import (
        EquityCurvePoint,
        RiskViolation,
        StrategyDefinition,
        StrategyExecutionArtifacts,
    )
else:
    from strategy_base import (
        EquityCurvePoint,
        RiskViolation,
        StrategyDefinition,
        StrategyExecutionArtifacts,
    )

BacktestReportStatus = Literal["completed", "failed", "strategy_input_required"]


@dataclass(frozen=True)
class BacktestJobSnapshot:
    job_id: str
    strategy_template_id: str
    strategy_yaml_filename: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_pnl: float
    max_consecutive_wins: int
    max_consecutive_losses: int


@dataclass(frozen=True)
class RiskSummary:
    source: Literal["yaml"]
    parameters: Dict[str, Any]
    violation_count: int
    breached_rules: List[str]
    max_observed_drawdown: float
    peak_position: int
    violations: List[RiskViolation]


@dataclass(frozen=True)
class BacktestReport:
    result_id: str
    job_id: str
    symbol: str
    strategy_template_id: str
    strategy_yaml_filename: str
    strategy_name: str
    timeframe: str
    start_date: date
    end_date: date
    initial_capital: float
    transaction_costs: Dict[str, Any]
    status: BacktestReportStatus
    final_equity: float
    max_drawdown: float
    total_trades: int
    equity_curve_path: str
    report_path: str
    completed_at: datetime
    performance_metrics: PerformanceMetrics
    risk_summary: RiskSummary
    equity_curve: List[EquityCurvePoint]
    notes: List[str]
    report_summary: str
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["start_date"] = self.start_date.isoformat()
        payload["end_date"] = self.end_date.isoformat()
        payload["completed_at"] = self.completed_at.isoformat()
        payload["equity_curve"] = [
            {
                "timestamp": point.timestamp.isoformat(),
                "equity": point.equity,
                "drawdown": point.drawdown,
                "position": point.position,
                "pnl": point.pnl,
                "cum_pnl": point.cum_pnl,
            }
            for point in self.equity_curve
        ]
        payload["risk_summary"]["violations"] = [
            {
                "rule_name": violation.rule_name,
                "message": violation.message,
                "actual_value": violation.actual_value,
                "threshold_value": violation.threshold_value,
                "observed_at": violation.observed_at.isoformat(),
            }
            for violation in self.risk_summary.violations
        ]
        return payload


class BacktestResultBuilder:
    def __init__(
        self,
        *,
        result_root: Optional[Path] = None,
        risk_free_rate: float = 0.03,
    ) -> None:
        self._result_root = Path(result_root or "/runtime/results")
        self._risk_free_rate = risk_free_rate

    def build(
        self,
        job: BacktestJobSnapshot,
        strategy_definition: StrategyDefinition,
        artifacts: StrategyExecutionArtifacts,
    ) -> BacktestReport:
        return self._build_report(
            job=job,
            status="completed",
            strategy_definition=strategy_definition,
            artifacts=artifacts,
        )

    def build_failed(
        self,
        job: BacktestJobSnapshot,
        *,
        reason: str,
        strategy_definition: Optional[StrategyDefinition] = None,
        notes: Optional[List[str]] = None,
    ) -> BacktestReport:
        artifacts = StrategyExecutionArtifacts(notes=list(notes or []))
        return self._build_report(
            job=job,
            status="failed",
            strategy_definition=strategy_definition,
            artifacts=artifacts,
            failure_reason=reason,
        )

    def build_strategy_input_required(
        self,
        job: BacktestJobSnapshot,
        *,
        reason: str,
        strategy_definition: Optional[StrategyDefinition] = None,
        notes: Optional[List[str]] = None,
    ) -> BacktestReport:
        artifacts = StrategyExecutionArtifacts(notes=list(notes or []))
        return self._build_report(
            job=job,
            status="strategy_input_required",
            strategy_definition=strategy_definition,
            artifacts=artifacts,
            failure_reason=reason,
        )

    def write_report(self, report: BacktestReport) -> bool:
        try:
            report_dir = self._result_root / report.job_id
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / "report.json"
            report_file.write_text(
                json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            return False
        return True

    def _build_report(
        self,
        *,
        job: BacktestJobSnapshot,
        status: BacktestReportStatus,
        artifacts: StrategyExecutionArtifacts,
        strategy_definition: Optional[StrategyDefinition],
        failure_reason: Optional[str] = None,
    ) -> BacktestReport:
        completed_at = artifacts.completed_at or datetime.now().astimezone()
        equity_curve = list(artifacts.equity_curve)
        if not equity_curve:
            equity_curve = [
                EquityCurvePoint(
                    timestamp=completed_at,
                    equity=job.initial_capital,
                    drawdown=0.0,
                    position=0,
                    pnl=0.0,
                    cum_pnl=0.0,
                )
            ]

        metrics = self._build_metrics(job.initial_capital, equity_curve, artifacts.trade_pnls)
        risk_summary = self._build_risk_summary(
            strategy_definition=strategy_definition,
            artifacts=artifacts,
            max_drawdown=metrics.max_drawdown,
            peak_position=max(abs(point.position) for point in equity_curve),
        )
        relative_dir = PurePosixPath(job.job_id)
        strategy_name = self._resolve_strategy_name(job, strategy_definition)
        timeframe = self._resolve_timeframe(strategy_definition)
        transaction_costs = self._build_transaction_costs(strategy_definition)

        return BacktestReport(
            result_id=str(uuid4()),
            job_id=job.job_id,
            symbol=job.symbol,
            strategy_template_id=job.strategy_template_id,
            strategy_yaml_filename=job.strategy_yaml_filename,
            strategy_name=strategy_name,
            timeframe=timeframe,
            start_date=job.start_date,
            end_date=job.end_date,
            initial_capital=job.initial_capital,
            transaction_costs=transaction_costs,
            status=status,
            final_equity=equity_curve[-1].equity,
            max_drawdown=metrics.max_drawdown,
            total_trades=metrics.total_trades,
            equity_curve_path=str(relative_dir / "equity_curve.parquet"),
            report_path=str(relative_dir / "report.json"),
            completed_at=completed_at,
            performance_metrics=metrics,
            risk_summary=risk_summary,
            equity_curve=equity_curve,
            notes=list(artifacts.notes),
            report_summary=self._build_report_summary(
                job=job,
                strategy_name=strategy_name,
                timeframe=timeframe,
                transaction_costs=transaction_costs,
                status=status,
                final_equity=equity_curve[-1].equity,
                total_trades=metrics.total_trades,
                max_drawdown=metrics.max_drawdown,
                failure_reason=failure_reason,
            ),
            failure_reason=failure_reason,
        )

    def _build_metrics(
        self,
        initial_capital: float,
        equity_curve: List[EquityCurvePoint],
        trade_pnls: List[float],
    ) -> PerformanceMetrics:
        final_equity = equity_curve[-1].equity
        total_return = 0.0 if initial_capital == 0 else (final_equity - initial_capital) / initial_capital
        bar_count = max(len(equity_curve) - 1, 1)
        if total_return <= -1.0:
            annualized_return = -1.0
        else:
            annualized_return = (1.0 + total_return) ** (252.0 / bar_count) - 1.0

        daily_returns: List[float] = []
        for previous, current in zip(equity_curve, equity_curve[1:]):
            if previous.equity != 0:
                daily_returns.append((current.equity - previous.equity) / previous.equity)

        if len(daily_returns) >= 2:
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((item - mean_return) ** 2 for item in daily_returns) / (len(daily_returns) - 1)
            daily_std = sqrt(variance)
        else:
            daily_std = 0.0

        sharpe_ratio = 0.0
        if daily_std > 0:
            sharpe_ratio = (annualized_return - self._risk_free_rate) / (daily_std * sqrt(252.0))

        wins = [pnl for pnl in trade_pnls if pnl > 0]
        losses = [pnl for pnl in trade_pnls if pnl < 0]
        total_trades = len(trade_pnls)
        win_rate = 0.0 if total_trades == 0 else len(wins) / total_trades

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        if total_trades == 0:
            profit_factor = 0.0
        elif gross_loss == 0:
            profit_factor = inf
        else:
            profit_factor = gross_profit / gross_loss

        avg_trade_pnl = 0.0 if total_trades == 0 else sum(trade_pnls) / total_trades
        max_consecutive_wins, max_consecutive_losses = self._count_consecutive_streaks(trade_pnls)

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max(point.drawdown for point in equity_curve),
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            avg_trade_pnl=avg_trade_pnl,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
        )

    def _build_risk_summary(
        self,
        *,
        strategy_definition: Optional[StrategyDefinition],
        artifacts: StrategyExecutionArtifacts,
        max_drawdown: float,
        peak_position: int,
    ) -> RiskSummary:
        parameters = {}
        if strategy_definition is not None:
            parameters = strategy_definition.risk.as_snapshot()

        violations = list(artifacts.risk_violations)
        return RiskSummary(
            source="yaml",
            parameters=parameters,
            violation_count=len(violations),
            breached_rules=sorted({violation.rule_name for violation in violations}),
            max_observed_drawdown=max_drawdown,
            peak_position=peak_position,
            violations=violations,
        )

    def _count_consecutive_streaks(self, trade_pnls: List[float]) -> Any:
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for pnl in trade_pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
            else:
                current_wins = 0
                current_losses = 0
            max_wins = max(max_wins, current_wins)
            max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    def _resolve_strategy_name(
        self,
        job: BacktestJobSnapshot,
        strategy_definition: Optional[StrategyDefinition],
    ) -> str:
        if strategy_definition is None:
            return job.strategy_template_id
        strategy_name = strategy_definition.metadata.get("name")
        if isinstance(strategy_name, str) and strategy_name.strip():
            return strategy_name.strip()
        return strategy_definition.template_id

    def _resolve_timeframe(self, strategy_definition: Optional[StrategyDefinition]) -> str:
        if strategy_definition is None or strategy_definition.timeframe_minutes is None:
            return "unknown"
        return f"{strategy_definition.timeframe_minutes}m"

    def _build_transaction_costs(
        self,
        strategy_definition: Optional[StrategyDefinition],
    ) -> Dict[str, Any]:
        if strategy_definition is None:
            return {
                "slippage_per_unit": None,
                "commission_per_lot_round_turn": None,
            }

        raw_costs = strategy_definition.transaction_costs
        return {
            "slippage_per_unit": _coerce_optional_number(raw_costs.get("slippage_per_unit")),
            "commission_per_lot_round_turn": _coerce_optional_number(
                raw_costs.get("commission_per_lot_round_turn")
            ),
        }

    def _build_report_summary(
        self,
        *,
        job: BacktestJobSnapshot,
        strategy_name: str,
        timeframe: str,
        transaction_costs: Dict[str, Any],
        status: BacktestReportStatus,
        final_equity: float,
        total_trades: int,
        max_drawdown: float,
        failure_reason: Optional[str],
    ) -> str:
        parts = [
            f"strategy={strategy_name}",
            f"symbol={job.symbol}",
            f"timeframe={timeframe}",
            f"window={job.start_date.isoformat()}~{job.end_date.isoformat()}",
            f"initial_capital={job.initial_capital:.2f}",
            (
                "slippage_per_unit="
                f"{_format_optional_number(transaction_costs.get('slippage_per_unit'))}"
            ),
            (
                "commission_per_lot_round_turn="
                f"{_format_optional_number(transaction_costs.get('commission_per_lot_round_turn'))}"
            ),
            f"status={status}",
        ]
        if failure_reason:
            parts.append(f"failure_reason={failure_reason}")
        else:
            parts.extend(
                [
                    f"final_equity={final_equity:.2f}",
                    f"total_trades={total_trades}",
                    f"max_drawdown={max_drawdown:.6f}",
                ]
            )
        return "; ".join(parts)


def _coerce_optional_number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_optional_number(value: Any) -> str:
    if value is None:
        return "unknown"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return "unknown"
