from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

try:
    from .factor_registry import FactorResult, factor_registry, normalize_bars
    from .strategy_base import FixedTemplateStrategy, StrategyConfigError, StrategyDefinition, register_strategy_template
except ImportError:
    from factor_registry import FactorResult, factor_registry, normalize_bars
    from strategy_base import FixedTemplateStrategy, StrategyConfigError, StrategyDefinition, register_strategy_template

FC_224_TEMPLATE_ID = "FC-224_v3_intraday_trend_cf605_5m"
FC_224_SYMBOL = "CZCE.CF605"
FC_224_TIMEFRAME_MINUTES = 5

SUPPORTED_SIGNAL_LONG = "macd_hist > 0 and rsi_slope > 0 and volume_ratio > 1.2"
SUPPORTED_SIGNAL_SHORT = "macd_hist < 0 and rsi_slope < 0 and volume_ratio > 1.2"
SUPPORTED_MARKET_FILTERS = {
    "atr > 0.005 * close",
    "adx > 20",
}


@dataclass(frozen=True)
class FC224TemplateConfig:
    position_fraction: float
    factor_params: Dict[str, Dict[str, Any]]
    atr_period: int
    transaction_costs: Dict[str, Any]

    @classmethod
    def from_definition(
        cls,
        definition: StrategyDefinition,
        *,
        requested_symbol: str,
    ) -> "FC224TemplateConfig":
        if definition.template_id != FC_224_TEMPLATE_ID:
            raise StrategyConfigError(
                f"FC-224 strategy template_id must be {FC_224_TEMPLATE_ID}"
            )
        if definition.symbols != [FC_224_SYMBOL]:
            raise StrategyConfigError(
                f"FC-224 symbols must be frozen to [{FC_224_SYMBOL}]"
            )
        if requested_symbol != FC_224_SYMBOL:
            raise StrategyConfigError(
                f"FC-224 requested symbol must be {FC_224_SYMBOL}"
            )
        if definition.timeframe_minutes != FC_224_TIMEFRAME_MINUTES:
            raise StrategyConfigError(
                f"FC-224 timeframe_minutes must be {FC_224_TIMEFRAME_MINUTES}"
            )

        factor_params: Dict[str, Dict[str, Any]] = {}
        for factor_config in definition.factors:
            normalized_name = _normalize_factor_name(factor_config.factor_name)
            if normalized_name not in {"macd", "rsi", "volumeratio"}:
                raise StrategyConfigError(
                    f"FC-224 only supports MACD, RSI and VolumeRatio in factors; got {factor_config.factor_name}"
                )
            factor_params[normalized_name] = dict(factor_config.params)

        missing_factors = {"macd", "rsi", "volumeratio"} - set(factor_params)
        if missing_factors:
            missing_names = ", ".join(sorted(missing_factors))
            raise StrategyConfigError(f"FC-224 missing required factors: {missing_names}")

        enabled = bool(definition.market_filter.get("enabled"))
        conditions = {
            _normalize_expression(item)
            for item in definition.market_filter.get("conditions", [])
        }
        if not enabled or conditions != {_normalize_expression(item) for item in SUPPORTED_MARKET_FILTERS}:
            raise StrategyConfigError(
                "FC-224 only supports the frozen market_filter conditions for ATR and ADX"
            )

        long_condition = definition.signal.get("long_condition")
        short_condition = definition.signal.get("short_condition")
        confirm_bars = definition.signal.get("confirm_bars")
        if _normalize_expression(long_condition) != _normalize_expression(SUPPORTED_SIGNAL_LONG):
            raise StrategyConfigError("FC-224 long_condition does not match the frozen expression")
        if _normalize_expression(short_condition) != _normalize_expression(SUPPORTED_SIGNAL_SHORT):
            raise StrategyConfigError("FC-224 short_condition does not match the frozen expression")
        if confirm_bars != 1:
            raise StrategyConfigError("FC-224 only supports confirm_bars=1")

        position_fraction = _read_positive_float(
            definition.params.get("position_fraction"),
            label="position_fraction",
        )
        position_adjustment = definition.params.get("position_adjustment") or {}
        if not isinstance(position_adjustment, Mapping):
            raise StrategyConfigError("position_adjustment must be a mapping")
        adjustment_method = position_adjustment.get("method", "atr_scaling")
        if adjustment_method != "atr_scaling":
            raise StrategyConfigError("FC-224 only supports position_adjustment.method=atr_scaling")
        atr_period = _read_positive_int(position_adjustment.get("atr_period", 14), label="position_adjustment.atr_period")

        return cls(
            position_fraction=position_fraction,
            factor_params=factor_params,
            atr_period=atr_period,
            transaction_costs=dict(definition.transaction_costs),
        )


@register_strategy_template
class FC224Strategy(FixedTemplateStrategy):
    template_id = FC_224_TEMPLATE_ID

    def run(self):
        config = FC224TemplateConfig.from_definition(
            self.strategy_config,
            requested_symbol=self.runtime_context.symbol,
        )
        bars = self._load_bars(config)
        merged_rows = self._compute_indicator_rows(bars, config)
        latest = merged_rows[-1]
        market_filter_passed = self._passes_market_filter(latest)
        signal_state = self._resolve_signal_state(latest, market_filter_passed)

        self.append_note(f"template={self.template_id}")
        self.append_note(f"market_filter_passed={str(market_filter_passed).lower()}")
        self.append_note(f"signal_state={signal_state}")
        self.append_note(f"position_fraction={config.position_fraction}")
        self.append_note(
            "transaction_costs="
            f"slippage_per_unit={config.transaction_costs.get('slippage_per_unit')},"
            f"commission_per_lot_round_turn={config.transaction_costs.get('commission_per_lot_round_turn')}"
        )

        try:
            self.record_account_snapshot()
        except Exception:
            self.record_equity(equity=self.runtime_context.initial_capital, position=0)

        return self.finish()

    def _load_bars(self, config: FC224TemplateConfig) -> List[Dict[str, Any]]:
        get_kline_serial = getattr(self.session.api, "get_kline_serial", None)
        if not callable(get_kline_serial):
            raise StrategyConfigError("FC-224 strategy requires session.api.get_kline_serial")

        raw_bars = get_kline_serial(
            self.runtime_context.symbol,
            FC_224_TIMEFRAME_MINUTES * 60,
            data_length=self._required_bar_count(config),
        )
        bars = normalize_bars(raw_bars)
        if len(bars) < self._required_bar_count(config):
            raise StrategyConfigError("FC-224 strategy requires sufficient K-line samples")
        return bars

    def _required_bar_count(self, config: FC224TemplateConfig) -> int:
        macd_params = config.factor_params["macd"]
        rsi_params = config.factor_params["rsi"]
        volume_ratio_params = config.factor_params["volumeratio"]
        return max(
            40,
            _read_positive_int(macd_params.get("slow", 26), label="MACD.slow") * 3,
            _read_positive_int(rsi_params.get("period", 14), label="RSI.period") * 3,
            _read_positive_int(volume_ratio_params.get("period", 10), label="VolumeRatio.period") * 3,
            config.atr_period * 3,
        )

    def _compute_indicator_rows(
        self,
        bars: List[Dict[str, Any]],
        config: FC224TemplateConfig,
    ) -> List[Dict[str, Any]]:
        results = [
            factor_registry.calculate("MACD", bars, config.factor_params["macd"]),
            factor_registry.calculate("RSI", bars, config.factor_params["rsi"]),
            factor_registry.calculate("VolumeRatio", bars, config.factor_params["volumeratio"]),
            factor_registry.calculate("ATR", bars, {"period": config.atr_period}),
            factor_registry.calculate("ADX", bars, {"period": config.atr_period}),
        ]

        merged_rows = [dict(row) for row in bars]
        for result in results:
            self._merge_factor_result(merged_rows, result)
        return merged_rows

    def _merge_factor_result(
        self,
        merged_rows: List[Dict[str, Any]],
        result: FactorResult,
    ) -> None:
        for row, factor_row in zip(merged_rows, result.rows):
            for key, value in factor_row.items():
                if key != "timestamp":
                    row[key] = value

    def _passes_market_filter(self, snapshot: Mapping[str, Any]) -> bool:
        atr_value = _optional_float(snapshot.get("atr"))
        adx_value = _optional_float(snapshot.get("adx"))
        close_value = _optional_float(snapshot.get("close"))
        if atr_value is None or adx_value is None or close_value is None:
            return False
        return atr_value > 0.005 * close_value and adx_value > 20.0

    def _resolve_signal_state(self, snapshot: Mapping[str, Any], market_filter_passed: bool) -> str:
        if not market_filter_passed:
            return "blocked"

        macd_hist = _optional_float(snapshot.get("macd_hist"))
        rsi_slope = _optional_float(snapshot.get("rsi_slope"))
        volume_ratio = _optional_float(snapshot.get("volume_ratio"))
        if macd_hist is None or rsi_slope is None or volume_ratio is None:
            return "flat"

        long_signal = macd_hist > 0.0 and rsi_slope > 0.0 and volume_ratio > 1.2
        short_signal = macd_hist < 0.0 and rsi_slope < 0.0 and volume_ratio > 1.2
        if long_signal and not short_signal:
            return "long"
        if short_signal and not long_signal:
            return "short"
        return "flat"


def _normalize_expression(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StrategyConfigError("FC-224 expression must be a non-empty string")
    return "".join(value.lower().split())


def _normalize_factor_name(value: str) -> str:
    return "".join(value.lower().split())


def _read_positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be a positive integer")
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be a positive integer") from exc
    if float(coerced) != float(value) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be a positive integer")
    return coerced


def _read_positive_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be numeric")
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be numeric") from exc
    if coerced <= 0:
        raise StrategyConfigError(f"{label} must be greater than zero")
    return coerced


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None