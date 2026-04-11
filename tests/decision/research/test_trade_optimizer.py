"""
交易参数调优引擎测试 — TASK-0061 CA4
"""
from __future__ import annotations

import math
from unittest.mock import patch, MagicMock

import pytest

from services.decision.src.research.trade_optimizer import TradeOptimizer, OptimizationResult


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_bars(n: int = 60, base_price: float = 100.0) -> list[dict]:
    """Generate n synthetic bars with a gentle uptrend + fluctuation."""
    bars = []
    for i in range(n):
        price = base_price + i * 0.5 + ((-1) ** i) * 0.3
        bars.append({
            "datetime": f"2025-01-{1 + i // 4:02d}T09:30:00",
            "open": price - 0.1,
            "high": price + 0.5,
            "low": price - 0.5,
            "close": price,
            "volume": 1000 + i * 10,
        })
    return bars


@pytest.fixture
def optimizer() -> TradeOptimizer:
    return TradeOptimizer(data_service_url="http://test:8105")


# ---------------------------------------------------------------------------
# Tests — _calculate_objective
# ---------------------------------------------------------------------------

class TestCalculateObjective:
    def test_sharpe(self):
        score = TradeOptimizer._calculate_objective({"sharpe": 1.5}, "sharpe")
        assert score == 1.5

    def test_max_drawdown(self):
        score = TradeOptimizer._calculate_objective({"max_drawdown": 0.05}, "max_drawdown")
        assert score == -0.05  # negated: lower dd → higher score

    def test_win_rate(self):
        score = TradeOptimizer._calculate_objective({"win_rate": 0.6}, "win_rate")
        assert score == 0.6

    def test_total_return(self):
        score = TradeOptimizer._calculate_objective({"total_return": 0.12}, "total_return")
        assert score == 0.12

    def test_unknown_objective_defaults_to_sharpe(self):
        score = TradeOptimizer._calculate_objective({"sharpe": 2.0}, "unknown")
        assert score == 2.0


# ---------------------------------------------------------------------------
# Tests — _run_single_backtest (no network)
# ---------------------------------------------------------------------------

class TestRunSingleBacktest:
    def test_basic_backtest(self, optimizer: TradeOptimizer):
        bars = _make_bars(60)
        metrics = optimizer._run_single_backtest(bars, {"fast_period": 5, "slow_period": 20}, "futures")
        assert "sharpe" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
        assert "total_return" in metrics
        assert "trades_count" in metrics

    def test_insufficient_bars(self, optimizer: TradeOptimizer):
        bars = _make_bars(3)
        metrics = optimizer._run_single_backtest(bars, {"fast_period": 5, "slow_period": 20}, "futures")
        assert metrics["trades_count"] == 0
        assert metrics["total_return"] == 0.0

    def test_stop_loss_triggers(self, optimizer: TradeOptimizer):
        # Create bars with a sudden drop to trigger stop-loss
        bars = _make_bars(40, base_price=100.0)
        # Add a sharp drop
        for i in range(40, 50):
            bars.append({
                "datetime": f"2025-02-{10 + i - 40:02d}T09:30:00",
                "open": 80.0 - i * 0.5,
                "high": 80.0,
                "low": 75.0 - i * 0.5,
                "close": 78.0 - i * 0.5,
                "volume": 2000,
            })
        metrics = optimizer._run_single_backtest(
            bars, {"fast_period": 5, "slow_period": 20, "stop_loss": 0.02}, "futures",
        )
        assert isinstance(metrics["max_drawdown"], float)


# ---------------------------------------------------------------------------
# Tests — optimize (mocked HTTP)
# ---------------------------------------------------------------------------

class TestOptimize:
    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_optimize_basic(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        result = optimizer.optimize(
            strategy_id="strat-001",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={"fast_period": [5, 10], "slow_period": [20, 40]},
            objective="sharpe",
        )
        assert isinstance(result, OptimizationResult)
        assert result.status == "completed"
        assert result.total_trials == 4  # 2 x 2
        assert result.best_params  # non-empty
        assert result.objective == "sharpe"
        mock_fetch.assert_called_once()

    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_optimize_max_drawdown_objective(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        result = optimizer.optimize(
            strategy_id="strat-dd",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={"fast_period": [5, 10], "slow_period": [20, 40]},
            objective="max_drawdown",
        )
        assert result.status == "completed"
        assert result.objective == "max_drawdown"
        # best_score should be <= 0 (negated drawdown)
        assert result.best_score <= 0

    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_optimize_win_rate_objective(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        result = optimizer.optimize(
            strategy_id="strat-wr",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={"fast_period": [5, 10], "slow_period": [20, 40]},
            objective="win_rate",
        )
        assert result.status == "completed"
        assert result.objective == "win_rate"

    def test_optimize_empty_param_grid(self, optimizer: TradeOptimizer):
        result = optimizer.optimize(
            strategy_id="strat-empty",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={},
        )
        assert result.status == "completed"
        assert result.total_trials == 0
        assert result.best_params == {}

    @patch.object(TradeOptimizer, "_fetch_bars", side_effect=Exception("data service down"))
    def test_optimize_fetch_failure(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        result = optimizer.optimize(
            strategy_id="strat-fail",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={"fast_period": [5, 10]},
        )
        assert result.status == "failed"


# ---------------------------------------------------------------------------
# Tests — get_result / list_results
# ---------------------------------------------------------------------------

class TestResultsQuery:
    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_get_result(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        result = optimizer.optimize(
            strategy_id="strat-q",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={"fast_period": [5]},
        )
        fetched = optimizer.get_result(result.opt_id)
        assert fetched is not None
        assert fetched.opt_id == result.opt_id

    def test_get_result_not_found(self, optimizer: TradeOptimizer):
        assert optimizer.get_result("nonexistent") is None

    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_list_results_all(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        optimizer.optimize("s1", "SYM", "2025-01-01", "2025-03-31", {"fast_period": [5]})
        optimizer.optimize("s2", "SYM", "2025-01-01", "2025-03-31", {"fast_period": [5]})
        assert len(optimizer.list_results()) == 2

    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_list_results_filter(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        optimizer.optimize("s1", "SYM", "2025-01-01", "2025-03-31", {"fast_period": [5]})
        optimizer.optimize("s2", "SYM", "2025-01-01", "2025-03-31", {"fast_period": [5]})
        assert len(optimizer.list_results(strategy_id="s1")) == 1


# ---------------------------------------------------------------------------
# Tests — to_dict serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    @patch.object(TradeOptimizer, "_fetch_bars")
    def test_to_dict(self, mock_fetch: MagicMock, optimizer: TradeOptimizer):
        mock_fetch.return_value = _make_bars(60)
        result = optimizer.optimize(
            strategy_id="strat-ser",
            symbol="KQ_m_CFFEX_IF",
            start_date="2025-01-01",
            end_date="2025-03-31",
            param_grid={"fast_period": [5, 10]},
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["opt_id"] == result.opt_id
        assert d["strategy_id"] == "strat-ser"
        assert isinstance(d["all_trials"], list)
        assert d["total_trials"] == 2
