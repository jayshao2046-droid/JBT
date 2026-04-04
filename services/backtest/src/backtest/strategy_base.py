from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, TypeVar

import yaml


class StrategyConfigError(ValueError):
    pass


class StrategyInputRequiredError(RuntimeError):
    pass


def _ensure_mapping(value: Any, *, label: str) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise StrategyConfigError(f"{label} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _first_value(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _as_non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StrategyConfigError(f"{label} must be a non-empty string")
    return value.strip()


def _coerce_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be numeric") from exc


def _coerce_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be an integer")
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be an integer") from exc
    if float(coerced) != float(value):
        raise StrategyConfigError(f"{label} must be an integer")
    return coerced


def _coerce_bool(value: Any, *, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    raise StrategyConfigError(f"{label} must be a boolean")


def _ensure_string_list(value: Any, *, label: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise StrategyConfigError(f"{label} must be a list of strings")

    items: List[str] = []
    for index, item in enumerate(value):
        items.append(_as_non_empty_string(item, label=f"{label}[{index}]"))
    return items


@dataclass(frozen=True)
class FactorConfig:
    factor_name: str
    weight: float
    params: Dict[str, Any]


def _load_factor_configs(value: Any) -> List[FactorConfig]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise StrategyConfigError("factors must be a list")

    configs: List[FactorConfig] = []
    for index, item in enumerate(value):
        factor_mapping = _ensure_mapping(item, label=f"factors[{index}]")
        factor_name = _as_non_empty_string(
            _first_value(factor_mapping, "factor_name", "name", "id"),
            label=f"factors[{index}].factor_name",
        )
        configs.append(
            FactorConfig(
                factor_name=factor_name,
                weight=_coerce_float(
                    factor_mapping.get("weight", 1.0),
                    label=f"factors[{index}].weight",
                ),
                params=_ensure_mapping(
                    factor_mapping.get("params"),
                    label=f"factors[{index}].params",
                ),
            )
        )
    return configs


@dataclass(frozen=True)
class IntegratedRiskModel:
    raw: Dict[str, Any]

    def get(self, *keys: str) -> Any:
        return _first_value(self.raw, *keys)

    def require_float(self, *keys: str) -> float:
        value = self.get(*keys)
        if value is None:
            raise StrategyConfigError(
                f"Missing numeric risk parameter, accepted keys: {', '.join(keys)}"
            )
        return _coerce_float(value, label=keys[0])

    def optional_float(self, *keys: str) -> Optional[float]:
        value = self.get(*keys)
        if value is None:
            return None
        return _coerce_float(value, label=keys[0])

    def require_int(self, *keys: str) -> int:
        value = self.get(*keys)
        if value is None:
            raise StrategyConfigError(
                f"Missing integer risk parameter, accepted keys: {', '.join(keys)}"
            )
        return _coerce_int(value, label=keys[0])

    def optional_int(self, *keys: str) -> Optional[int]:
        value = self.get(*keys)
        if value is None:
            return None
        return _coerce_int(value, label=keys[0])

    def optional_bool(self, *keys: str) -> Optional[bool]:
        value = self.get(*keys)
        if value is None:
            return None
        return _coerce_bool(value, label=keys[0])

    def as_snapshot(self) -> Dict[str, Any]:
        return dict(self.raw)


@dataclass(frozen=True)
class StrategyDefinition:
    template_id: str
    params: Dict[str, Any]
    risk: IntegratedRiskModel
    metadata: Dict[str, Any]
    source_path: Path
    factors: List[FactorConfig] = field(default_factory=list)
    market_filter: Dict[str, Any] = field(default_factory=dict)
    signal: Dict[str, Any] = field(default_factory=dict)
    transaction_costs: Dict[str, Any] = field(default_factory=dict)
    symbols: List[str] = field(default_factory=list)
    timeframe_minutes: Optional[int] = None

    @classmethod
    def load(
        cls,
        yaml_path: Path,
        *,
        expected_template_id: Optional[str] = None,
    ) -> "StrategyDefinition":
        raw_payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw_payload, Mapping):
            raise StrategyConfigError("strategy YAML root must be a mapping")

        payload = _ensure_mapping(raw_payload, label="root")
        strategy_section = _ensure_mapping(payload.get("strategy"), label="strategy")

        template_id = _first_value(payload, "strategy_template_id", "template_id", "name")
        if template_id is None:
            template_id = _first_value(strategy_section, "template_id", "id", "name")
        template_id = _as_non_empty_string(template_id, label="template_id")

        if expected_template_id and template_id != expected_template_id:
            raise StrategyConfigError(
                f"strategy YAML template_id {template_id} does not match requested {expected_template_id}"
            )

        params = _ensure_mapping(
            _first_value(payload, "params", "parameters", "strategy_params")
            or _first_value(strategy_section, "params", "parameters"),
            label="params",
        )
        for key in ("position_fraction", "position_adjustment"):
            extra_value = _first_value(payload, key)
            if extra_value is None:
                extra_value = _first_value(strategy_section, key)
            if extra_value is not None and key not in params:
                params[key] = extra_value

        risk_mapping = _ensure_mapping(
            _first_value(payload, "risk", "risk_config", "risk_controls")
            or _first_value(strategy_section, "risk", "risk_config", "risk_controls"),
            label="risk",
        )
        if not risk_mapping:
            raise StrategyConfigError("strategy YAML must contain a non-empty risk mapping")

        metadata = _ensure_mapping(
            _first_value(payload, "metadata") or _first_value(strategy_section, "metadata"),
            label="metadata",
        )
        strategy_name = _first_value(payload, "name")
        if strategy_name is None:
            strategy_name = _first_value(strategy_section, "name")
        if strategy_name is not None and "name" not in metadata:
            metadata["name"] = _as_non_empty_string(strategy_name, label="name")

        for key in ("description", "version", "category"):
            value = _first_value(payload, key)
            if value is None:
                value = _first_value(strategy_section, key)
            if value is not None and key not in metadata:
                metadata[key] = value

        tags = _first_value(payload, "tags")
        if tags is None:
            tags = _first_value(strategy_section, "tags")
        if tags is not None and "tags" not in metadata:
            metadata["tags"] = _ensure_string_list(tags, label="tags")

        factors_payload = _first_value(payload, "factors")
        if factors_payload is None:
            factors_payload = _first_value(strategy_section, "factors")
        factors = _load_factor_configs(factors_payload)

        market_filter = _ensure_mapping(
            _first_value(payload, "market_filter") or _first_value(strategy_section, "market_filter"),
            label="market_filter",
        )
        if "enabled" in market_filter:
            market_filter["enabled"] = _coerce_bool(
                market_filter["enabled"],
                label="market_filter.enabled",
            )
        if "conditions" in market_filter:
            market_filter["conditions"] = _ensure_string_list(
                market_filter["conditions"],
                label="market_filter.conditions",
            )

        signal = _ensure_mapping(
            _first_value(payload, "signal") or _first_value(strategy_section, "signal"),
            label="signal",
        )
        for key in ("long_condition", "short_condition"):
            if key in signal:
                signal[key] = _as_non_empty_string(signal[key], label=f"signal.{key}")
        if "confirm_bars" in signal:
            signal["confirm_bars"] = _coerce_int(signal["confirm_bars"], label="signal.confirm_bars")

        transaction_costs = _ensure_mapping(
            _first_value(payload, "transaction_costs")
            or _first_value(strategy_section, "transaction_costs"),
            label="transaction_costs",
        )

        symbols_payload = _first_value(payload, "symbols")
        if symbols_payload is None:
            symbols_payload = _first_value(strategy_section, "symbols")
        symbols = _ensure_string_list(symbols_payload, label="symbols")

        timeframe_raw = _first_value(payload, "timeframe_minutes")
        if timeframe_raw is None:
            timeframe_raw = _first_value(strategy_section, "timeframe_minutes")
        timeframe_minutes = None
        if timeframe_raw is not None:
            timeframe_minutes = _coerce_int(timeframe_raw, label="timeframe_minutes")

        return cls(
            template_id=template_id,
            params=params,
            risk=IntegratedRiskModel(raw=risk_mapping),
            metadata=metadata,
            source_path=yaml_path,
            factors=factors,
            market_filter=market_filter,
            signal=signal,
            transaction_costs=transaction_costs,
            symbols=symbols,
            timeframe_minutes=timeframe_minutes,
        )


@dataclass(frozen=True)
class EquityCurvePoint:
    timestamp: datetime
    equity: float
    drawdown: float
    position: int
    pnl: float
    cum_pnl: float


@dataclass(frozen=True)
class RiskViolation:
    rule_name: str
    message: str
    actual_value: Any
    threshold_value: Any
    observed_at: datetime


@dataclass
class StrategyExecutionArtifacts:
    equity_curve: List[EquityCurvePoint] = field(default_factory=list)
    trade_pnls: List[float] = field(default_factory=list)
    risk_violations: List[RiskViolation] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None


@dataclass(frozen=True)
class StrategyRuntimeContext:
    job_id: str
    symbol: str
    initial_capital: float
    strategy_config: StrategyDefinition
    settings: Any
    session: Any
    submitted_at: datetime


class FixedTemplateStrategy(ABC):
    template_id = ""

    def __init__(self, runtime_context: StrategyRuntimeContext) -> None:
        self.runtime_context = runtime_context
        self.session = runtime_context.session
        self.strategy_config = runtime_context.strategy_config
        self._artifacts = StrategyExecutionArtifacts()
        self._peak_equity = runtime_context.initial_capital

    @property
    def params(self) -> Dict[str, Any]:
        return self.strategy_config.params

    @property
    def risk(self) -> IntegratedRiskModel:
        return self.strategy_config.risk

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.strategy_config.metadata

    @property
    def factor_configs(self) -> List[FactorConfig]:
        return list(self.strategy_config.factors)

    @property
    def market_filter_config(self) -> Dict[str, Any]:
        return dict(self.strategy_config.market_filter)

    @property
    def signal_config(self) -> Dict[str, Any]:
        return dict(self.strategy_config.signal)

    @property
    def transaction_costs(self) -> Dict[str, Any]:
        return dict(self.strategy_config.transaction_costs)

    @property
    def symbols(self) -> List[str]:
        return list(self.strategy_config.symbols)

    @property
    def timeframe_minutes(self) -> Optional[int]:
        return self.strategy_config.timeframe_minutes

    def build_target_pos_task(
        self,
        *,
        symbol: Optional[str] = None,
        price: str = "ACTIVE",
        offset_priority: str = "今昨,开",
    ) -> Any:
        from tqsdk import TargetPosTask

        return TargetPosTask(
            self.session.api,
            symbol or self.runtime_context.symbol,
            price=price,
            offset_priority=offset_priority,
            account=self.session.account,
        )

    def append_note(self, message: str) -> None:
        if message:
            self._artifacts.notes.append(message)

    def record_trade_pnl(self, pnl: float) -> None:
        self._artifacts.trade_pnls.append(float(pnl))

    def record_risk_violation(
        self,
        *,
        rule_name: str,
        message: str,
        actual_value: Any,
        threshold_value: Any,
        observed_at: Optional[datetime] = None,
    ) -> None:
        self._artifacts.risk_violations.append(
            RiskViolation(
                rule_name=rule_name,
                message=message,
                actual_value=actual_value,
                threshold_value=threshold_value,
                observed_at=observed_at or datetime.now().astimezone(),
            )
        )

    def record_equity(
        self,
        *,
        equity: float,
        position: int = 0,
        timestamp: Optional[datetime] = None,
    ) -> None:
        timestamp = timestamp or datetime.now().astimezone()
        previous = self._artifacts.equity_curve[-1] if self._artifacts.equity_curve else None
        self._peak_equity = max(self._peak_equity, float(equity))
        drawdown = 0.0
        if self._peak_equity > 0:
            drawdown = max(0.0, (self._peak_equity - float(equity)) / self._peak_equity)
        pnl = 0.0 if previous is None else float(equity) - previous.equity
        self._artifacts.equity_curve.append(
            EquityCurvePoint(
                timestamp=timestamp,
                equity=float(equity),
                drawdown=drawdown,
                position=int(position),
                pnl=pnl,
                cum_pnl=float(equity) - self.runtime_context.initial_capital,
            )
        )

    def record_account_snapshot(self, *, timestamp: Optional[datetime] = None) -> None:
        account_snapshot = self.session.api.get_account(account=self.session.account)
        position_snapshot = self.session.api.get_position(
            self.runtime_context.symbol,
            account=self.session.account,
        )
        equity = self._extract_number(
            account_snapshot,
            "balance",
            "equity",
            "static_balance",
            default=self.runtime_context.initial_capital,
        )
        position = self._extract_position(position_snapshot)
        self.record_equity(equity=equity, position=position, timestamp=timestamp)

    def finish(self) -> StrategyExecutionArtifacts:
        if self._artifacts.completed_at is None:
            self._artifacts.completed_at = datetime.now().astimezone()
        return self._artifacts

    @abstractmethod
    def run(self) -> StrategyExecutionArtifacts:
        pass

    def _extract_number(self, snapshot: Any, *keys: str, default: float = 0.0) -> float:
        if not isinstance(snapshot, Mapping):
            return default
        for key in keys:
            if key in snapshot and snapshot[key] not in {None, ""}:
                candidate = snapshot[key]
                if isinstance(candidate, bool):
                    continue
                try:
                    return float(candidate)
                except (TypeError, ValueError):
                    continue
        return default

    def _extract_position(self, snapshot: Any) -> int:
        if not isinstance(snapshot, Mapping):
            return 0
        long_value = self._extract_number(
            snapshot,
            "volume_long",
            "pos_long",
            "pos_long_today",
            default=0.0,
        )
        short_value = self._extract_number(
            snapshot,
            "volume_short",
            "pos_short",
            "pos_short_today",
            default=0.0,
        )
        if long_value == 0.0 and short_value == 0.0:
            fallback = self._extract_number(snapshot, "volume", default=0.0)
            return int(fallback)
        return int(long_value - short_value)


StrategyTemplateType = TypeVar("StrategyTemplateType", bound=FixedTemplateStrategy)


class StrategyTemplateRegistry:
    def __init__(self) -> None:
        self._templates: Dict[str, Type[FixedTemplateStrategy]] = {}
        self._fallback_template: Optional[Type[FixedTemplateStrategy]] = None

    def register(self, template_cls: Type[StrategyTemplateType]) -> Type[StrategyTemplateType]:
        template_id = getattr(template_cls, "template_id", "")
        if not isinstance(template_id, str) or not template_id.strip():
            raise StrategyConfigError("strategy template must declare a non-empty template_id")
        self._templates[template_id.strip()] = template_cls
        if getattr(template_cls, "accepts_any_template_id", False):
            self._fallback_template = template_cls
        return template_cls

    def resolve(self, template_id: str) -> Type[FixedTemplateStrategy]:
        _load_builtin_templates()
        template = self._templates.get(template_id)
        if template is None and self._fallback_template is not None:
            return self._fallback_template
        if template is None:
            raise StrategyInputRequiredError(
                f"策略模板 {template_id} 尚未注册，当前已到达需要 Jay.S 提供策略输入的检查点"
            )
        return template

    def list_template_ids(self) -> List[str]:
        _load_builtin_templates()
        return sorted(self._templates)


strategy_registry = StrategyTemplateRegistry()


def register_strategy_template(
    template_cls: Type[StrategyTemplateType],
) -> Type[StrategyTemplateType]:
    return strategy_registry.register(template_cls)


def _load_builtin_templates() -> None:
    try:
        if __package__:
            from . import fc_224_strategy as builtin_fc_224_strategy
            from . import generic_factor_strategy as builtin_generic_strategy
        else:
            import fc_224_strategy as builtin_fc_224_strategy
            import generic_factor_strategy as builtin_generic_strategy
    except ImportError:
        return

    _ = builtin_fc_224_strategy
    _ = builtin_generic_strategy


_load_builtin_templates()