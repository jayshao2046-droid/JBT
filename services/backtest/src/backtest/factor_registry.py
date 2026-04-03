from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

try:
    from .strategy_base import StrategyConfigError
except ImportError:
    from strategy_base import StrategyConfigError

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


@factor_registry.register("MACD")
def _calculate_macd(bars: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    fast = _require_positive_int(params.get("fast", 12), label="MACD.fast")
    slow = _require_positive_int(params.get("slow", 26), label="MACD.slow")
    signal = _require_positive_int(params.get("signal", 9), label="MACD.signal")

    closes = [_read_number(bar, "close", label="MACD") for bar in bars]
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
    closes = [_read_number(bar, "close", label="RSI") for bar in bars]

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
    volumes = [_read_number(bar, "volume", label="VolumeRatio") for bar in bars]
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
    trs: List[float] = []
    previous_close: Optional[float] = None

    for bar in bars:
        high = _read_number(bar, "high", label="ATR")
        low = _read_number(bar, "low", label="ATR")
        close = _read_number(bar, "close", label="ATR")
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
    trs: List[float] = []
    plus_dm: List[float] = []
    minus_dm: List[float] = []

    previous_high: Optional[float] = None
    previous_low: Optional[float] = None
    previous_close: Optional[float] = None

    for bar in bars:
        high = _read_number(bar, "high", label="ADX")
        low = _read_number(bar, "low", label="ADX")
        close = _read_number(bar, "close", label="ADX")

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