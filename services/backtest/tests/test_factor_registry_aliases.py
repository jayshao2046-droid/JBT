from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.factor_registry import factor_registry
from services.backtest.src.backtest.strategy_base import StrategyConfigError
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bars(n: int = 40) -> list[dict]:
    """Generate synthetic OHLCV bars with two close columns for spread tests."""
    bars = []
    for i in range(n):
        close_a = 100.0 + i * 0.5
        close_b = 98.0 + i * 0.4
        bars.append({
            "timestamp": i,
            "open": close_a - 0.2,
            "high": close_a + 1.0,
            "low": close_a - 1.0,
            "close": close_a,
            "close_ref": close_b,
            "volume": 1000 + i * 10,
        })
    return bars


# ---------------------------------------------------------------------------
# Spread factor tests
# ---------------------------------------------------------------------------

def test_spread_registered():
    """spread must be discoverable in the registry."""
    assert "spread" in factor_registry.list_factors()


def test_spread_calculate_non_empty():
    """spread calculation must return non-empty rows with expected keys."""
    bars = _make_bars()
    result = factor_registry.calculate("spread", bars, {"period": 10})
    assert len(result.rows) == len(bars)
    last = result.latest()
    assert "spread" in last
    assert last["spread"] is not None


def test_spread_values_correct():
    """spread value should equal col_a - col_b for each bar."""
    bars = _make_bars(5)
    result = factor_registry.calculate("spread", bars, {"period": 3, "col_a": "close", "col_b": "close_ref"})
    for row, bar in zip(result.rows, bars):
        expected = bar["close"] - bar["close_ref"]
        assert row["spread"] is not None
        assert abs(row["spread"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# Spread_RSI factor tests
# ---------------------------------------------------------------------------

def test_spread_rsi_registered():
    """spread_rsi must be discoverable in the registry."""
    assert "spread_rsi" in factor_registry.list_factors()


def test_spread_rsi_calculate_non_empty():
    """spread_rsi calculation must return non-empty rows with expected keys."""
    bars = _make_bars()
    result = factor_registry.calculate("spread_rsi", bars, {"period": 14})
    assert len(result.rows) == len(bars)
    last = result.latest()
    assert "spread_rsi" in last
    assert last["spread_rsi"] is not None


def test_spread_rsi_range():
    """spread_rsi values (when not None) should be within 0..100."""
    bars = _make_bars(60)
    result = factor_registry.calculate("spread_rsi", bars, {"period": 14})
    for row in result.rows:
        value = row["spread_rsi"]
        if value is not None:
            assert 0.0 <= value <= 100.0, f"spread_rsi out of range: {value}"


# ---------------------------------------------------------------------------
# Underscore alias compatibility tests
# ---------------------------------------------------------------------------

def test_alias_volume_ratio_underscore():
    """volume_ratio (snake_case) should resolve to VolumeRatio."""
    resolved = factor_registry.resolve_factor_name("volume_ratio")
    assert resolved == factor_registry.resolve_factor_name("VolumeRatio")
    # Also verify calculation works via alias
    bars = _make_bars()
    result = factor_registry.calculate("volume_ratio", bars, {"period": 5})
    assert len(result.rows) == len(bars)


def test_alias_spread_rsi_case_insensitive():
    """SPREAD_RSI (upper-case) should resolve to spread_rsi."""
    resolved = factor_registry.resolve_factor_name("SPREAD_RSI")
    assert resolved == factor_registry.resolve_factor_name("spread_rsi")
    bars = _make_bars()
    result = factor_registry.calculate("SPREAD_RSI", bars, {"period": 14})
    assert len(result.rows) == len(bars)


def test_alias_nonexistent_factor_raises():
    """A completely nonexistent factor name should raise StrategyConfigError."""
    with pytest.raises(StrategyConfigError, match="Unsupported factor"):
        factor_registry.resolve_factor_name("nonexistent_factor_xyz")


def test_alias_bollinger_bands_underscore():
    """bollinger_bands should resolve to the same as BollingerBands."""
    resolved = factor_registry.resolve_factor_name("bollinger_bands")
    assert resolved == factor_registry.resolve_factor_name("BollingerBands")
