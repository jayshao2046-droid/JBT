"""
全 A 股选股引擎测试 — TASK-0062 CB3
"""
from __future__ import annotations

import math
from unittest.mock import patch, MagicMock

import pytest

from services.decision.src.research.stock_screener import StockScreener, ScreenResult


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_bars(n: int = 25, base_price: float = 10.0, trend: float = 0.1) -> list[dict]:
    """Generate n synthetic daily bars with configurable trend."""
    bars = []
    for i in range(n):
        price = base_price + i * trend + ((-1) ** i) * 0.05
        bars.append({
            "open": round(price - 0.02, 4),
            "high": round(price + 0.2, 4),
            "low": round(price - 0.2, 4),
            "close": round(price, 4),
            "volume": 5000 + i * 100,
        })
    return bars


def _mock_get_success(bars_map: dict[str, list[dict]]):
    """Return a side_effect for httpx.get that resolves symbols from *bars_map*."""
    def _side_effect(url, *, params=None, timeout=None):
        symbol = params.get("symbol", "") if params else ""
        if symbol not in bars_map:
            resp = MagicMock()
            resp.status_code = 404
            resp.raise_for_status.side_effect = Exception(f"404 for {symbol}")
            return resp
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status.return_value = None
        resp.json.return_value = bars_map[symbol]
        return resp
    return _side_effect


@pytest.fixture
def screener() -> StockScreener:
    return StockScreener(data_service_url="http://test:8105")


# ---------------------------------------------------------------------------
# Tests: _score_stock
# ---------------------------------------------------------------------------

class TestScoreStock:
    def test_momentum_positive(self, screener: StockScreener):
        bars = _make_bars(20, base_price=10.0, trend=0.5)
        factors = screener._score_stock(bars, 20)
        assert factors["momentum"] > 0

    def test_momentum_negative(self, screener: StockScreener):
        bars = _make_bars(20, base_price=100.0, trend=-1.0)
        factors = screener._score_stock(bars, 20)
        assert factors["momentum"] < 0

    def test_price_position_range(self, screener: StockScreener):
        bars = _make_bars(20)
        factors = screener._score_stock(bars, 20)
        assert 0.0 <= factors["price_position"] <= 1.0

    def test_volume_ratio_default(self, screener: StockScreener):
        bars = _make_bars(25)
        factors = screener._score_stock(bars, 25)
        # volume_ratio should be positive
        assert factors["volume_ratio"] > 0

    def test_score_weighted_sum(self, screener: StockScreener):
        bars = _make_bars(20)
        factors = screener._score_stock(bars, 20)
        vr_norm = min(factors["volume_ratio"] / 2.0, 1.0)
        expected = factors["momentum"] * 0.4 + vr_norm * 0.3 + factors["price_position"] * 0.3
        assert abs(factors["score"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# Tests: screen (full flow, mocked httpx)
# ---------------------------------------------------------------------------

class TestScreen:
    def test_basic_screen(self, screener: StockScreener):
        bars_map = {
            "000001.SZ": _make_bars(25, 10.0, 0.5),
            "000002.SZ": _make_bars(25, 20.0, 0.2),
            "600519.SH": _make_bars(25, 50.0, 1.0),
        }
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(
                symbols=["000001.SZ", "000002.SZ", "600519.SH"],
                top_n=2,
                lookback_days=20,
            )
        assert isinstance(result, ScreenResult)
        assert result.universe_size == 3
        assert len(result.ranked_list) == 2
        assert result.ranked_list[0]["rank"] == 1
        assert result.ranked_list[1]["rank"] == 2
        # first should have higher score
        assert result.ranked_list[0]["score"] >= result.ranked_list[1]["score"]

    def test_top_n_limits_output(self, screener: StockScreener):
        bars_map = {f"SYM{i}": _make_bars(25, 10.0 + i, 0.1 * i) for i in range(10)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(symbols=list(bars_map.keys()), top_n=3)
        assert len(result.ranked_list) == 3

    def test_empty_symbols(self, screener: StockScreener):
        result = screener.screen(symbols=[], top_n=5)
        assert result.universe_size == 0
        assert result.ranked_list == []

    def test_result_stored(self, screener: StockScreener):
        bars_map = {"A": _make_bars(25)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(symbols=["A"], top_n=5)
        assert screener.get_result(result.screen_id) is result

    def test_list_results(self, screener: StockScreener):
        bars_map = {"A": _make_bars(25)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            screener.screen(symbols=["A"])
            screener.screen(symbols=["A"])
        assert len(screener.list_results()) == 2

    def test_fetch_failure_skipped(self, screener: StockScreener):
        """Symbols that fail to fetch are silently skipped."""
        bars_map = {"GOOD": _make_bars(25)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(symbols=["GOOD", "BAD_SYM"], top_n=5)
        assert result.universe_size == 2
        assert len(result.ranked_list) == 1
        assert result.ranked_list[0]["symbol"] == "GOOD"


# ---------------------------------------------------------------------------
# Tests: benchmark
# ---------------------------------------------------------------------------

class TestBenchmark:
    def test_benchmark_included(self, screener: StockScreener):
        bars_map = {
            "A": _make_bars(25, 10.0, 0.3),
            "000300.SH": _make_bars(25, 100.0, 0.5),
        }
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(
                symbols=["A"],
                benchmark_symbol="000300.SH",
            )
        assert result.benchmark is not None
        assert result.benchmark["symbol"] == "000300.SH"
        assert "return_pct" in result.benchmark
        assert "sharpe" in result.benchmark

    def test_benchmark_none_when_not_requested(self, screener: StockScreener):
        bars_map = {"A": _make_bars(25)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(symbols=["A"])
        assert result.benchmark is None

    def test_benchmark_failure_returns_none(self, screener: StockScreener):
        bars_map = {"A": _make_bars(25)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(symbols=["A"], benchmark_symbol="MISSING")
        assert result.benchmark is None

    def test_calculate_benchmark_sharpe(self, screener: StockScreener):
        bars = _make_bars(25, 100.0, 1.0)
        bench = screener._calculate_benchmark(bars)
        assert "return_pct" in bench
        assert "sharpe" in bench
        assert bench["return_pct"] > 0  # uptrend


# ---------------------------------------------------------------------------
# Tests: to_dict serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict(self, screener: StockScreener):
        bars_map = {"X": _make_bars(25)}
        with patch("httpx.get", side_effect=_mock_get_success(bars_map)):
            result = screener.screen(symbols=["X"], top_n=1)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "screen_id" in d
        assert "ranked_list" in d
        assert "screening_params" in d
