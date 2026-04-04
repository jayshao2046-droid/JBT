from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

try:
    from .strategy_base import StrategyConfigError
except ImportError:
    from strategy_base import StrategyConfigError

FactorCalculator = Callable[[List[Dict[str, Any]], Dict[str, Any]], List[Dict[str, Any]]]

OFFICIAL_FACTOR_BASELINE = (
    "ADX",
    "ATR",
    "BollingerBands",
    "CCI",
    "DEMA",
    "EMA",
    "Ichimoku",
    "MACD",
    "MFI",
    "OBV",
    "ParabolicSAR",
    "RSI",
    "SMA",
    "Supertrend",
    "VolumeRatio",
    "VWAP",
    "WilliamsR",
    "GarmanKlass",
    "HistoricalVol",
    "ImpliedVolatility",
    "VolatilityFactor",
    "BasisSpread",
    "CointResidual",
    "SpreadCrosscommodity",
    "SpreadCrossperiod",
    "SpreadRatio",
    "ZScoreSpread",
    "NewsSentiment",
    "SocialSentiment",
    "SentimentFactor",
    "InventoryFactor",
    "OpenInterestFactor",
    "WarehouseReceiptFactor",
)


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

    def register(
        self,
        factor_name: str,
        calculator: Optional[FactorCalculator] = None,
    ) -> Any:
        if calculator is None:
            return lambda func: self.register(factor_name, func)

        self._calculators[_normalize_factor_name(factor_name)] = calculator
        return calculator

    def calculate(
        self,
        factor_name: str,
        bars: Any,
        params: Optional[Mapping[str, Any]] = None,
    ) -> FactorResult:
        normalized_name = _normalize_factor_name(factor_name)
        calculator = self._calculators.get(normalized_name)
        if calculator is None:
            raise StrategyConfigError(f"Unsupported factor {factor_name}")

        normalized_bars = normalize_bars(bars)
        rows = calculator(normalized_bars, dict(params or {}))
        return FactorResult(factor_name=factor_name, rows=rows)

    def list_factors(self) -> List[str]:
        return sorted(self._calculators)


factor_registry = FactorRegistry()


def _normalize_factor_name(factor_name: str) -> str:
    if not isinstance(factor_name, str) or not factor_name.strip():
        raise StrategyConfigError("factor_name must be a non-empty string")
    return factor_name.strip().lower()


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
    if coerced <= 0:
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


def _append_candidate_keys(target: List[str], raw_value: Any) -> None:
    if isinstance(raw_value, str) and raw_value.strip():
        target.append(raw_value.strip())
        return
    if isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes, bytearray)):
        for item in raw_value:
            if isinstance(item, str) and item.strip():
                target.append(item.strip())


def _candidate_keys(
    params: Mapping[str, Any],
    *default_keys: str,
    param_keys: Sequence[str] = ("column",),
) -> List[str]:
    keys: List[str] = []
    for param_key in param_keys:
        _append_candidate_keys(keys, params.get(param_key))
    for default_key in default_keys:
        _append_candidate_keys(keys, default_key)

    deduped: List[str] = []
    seen = set()
    for key in keys:
        if key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped


def _read_optional_number_from_keys(
    bar: Mapping[str, Any],
    keys: Sequence[str],
    *,
    label: str,
) -> Optional[float]:
    for key in keys:
        if key not in bar:
            continue
        value = bar[key]
        if value in {None, ""}:
            continue
        if isinstance(value, bool):
            raise StrategyConfigError(f"bars[{key}] must be numeric for {label}")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise StrategyConfigError(f"bars[{key}] must be numeric for {label}") from exc
    return None


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
        value = float(value)
        window.append(value)
        running_total += value
        if len(window) > period:
            running_total -= window.pop(0)
        if len(window) == period:
            result.append(running_total / period)
        else:
            result.append(None)
    return result


def _rolling_sum(values: Sequence[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    window: List[float] = []
    running_total = 0.0

    for value in values:
        value = float(value)
        window.append(value)
        running_total += value
        if len(window) > period:
            running_total -= window.pop(0)
        if len(window) == period:
            result.append(running_total)
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


def _build_rows(
    bars: Sequence[Mapping[str, Any]],
    **series_map: Sequence[Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, bar in enumerate(bars):
        row = {"timestamp": bar["timestamp"]}
        for key, series in series_map.items():
            row[key] = series[index]
        rows.append(row)
    return rows


def _close_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    return [_read_number(bar, "close", label=label) for bar in bars]


def _open_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    return [_read_number(bar, "open", label=label) for bar in bars]


def _high_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    return [_read_number(bar, "high", label=label) for bar in bars]


def _low_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    return [_read_number(bar, "low", label=label) for bar in bars]


def _volume_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    return [_read_number(bar, "volume", label=label) for bar in bars]


def _typical_price_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    highs = _high_series(bars, label=label)
    lows = _low_series(bars, label=label)
    closes = _close_series(bars, label=label)
    return [(high + low + close) / 3.0 for high, low, close in zip(highs, lows, closes)]


def _true_range_series(bars: Sequence[Mapping[str, Any]], *, label: str) -> List[float]:
    trs: List[float] = []
    previous_close: Optional[float] = None
    for bar in bars:
        high = _read_number(bar, "high", label=label)
        low = _read_number(bar, "low", label=label)
        close = _read_number(bar, "close", label=label)
        if previous_close is None:
            true_range = high - low
        else:
            true_range = max(high - low, abs(high - previous_close), abs(low - previous_close))
        trs.append(true_range)
        previous_close = close
    return trs


def _spread_values(
    bars: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    *,
    label: str,
    explicit_keys: Sequence[str],
    reference_keys: Sequence[str],
    mode: str = "difference",
) -> List[float]:
    explicit_candidates = _candidate_keys(
        params,
        *explicit_keys,
        param_keys=("column", "spread_column", "value_column"),
    )
    reference_candidates = _candidate_keys(
        params,
        *reference_keys,
        param_keys=("reference_column", "pair_column", "spot_column", "benchmark_column"),
    )
    hedge_ratio = float(params.get("hedge_ratio", 1.0))

    values: List[float] = []
    for bar in bars:
        explicit_value = _read_optional_number_from_keys(bar, explicit_candidates, label=label)
        if explicit_value is not None:
            values.append(explicit_value)
            continue

        reference_value = _read_optional_number_from_keys(bar, reference_candidates, label=label)
        if reference_value is None:
            values.append(0.0)
            continue

        close = _read_number(bar, "close", label=label)
        if mode == "ratio":
            values.append(0.0 if reference_value == 0 else close / reference_value - 1.0)
        else:
            values.append(close - hedge_ratio * reference_value)
    return values


def _single_column_values(
    bars: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    *,
    label: str,
    default_keys: Sequence[str],
    neutral_value: float = 0.0,
) -> List[float]:
    candidates = _candidate_keys(
        params,
        *default_keys,
        param_keys=("column", "value_column", "source_column"),
    )
    values: List[float] = []
    for bar in bars:
        value = _read_optional_number_from_keys(bar, candidates, label=label)
        values.append(neutral_value if value is None else value)
    return values


def _change_factor_rows(
    bars: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    *,
    label: str,
    output_key: str,
    explicit_keys: Sequence[str],
    raw_keys: Sequence[str],
) -> List[Dict[str, Any]]:
    explicit_candidates = _candidate_keys(
        params,
        *explicit_keys,
        param_keys=("column", "factor_column", "value_column"),
    )
    raw_candidates = _candidate_keys(
        params,
        *raw_keys,
        param_keys=("raw_column", "source_column", "base_column"),
    )

    factor_values: List[float] = []
    raw_values: List[float] = []
    delta_values: List[Optional[float]] = []
    previous_raw: Optional[float] = None

    for bar in bars:
        explicit_value = _read_optional_number_from_keys(bar, explicit_candidates, label=label)
        raw_value = _read_optional_number_from_keys(bar, raw_candidates, label=label)

        if explicit_value is not None:
            factor_value = explicit_value
        elif raw_value is not None and previous_raw not in {None, 0.0}:
            factor_value = (raw_value - previous_raw) / abs(previous_raw)
        elif raw_value is not None and previous_raw is not None:
            factor_value = raw_value - previous_raw
        else:
            factor_value = 0.0

        delta = None if raw_value is None or previous_raw is None else raw_value - previous_raw
        factor_values.append(factor_value)
        raw_values.append(0.0 if raw_value is None else raw_value)
        delta_values.append(delta)
        if raw_value is not None:
            previous_raw = raw_value

    return _build_rows(
        bars,
        **{
            output_key: factor_values,
            f"{output_key}_raw": raw_values,
            f"{output_key}_delta": delta_values,
        },
    )


@factor_registry.register("MACD")
def _calculate_macd(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    fast = _require_positive_int(params.get("fast", 12), label="MACD.fast")
    slow = _require_positive_int(params.get("slow", 26), label="MACD.slow")
    signal = _require_positive_int(params.get("signal", 9), label="MACD.signal")

    closes = _close_series(bars, label="MACD")
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line = [
        None if fast_value is None or slow_value is None else fast_value - slow_value
        for fast_value, slow_value in zip(ema_fast, ema_slow)
    ]
    signal_line = _ema(macd_line, signal)
    histogram = [
        None if macd_value is None or signal_value is None else macd_value - signal_value
        for macd_value, signal_value in zip(macd_line, signal_line)
    ]
    return _build_rows(
        bars,
        macd_line=macd_line,
        macd_signal=signal_line,
        macd_hist=histogram,
    )


@factor_registry.register("RSI")
def _calculate_rsi(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="RSI.period")
    closes = _close_series(bars, label="RSI")

    changes: List[float] = [0.0]
    for previous, current in zip(closes, closes[1:]):
        changes.append(current - previous)

    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    avg_gain = _ema(gains, period)
    avg_loss = _ema(losses, period)

    rsi_values: List[Optional[float]] = []
    slopes: List[Optional[float]] = []
    previous_rsi: Optional[float] = None
    for gain_value, loss_value in zip(avg_gain, avg_loss):
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

        rsi_values.append(rsi_value)
        slopes.append(slope)

    return _build_rows(bars, rsi=rsi_values, rsi_slope=slopes)


@factor_registry.register("VolumeRatio")
def _calculate_volume_ratio(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 5), label="VolumeRatio.period")
    volumes = _volume_series(bars, label="VolumeRatio")
    averages = _rolling_mean(volumes, period)
    ratios = [
        None if average in {None, 0.0} else volume / average
        for volume, average in zip(volumes, averages)
    ]
    return _build_rows(bars, volume_ratio=ratios)


@factor_registry.register("ATR")
def _calculate_atr(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="ATR.period")
    atr_values = _ema(_true_range_series(bars, label="ATR"), period)
    return _build_rows(bars, atr=atr_values)


@factor_registry.register("ADX")
def _calculate_adx(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="ADX.period")
    highs = _high_series(bars, label="ADX")
    lows = _low_series(bars, label="ADX")
    closes = _close_series(bars, label="ADX")
    trs: List[float] = []
    plus_dm: List[float] = []
    minus_dm: List[float] = []

    previous_high: Optional[float] = None
    previous_low: Optional[float] = None
    previous_close: Optional[float] = None

    for high, low, close in zip(highs, lows, closes):
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
    return _build_rows(bars, adx=adx_values)


@factor_registry.register("EMA")
def _calculate_ema_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="EMA.period")
    closes = _close_series(bars, label="EMA")
    ema_values = _ema(closes, period)
    gap_values = [
        None if ema_value is None else close - ema_value
        for close, ema_value in zip(closes, ema_values)
    ]
    return _build_rows(bars, ema=ema_values, ema_gap=gap_values)


@factor_registry.register("SMA")
def _calculate_sma_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="SMA.period")
    closes = _close_series(bars, label="SMA")
    sma_values = _rolling_mean(closes, period)
    gaps = [
        None if sma_value is None else close - sma_value
        for close, sma_value in zip(closes, sma_values)
    ]
    return _build_rows(bars, sma=sma_values, sma_gap=gaps)


@factor_registry.register("DEMA")
def _calculate_dema_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="DEMA.period")
    closes = _close_series(bars, label="DEMA")
    ema_one = _ema(closes, period)
    ema_two = _ema(ema_one, period)
    dema_values = [
        None if ema_a is None or ema_b is None else 2.0 * ema_a - ema_b
        for ema_a, ema_b in zip(ema_one, ema_two)
    ]
    return _build_rows(bars, dema=dema_values)


@factor_registry.register("BollingerBands")
def _calculate_bollinger_bands(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="BollingerBands.period")
    stddev_multiplier = _require_positive_float(
        params.get("stddev", params.get("multiplier", 2.0)),
        label="BollingerBands.stddev",
    )
    closes = _close_series(bars, label="BollingerBands")
    means = _rolling_mean(closes, period)
    stds = _rolling_std(closes, period)

    upper_band: List[Optional[float]] = []
    lower_band: List[Optional[float]] = []
    bandwidth: List[Optional[float]] = []
    percent_b: List[Optional[float]] = []
    for close, mean, std in zip(closes, means, stds):
        if mean is None or std is None:
            upper_band.append(None)
            lower_band.append(None)
            bandwidth.append(None)
            percent_b.append(None)
            continue
        upper = mean + stddev_multiplier * std
        lower = mean - stddev_multiplier * std
        width = None if mean == 0 else (upper - lower) / abs(mean)
        band_range = upper - lower
        band_position = None if band_range == 0 else (close - lower) / band_range
        upper_band.append(upper)
        lower_band.append(lower)
        bandwidth.append(width)
        percent_b.append(band_position)

    return _build_rows(
        bars,
        bollinger_mid=means,
        bollinger_upper=upper_band,
        bollinger_lower=lower_band,
        bollinger_width=bandwidth,
        bollinger_percent_b=percent_b,
    )


@factor_registry.register("CCI")
def _calculate_cci(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="CCI.period")
    typical_prices = _typical_price_series(bars, label="CCI")
    averages = _rolling_mean(typical_prices, period)

    cci_values: List[Optional[float]] = []
    for index, typical_price in enumerate(typical_prices):
        average = averages[index]
        if average is None or index + 1 < period:
            cci_values.append(None)
            continue
        window = typical_prices[index + 1 - period : index + 1]
        mean_deviation = sum(abs(value - average) for value in window) / period
        if mean_deviation == 0:
            cci_values.append(0.0)
            continue
        cci_values.append((typical_price - average) / (0.015 * mean_deviation))

    return _build_rows(bars, cci=cci_values)


@factor_registry.register("Ichimoku")
def _calculate_ichimoku(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    conversion_period = _require_positive_int(
        params.get("conversion_period", 9),
        label="Ichimoku.conversion_period",
    )
    base_period = _require_positive_int(
        params.get("base_period", 26),
        label="Ichimoku.base_period",
    )
    span_b_period = _require_positive_int(
        params.get("span_b_period", 52),
        label="Ichimoku.span_b_period",
    )
    highs = _high_series(bars, label="Ichimoku")
    lows = _low_series(bars, label="Ichimoku")
    closes = _close_series(bars, label="Ichimoku")
    conversion_high = _rolling_max(highs, conversion_period)
    conversion_low = _rolling_min(lows, conversion_period)
    base_high = _rolling_max(highs, base_period)
    base_low = _rolling_min(lows, base_period)
    span_b_high = _rolling_max(highs, span_b_period)
    span_b_low = _rolling_min(lows, span_b_period)

    conversion_line = [
        None if high is None or low is None else (high + low) / 2.0
        for high, low in zip(conversion_high, conversion_low)
    ]
    base_line = [
        None if high is None or low is None else (high + low) / 2.0
        for high, low in zip(base_high, base_low)
    ]
    span_a = [
        None if conversion is None or base is None else (conversion + base) / 2.0
        for conversion, base in zip(conversion_line, base_line)
    ]
    span_b = [
        None if high is None or low is None else (high + low) / 2.0
        for high, low in zip(span_b_high, span_b_low)
    ]
    cloud_bias: List[Optional[int]] = []
    for close, leading_a, leading_b in zip(closes, span_a, span_b):
        if leading_a is None or leading_b is None:
            cloud_bias.append(None)
            continue
        cloud_top = max(leading_a, leading_b)
        cloud_bottom = min(leading_a, leading_b)
        if close > cloud_top:
            cloud_bias.append(1)
        elif close < cloud_bottom:
            cloud_bias.append(-1)
        else:
            cloud_bias.append(0)

    return _build_rows(
        bars,
        ichimoku_conversion=conversion_line,
        ichimoku_base=base_line,
        ichimoku_span_a=span_a,
        ichimoku_span_b=span_b,
        ichimoku_cloud_bias=cloud_bias,
    )


@factor_registry.register("MFI")
def _calculate_mfi(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="MFI.period")
    typical_prices = _typical_price_series(bars, label="MFI")
    volumes = _volume_series(bars, label="MFI")
    raw_money_flow = [price * volume for price, volume in zip(typical_prices, volumes)]

    positive_flow = [0.0]
    negative_flow = [0.0]
    for previous_price, current_price, flow in zip(
        typical_prices,
        typical_prices[1:],
        raw_money_flow[1:],
    ):
        if current_price > previous_price:
            positive_flow.append(flow)
            negative_flow.append(0.0)
        elif current_price < previous_price:
            positive_flow.append(0.0)
            negative_flow.append(flow)
        else:
            positive_flow.append(0.0)
            negative_flow.append(0.0)

    positive_totals = _rolling_sum(positive_flow, period)
    negative_totals = _rolling_sum(negative_flow, period)
    mfi_values: List[Optional[float]] = []
    for positive_total, negative_total in zip(positive_totals, negative_totals):
        if positive_total is None or negative_total is None:
            mfi_values.append(None)
            continue
        if negative_total == 0:
            mfi_values.append(50.0 if positive_total == 0 else 100.0)
            continue
        money_ratio = positive_total / negative_total
        mfi_values.append(100.0 - 100.0 / (1.0 + money_ratio))

    return _build_rows(bars, mfi=mfi_values)


@factor_registry.register("OBV")
def _calculate_obv(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    _ = params
    closes = _close_series(bars, label="OBV")
    volumes = _volume_series(bars, label="OBV")
    obv_values: List[float] = []
    running_value = 0.0

    for index, (close, volume) in enumerate(zip(closes, volumes)):
        if index == 0:
            obv_values.append(running_value)
            continue
        previous_close = closes[index - 1]
        if close > previous_close:
            running_value += volume
        elif close < previous_close:
            running_value -= volume
        obv_values.append(running_value)

    return _build_rows(bars, obv=obv_values)


@factor_registry.register("ParabolicSAR")
def _calculate_parabolic_sar(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    step = _require_positive_float(params.get("step", 0.02), label="ParabolicSAR.step")
    max_step = _require_positive_float(
        params.get("max_step", 0.2),
        label="ParabolicSAR.max_step",
    )
    if max_step < step:
        raise StrategyConfigError("ParabolicSAR.max_step must be greater than or equal to step")

    highs = _high_series(bars, label="ParabolicSAR")
    lows = _low_series(bars, label="ParabolicSAR")
    closes = _close_series(bars, label="ParabolicSAR")
    if not bars:
        return []

    sar_values: List[float] = [lows[0]]
    trend_values: List[int] = [0]
    if len(bars) == 1:
        return _build_rows(bars, parabolic_sar=sar_values, parabolic_trend=trend_values)

    uptrend = closes[1] >= closes[0]
    sar = min(lows[0], lows[1]) if uptrend else max(highs[0], highs[1])
    extreme_point = max(highs[0], highs[1]) if uptrend else min(lows[0], lows[1])
    acceleration = step
    sar_values.append(sar)
    trend_values.append(1 if uptrend else -1)

    for index in range(2, len(bars)):
        sar = sar + acceleration * (extreme_point - sar)
        if uptrend:
            sar = min(sar, lows[index - 1], lows[index - 2])
            if lows[index] < sar:
                uptrend = False
                sar = extreme_point
                extreme_point = lows[index]
                acceleration = step
            else:
                if highs[index] > extreme_point:
                    extreme_point = highs[index]
                    acceleration = min(max_step, acceleration + step)
        else:
            sar = max(sar, highs[index - 1], highs[index - 2])
            if highs[index] > sar:
                uptrend = True
                sar = extreme_point
                extreme_point = highs[index]
                acceleration = step
            else:
                if lows[index] < extreme_point:
                    extreme_point = lows[index]
                    acceleration = min(max_step, acceleration + step)

        sar_values.append(sar)
        trend_values.append(1 if uptrend else -1)

    return _build_rows(bars, parabolic_sar=sar_values, parabolic_trend=trend_values)


@factor_registry.register("Supertrend")
def _calculate_supertrend(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 10), label="Supertrend.period")
    multiplier = _require_positive_float(
        params.get("multiplier", 3.0),
        label="Supertrend.multiplier",
    )
    highs = _high_series(bars, label="Supertrend")
    lows = _low_series(bars, label="Supertrend")
    closes = _close_series(bars, label="Supertrend")
    atr_values = [row["atr"] for row in _calculate_atr(bars, {"period": period})]
    final_upper: List[Optional[float]] = []
    final_lower: List[Optional[float]] = []
    supertrend_values: List[Optional[float]] = []
    direction_values: List[Optional[int]] = []

    for index, (high, low, close, atr_value) in enumerate(zip(highs, lows, closes, atr_values)):
        if atr_value is None:
            final_upper.append(None)
            final_lower.append(None)
            supertrend_values.append(None)
            direction_values.append(None)
            continue

        hl2 = (high + low) / 2.0
        basic_upper = hl2 + multiplier * atr_value
        basic_lower = hl2 - multiplier * atr_value
        if index == 0 or final_upper[-1] is None or final_lower[-1] is None:
            upper = basic_upper
            lower = basic_lower
            supertrend = None
        else:
            previous_upper = final_upper[-1]
            previous_lower = final_lower[-1]
            previous_close = closes[index - 1]
            upper = basic_upper if basic_upper < previous_upper or previous_close > previous_upper else previous_upper
            lower = basic_lower if basic_lower > previous_lower or previous_close < previous_lower else previous_lower

            previous_supertrend = supertrend_values[-1]
            if previous_supertrend is None:
                supertrend = lower if close >= lower else upper
            elif previous_supertrend == previous_upper:
                supertrend = upper if close <= upper else lower
            else:
                supertrend = lower if close >= lower else upper

        direction = None if supertrend is None else (1 if supertrend == lower else -1)
        final_upper.append(upper)
        final_lower.append(lower)
        supertrend_values.append(supertrend)
        direction_values.append(direction)

    return _build_rows(
        bars,
        supertrend=supertrend_values,
        supertrend_direction=direction_values,
        supertrend_upper=final_upper,
        supertrend_lower=final_lower,
    )


@factor_registry.register("VWAP")
def _calculate_vwap(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    _ = params
    typical_prices = _typical_price_series(bars, label="VWAP")
    volumes = _volume_series(bars, label="VWAP")
    cumulative_price_volume = 0.0
    cumulative_volume = 0.0
    vwap_values: List[Optional[float]] = []
    deviations: List[Optional[float]] = []

    for typical_price, volume, bar in zip(typical_prices, volumes, bars):
        cumulative_price_volume += typical_price * volume
        cumulative_volume += volume
        vwap_value = None if cumulative_volume == 0 else cumulative_price_volume / cumulative_volume
        close = _read_number(bar, "close", label="VWAP")
        deviation = None if vwap_value is None else close - vwap_value
        vwap_values.append(vwap_value)
        deviations.append(deviation)

    return _build_rows(bars, vwap=vwap_values, vwap_deviation=deviations)


@factor_registry.register("WilliamsR")
def _calculate_williams_r(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 14), label="WilliamsR.period")
    highs = _high_series(bars, label="WilliamsR")
    lows = _low_series(bars, label="WilliamsR")
    closes = _close_series(bars, label="WilliamsR")
    highest_high = _rolling_max(highs, period)
    lowest_low = _rolling_min(lows, period)
    values: List[Optional[float]] = []
    for close, high, low in zip(closes, highest_high, lowest_low):
        if high is None or low is None:
            values.append(None)
            continue
        denominator = high - low
        values.append(0.0 if denominator == 0 else -100.0 * (high - close) / denominator)
    return _build_rows(bars, williams_r=values)


@factor_registry.register("GarmanKlass")
def _calculate_garman_klass(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="GarmanKlass.period")
    annualization = _require_positive_int(
        params.get("annualization", 252),
        label="GarmanKlass.annualization",
    )
    opens = _open_series(bars, label="GarmanKlass")
    highs = _high_series(bars, label="GarmanKlass")
    lows = _low_series(bars, label="GarmanKlass")
    closes = _close_series(bars, label="GarmanKlass")
    variance_terms: List[float] = []
    for open_price, high, low, close in zip(opens, highs, lows, closes):
        safe_open = max(open_price, 1e-12)
        safe_high = max(high, 1e-12)
        safe_low = max(low, 1e-12)
        safe_close = max(close, 1e-12)
        high_low_term = math.log(safe_high / safe_low)
        close_open_term = math.log(safe_close / safe_open)
        variance = 0.5 * high_low_term ** 2 - (2.0 * math.log(2.0) - 1.0) * close_open_term ** 2
        variance_terms.append(max(variance, 0.0))

    mean_variance = _rolling_mean(variance_terms, period)
    values = [
        None if item is None else math.sqrt(max(item, 0.0) * annualization)
        for item in mean_variance
    ]
    return _build_rows(bars, garman_klass_vol=values)


@factor_registry.register("HistoricalVol")
def _calculate_historical_vol(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="HistoricalVol.period")
    annualization = _require_positive_int(
        params.get("annualization", 252),
        label="HistoricalVol.annualization",
    )
    closes = _close_series(bars, label="HistoricalVol")
    log_returns = [0.0]
    for previous_close, current_close in zip(closes, closes[1:]):
        safe_previous = max(previous_close, 1e-12)
        safe_current = max(current_close, 1e-12)
        log_returns.append(math.log(safe_current / safe_previous))

    std_values = _rolling_std(log_returns, period)
    historical_vol = [
        None if std_value is None else std_value * math.sqrt(annualization)
        for std_value in std_values
    ]
    return _build_rows(bars, historical_vol=historical_vol)


@factor_registry.register("ImpliedVolatility")
def _calculate_implied_volatility(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    neutral_value = float(params.get("neutral_value", 0.0))
    values = _single_column_values(
        bars,
        params,
        label="ImpliedVolatility",
        default_keys=("implied_volatility", "implied_vol", "iv"),
        neutral_value=neutral_value,
    )
    return _build_rows(bars, implied_volatility=values)


@factor_registry.register("VolatilityFactor")
def _calculate_volatility_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    explicit_values = _single_column_values(
        bars,
        params,
        label="VolatilityFactor",
        default_keys=("volatility_factor",),
        neutral_value=float("nan"),
    )
    historical_vol = [
        row["historical_vol"]
        for row in _calculate_historical_vol(bars, {"period": params.get("period", 20)})
    ]
    garman_klass = [
        row["garman_klass_vol"]
        for row in _calculate_garman_klass(bars, {"period": params.get("period", 20)})
    ]
    implied_vol = [
        row["implied_volatility"]
        for row in _calculate_implied_volatility(bars, params)
    ]
    factor_values: List[float] = []
    for explicit_value, hv_value, gk_value, iv_value in zip(
        explicit_values,
        historical_vol,
        garman_klass,
        implied_vol,
    ):
        if not math.isnan(explicit_value):
            factor_values.append(explicit_value)
            continue
        candidates = [value for value in (hv_value, gk_value, iv_value) if value is not None]
        factor_values.append(sum(candidates) / len(candidates) if candidates else 0.0)
    return _build_rows(
        bars,
        volatility_factor=factor_values,
        historical_vol=historical_vol,
        garman_klass_vol=garman_klass,
        implied_volatility=implied_vol,
    )


@factor_registry.register("BasisSpread")
def _calculate_basis_spread(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _spread_values(
        bars,
        params,
        label="BasisSpread",
        explicit_keys=("basis_spread",),
        reference_keys=("spot_price", "spot_close", "cash_close"),
    )
    return _build_rows(bars, basis_spread=values)


@factor_registry.register("CointResidual")
def _calculate_coint_residual(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _spread_values(
        bars,
        params,
        label="CointResidual",
        explicit_keys=("coint_residual",),
        reference_keys=("pair_close", "benchmark_close", "reference_close"),
    )
    return _build_rows(bars, coint_residual=values)


@factor_registry.register("SpreadCrosscommodity")
def _calculate_spread_crosscommodity(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _spread_values(
        bars,
        params,
        label="SpreadCrosscommodity",
        explicit_keys=("spread_crosscommodity",),
        reference_keys=("crosscommodity_close", "pair_close", "benchmark_close"),
    )
    return _build_rows(bars, spread_crosscommodity=values)


@factor_registry.register("SpreadCrossperiod")
def _calculate_spread_crossperiod(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _spread_values(
        bars,
        params,
        label="SpreadCrossperiod",
        explicit_keys=("spread_crossperiod",),
        reference_keys=("crossperiod_close", "far_close", "next_contract_close", "pair_close"),
    )
    return _build_rows(bars, spread_crossperiod=values)


@factor_registry.register("SpreadRatio")
def _calculate_spread_ratio(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _spread_values(
        bars,
        params,
        label="SpreadRatio",
        explicit_keys=("spread_ratio",),
        reference_keys=("pair_close", "crosscommodity_close", "far_close", "benchmark_close"),
        mode="ratio",
    )
    return _build_rows(bars, spread_ratio=values)


@factor_registry.register("ZScoreSpread")
def _calculate_zscore_spread(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    period = _require_positive_int(params.get("period", 20), label="ZScoreSpread.period")
    explicit_candidates = _candidate_keys(
        params,
        "zscore_spread",
        param_keys=("column", "value_column"),
    )
    explicit_values: List[Optional[float]] = []
    for bar in bars:
        explicit_values.append(
            _read_optional_number_from_keys(bar, explicit_candidates, label="ZScoreSpread")
        )

    spread_values = _spread_values(
        bars,
        params,
        label="ZScoreSpread",
        explicit_keys=("spread_value", "basis_spread", "spread_crosscommodity", "spread_crossperiod", "coint_residual"),
        reference_keys=("pair_close", "crosscommodity_close", "far_close", "benchmark_close", "spot_price"),
    )
    means = _rolling_mean(spread_values, period)
    stds = _rolling_std(spread_values, period)
    zscores: List[float] = []
    for explicit_value, spread_value, mean, std in zip(explicit_values, spread_values, means, stds):
        if explicit_value is not None:
            zscores.append(explicit_value)
            continue
        if mean is None or std in {None, 0.0}:
            zscores.append(0.0)
            continue
        zscores.append((spread_value - mean) / std)

    return _build_rows(bars, zscore_spread=zscores, spread_value=spread_values)


@factor_registry.register("NewsSentiment")
def _calculate_news_sentiment(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _single_column_values(
        bars,
        params,
        label="NewsSentiment",
        default_keys=("news_sentiment", "news_sentiment_score", "news_score"),
    )
    return _build_rows(bars, news_sentiment=values)


@factor_registry.register("SocialSentiment")
def _calculate_social_sentiment(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = _single_column_values(
        bars,
        params,
        label="SocialSentiment",
        default_keys=("social_sentiment", "social_sentiment_score", "social_score"),
    )
    return _build_rows(bars, social_sentiment=values)


@factor_registry.register("SentimentFactor")
def _calculate_sentiment_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    explicit_values = _single_column_values(
        bars,
        params,
        label="SentimentFactor",
        default_keys=("sentiment_factor", "sentiment"),
        neutral_value=float("nan"),
    )
    news_values = [row["news_sentiment"] for row in _calculate_news_sentiment(bars, params)]
    social_values = [row["social_sentiment"] for row in _calculate_social_sentiment(bars, params)]
    factor_values: List[float] = []
    for explicit_value, news_value, social_value in zip(explicit_values, news_values, social_values):
        if not math.isnan(explicit_value):
            factor_values.append(explicit_value)
            continue
        candidates = [value for value in (news_value, social_value) if value is not None]
        factor_values.append(sum(candidates) / len(candidates) if candidates else 0.0)
    return _build_rows(
        bars,
        sentiment_factor=factor_values,
        news_sentiment=news_values,
        social_sentiment=social_values,
    )


@factor_registry.register("InventoryFactor")
def _calculate_inventory_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return _change_factor_rows(
        bars,
        params,
        label="InventoryFactor",
        output_key="inventory_factor",
        explicit_keys=("inventory_factor",),
        raw_keys=("inventory", "inventory_level", "stocks"),
    )


@factor_registry.register("OpenInterestFactor")
def _calculate_open_interest_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return _change_factor_rows(
        bars,
        params,
        label="OpenInterestFactor",
        output_key="open_interest_factor",
        explicit_keys=("open_interest_factor",),
        raw_keys=("open_interest", "oi"),
    )


@factor_registry.register("WarehouseReceiptFactor")
def _calculate_warehouse_receipt_factor(
    bars: List[Dict[str, Any]],
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return _change_factor_rows(
        bars,
        params,
        label="WarehouseReceiptFactor",
        output_key="warehouse_receipt_factor",
        explicit_keys=("warehouse_receipt_factor",),
        raw_keys=("warehouse_receipt", "warehouse_receipts", "receipt_inventory"),
    )