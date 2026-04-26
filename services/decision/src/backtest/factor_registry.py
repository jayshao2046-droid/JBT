from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

try:
    from .strategy_base import StrategyConfigError
except ImportError:
    from strategy_base import StrategyConfigError

# TASK-0083: 接入共享因子注册表
try:
    from shared.python_common.factors.registry import (
        FactorRegistry as SharedFactorRegistry,
        get_jbt_factors,
        register_global,
    )
    _shared_registry = SharedFactorRegistry()
except ImportError:
    _shared_registry = None
    register_global = None
    def get_jbt_factors():
        return []

logger = logging.getLogger(__name__)

FactorCalculator = Callable[[List[Dict[str, Any]], Dict[str, Any]], List[Dict[str, Any]]]


@dataclass(frozen=True)
class FactorResult:
    factor_name: str
    rows: List[Dict[str, Any]]

    def latest(self) -> Dict[str, Any]:
        if not self.rows:
            return {}
        return dict(self.rows[-1])


def normalize_bars(raw_bars: Any) -> List[Dict[str, Any]]:
    if isinstance(raw_bars, Mapping):
        return _normalize_column_mapping(raw_bars)

    if isinstance(raw_bars, Sequence) and not isinstance(raw_bars, (str, bytes, bytearray)):
        normalized_rows: List[Dict[str, Any]] = []
        for index, item in enumerate(raw_bars):
            if not isinstance(item, Mapping):
                raise StrategyConfigError(f"bars[{index}] must be a mapping")
            row = {str(key): value for key, value in item.items()}
            if "timestamp" not in row:
                row["timestamp"] = row.get("datetime", index)
            normalized_rows.append(row)
        return normalized_rows

    to_dict = getattr(raw_bars, "to_dict", None)
    if callable(to_dict):
        candidates: List[Any] = []
        for args, kwargs in ((["records"], {}), ([], {"orient": "records"}), ([], {})):
            try:
                candidates.append(to_dict(*args, **kwargs))
            except TypeError:
                continue
        for candidate in candidates:
            if isinstance(candidate, (list, tuple, Mapping)):
                return normalize_bars(candidate)

    raise StrategyConfigError(
        "bars must be a sequence of mappings or a tabular object exposing to_dict()"
    )


class FactorRegistry:
    def __init__(self) -> None:
        self._calculators: Dict[str, FactorCalculator] = {}
        self._alias_index: Dict[str, str] = {}
        self._display_names: Dict[str, str] = {}

    def register(
        self,
        factor_name: str,
        calculator: Optional[FactorCalculator] = None,
    ) -> Any:
        if calculator is None:
            return lambda func: self.register(factor_name, func)

        normalized = _normalize_factor_name(factor_name)
        self._calculators[normalized] = calculator
        self._display_names[normalized] = factor_name.strip()
        alias_key = _make_alias_key(normalized)
        if alias_key != normalized:
            self._alias_index[alias_key] = normalized

        # TASK-0084: 同步注册到全局共享注册表
        if register_global is not None:
            try:
                register_global(
                    name=factor_name.strip(),
                    calculator=calculator,
                    version="1.0.0",
                    description=f"Backtest factor: {factor_name}",
                )
            except Exception as e:
                logger.debug(f"Failed to register {factor_name} to global registry: {e}")

        return calculator

    def resolve_factor_name(self, factor_name: str) -> str:
        normalized = _normalize_factor_name(factor_name)
        if normalized in self._calculators:
            return normalized
        alias_key = _make_alias_key(normalized)
        resolved = self._alias_index.get(alias_key)
        if resolved is not None:
            return resolved
        for canonical, calc in self._calculators.items():
            if _make_alias_key(canonical) == alias_key:
                self._alias_index[alias_key] = canonical
                return canonical
        raise StrategyConfigError(f"Unsupported factor {factor_name}")

    def calculate(
        self,
        factor_name: str,
        bars: Any,
        params: Optional[Mapping[str, Any]] = None,
    ) -> FactorResult:
        resolved_name = self.resolve_factor_name(factor_name)
        calculator = self._calculators[resolved_name]

        normalized_bars = normalize_bars(bars)
        rows = calculator(normalized_bars, dict(params or {}))
        return FactorResult(factor_name=factor_name, rows=rows)

    def list_factors(self) -> List[str]:
        return sorted(self._calculators)

    def list_factors_with_aliases(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for canonical in sorted(self._calculators):
            display = self._display_names.get(canonical, canonical)
            aliases = set()
            aliases.add(canonical)
            no_underscore = _make_alias_key(canonical)
            if no_underscore != canonical:
                aliases.add(no_underscore)
            with_underscores = _camel_to_snake(display)
            if with_underscores != canonical:
                aliases.add(with_underscores)
            result.append({
                "name": canonical,
                "display_name": display,
                "aliases": sorted(aliases),
            })
        return result


factor_registry = FactorRegistry()


# TASK-0083: 启动时校验本地因子与共享注册表的一致性
def _validate_factor_consistency():
    """启动时校验本地因子与共享注册表的一致性。"""
    if _shared_registry is None:
        logger.warning("共享因子注册表未加载，跳过一致性校验")
        return

    local_factors = factor_registry.list_factors()
    jbt_factors = get_jbt_factors()

    missing = set(jbt_factors) - set(local_factors)
    if missing:
        logger.warning(f"本地因子注册表缺失 JBT 标准因子: {', '.join(sorted(missing))}")

    extra = set(local_factors) - set(jbt_factors)
    if extra:
        logger.info(f"本地因子注册表包含额外因子: {', '.join(sorted(extra))}")

    logger.info(f"因子注册表校验完成: 本地 {len(local_factors)} 个，JBT 标准 {len(jbt_factors)} 个")


# 模块加载时自动校验
_validate_factor_consistency()


def _normalize_factor_name(factor_name: str) -> str:
    if not isinstance(factor_name, str) or not factor_name.strip():
        raise StrategyConfigError("factor_name must be a non-empty string")
    return factor_name.strip().lower()


def _make_alias_key(normalized_name: str) -> str:
    return normalized_name.replace("_", "")


def _camel_to_snake(name: str) -> str:
    import re as _re
    s1 = _re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return _re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _normalize_column_mapping(columns: Mapping[str, Any]) -> List[Dict[str, Any]]:
    normalized_columns: Dict[str, List[Any]] = {}
    expected_length: Optional[int] = None

    for key, value in columns.items():
        values = _coerce_column_values(value, label=str(key))
        if expected_length is None:
            expected_length = len(values)
        elif len(values) != expected_length:
            raise StrategyConfigError("all bar columns must have the same length")
        normalized_columns[str(key)] = values

    if expected_length is None:
        return []

    rows: List[Dict[str, Any]] = []
    for index in range(expected_length):
        row = {key: values[index] for key, values in normalized_columns.items()}
        if "timestamp" not in row:
            row["timestamp"] = row.get("datetime", index)
        rows.append(row)
    return rows


def _coerce_column_values(value: Any, *, label: str) -> List[Any]:
    to_list = getattr(value, "tolist", None)
    if callable(to_list):
        return list(to_list())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    raise StrategyConfigError(f"column {label} must be list-like")


def _require_positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be a positive integer")
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be a positive integer") from exc
    if float(coerced) != float(value) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be a positive integer")
    return coerced


def _require_positive_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be a positive number")
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be a positive number") from exc
    if not math.isfinite(coerced) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be a positive number")
    return coerced


def _read_number(bar: Mapping[str, Any], key: str, *, label: str) -> float:
    if key not in bar:
        raise StrategyConfigError(f"bars must contain {key} for {label}")
    value = bar[key]
    if isinstance(value, bool):
        raise StrategyConfigError(f"bars[{key}] must be numeric for {label}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"bars[{key}] must be numeric for {label}") from exc


def _read_column_name(value: Any, *, label: str, default: str) -> str:
    candidate = default if value is None else value
    if not isinstance(candidate, str) or not candidate.strip():
        raise StrategyConfigError(f"{label} must be a non-empty string")
    return candidate.strip()


def _ema(values: Sequence[Optional[float]], period: int) -> List[Optional[float]]:
    alpha = 2.0 / (period + 1.0)
    smoothed: List[Optional[float]] = []
    previous: Optional[float] = None

    for value in values:
        if value is None:
            smoothed.append(previous)
            continue
        if previous is None:
            previous = float(value)
        else:
            previous = previous + alpha * (float(value) - previous)
        smoothed.append(previous)
    return smoothed


def _rolling_mean(values: Sequence[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[float] = []
    running_total = 0.0

    for value in values:
        window.append(float(value))
        running_total += float(value)
        if len(window) > period:
            running_total -= window.pop(0)
        if len(window) == period:
            result.append(running_total / period)
        else:
            result.append(None)
    return result


def _rolling_std(values: Sequence[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[float] = []

    for value in values:
        window.append(float(value))
        if len(window) > period:
            window.pop(0)
        if len(window) == period:
            mean = sum(window) / period
            variance = sum((item - mean) ** 2 for item in window) / period
            result.append(math.sqrt(max(variance, 0.0)))
        else:
            result.append(None)
    return result


def _rolling_min(values: Sequence[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[float] = []

    for value in values:
        window.append(float(value))
        if len(window) > period:
            window.pop(0)
        result.append(min(window) if len(window) == period else None)
    return result


def _rolling_max(values: Sequence[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[float] = []

    for value in values:
        window.append(float(value))
        if len(window) > period:
            window.pop(0)
        result.append(max(window) if len(window) == period else None)
    return result


def _rolling_sum(values: Sequence[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[float] = []
    running_total = 0.0

    for value in values:
        numeric = float(value)
        window.append(numeric)
        running_total += numeric
        if len(window) > period:
            running_total -= window.pop(0)
        result.append(running_total if len(window) == period else None)
    return result


def _rolling_mean_optional(
    values: Sequence[Optional[float]],
    period: int,
) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[Optional[float]] = []

    for value in values:
        window.append(None if value is None else float(value))
        if len(window) > period:
            window.pop(0)
        if len(window) == period and all(item is not None for item in window):
            result.append(sum(float(item) for item in window) / period)
        else:
            result.append(None)
    return result


def _rolling_std_optional(
    values: Sequence[Optional[float]],
    period: int,
) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[Optional[float]] = []

    for value in values:
        window.append(None if value is None else float(value))
        if len(window) > period:
            window.pop(0)
        if len(window) == period and all(item is not None for item in window):
            numeric = [float(item) for item in window]  # type: ignore[arg-type]
            mean = sum(numeric) / period
            variance = sum((x - mean) ** 2 for x in numeric) / period
            result.append(math.sqrt(max(variance, 0.0)))
        else:
            result.append(None)
    return result


def _rolling_weighted_mean(
    values: Sequence[Optional[float]],
    period: int,
) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[Optional[float]] = []
    weights = [float(index + 1) for index in range(period)]
    total_weight = sum(weights)

    for value in values:
        window.append(None if value is None else float(value))
        if len(window) > period:
            window.pop(0)
        if len(window) == period and all(item is not None for item in window):
            numeric_window = [float(item) for item in window]
            result.append(
                sum(item * weight for item, weight in zip(numeric_window, weights)) / total_weight
            )
        else:
            result.append(None)
    return result


@factor_registry.register("SMA")
def _calculate_sma(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 5), label="SMA.period")
    source = _read_column_name(params.get("source"), label="SMA.source", default="close")
    values = [_read_number(bar, source, label="SMA") for bar in bars]
    averages = _rolling_mean(values, period)
    return [
        {
            "timestamp": bar["timestamp"],
            "sma": average,
        }
        for bar, average in zip(bars, averages)
    ]


@factor_registry.register("EMA")
def _calculate_ema(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 5), label="EMA.period")
    source = _read_column_name(params.get("source"), label="EMA.source", default="close")
    values = [_read_number(bar, source, label="EMA") for bar in bars]
    averages = _ema(values, period)
    return [
        {
            "timestamp": bar["timestamp"],
            "ema": average,
        }
        for bar, average in zip(bars, averages)
    ]


@factor_registry.register("MACD")
def _calculate_macd(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    fast = _require_positive_int(params.get("fast", 12), label="MACD.fast")
    slow = _require_positive_int(params.get("slow", 26), label="MACD.slow")
    signal = _require_positive_int(params.get("signal", 9), label="MACD.signal")
    source = _read_column_name(params.get("source"), label="MACD.source", default="close")

    closes = [_read_number(bar, source, label="MACD") for bar in bars]
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line = [
        None if fast_value is None or slow_value is None else fast_value - slow_value
        for fast_value, slow_value in zip(ema_fast, ema_slow)
    ]
    signal_line = _ema(macd_line, signal)

    rows: List[Dict[str, Any]] = []
    for bar, macd_value, signal_value in zip(bars, macd_line, signal_line):
        histogram = None
        if macd_value is not None and signal_value is not None:
            histogram = macd_value - signal_value
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "macd_line": macd_value,
                "macd_signal": signal_value,
                "macd_hist": histogram,
            }
        )
    return rows


@factor_registry.register("RSI")
def _calculate_rsi(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="RSI.period")
    source = _read_column_name(params.get("source"), label="RSI.source", default="close")
    closes = [_read_number(bar, source, label="RSI") for bar in bars]

    changes: List[float] = [0.0]
    for previous, current in zip(closes, closes[1:]):
        changes.append(current - previous)

    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = _ema(gains, period)
    avg_loss = _ema(losses, period)

    rows: List[Dict[str, Any]] = []
    previous_rsi: Optional[float] = None
    for bar, gain_value, loss_value in zip(bars, avg_gain, avg_loss):
        if gain_value is None or loss_value is None:
            rsi_value = None
        elif loss_value == 0:
            rsi_value = 50.0 if gain_value == 0 else 100.0
        else:
            relative_strength = gain_value / loss_value
            rsi_value = 100.0 - 100.0 / (1.0 + relative_strength)

        slope = None
        if previous_rsi is not None and rsi_value is not None:
            slope = rsi_value - previous_rsi
        if rsi_value is not None:
            previous_rsi = rsi_value

        rows.append(
            {
                "timestamp": bar["timestamp"],
                "rsi": rsi_value,
                "rsi_slope": slope,
            }
        )
    return rows


@factor_registry.register("VolumeRatio")
def _calculate_volume_ratio(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 5), label="VolumeRatio.period")
    source = _read_column_name(params.get("source"), label="VolumeRatio.source", default="volume")
    volumes = [_read_number(bar, source, label="VolumeRatio") for bar in bars]
    rolling_mean = _rolling_mean(volumes, period)

    rows: List[Dict[str, Any]] = []
    for bar, volume, average in zip(bars, volumes, rolling_mean):
        ratio = None
        if average not in {None, 0.0}:
            ratio = volume / average
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "volume_ratio": ratio,
            }
        )
    return rows


@factor_registry.register("ATR")
def _calculate_atr(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="ATR.period")
    high_key = _read_column_name(params.get("high"), label="ATR.high", default="high")
    low_key = _read_column_name(params.get("low"), label="ATR.low", default="low")
    close_key = _read_column_name(params.get("close"), label="ATR.close", default="close")
    trs: List[float] = []
    previous_close: Optional[float] = None

    for bar in bars:
        high = _read_number(bar, high_key, label="ATR")
        low = _read_number(bar, low_key, label="ATR")
        close = _read_number(bar, close_key, label="ATR")
        high_low = high - low
        if previous_close is None:
            true_range = high_low
        else:
            true_range = max(high_low, abs(high - previous_close), abs(low - previous_close))
        trs.append(true_range)
        previous_close = close

    atr_values = _ema(trs, period)
    return [
        {
            "timestamp": bar["timestamp"],
            "atr": atr_value,
        }
        for bar, atr_value in zip(bars, atr_values)
    ]


@factor_registry.register("ADX")
def _calculate_adx(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="ADX.period")
    high_key = _read_column_name(params.get("high"), label="ADX.high", default="high")
    low_key = _read_column_name(params.get("low"), label="ADX.low", default="low")
    close_key = _read_column_name(params.get("close"), label="ADX.close", default="close")
    trs: List[float] = []
    plus_dm: List[float] = []
    minus_dm: List[float] = []

    previous_high: Optional[float] = None
    previous_low: Optional[float] = None
    previous_close: Optional[float] = None

    for bar in bars:
        high = _read_number(bar, high_key, label="ADX")
        low = _read_number(bar, low_key, label="ADX")
        close = _read_number(bar, close_key, label="ADX")

        if previous_close is None or previous_high is None or previous_low is None:
            trs.append(high - low)
            plus_dm.append(0.0)
            minus_dm.append(0.0)
        else:
            trs.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))

            up_move = high - previous_high
            down_move = previous_low - low
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)

        previous_high = high
        previous_low = low
        previous_close = close

    atr_values = _ema(trs, period)
    smooth_plus = _ema(plus_dm, period)
    smooth_minus = _ema(minus_dm, period)

    dx_values: List[Optional[float]] = []
    for atr_value, plus_value, minus_value in zip(atr_values, smooth_plus, smooth_minus):
        if atr_value in {None, 0.0} or plus_value is None or minus_value is None:
            dx_values.append(None)
            continue
        plus_di = plus_value / atr_value * 100.0
        minus_di = minus_value / atr_value * 100.0
        denominator = plus_di + minus_di
        dx_values.append(0.0 if denominator == 0 else abs(plus_di - minus_di) / denominator * 100.0)

    adx_values = _ema(dx_values, period)
    return [
        {
            "timestamp": bar["timestamp"],
            "adx": adx_value,
        }
        for bar, adx_value in zip(bars, adx_values)
    ]


@factor_registry.register("BollingerBands")
def _calculate_bollinger_bands(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="BollingerBands.period")
    std_multiplier = _require_positive_float(
        params.get("stddev", params.get("std_dev", params.get("multiplier", 2.0))),
        label="BollingerBands.stddev",
    )
    source = _read_column_name(params.get("source"), label="BollingerBands.source", default="close")
    values = [_read_number(bar, source, label="BollingerBands") for bar in bars]
    means = _rolling_mean(values, period)
    stds = _rolling_std(values, period)

    rows: List[Dict[str, Any]] = []
    for bar, close, mean, std in zip(bars, values, means, stds):
        upper = None
        lower = None
        bb_position = None
        if mean is not None and std is not None:
            upper = mean + std_multiplier * std
            lower = mean - std_multiplier * std
            if close <= lower:
                bb_position = "lower_band"
            elif close >= upper:
                bb_position = "upper_band"
            else:
                bb_position = "inside_band"
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "bollinger_mid": mean,
                "bollinger_upper": upper,
                "bollinger_lower": lower,
                "bb_position": bb_position,
            }
        )
    return rows


@factor_registry.register("DonchianBreakout")
def _calculate_donchian_breakout(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    entry_period = _require_positive_int(
        params.get("entry_period", params.get("period", 20)),
        label="DonchianBreakout.entry_period",
    )
    exit_period = _require_positive_int(
        params.get("exit_period", max(1, entry_period // 2)),
        label="DonchianBreakout.exit_period",
    )
    high_key = _read_column_name(params.get("high"), label="DonchianBreakout.high", default="high")
    low_key = _read_column_name(params.get("low"), label="DonchianBreakout.low", default="low")
    highs = [_read_number(bar, high_key, label="DonchianBreakout") for bar in bars]
    lows = [_read_number(bar, low_key, label="DonchianBreakout") for bar in bars]
    entry_highs = _rolling_max(highs, entry_period)
    entry_lows = _rolling_min(lows, entry_period)
    exit_highs = _rolling_max(highs, exit_period)
    exit_lows = _rolling_min(lows, exit_period)

    return [
        {
            "timestamp": bar["timestamp"],
            "donchian_high": entry_high,
            "donchian_low": entry_low,
            "donchian_exit_high": exit_high,
            "donchian_exit_low": exit_low,
        }
        for bar, entry_high, entry_low, exit_high, exit_low in zip(
            bars,
            entry_highs,
            entry_lows,
            exit_highs,
            exit_lows,
        )
    ]


# ---------------------------------------------------------------------------
# Migrated from J_BotQuant legacy factors (reversal, volatility, volume_price,
# trend extras) — pure-Python implementations, no external dependencies
# ---------------------------------------------------------------------------

@factor_registry.register("WilliamsR")
def _calculate_williams_r(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Williams %R oscillator. Returns: williams_r (range -100..0)."""
    period = _require_positive_int(params.get("period", 14), label="WilliamsR.period")
    highs = [_read_number(bar, "high", label="WilliamsR") for bar in bars]
    lows = [_read_number(bar, "low", label="WilliamsR") for bar in bars]
    closes = [_read_number(bar, "close", label="WilliamsR") for bar in bars]
    roll_high = _rolling_max(highs, period)
    roll_low = _rolling_min(lows, period)
    rows: List[Dict[str, Any]] = []
    for bar, close, hh, ll in zip(bars, closes, roll_high, roll_low):
        value = None
        if hh is not None and ll is not None and (hh - ll) != 0:
            value = (hh - close) / (hh - ll) * -100.0
        rows.append({"timestamp": bar["timestamp"], "williams_r": value})
    return rows


@factor_registry.register("KDJ")
def _calculate_kdj(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """KDJ Stochastic — K, D, J lines. J = 3K - 2D.
    Returns: kdj_k, kdj_d, kdj_j per bar.
    """
    k_period = _require_positive_int(params.get("k_period", 9), label="KDJ.k_period")
    d_period = _require_positive_int(params.get("d_period", 3), label="KDJ.d_period")
    j_smooth = _require_positive_int(params.get("j_smooth", 3), label="KDJ.j_smooth")
    highs = [_read_number(bar, "high", label="KDJ") for bar in bars]
    lows = [_read_number(bar, "low", label="KDJ") for bar in bars]
    closes = [_read_number(bar, "close", label="KDJ") for bar in bars]
    roll_high = _rolling_max(highs, k_period)
    roll_low = _rolling_min(lows, k_period)

    rsv: List[Optional[float]] = []
    for close, hh, ll in zip(closes, roll_high, roll_low):
        if hh is None or ll is None or (hh - ll) == 0:
            rsv.append(None)
        else:
            rsv.append((close - ll) / (hh - ll) * 100.0)

    k_values = _ema(rsv, d_period)
    d_values = _ema(k_values, j_smooth)

    rows: List[Dict[str, Any]] = []
    for bar, k, d in zip(bars, k_values, d_values):
        j = None if k is None or d is None else 3.0 * k - 2.0 * d
        rows.append({"timestamp": bar["timestamp"], "kdj_k": k, "kdj_d": d, "kdj_j": j})
    return rows


@factor_registry.register("CCI")
def _calculate_cci(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Commodity Channel Index. Returns: cci."""
    period = _require_positive_int(params.get("period", 20), label="CCI.period")
    highs = [_read_number(bar, "high", label="CCI") for bar in bars]
    lows = [_read_number(bar, "low", label="CCI") for bar in bars]
    closes = [_read_number(bar, "close", label="CCI") for bar in bars]
    typical = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    tp_ma = _rolling_mean(typical, period)

    rows: List[Dict[str, Any]] = []
    window: List[float] = []
    for bar, tp, ma in zip(bars, typical, tp_ma):
        window.append(tp)
        if len(window) > period:
            window.pop(0)
        cci_value = None
        if ma is not None and len(window) == period:
            mad = sum(abs(v - ma) for v in window) / period
            if mad != 0:
                cci_value = (tp - ma) / (0.015 * mad)
        rows.append({"timestamp": bar["timestamp"], "cci": cci_value})
    return rows


@factor_registry.register("OBV")
def _calculate_obv(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """On-Balance Volume. Returns: obv (cumulative signed volume)."""
    closes = [_read_number(bar, "close", label="OBV") for bar in bars]
    volumes = [_read_number(bar, "volume", label="OBV") for bar in bars]
    obv = 0.0
    rows: List[Dict[str, Any]] = []
    for i, (bar, close, vol) in enumerate(zip(bars, closes, volumes)):
        if i > 0:
            prev = closes[i - 1]
            obv += vol if close > prev else (-vol if close < prev else 0.0)
        rows.append({"timestamp": bar["timestamp"], "obv": obv})
    return rows


@factor_registry.register("VWAP")
def _calculate_vwap(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Volume Weighted Average Price (session cumulative). Returns: vwap."""
    cum_tp_vol = 0.0
    cum_vol = 0.0
    rows: List[Dict[str, Any]] = []
    for bar in bars:
        high = _read_number(bar, "high", label="VWAP")
        low = _read_number(bar, "low", label="VWAP")
        close = _read_number(bar, "close", label="VWAP")
        vol = _read_number(bar, "volume", label="VWAP")
        tp = (high + low + close) / 3.0
        cum_tp_vol += tp * vol
        cum_vol += vol
        vwap = cum_tp_vol / cum_vol if cum_vol != 0 else None
        rows.append({"timestamp": bar["timestamp"], "vwap": vwap})
    return rows


@factor_registry.register("MFI")
def _calculate_mfi(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Money Flow Index (0-100). Returns: mfi."""
    period = _require_positive_int(params.get("period", 14), label="MFI.period")
    rows: List[Dict[str, Any]] = []
    tps: List[float] = []
    raw_mfs: List[float] = []
    for bar in bars:
        h = _read_number(bar, "high", label="MFI")
        l = _read_number(bar, "low", label="MFI")
        c = _read_number(bar, "close", label="MFI")
        v = _read_number(bar, "volume", label="MFI")
        tp = (h + l + c) / 3.0
        tps.append(tp)
        raw_mfs.append(tp * v)

    for i, bar in enumerate(bars):
        if i < period:
            rows.append({"timestamp": bar["timestamp"], "mfi": None})
            continue
        window_tp = tps[i - period + 1:i + 1]
        window_mf = raw_mfs[i - period + 1:i + 1]
        pos_sum = sum(mf for j, mf in enumerate(window_mf) if j > 0 and window_tp[j] > window_tp[j - 1])
        neg_sum = sum(mf for j, mf in enumerate(window_mf) if j > 0 and window_tp[j] < window_tp[j - 1])
        mfi = 100.0 - 100.0 / (1.0 + pos_sum / neg_sum) if neg_sum != 0 else 100.0
        rows.append({"timestamp": bar["timestamp"], "mfi": mfi})
    return rows


@factor_registry.register("ATRTrailingStop")
def _calculate_atr_trailing_stop(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ATR-based trailing stop level and direction.
    Returns: atr_trail_stop, atr_trail_direction (+1 bullish / -1 bearish).
    """
    period = _require_positive_int(params.get("period", 14), label="ATRTrailingStop.period")
    multiplier = _require_positive_float(
        params.get("multiplier", params.get("atr_multiplier", 2.0)),
        label="ATRTrailingStop.multiplier",
    )
    high_key = _read_column_name(params.get("high"), label="ATRTrailingStop.high", default="high")
    low_key = _read_column_name(params.get("low"), label="ATRTrailingStop.low", default="low")
    close_key = _read_column_name(params.get("close"), label="ATRTrailingStop.close", default="close")

    trs: List[float] = []
    previous_close: Optional[float] = None
    for bar in bars:
        h = _read_number(bar, high_key, label="ATRTrailingStop")
        l = _read_number(bar, low_key, label="ATRTrailingStop")
        c = _read_number(bar, close_key, label="ATRTrailingStop")
        tr = max(h - l, abs(h - previous_close) if previous_close else 0, abs(l - previous_close) if previous_close else 0)
        trs.append(tr)
        previous_close = c

    atr_values = _ema(trs, period)
    closes = [_read_number(bar, close_key, label="ATRTrailingStop") for bar in bars]

    trail_stop: Optional[float] = None
    direction = 1
    rows: List[Dict[str, Any]] = []
    for bar, close, atr in zip(bars, closes, atr_values):
        if atr is None:
            rows.append({"timestamp": bar["timestamp"], "atr_trail_stop": None, "atr_trail_direction": None})
            continue
        band = multiplier * atr
        if trail_stop is None:
            trail_stop = close - band
            direction = 1
        else:
            if direction == 1:
                new_stop = close - band
                trail_stop = max(trail_stop, new_stop)
                if close < trail_stop:
                    direction = -1
                    trail_stop = close + band
            else:
                new_stop = close + band
                trail_stop = min(trail_stop, new_stop)
                if close > trail_stop:
                    direction = 1
                    trail_stop = close - band
        rows.append({"timestamp": bar["timestamp"], "atr_trail_stop": trail_stop, "atr_trail_direction": float(direction)})
    return rows


@factor_registry.register("HistoricalVol")
def _calculate_historical_vol(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Historical (log-return) volatility. Returns: hist_vol."""
    period = _require_positive_int(params.get("period", 20), label="HistoricalVol.period")
    closes = [_read_number(bar, "close", label="HistoricalVol") for bar in bars]
    log_rets: List[Optional[float]] = [None]
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev > 0 and cur > 0:
            log_rets.append(math.log(cur / prev))
        else:
            log_rets.append(None)
    vol_values = _rolling_std([r if r is not None else 0.0 for r in log_rets], period)
    rows: List[Dict[str, Any]] = []
    for bar, vol in zip(bars, vol_values):
        rows.append({"timestamp": bar["timestamp"], "hist_vol": vol})
    return rows


@factor_registry.register("EMA_Cross")
def _calculate_ema_cross(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """EMA crossover: fast EMA minus slow EMA.
    Returns: ema_cross (positive = fast above slow = bullish).
    """
    fast = _require_positive_int(params.get("fast_period", params.get("fast", 10)), label="EMA_Cross.fast_period")
    slow = _require_positive_int(params.get("slow_period", params.get("slow", 20)), label="EMA_Cross.slow_period")
    source = _read_column_name(params.get("source"), label="EMA_Cross.source", default="close")
    values = [_read_number(bar, source, label="EMA_Cross") for bar in bars]
    ema_fast = _ema(values, fast)
    ema_slow = _ema(values, slow)
    rows: List[Dict[str, Any]] = []
    for bar, ef, es in zip(bars, ema_fast, ema_slow):
        cross = None if ef is None or es is None else ef - es
        rows.append({"timestamp": bar["timestamp"], "ema_cross": cross, "ema_fast": ef, "ema_slow": es})
    return rows


@factor_registry.register("EMA_Slope")
def _calculate_ema_slope(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalized EMA slope (first difference / previous EMA).
    Returns: ema_slope.
    """
    period = _require_positive_int(params.get("period", 20), label="EMA_Slope.period")
    source = _read_column_name(params.get("source"), label="EMA_Slope.source", default="close")
    values = [_read_number(bar, source, label="EMA_Slope") for bar in bars]
    ema_vals = _ema(values, period)
    rows: List[Dict[str, Any]] = []
    prev_ema: Optional[float] = None
    for bar, ema in zip(bars, ema_vals):
        slope = None
        if ema is not None and prev_ema is not None and prev_ema != 0:
            slope = (ema - prev_ema) / prev_ema
        if ema is not None:
            prev_ema = ema
        rows.append({"timestamp": bar["timestamp"], "ema_slope": slope})
    return rows


@factor_registry.register("DEMA")
def _calculate_dema(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Double Exponential Moving Average. DEMA = 2*EMA - EMA(EMA).
    Returns: dema.
    """
    period = _require_positive_int(params.get("period", 20), label="DEMA.period")
    source = _read_column_name(params.get("source"), label="DEMA.source", default="close")
    values = [_read_number(bar, source, label="DEMA") for bar in bars]
    ema1 = _ema(values, period)
    ema2 = _ema(ema1, period)
    rows: List[Dict[str, Any]] = []
    for bar, e1, e2 in zip(bars, ema1, ema2):
        dema = None if e1 is None or e2 is None else 2.0 * e1 - e2
        rows.append({"timestamp": bar["timestamp"], "dema": dema})
    return rows


@factor_registry.register("ParabolicSAR")
def _calculate_parabolic_sar(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parabolic SAR. Returns: psar (stop-and-reverse price), psar_direction (+1 long / -1 short)."""
    af_start = _require_positive_float(params.get("af_start", 0.02), label="ParabolicSAR.af_start")
    af_max = _require_positive_float(params.get("af_max", 0.2), label="ParabolicSAR.af_max")
    highs = [_read_number(bar, "high", label="ParabolicSAR") for bar in bars]
    lows = [_read_number(bar, "low", label="ParabolicSAR") for bar in bars]
    closes = [_read_number(bar, "close", label="ParabolicSAR") for bar in bars]
    n = len(closes)
    if n < 2:
        return [{"timestamp": bar["timestamp"], "psar": None, "psar_direction": None} for bar in bars]

    sar = [0.0] * n
    direction = [1] * n
    sar[0] = lows[0]
    ep = highs[0]
    af = af_start

    for i in range(1, n):
        prev_sar = sar[i - 1]
        prev_dir = direction[i - 1]
        if prev_dir == 1:
            new_sar = prev_sar + af * (ep - prev_sar)
            new_sar = min(new_sar, lows[i - 1])
            if i >= 2:
                new_sar = min(new_sar, lows[i - 2])
            if new_sar > lows[i]:
                direction[i] = -1
                sar[i] = ep
                ep = lows[i]
                af = af_start
            else:
                direction[i] = 1
                sar[i] = new_sar
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af + af_start, af_max)
        else:
            new_sar = prev_sar + af * (ep - prev_sar)
            new_sar = max(new_sar, highs[i - 1])
            if i >= 2:
                new_sar = max(new_sar, highs[i - 2])
            if new_sar < highs[i]:
                direction[i] = 1
                sar[i] = ep
                ep = highs[i]
                af = af_start
            else:
                direction[i] = -1
                sar[i] = new_sar
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af + af_start, af_max)

    return [
        {"timestamp": bar["timestamp"], "psar": sar[i], "psar_direction": float(direction[i])}
        for i, bar in enumerate(bars)
    ]


@factor_registry.register("Supertrend")
def _calculate_supertrend(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Supertrend band indicator. Returns: supertrend_stop, supertrend_direction (+1 bullish / -1 bearish)."""
    period = _require_positive_int(params.get("period", 10), label="Supertrend.period")
    multiplier = _require_positive_float(params.get("multiplier", 3.0), label="Supertrend.multiplier")
    highs = [_read_number(bar, "high", label="Supertrend") for bar in bars]
    lows = [_read_number(bar, "low", label="Supertrend") for bar in bars]
    closes = [_read_number(bar, "close", label="Supertrend") for bar in bars]
    n = len(closes)

    trs: List[float] = []
    prev_c: Optional[float] = None
    for h, l, c in zip(highs, lows, closes):
        tr = max(h - l, abs(h - prev_c) if prev_c else 0, abs(l - prev_c) if prev_c else 0)
        trs.append(tr)
        prev_c = c

    atr_values = _ema(trs, period)
    hl_avg = [(h + l) / 2.0 for h, l in zip(highs, lows)]

    supertrend = [0.0] * n
    direction = [1] * n

    for i in range(period, n):
        atr = atr_values[i]
        if atr is None:
            continue
        upper = hl_avg[i] + multiplier * atr
        lower = hl_avg[i] - multiplier * atr
        if i == period:
            if closes[i] <= upper:
                supertrend[i] = upper
                direction[i] = -1
            else:
                supertrend[i] = lower
                direction[i] = 1
        else:
            prev_st = supertrend[i - 1]
            prev_dir = direction[i - 1]
            if prev_dir == 1:
                lower = max(lower, prev_st)
                if closes[i] < lower:
                    supertrend[i] = upper
                    direction[i] = -1
                else:
                    supertrend[i] = lower
                    direction[i] = 1
            else:
                upper = min(upper, prev_st)
                if closes[i] > upper:
                    supertrend[i] = lower
                    direction[i] = 1
                else:
                    supertrend[i] = upper
                    direction[i] = -1

    return [
        {"timestamp": bar["timestamp"], "supertrend_stop": supertrend[i], "supertrend_direction": float(direction[i])}
        for i, bar in enumerate(bars)
    ]


@factor_registry.register("Ichimoku")
def _calculate_ichimoku(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Ichimoku Cloud. Returns: tenkan_sen, kijun_sen, senkou_a, senkou_b, ichimoku_signal."""
    tenkan = _require_positive_int(params.get("tenkan", 9), label="Ichimoku.tenkan")
    kijun = _require_positive_int(params.get("kijun", 26), label="Ichimoku.kijun")
    senkou_b_period = _require_positive_int(params.get("senkou_b", 52), label="Ichimoku.senkou_b")
    highs = [_read_number(bar, "high", label="Ichimoku") for bar in bars]
    lows = [_read_number(bar, "low", label="Ichimoku") for bar in bars]
    closes = [_read_number(bar, "close", label="Ichimoku") for bar in bars]

    def _midpoint(h_list: List[float], l_list: List[float], p: int) -> List[Optional[float]]:
        roll_h = _rolling_max(h_list, p)
        roll_l = _rolling_min(l_list, p)
        return [
            None if rh is None or rl is None else (rh + rl) / 2.0
            for rh, rl in zip(roll_h, roll_l)
        ]

    tenkan_vals = _midpoint(highs, lows, tenkan)
    kijun_vals = _midpoint(highs, lows, kijun)
    senkou_b_vals = _midpoint(highs, lows, senkou_b_period)

    rows: List[Dict[str, Any]] = []
    for bar, close, tk, kj, sb in zip(bars, closes, tenkan_vals, kijun_vals, senkou_b_vals):
        sa = None if tk is None or kj is None else (tk + kj) / 2.0
        signal = None if kj is None else (close - kj)
        rows.append({
            "timestamp": bar["timestamp"],
            "tenkan_sen": tk,
            "kijun_sen": kj,
            "senkou_a": sa,
            "senkou_b": sb,
            "ichimoku_signal": signal,
        })
    return rows


@factor_registry.register("WMA")
def _calculate_wma(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="WMA.period")
    source = _read_column_name(params.get("source"), label="WMA.source", default="close")
    values = [_read_number(bar, source, label="WMA") for bar in bars]
    wma_values = _rolling_weighted_mean(values, period)
    return [
        {
            "timestamp": bar["timestamp"],
            "wma": wma_value,
        }
        for bar, wma_value in zip(bars, wma_values)
    ]


@factor_registry.register("HMA")
def _calculate_hma(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="HMA.period")
    source = _read_column_name(params.get("source"), label="HMA.source", default="close")
    values = [_read_number(bar, source, label="HMA") for bar in bars]
    half_period = max(1, period // 2)
    sqrt_period = max(1, int(math.sqrt(period)))
    wma_half = _rolling_weighted_mean(values, half_period)
    wma_full = _rolling_weighted_mean(values, period)
    bridge_values = [
        None if half_value is None or full_value is None else 2.0 * half_value - full_value
        for half_value, full_value in zip(wma_half, wma_full)
    ]
    hma_values = _rolling_weighted_mean(bridge_values, sqrt_period)
    return [
        {
            "timestamp": bar["timestamp"],
            "hma": hma_value,
        }
        for bar, hma_value in zip(bars, hma_values)
    ]


@factor_registry.register("TEMA")
def _calculate_tema(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="TEMA.period")
    source = _read_column_name(params.get("source"), label="TEMA.source", default="close")
    values = [_read_number(bar, source, label="TEMA") for bar in bars]
    ema1 = _ema(values, period)
    ema2 = _ema(ema1, period)
    ema3 = _ema(ema2, period)
    rows: List[Dict[str, Any]] = []
    for bar, first, second, third in zip(bars, ema1, ema2, ema3):
        tema = None if first is None or second is None or third is None else 3.0 * first - 3.0 * second + third
        rows.append({"timestamp": bar["timestamp"], "tema": tema})
    return rows


@factor_registry.register("Stochastic")
def _calculate_stochastic(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    k_period = _require_positive_int(params.get("k_period", 14), label="Stochastic.k_period")
    d_period = _require_positive_int(params.get("d_period", 3), label="Stochastic.d_period")
    smooth_k = _require_positive_int(
        params.get("smooth_k", params.get("smooth", 1)),
        label="Stochastic.smooth_k",
    )
    high_key = _read_column_name(params.get("high"), label="Stochastic.high", default="high")
    low_key = _read_column_name(params.get("low"), label="Stochastic.low", default="low")
    close_key = _read_column_name(params.get("close"), label="Stochastic.close", default="close")
    highs = [_read_number(bar, high_key, label="Stochastic") for bar in bars]
    lows = [_read_number(bar, low_key, label="Stochastic") for bar in bars]
    closes = [_read_number(bar, close_key, label="Stochastic") for bar in bars]
    roll_high = _rolling_max(highs, k_period)
    roll_low = _rolling_min(lows, k_period)

    raw_k_values: List[Optional[float]] = []
    for close, highest, lowest in zip(closes, roll_high, roll_low):
        if highest is None or lowest is None or highest == lowest:
            raw_k_values.append(None)
        else:
            raw_k_values.append((close - lowest) / (highest - lowest) * 100.0)

    stoch_k_values = raw_k_values if smooth_k == 1 else _rolling_mean_optional(raw_k_values, smooth_k)
    stoch_d_values = _rolling_mean_optional(stoch_k_values, d_period)
    rows: List[Dict[str, Any]] = []
    for bar, stoch_k, stoch_d in zip(bars, stoch_k_values, stoch_d_values):
        rows.append({"timestamp": bar["timestamp"], "stoch_k": stoch_k, "stoch_d": stoch_d})
    return rows


@factor_registry.register("StochasticRSI")
def _calculate_stochastic_rsi(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    source = _read_column_name(params.get("source"), label="StochasticRSI.source", default="close")
    rsi_period = _require_positive_int(params.get("rsi_period", 14), label="StochasticRSI.rsi_period")
    stoch_period = _require_positive_int(
        params.get("stoch_period", 14),
        label="StochasticRSI.stoch_period",
    )
    k_period = _require_positive_int(params.get("k_period", 3), label="StochasticRSI.k_period")
    d_period = _require_positive_int(params.get("d_period", 3), label="StochasticRSI.d_period")
    rsi_rows = factor_registry.calculate("RSI", bars, {"source": source, "period": rsi_period}).rows
    rsi_values = [row.get("rsi") for row in rsi_rows]

    raw_values: List[Optional[float]] = []
    window: List[Optional[float]] = []
    for rsi_value in rsi_values:
        window.append(rsi_value)
        if len(window) > stoch_period:
            window.pop(0)
        if len(window) == stoch_period and all(item is not None for item in window):
            numeric_window = [float(item) for item in window]
            highest = max(numeric_window)
            lowest = min(numeric_window)
            if highest == lowest:
                raw_values.append(0.0)
            else:
                raw_values.append((float(rsi_value) - lowest) / (highest - lowest) * 100.0)
        else:
            raw_values.append(None)

    stochrsi_k_values = _rolling_mean_optional(raw_values, k_period)
    stochrsi_d_values = _rolling_mean_optional(stochrsi_k_values, d_period)
    rows: List[Dict[str, Any]] = []
    for bar, stochrsi_k, stochrsi_d in zip(bars, stochrsi_k_values, stochrsi_d_values):
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "stochrsi_k": stochrsi_k,
                "stochrsi_d": stochrsi_d,
            }
        )
    return rows


@factor_registry.register("ROC")
def _calculate_roc(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 12), label="ROC.period")
    source = _read_column_name(params.get("source"), label="ROC.source", default="close")
    values = [_read_number(bar, source, label="ROC") for bar in bars]
    rows: List[Dict[str, Any]] = []
    for index, (bar, value) in enumerate(zip(bars, values)):
        roc = None
        if index >= period and values[index - period] != 0:
            roc = (value - values[index - period]) / values[index - period] * 100.0
        rows.append({"timestamp": bar["timestamp"], "roc": roc})
    return rows


@factor_registry.register("MOM")
def _calculate_mom(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 10), label="MOM.period")
    source = _read_column_name(params.get("source"), label="MOM.source", default="close")
    values = [_read_number(bar, source, label="MOM") for bar in bars]
    rows: List[Dict[str, Any]] = []
    for index, (bar, value) in enumerate(zip(bars, values)):
        momentum = None if index < period else value - values[index - period]
        rows.append({"timestamp": bar["timestamp"], "mom": momentum})
    return rows


@factor_registry.register("CMO")
def _calculate_cmo(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="CMO.period")
    source = _read_column_name(params.get("source"), label="CMO.source", default="close")
    values = [_read_number(bar, source, label="CMO") for bar in bars]
    changes = [0.0]
    for previous, current in zip(values, values[1:]):
        changes.append(current - previous)

    rows: List[Dict[str, Any]] = []
    for index, bar in enumerate(bars):
        cmo = None
        if index >= period:
            window = changes[index - period + 1:index + 1]
            up_sum = sum(max(change, 0.0) for change in window)
            down_sum = sum(max(-change, 0.0) for change in window)
            denominator = up_sum + down_sum
            cmo = 0.0 if denominator == 0 else (up_sum - down_sum) / denominator * 100.0
        rows.append({"timestamp": bar["timestamp"], "cmo": cmo})
    return rows


@factor_registry.register("KeltnerChannel")
def _calculate_keltner_channel(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    source = _read_column_name(params.get("source"), label="KeltnerChannel.source", default="close")
    ema_period = _require_positive_int(
        params.get("ema_period", params.get("period", 20)),
        label="KeltnerChannel.ema_period",
    )
    atr_period = _require_positive_int(
        params.get("atr_period", ema_period),
        label="KeltnerChannel.atr_period",
    )
    multiplier = _require_positive_float(
        params.get("multiplier", 2.0),
        label="KeltnerChannel.multiplier",
    )
    high_key = _read_column_name(params.get("high"), label="KeltnerChannel.high", default="high")
    low_key = _read_column_name(params.get("low"), label="KeltnerChannel.low", default="low")
    close_key = _read_column_name(params.get("close"), label="KeltnerChannel.close", default="close")
    mid_rows = factor_registry.calculate("EMA", bars, {"source": source, "period": ema_period}).rows
    atr_rows = factor_registry.calculate(
        "ATR",
        bars,
        {"high": high_key, "low": low_key, "close": close_key, "period": atr_period},
    ).rows

    rows: List[Dict[str, Any]] = []
    for bar, mid_row, atr_row in zip(bars, mid_rows, atr_rows):
        middle = mid_row.get("ema")
        atr_value = atr_row.get("atr")
        upper = None if middle is None or atr_value is None else middle + multiplier * atr_value
        lower = None if middle is None or atr_value is None else middle - multiplier * atr_value
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "keltner_mid": middle,
                "keltner_upper": upper,
                "keltner_lower": lower,
            }
        )
    return rows


@factor_registry.register("NTR")
def _calculate_ntr(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="NTR.period")
    scale = _require_positive_float(params.get("scale", 100.0), label="NTR.scale")
    high_key = _read_column_name(params.get("high"), label="NTR.high", default="high")
    low_key = _read_column_name(params.get("low"), label="NTR.low", default="low")
    close_key = _read_column_name(params.get("close"), label="NTR.close", default="close")
    closes = [_read_number(bar, close_key, label="NTR") for bar in bars]
    atr_rows = factor_registry.calculate(
        "ATR",
        bars,
        {"high": high_key, "low": low_key, "close": close_key, "period": period},
    ).rows
    rows: List[Dict[str, Any]] = []
    for bar, close, atr_row in zip(bars, closes, atr_rows):
        atr_value = atr_row.get("atr")
        ntr = None if atr_value is None or close == 0 else atr_value / close * scale
        rows.append({"timestamp": bar["timestamp"], "ntr": ntr})
    return rows


@factor_registry.register("Aroon")
def _calculate_aroon(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 25), label="Aroon.period")
    high_key = _read_column_name(params.get("high"), label="Aroon.high", default="high")
    low_key = _read_column_name(params.get("low"), label="Aroon.low", default="low")
    highs = [_read_number(bar, high_key, label="Aroon") for bar in bars]
    lows = [_read_number(bar, low_key, label="Aroon") for bar in bars]
    rows: List[Dict[str, Any]] = []

    for index, bar in enumerate(bars):
        aroon_up = None
        aroon_down = None
        oscillator = None
        if index + 1 >= period:
            high_window = highs[index - period + 1:index + 1]
            low_window = lows[index - period + 1:index + 1]
            highest = max(high_window)
            lowest = min(low_window)
            periods_since_high = period - 1 - max(
                idx for idx, value in enumerate(high_window) if value == highest
            )
            periods_since_low = period - 1 - max(
                idx for idx, value in enumerate(low_window) if value == lowest
            )
            aroon_up = (period - periods_since_high) / period * 100.0
            aroon_down = (period - periods_since_low) / period * 100.0
            oscillator = aroon_up - aroon_down
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "aroon_up": aroon_up,
                "aroon_down": aroon_down,
                "aroon_oscillator": oscillator,
            }
        )
    return rows


@factor_registry.register("TRIX")
def _calculate_trix(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 15), label="TRIX.period")
    signal_period = _require_positive_int(params.get("signal", 9), label="TRIX.signal")
    source = _read_column_name(params.get("source"), label="TRIX.source", default="close")
    values = [_read_number(bar, source, label="TRIX") for bar in bars]
    ema1 = _ema(values, period)
    ema2 = _ema(ema1, period)
    ema3 = _ema(ema2, period)

    trix_values: List[Optional[float]] = [None]
    for previous, current in zip(ema3, ema3[1:]):
        if previous in {None, 0.0} or current is None:
            trix_values.append(None)
        else:
            trix_values.append((current - previous) / previous * 100.0)

    signal_values = _ema(trix_values, signal_period)
    rows: List[Dict[str, Any]] = []
    for bar, trix_value, signal_value in zip(bars, trix_values, signal_values):
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "trix": trix_value,
                "trix_signal": signal_value,
            }
        )
    return rows


@factor_registry.register("LinReg")
def _calculate_linreg(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="LinReg.period")
    source = _read_column_name(params.get("source"), label="LinReg.source", default="close")
    values = [_read_number(bar, source, label="LinReg") for bar in bars]
    x_values = list(range(period))
    x_sum = sum(x_values)
    x_sq_sum = sum(value * value for value in x_values)
    denominator = period * x_sq_sum - x_sum * x_sum
    rows: List[Dict[str, Any]] = []

    for index, bar in enumerate(bars):
        reg_value = None
        slope = None
        r_squared = None
        if index + 1 >= period and denominator != 0:
            window = values[index - period + 1:index + 1]
            y_sum = sum(window)
            xy_sum = sum(x * y for x, y in zip(x_values, window))
            slope = (period * xy_sum - x_sum * y_sum) / denominator
            intercept = (y_sum - slope * x_sum) / period
            reg_value = intercept + slope * (period - 1)
            mean_y = y_sum / period
            fitted = [intercept + slope * x for x in x_values]
            ss_tot = sum((value - mean_y) ** 2 for value in window)
            ss_res = sum((value - fit) ** 2 for value, fit in zip(window, fitted))
            r_squared = 1.0 if ss_tot == 0 else max(0.0, min(1.0, 1.0 - ss_res / ss_tot))
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "linreg": reg_value,
                "linreg_slope": slope,
                "linreg_r2": r_squared,
            }
        )
    return rows


@factor_registry.register("ChaikinAD")
def _calculate_chaikin_ad(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    high_key = _read_column_name(params.get("high"), label="ChaikinAD.high", default="high")
    low_key = _read_column_name(params.get("low"), label="ChaikinAD.low", default="low")
    close_key = _read_column_name(params.get("close"), label="ChaikinAD.close", default="close")
    volume_key = _read_column_name(params.get("volume"), label="ChaikinAD.volume", default="volume")
    ad_value = 0.0
    rows: List[Dict[str, Any]] = []

    for bar in bars:
        high = _read_number(bar, high_key, label="ChaikinAD")
        low = _read_number(bar, low_key, label="ChaikinAD")
        close = _read_number(bar, close_key, label="ChaikinAD")
        volume = _read_number(bar, volume_key, label="ChaikinAD")
        spread = high - low
        money_flow_multiplier = 0.0 if spread == 0 else ((close - low) - (high - close)) / spread
        ad_value += money_flow_multiplier * volume
        rows.append({"timestamp": bar["timestamp"], "chaikin_ad": ad_value})
    return rows


@factor_registry.register("CMF")
def _calculate_cmf(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="CMF.period")
    high_key = _read_column_name(params.get("high"), label="CMF.high", default="high")
    low_key = _read_column_name(params.get("low"), label="CMF.low", default="low")
    close_key = _read_column_name(params.get("close"), label="CMF.close", default="close")
    volume_key = _read_column_name(params.get("volume"), label="CMF.volume", default="volume")
    money_flow_volume: List[float] = []
    volumes: List[float] = []

    for bar in bars:
        high = _read_number(bar, high_key, label="CMF")
        low = _read_number(bar, low_key, label="CMF")
        close = _read_number(bar, close_key, label="CMF")
        volume = _read_number(bar, volume_key, label="CMF")
        spread = high - low
        multiplier = 0.0 if spread == 0 else ((close - low) - (high - close)) / spread
        money_flow_volume.append(multiplier * volume)
        volumes.append(volume)

    mfv_sum = _rolling_sum(money_flow_volume, period)
    volume_sum = _rolling_sum(volumes, period)
    rows: List[Dict[str, Any]] = []
    for bar, current_mfv_sum, current_volume_sum in zip(bars, mfv_sum, volume_sum):
        cmf = None
        if current_mfv_sum is not None and current_volume_sum not in {None, 0.0}:
            cmf = current_mfv_sum / current_volume_sum
        rows.append({"timestamp": bar["timestamp"], "cmf": cmf})
    return rows


@factor_registry.register("PVT")
def _calculate_pvt(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    close_key = _read_column_name(params.get("close"), label="PVT.close", default="close")
    volume_key = _read_column_name(params.get("volume"), label="PVT.volume", default="volume")
    closes = [_read_number(bar, close_key, label="PVT") for bar in bars]
    volumes = [_read_number(bar, volume_key, label="PVT") for bar in bars]
    pvt = 0.0
    rows: List[Dict[str, Any]] = []

    for index, (bar, close, volume) in enumerate(zip(bars, closes, volumes)):
        if index > 0 and closes[index - 1] != 0:
            pvt += volume * (close - closes[index - 1]) / closes[index - 1]
        rows.append({"timestamp": bar["timestamp"], "pvt": pvt})
    return rows


@factor_registry.register("Stdev")
def _calculate_stdev(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="Stdev.period")
    source = _read_column_name(params.get("source"), label="Stdev.source", default="close")
    values = [_read_number(bar, source, label="Stdev") for bar in bars]
    std_values = _rolling_std(values, period)
    return [
        {
            "timestamp": bar["timestamp"],
            "stdev": std_value,
        }
        for bar, std_value in zip(bars, std_values)
    ]


@factor_registry.register("ZScore")
def _calculate_zscore(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="ZScore.period")
    source = _read_column_name(params.get("source"), label="ZScore.source", default="close")
    values = [_read_number(bar, source, label="ZScore") for bar in bars]
    means = _rolling_mean(values, period)
    stds = _rolling_std(values, period)
    rows: List[Dict[str, Any]] = []
    for bar, value, mean, std in zip(bars, values, means, stds):
        zscore = None if mean is None or std in {None, 0.0} else (value - mean) / std
        rows.append({"timestamp": bar["timestamp"], "zscore": zscore})
    return rows


@factor_registry.register("BullBearPower")
def _calculate_bull_bear_power(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 13), label="BullBearPower.period")
    high_key = _read_column_name(params.get("high"), label="BullBearPower.high", default="high")
    low_key = _read_column_name(params.get("low"), label="BullBearPower.low", default="low")
    close_key = _read_column_name(params.get("close"), label="BullBearPower.close", default="close")
    ema_rows = factor_registry.calculate("EMA", bars, {"source": close_key, "period": period}).rows
    highs = [_read_number(bar, high_key, label="BullBearPower") for bar in bars]
    lows = [_read_number(bar, low_key, label="BullBearPower") for bar in bars]
    rows: List[Dict[str, Any]] = []

    for bar, high, low, ema_row in zip(bars, highs, lows, ema_rows):
        ema_value = ema_row.get("ema")
        bull_power = None if ema_value is None else high - ema_value
        bear_power = None if ema_value is None else low - ema_value
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "bull_power": bull_power,
                "bear_power": bear_power,
            }
        )
    return rows


@factor_registry.register("DPO")
def _calculate_dpo(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="DPO.period")
    source = _read_column_name(params.get("source"), label="DPO.source", default="close")
    values = [_read_number(bar, source, label="DPO") for bar in bars]
    sma_values = _rolling_mean(values, period)
    lag = period // 2 + 1
    rows: List[Dict[str, Any]] = []

    for index, (bar, sma_value) in enumerate(zip(bars, sma_values)):
        reference_index = index - lag
        dpo = None
        if sma_value is not None and reference_index >= 0:
            dpo = values[reference_index] - sma_value
        rows.append({"timestamp": bar["timestamp"], "dpo": dpo})
    return rows


@factor_registry.register("Spread")
def _calculate_spread(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute price spread between two columns with rolling z-score normalization.

    Returns per-bar: spread, spread_mean, spread_std, spread_zscore.
    col_a defaults to "close"; col_b defaults to "close_ref".
    """
    period = _require_positive_int(params.get("period", 20), label="Spread.period")
    col_a = _read_column_name(params.get("col_a"), label="Spread.col_a", default="close")
    col_b = _read_column_name(params.get("col_b"), label="Spread.col_b", default="close_ref")

    spread_values: List[Optional[float]] = []
    for bar in bars:
        a = bar.get(col_a)
        b = bar.get(col_b)
        if a is not None and b is not None:
            try:
                spread_values.append(float(a) - float(b))
            except (TypeError, ValueError):
                spread_values.append(None)
        else:
            spread_values.append(None)

    mean_values = _rolling_mean_optional(spread_values, period)
    std_values = _rolling_std_optional(spread_values, period)

    rows: List[Dict[str, Any]] = []
    for bar, spread, mean, std in zip(bars, spread_values, mean_values, std_values):
        zscore: Optional[float] = None
        if spread is not None and mean is not None and std is not None and std > 0.0:
            zscore = (spread - mean) / std
        rows.append(
            {
                "timestamp": bar["timestamp"],
                "spread": spread,
                "spread_mean": mean,
                "spread_std": std,
                "spread_zscore": zscore,
            }
        )
    return rows


@factor_registry.register("Spread_RSI")
def _calculate_spread_rsi(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute RSI of the price spread between two columns.

    Returns per-bar: spread_rsi.
    col_a defaults to "close"; col_b defaults to "close_ref".
    """
    period = _require_positive_int(params.get("period", 14), label="Spread_RSI.period")
    col_a = _read_column_name(params.get("col_a"), label="Spread_RSI.col_a", default="close")
    col_b = _read_column_name(params.get("col_b"), label="Spread_RSI.col_b", default="close_ref")

    spread_values: List[Optional[float]] = []
    for bar in bars:
        a = bar.get(col_a)
        b = bar.get(col_b)
        if a is not None and b is not None:
            try:
                spread_values.append(float(a) - float(b))
            except (TypeError, ValueError):
                spread_values.append(None)
        else:
            spread_values.append(None)

    changes: List[Optional[float]] = [None]
    for prev, curr in zip(spread_values, spread_values[1:]):
        if prev is None or curr is None:
            changes.append(None)
        else:
            changes.append(curr - prev)

    gains: List[Optional[float]] = [max(c, 0.0) if c is not None else None for c in changes]
    losses: List[Optional[float]] = [max(-c, 0.0) if c is not None else None for c in changes]

    avg_gain = _ema(gains, period)
    avg_loss = _ema(losses, period)

    rows: List[Dict[str, Any]] = []
    for bar, g, loss in zip(bars, avg_gain, avg_loss):
        rsi: Optional[float] = None
        if g is not None and loss is not None:
            if loss == 0.0:
                rsi = 50.0 if g == 0.0 else 100.0
            else:
                rsi = 100.0 - 100.0 / (1.0 + g / loss)
        rows.append({"timestamp": bar["timestamp"], "spread_rsi": rsi})
    return rows


# TASK-0084: 导出 backtest 端因子 hash 映射
def export_backtest_hash_map() -> Dict[str, str]:
    """导出 backtest 端所有因子的 hash 映射。

    Returns:
        Dict[因子名称, hash]
    """
    try:
        from shared.python_common.factors.registry import get_global_registry
        global_registry = get_global_registry()
        return global_registry.export_hash_map()
    except ImportError:
        logger.warning("共享因子注册表未加载，无法导出 hash 映射")
        return {}