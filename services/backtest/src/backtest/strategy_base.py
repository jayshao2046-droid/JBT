from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, TypeVar

import yaml


GENERIC_FORMAL_TEMPLATE_ID = "generic_formal_strategy_v1"


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
    if isinstance(value, str):
        normalized = value.strip().replace("_", "")
        if not normalized:
            raise StrategyConfigError(f"{label} must be numeric")
        try:
            if normalized.endswith("%"):
                return float(normalized[:-1].strip()) / 100.0
            return float(normalized)
        except ValueError as exc:
            raise StrategyConfigError(f"{label} must be numeric") from exc
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


def _coerce_scalar_list(value: Any, *, label: str) -> List[Any]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise StrategyConfigError(f"{label} must be a list")
    return list(value)


def _parse_timeframe_minutes(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be an integer minute value")
    if isinstance(value, (int, float)):
        return _coerce_int(value, label=label)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            raise StrategyConfigError(f"{label} must be an integer minute value")
        if normalized.endswith("m"):
            return _coerce_int(normalized[:-1], label=label)
        if normalized.endswith("h"):
            return _coerce_int(normalized[:-1], label=label) * 60
        if normalized.endswith("d"):
            return _coerce_int(normalized[:-1], label=label) * 1440
        return _coerce_int(normalized, label=label)
    raise StrategyConfigError(f"{label} must be an integer minute value")


def _looks_like_generic_strategy(*mappings: Mapping[str, Any]) -> bool:
    seen_factors = False
    generic_markers = {"indicators", "signal_rule", "factor_weights", "position_size", "risk_control"}

    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            continue
        if mapping.get("factors") is not None:
            seen_factors = True
        if generic_markers.intersection(mapping.keys()):
            return seen_factors or mapping.get("factors") is not None
    return False


def _looks_like_legacy_factor_strategy(*mappings: Mapping[str, Any]) -> bool:
    has_factors = False
    has_signal = False
    has_market_filter = False
    has_symbol = False
    has_timeframe = False
    has_position = False

    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            continue
        has_factors = has_factors or mapping.get("factors") is not None
        has_signal = has_signal or mapping.get("signal") is not None
        has_market_filter = has_market_filter or mapping.get("market_filter") is not None
        has_symbol = has_symbol or mapping.get("symbols") is not None or mapping.get("symbol") is not None
        has_timeframe = has_timeframe or any(
            mapping.get(key) is not None for key in ("timeframe", "timeframe_minutes")
        )
        has_position = has_position or any(
            mapping.get(key) is not None for key in ("position_fraction", "position_adjustment")
        )

    return has_factors and (has_signal or has_market_filter) and (has_symbol or has_timeframe or has_position)


@dataclass(frozen=True)
class FactorConfig:
    factor_name: str
    weight: float
    params: Dict[str, Any]
    formula: Optional[str] = None
    description: str = ""
    factor_type: str = ""


@dataclass(frozen=True)
class IndicatorConfig:
    name: str
    indicator_type: str
    params: List[Any]


def _load_factor_configs(
    value: Any,
    *,
    factor_weights: Optional[Mapping[str, Any]] = None,
) -> List[FactorConfig]:
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
        explicit_weight = factor_mapping.get("weight")
        if explicit_weight is None and factor_weights is not None:
            explicit_weight = factor_weights.get(factor_name)
        formula = factor_mapping.get("formula")
        configs.append(
            FactorConfig(
                factor_name=factor_name,
                weight=_coerce_float(
                    1.0 if explicit_weight is None else explicit_weight,
                    label=f"factors[{index}].weight",
                ),
                params=_ensure_mapping(
                    factor_mapping.get("params"),
                    label=f"factors[{index}].params",
                ),
                formula=None
                if formula is None
                else _as_non_empty_string(formula, label=f"factors[{index}].formula"),
                description=str(factor_mapping.get("description") or "").strip(),
                factor_type=str(
                    factor_mapping.get("type")
                    or factor_mapping.get("factor_type")
                    or ""
                ).strip(),
            )
        )
    return configs


def _load_indicator_configs(value: Any) -> List[IndicatorConfig]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise StrategyConfigError("indicators must be a list")

    configs: List[IndicatorConfig] = []
    for index, item in enumerate(value):
        indicator_mapping = _ensure_mapping(item, label=f"indicators[{index}]")
        indicator_name = _as_non_empty_string(
            _first_value(indicator_mapping, "name", "id"),
            label=f"indicators[{index}].name",
        )
        indicator_type = _as_non_empty_string(
            _first_value(indicator_mapping, "type", "indicator_type"),
            label=f"indicators[{index}].type",
        )
        configs.append(
            IndicatorConfig(
                name=indicator_name,
                indicator_type=indicator_type,
                params=_coerce_scalar_list(
                    indicator_mapping.get("params", []),
                    label=f"indicators[{index}].params",
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
    capital_params: Dict[str, Any] = field(default_factory=dict)
    factors: List[FactorConfig] = field(default_factory=list)
    indicators: List[IndicatorConfig] = field(default_factory=list)
    market_filter: Dict[str, Any] = field(default_factory=dict)
    signal: Dict[str, Any] = field(default_factory=dict)
    transaction_costs: Dict[str, Any] = field(default_factory=dict)
    symbols: List[str] = field(default_factory=list)
    timeframe_minutes: Optional[int] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    yaml_snapshot_hash: Optional[str] = None

    @classmethod
    def load(
        cls,
        yaml_path: Path,
        *,
        expected_template_id: Optional[str] = None,
    ) -> "StrategyDefinition":
        raw_bytes = yaml_path.read_bytes()
        raw_payload = yaml.safe_load(raw_bytes.decode("utf-8")) or {}
        snapshot_hash = hashlib.sha256(raw_bytes).hexdigest()
        if not isinstance(raw_payload, Mapping):
            raise StrategyConfigError("strategy YAML root must be a mapping")

        payload = _ensure_mapping(raw_payload, label="root")
        strategy_section = _ensure_mapping(payload.get("strategy"), label="strategy")

        template_id = _first_value(payload, "strategy_template_id", "template_id")
        if template_id is None:
            template_id = _first_value(strategy_section, "template_id", "id", "name")

        # If explicit template_id not found, try matching name against expected
        if template_id is None and expected_template_id:
            name_candidate = _first_value(payload, "name")
            if name_candidate == expected_template_id:
                template_id = name_candidate

        # Auto-detect as generic if still unknown
        if template_id is None and (
            _looks_like_generic_strategy(payload, strategy_section)
            or _looks_like_legacy_factor_strategy(payload, strategy_section)
        ):
            template_id = GENERIC_FORMAL_TEMPLATE_ID
        if template_id is None:
            template_id = _first_value(payload, "name")
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
        for key in ("position_fraction", "position_adjustment", "position_size", "factor_weights"):
            extra_value = _first_value(payload, key)
            if extra_value is None:
                extra_value = _first_value(strategy_section, key)
            if extra_value is not None and key not in params:
                params[key] = extra_value

        capital_params: Dict[str, Any] = {}
        for key in (
            "initial_capital",
            "contract_size",
            "price_tick",
            "commission",
            "slippage",
            "margin",
        ):
            extra_value = _first_value(payload, key)
            if extra_value is None:
                extra_value = _first_value(strategy_section, key)
            if extra_value is None:
                extra_value = params.get(key)
            if extra_value is not None:
                capital_params[key] = extra_value

        risk_mapping = _ensure_mapping(
            _first_value(payload, "risk", "risk_config", "risk_controls", "risk_control")
            or _first_value(strategy_section, "risk", "risk_config", "risk_controls", "risk_control"),
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

        factor_weights = _ensure_mapping(
            _first_value(payload, "factor_weights") or _first_value(strategy_section, "factor_weights"),
            label="factor_weights",
        )

        factors_payload = _first_value(payload, "factors")
        if factors_payload is None:
            factors_payload = _first_value(strategy_section, "factors")
        factors = _load_factor_configs(factors_payload, factor_weights=factor_weights)

        indicators_payload = _first_value(payload, "indicators")
        if indicators_payload is None:
            indicators_payload = _first_value(strategy_section, "indicators")
        indicators = _load_indicator_configs(indicators_payload)

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
            _first_value(payload, "signal")
            or _first_value(strategy_section, "signal")
            or _first_value(payload, "signal_rule")
            or _first_value(strategy_section, "signal_rule"),
            label="signal",
        )
        for key in ("long_condition", "short_condition"):
            if key in signal and signal[key] not in {True, False, None}:
                signal[key] = _as_non_empty_string(signal[key], label=f"signal.{key}")
        if "confirm_bars" in signal:
            signal["confirm_bars"] = _coerce_int(signal["confirm_bars"], label="signal.confirm_bars")

        transaction_costs = _ensure_mapping(
            _first_value(payload, "transaction_costs")
            or _first_value(strategy_section, "transaction_costs"),
            label="transaction_costs",
        )
        if not transaction_costs:
            if "slippage" in capital_params:
                transaction_costs["slippage_per_unit"] = capital_params["slippage"]
            if "commission" in capital_params:
                transaction_costs["commission_per_lot_round_turn"] = capital_params["commission"]

        symbols_payload = _first_value(payload, "symbols")
        if symbols_payload is None:
            symbols_payload = _first_value(strategy_section, "symbols")
        if symbols_payload is None:
            symbols_payload = params.get("symbols")
        symbols = _ensure_string_list(symbols_payload, label="symbols")
        if not symbols:
            single_symbol = _first_value(payload, "symbol")
            if single_symbol is None:
                single_symbol = _first_value(strategy_section, "symbol")
            if single_symbol is None:
                single_symbol = params.get("symbol")
            if single_symbol is not None:
                symbols = [_as_non_empty_string(single_symbol, label="symbol")]

        timeframe_raw = _first_value(payload, "timeframe_minutes")
        if timeframe_raw is None:
            timeframe_raw = _first_value(strategy_section, "timeframe_minutes")
        if timeframe_raw is None:
            timeframe_raw = params.get("timeframe_minutes")
        if timeframe_raw is None:
            timeframe_raw = _first_value(payload, "timeframe")
        if timeframe_raw is None:
            timeframe_raw = _first_value(strategy_section, "timeframe")
        if timeframe_raw is None:
            timeframe_raw = params.get("timeframe")
        timeframe_minutes = None
        if timeframe_raw is not None:
            timeframe_minutes = _parse_timeframe_minutes(timeframe_raw, label="timeframe_minutes")

        return cls(
            template_id=template_id,
            params=params,
            risk=IntegratedRiskModel(raw=risk_mapping),
            metadata=metadata,
            source_path=yaml_path,
            capital_params=capital_params,
            factors=factors,
            indicators=indicators,
            market_filter=market_filter,
            signal=signal,
            transaction_costs=transaction_costs,
            symbols=symbols,
            timeframe_minutes=timeframe_minutes,
            raw_payload=payload,
            yaml_snapshot_hash=snapshot_hash,
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
    trade_records: List[dict] = field(default_factory=list)
    risk_violations: List[RiskViolation] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    tqsdk_account_snapshot: Dict[str, Any] = field(default_factory=dict)
    tqsdk_position_snapshot: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyRuntimeContext:
    job_id: str
    symbol: str
    initial_capital: float
    strategy_config: StrategyDefinition
    settings: Any
    session: Any
    submitted_at: datetime


class _ManualTargetPos:
    """Fallback position manager for contracts where TargetPosTask is
    unsupported (exchange min_lot > 1).  Uses ``api.insert_order()``
    directly so it bypasses the TargetPosTask restriction."""

    def __init__(self, *, api: Any, symbol: str, account: Any = None) -> None:
        self._api = api
        self._symbol = symbol
        self._account = account
        self._target: int = 0
        self._trading_symbol: str = self._resolve_trading_symbol()

    def _resolve_trading_symbol(self) -> str:
        """Resolve the actual tradable contract.  Continuous main-contract
        symbols like ``KQ.m@CZCE.CF`` cannot be used for order placement
        in TqSim; the real underlying (e.g. ``CZCE.CF505``) must be used."""
        try:
            quote = self._api.get_quote(self._symbol)
            underlying = getattr(quote, "underlying_symbol", None)
            if underlying and isinstance(underlying, str) and underlying.strip():
                return underlying.strip()
        except Exception:
            pass
        return self._symbol

    @property
    def trading_symbol(self) -> str:
        return self._trading_symbol

    # ── public interface (same as TargetPosTask) ──────────────────
    def set_target_volume(self, volume: int) -> None:
        if volume == self._target:
            return
        self._target = int(volume)
        self._sync_position()

    # ── internals ─────────────────────────────────────────────────
    def _sync_position(self) -> None:
        # Refresh underlying in case of main-contract rollover
        self._trading_symbol = self._resolve_trading_symbol()
        tsym = self._trading_symbol

        pos = self._api.get_position(tsym)
        current_long = int(getattr(pos, "pos_long", 0) or 0)
        current_short = int(getattr(pos, "pos_short", 0) or 0)
        current_net = current_long - current_short
        delta = self._target - current_net
        if delta == 0:
            return

        quote = self._api.get_quote(tsym)

        if delta > 0:
            # Buy direction: close short first, then open long
            to_close = min(current_short, delta)
            if to_close > 0:
                price = self._buy_price(quote)
                self._api.insert_order(
                    tsym, "BUY", "CLOSE", to_close,
                    limit_price=price, account=self._account,
                )
                delta -= to_close
            if delta > 0:
                price = self._buy_price(quote)
                self._api.insert_order(
                    tsym, "BUY", "OPEN", delta,
                    limit_price=price, account=self._account,
                )
        else:
            abs_delta = abs(delta)
            # Sell direction: close long first, then open short
            to_close = min(current_long, abs_delta)
            if to_close > 0:
                price = self._sell_price(quote)
                self._api.insert_order(
                    tsym, "SELL", "CLOSE", to_close,
                    limit_price=price, account=self._account,
                )
                abs_delta -= to_close
            if abs_delta > 0:
                price = self._sell_price(quote)
                self._api.insert_order(
                    tsym, "SELL", "OPEN", abs_delta,
                    limit_price=price, account=self._account,
                )

    @staticmethod
    def _buy_price(quote: Any) -> float:
        """Use upper_limit to guarantee fill in backtest mode."""
        for attr in ("upper_limit", "ask_price1", "last_price"):
            val = getattr(quote, attr, None)
            if val is not None and float(val) > 0:
                return float(val)
        return 99999999.0

    @staticmethod
    def _sell_price(quote: Any) -> float:
        """Use lower_limit to guarantee fill in backtest mode."""
        for attr in ("lower_limit", "bid_price1", "last_price"):
            val = getattr(quote, attr, None)
            if val is not None and float(val) > 0:
                return float(val)
        return 1.0


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
    def indicator_configs(self) -> List[IndicatorConfig]:
        return list(self.strategy_config.indicators)

    @property
    def capital(self) -> Dict[str, Any]:
        return dict(self.strategy_config.capital_params)

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
        min_volume: Optional[int] = None,
        max_volume: Optional[int] = None,
    ) -> Any:
        sym = symbol or self.runtime_context.symbol
        # In backtest mode, always use ManualTargetPos to avoid TqSdk's
        # async TargetPosTask validation that rejects contracts with
        # min_lot > 1 (e.g. DCE.l2605, DCE.v2605).  The backtest
        # simulator fills orders instantly, so TargetPosTask's smart
        # order splitting provides no benefit.
        mtp = _ManualTargetPos(
            api=self.session.api, symbol=sym, account=self.session.account,
        )
        self._artifacts.notes.append(
            f"target_pos=manual_order({sym})->trading={mtp.trading_symbol}"
        )
        self._position_symbol: str = mtp.trading_symbol
        return mtp

    def append_note(self, message: str) -> None:
        if message:
            self._artifacts.notes.append(message)

    def record_trade_pnl(self, pnl: float) -> None:
        self._artifacts.trade_pnls.append(float(pnl))

    def record_trade_detail(self, detail: dict) -> None:
        self._artifacts.trade_records.append(detail)

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
        # Capture final TQSDK account and position snapshot
        try:
            acct = self.session.api.get_account(account=self.session.account)
            self._artifacts.tqsdk_account_snapshot = self._extract_tqsdk_snapshot(acct)
        except Exception:
            pass
        try:
            pos = self.session.api.get_position(self.runtime_context.symbol, account=self.session.account)
            self._artifacts.tqsdk_position_snapshot = self._extract_tqsdk_snapshot(pos)
        except Exception:
            pass
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

    def _extract_tqsdk_snapshot(self, snapshot: Any) -> dict:
        """将 TQSDK 对象/Mapping 转换为可序列化的 dict"""
        if snapshot is None:
            return {}
        try:
            if hasattr(snapshot, '_data'):
                raw = dict(snapshot._data)
            elif isinstance(snapshot, Mapping):
                raw = dict(snapshot)
            else:
                raw = {k: getattr(snapshot, k) for k in dir(snapshot) if not k.startswith('_')}
            result = {}
            for k, v in raw.items():
                if callable(v):
                    continue
                try:
                    import json as _json
                    _json.dumps(v)
                    result[k] = v
                except (TypeError, ValueError):
                    result[k] = str(v)
            return result
        except Exception:
            return {}

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

    def register(self, template_cls: Type[StrategyTemplateType]) -> Type[StrategyTemplateType]:
        template_id = getattr(template_cls, "template_id", "")
        if not isinstance(template_id, str) or not template_id.strip():
            raise StrategyConfigError("strategy template must declare a non-empty template_id")
        self._templates[template_id.strip()] = template_cls
        return template_cls

    def resolve(self, template_id: str) -> Type[FixedTemplateStrategy]:
        _load_builtin_templates()
        template = self._templates.get(template_id)
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
            from . import fc_224_strategy as builtin_strategy
            from . import generic_strategy as generic_builtin_strategy
        else:
            import fc_224_strategy as builtin_strategy
            import generic_strategy as generic_builtin_strategy
    except ImportError:
        return

    _ = (builtin_strategy, generic_builtin_strategy)


_load_builtin_templates()