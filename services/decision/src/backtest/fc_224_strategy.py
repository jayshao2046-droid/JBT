from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, time as time_of_day, timezone
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
    atr_multiplier: float
    transaction_costs: Dict[str, Any]
    force_close_day: Optional[time_of_day]
    force_close_night: Optional[time_of_day]
    no_overnight: bool

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
        base_position = position_adjustment.get("base_position", position_fraction)
        atr_multiplier = _read_positive_float(
            position_adjustment.get("atr_multiplier", 1.0),
            label="position_adjustment.atr_multiplier",
        )
        no_overnight = bool(definition.risk.optional_bool("no_overnight") or False)

        return cls(
            position_fraction=_read_positive_float(
                base_position,
                label="position_adjustment.base_position",
            ),
            factor_params=factor_params,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            transaction_costs=dict(definition.transaction_costs),
            force_close_day=_read_optional_time(
                definition.risk.get("force_close_day"),
                label="risk.force_close_day",
            ),
            force_close_night=_read_optional_time(
                definition.risk.get("force_close_night"),
                label="risk.force_close_night",
            ),
            no_overnight=no_overnight,
        )


@register_strategy_template
class FC224Strategy(FixedTemplateStrategy):
    template_id = FC_224_TEMPLATE_ID

    def run(self):
        config = FC224TemplateConfig.from_definition(
            self.strategy_config,
            requested_symbol=self.runtime_context.symbol,
        )
        if not self._supports_live_execution():
            return self._run_static_snapshot(config)

        quote = self._get_quote()
        kline_serial = self._subscribe_bars(config)
        target_pos_task = self.build_target_pos_task()

        seen_trade_ids = self._collect_trade_ids()
        last_observed_position = self._read_current_position()
        last_target_volume = last_observed_position
        last_signal_state: Optional[str] = None
        loop_entered = False
        signal_transitions = 0
        target_updates = 0
        observed_trade_records = 0

        self.append_note(f"template={self.template_id}")
        self.append_note("execution_loop=wait_update_target_pos")
        self.append_note(f"position_fraction={config.position_fraction}")
        self.append_note(
            "transaction_costs="
            f"slippage_per_unit={config.transaction_costs.get('slippage_per_unit')},"
            f"commission_per_lot_round_turn={config.transaction_costs.get('commission_per_lot_round_turn')}"
        )
        self.append_note(f"no_overnight={str(config.no_overnight).lower()}")

        backtest_finished_exception = _resolve_backtest_finished_exception()
        try:
            while True:
                self.session.api.wait_update()
                loop_entered = True

                latest_row = self._get_latest_kline_row(kline_serial)
                latest_timestamp = _coerce_timestamp(_extract_timestamp(latest_row))
                (
                    last_observed_position,
                    observed_updates,
                ) = self._record_execution_changes(
                    seen_trade_ids=seen_trade_ids,
                    last_observed_position=last_observed_position,
                    timestamp=latest_timestamp,
                )
                observed_trade_records += observed_updates

                if latest_row is None or not self._is_new_kline(latest_row):
                    continue

                bars = self._normalize_streaming_bars(kline_serial, config)
                if len(bars) < self._required_bar_count(config):
                    continue

                merged_rows = self._compute_indicator_rows(bars, config)
                signal_snapshot = self._select_signal_snapshot(merged_rows)
                signal_timestamp = _coerce_timestamp(_extract_timestamp(signal_snapshot))
                market_filter_passed = self._passes_market_filter(signal_snapshot)
                signal_state = self._resolve_signal_state(signal_snapshot, market_filter_passed)
                if self._should_force_flat(signal_timestamp, config):
                    signal_state = "flat"

                if signal_state != last_signal_state:
                    signal_transitions += 1
                    last_signal_state = signal_state

                target_volume = self._resolve_target_volume(
                    signal_state=signal_state,
                    snapshot=signal_snapshot,
                    quote=quote,
                    config=config,
                )
                if target_volume != last_target_volume:
                    target_pos_task.set_target_volume(target_volume)
                    last_target_volume = target_volume
                    target_updates += 1

                try:
                    self.record_account_snapshot(timestamp=signal_timestamp or latest_timestamp)
                except Exception:
                    self.record_equity(
                        equity=self.runtime_context.initial_capital,
                        position=last_observed_position,
                        timestamp=signal_timestamp or latest_timestamp,
                    )
        except backtest_finished_exception:
            pass

        self.append_note(f"execution_loop_entered={str(loop_entered).lower()}")
        self.append_note(f"signal_transitions={signal_transitions}")
        self.append_note(f"target_updates={target_updates}")
        self.append_note(f"observed_trade_records={observed_trade_records}")
        self.append_note(f"final_signal_state={last_signal_state or 'flat'}")

        try:
            self.record_account_snapshot()
        except Exception:
            self.record_equity(
                equity=self.runtime_context.initial_capital,
                position=last_observed_position,
            )

        return self.finish()

    def _supports_live_execution(self) -> bool:
        wait_update = getattr(self.session.api, "wait_update", None)
        is_changing = getattr(self.session.api, "is_changing", None)
        return callable(wait_update) and callable(is_changing)

    def _run_static_snapshot(self, config: FC224TemplateConfig):
        bars = self._normalize_streaming_bars(self._subscribe_bars(config), config)
        if len(bars) < self._required_bar_count(config):
            raise StrategyConfigError("FC-224 strategy requires sufficient K-line samples")

        merged_rows = self._compute_indicator_rows(bars, config)
        latest = merged_rows[-1]
        market_filter_passed = self._passes_market_filter(latest)
        signal_state = self._resolve_signal_state(latest, market_filter_passed)

        self.append_note(f"template={self.template_id}")
        self.append_note("execution_loop=static_snapshot")
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

    def _subscribe_bars(self, config: FC224TemplateConfig) -> Any:
        get_kline_serial = getattr(self.session.api, "get_kline_serial", None)
        if not callable(get_kline_serial):
            raise StrategyConfigError("FC-224 strategy requires session.api.get_kline_serial")

        return get_kline_serial(
            self.runtime_context.symbol,
            FC_224_TIMEFRAME_MINUTES * 60,
            data_length=self._required_bar_count(config),
        )

    def _normalize_streaming_bars(
        self,
        raw_bars: Any,
        config: FC224TemplateConfig,
    ) -> List[Dict[str, Any]]:
        bars = normalize_bars(raw_bars)
        if len(bars) < self._required_bar_count(config):
            return []
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

    def _get_quote(self) -> Any:
        get_quote = getattr(self.session.api, "get_quote", None)
        if not callable(get_quote):
            return None
        return get_quote(self.runtime_context.symbol)

    def _get_latest_kline_row(self, raw_bars: Any) -> Optional[Any]:
        iloc = getattr(raw_bars, "iloc", None)
        if iloc is not None:
            try:
                return iloc[-1]
            except Exception:
                pass

        bars = normalize_bars(raw_bars)
        if not bars:
            return None
        return bars[-1]

    def _select_signal_snapshot(
        self,
        merged_rows: List[Dict[str, Any]],
    ) -> Mapping[str, Any]:
        if len(merged_rows) >= 2:
            return merged_rows[-2]
        return merged_rows[-1]

    def _is_new_kline(self, latest_row: Any) -> bool:
        return bool(self.session.api.is_changing(latest_row, "datetime"))

    def _record_execution_changes(
        self,
        *,
        seen_trade_ids: set[str],
        last_observed_position: int,
        timestamp: Optional[datetime],
    ) -> tuple[int, int]:
        trade_events = len(self._consume_new_trade_ids(seen_trade_ids))
        current_position = self._read_current_position()
        if trade_events == 0 and current_position != last_observed_position:
            trade_events = max(1, abs(current_position - last_observed_position))

        for _ in range(trade_events):
            self.record_trade_pnl(0.0)

        if trade_events > 0:
            try:
                self.record_account_snapshot(timestamp=timestamp)
            except Exception:
                pass

        return current_position, trade_events

    def _consume_new_trade_ids(self, seen_trade_ids: set[str]) -> List[str]:
        get_trade = getattr(self.session.api, "get_trade", None)
        if not callable(get_trade):
            return []

        try:
            trade_book = get_trade(account=self.session.account)
        except Exception:
            return []

        current_trade_ids = _collect_mapping_keys(trade_book)
        new_trade_ids = sorted(current_trade_ids - seen_trade_ids)
        seen_trade_ids.update(new_trade_ids)
        return new_trade_ids

    def _collect_trade_ids(self) -> set[str]:
        get_trade = getattr(self.session.api, "get_trade", None)
        if not callable(get_trade):
            return set()

        try:
            trade_book = get_trade(account=self.session.account)
        except Exception:
            return set()
        return _collect_mapping_keys(trade_book)

    def _read_current_position(self) -> int:
        get_position = getattr(self.session.api, "get_position", None)
        if not callable(get_position):
            return 0

        try:
            position_snapshot = get_position(
                self.runtime_context.symbol,
                account=self.session.account,
            )
        except Exception:
            return 0
        return self._extract_position(position_snapshot)

    def _resolve_target_volume(
        self,
        *,
        signal_state: str,
        snapshot: Mapping[str, Any],
        quote: Any,
        config: FC224TemplateConfig,
    ) -> int:
        if signal_state not in {"long", "short"}:
            return 0

        reference_price = self._resolve_reference_price(snapshot, quote)
        if reference_price is None or reference_price <= 0:
            return 0

        volume_multiple = self._resolve_volume_multiple(quote)
        atr_value = _optional_float(snapshot.get("atr"))
        close_value = _optional_float(snapshot.get("close")) or reference_price

        volatility_scale = 1.0
        if atr_value is not None and close_value > 0:
            normalized_atr = atr_value * config.atr_multiplier
            if normalized_atr > 0:
                volatility_scale = max(
                    0.5,
                    min(1.5, (0.005 * close_value) / normalized_atr),
                )

        raw_volume = (
            self.runtime_context.initial_capital
            * config.position_fraction
            * volatility_scale
        ) / max(reference_price * volume_multiple, 1.0)
        target_volume = max(1, int(round(raw_volume)))
        return target_volume if signal_state == "long" else -target_volume

    def _resolve_reference_price(
        self,
        snapshot: Mapping[str, Any],
        quote: Any,
    ) -> Optional[float]:
        if quote is not None:
            last_price = _optional_float(getattr(quote, "last_price", None))
            if last_price is not None and last_price > 0:
                return last_price
        return _optional_float(snapshot.get("close"))

    def _resolve_volume_multiple(self, quote: Any) -> float:
        if quote is None:
            return 1.0
        volume_multiple = _optional_float(getattr(quote, "volume_multiple", None))
        if volume_multiple is None or volume_multiple <= 0:
            return 1.0
        return volume_multiple

    def _should_force_flat(
        self,
        timestamp: Optional[datetime],
        config: FC224TemplateConfig,
    ) -> bool:
        if not config.no_overnight or timestamp is None:
            return False

        current_time = timestamp.timetz().replace(tzinfo=None)
        if current_time.hour >= 20:
            cutoff = config.force_close_night
        else:
            cutoff = config.force_close_day
        return cutoff is not None and current_time >= cutoff

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
    if not math.isfinite(float(coerced)) or float(coerced) != float(value) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be a positive integer")
    return coerced


def _read_positive_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be numeric")
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be numeric") from exc
    if not math.isfinite(coerced) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be greater than zero")
    return coerced


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        coerced = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(coerced):
        return None
    return coerced


def _read_optional_time(value: Any, *, label: str) -> Optional[time_of_day]:
    if value in {None, ""}:
        return None
    if not isinstance(value, str):
        raise StrategyConfigError(f"{label} must be an HH:MM string")
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError as exc:
        raise StrategyConfigError(f"{label} must be an HH:MM string") from exc


def _extract_timestamp(row: Any) -> Any:
    if isinstance(row, Mapping):
        if "timestamp" in row:
            return row["timestamp"]
        if "datetime" in row:
            return row["datetime"]
    return getattr(row, "timestamp", getattr(row, "datetime", None))


def _coerce_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=timezone.utc).astimezone()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            return None
        abs_value = abs(numeric_value)
        if abs_value >= 1e14:
            seconds = numeric_value / 1e9
        elif abs_value >= 1e11:
            seconds = numeric_value / 1e3
        else:
            seconds = numeric_value
        return datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()
    return None


def _collect_mapping_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        return {str(key) for key in value.keys()}

    keys = getattr(value, "keys", None)
    if callable(keys):
        try:
            return {str(key) for key in keys()}
        except Exception:
            return set()
    return set()


def _resolve_backtest_finished_exception() -> type[BaseException]:
    try:
        from tqsdk import BacktestFinished
    except ImportError:
        return RuntimeError
    return BacktestFinished