# Tests for statistics modules (SIMWEB-01)

import pytest
from datetime import datetime, timedelta
from src.stats.performance import PerformanceCalculator
from src.stats.execution import ExecutionQualityCalculator
from src.stats.market import MarketMoverCalculator


class TestPerformanceCalculator:
    """测试绩效统计计算器"""

    def test_calculate_win_rate(self):
        calculator = PerformanceCalculator()
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 200},
            {"pnl": -30},
            {"pnl": 150},
        ]
        win_rate = calculator.calculate_win_rate(trades)
        assert win_rate == 60.0  # 3/5 = 60%

    def test_calculate_win_rate_empty(self):
        calculator = PerformanceCalculator()
        assert calculator.calculate_win_rate([]) == 0.0

    def test_calculate_profit_loss_ratio(self):
        calculator = PerformanceCalculator()
        trades = [
            {"pnl": 100},
            {"pnl": 200},
            {"pnl": -50},
            {"pnl": -100},
        ]
        ratio = calculator.calculate_profit_loss_ratio(trades)
        # avg_profit = (100+200)/2 = 150, avg_loss = (50+100)/2 = 75
        assert ratio == 2.0

    def test_calculate_max_drawdown(self):
        calculator = PerformanceCalculator()
        equity_history = [
            {"equity": 100000},
            {"equity": 110000},
            {"equity": 105000},
            {"equity": 95000},
            {"equity": 100000},
        ]
        max_dd = calculator.calculate_max_drawdown(equity_history)
        # peak = 110000, trough = 95000, dd = (110000-95000)/110000 = 13.64%
        assert 13.0 < max_dd < 14.0

    def test_calculate_period_pnl_today(self):
        calculator = PerformanceCalculator()
        now = datetime.now()
        trades = [
            {"pnl": 100, "timestamp": now.isoformat()},
            {"pnl": 200, "timestamp": (now - timedelta(hours=1)).isoformat()},
            {"pnl": -50, "timestamp": (now - timedelta(days=1)).isoformat()},
        ]
        today_pnl = calculator.calculate_period_pnl(trades, "today")
        assert today_pnl == 300.0  # 只统计今天的


class TestExecutionQualityCalculator:
    """测试执行质量统计计算器"""

    def test_calculate_slippage(self):
        calculator = ExecutionQualityCalculator()
        trades = [
            {"signal_price": 100, "actual_price": 100.5},
            {"signal_price": 200, "actual_price": 199.5},
            {"signal_price": 150, "actual_price": 150.2},
        ]
        slippage = calculator.calculate_slippage(trades)
        # avg = (0.5 + 0.5 + 0.2) / 3 = 0.4
        assert 0.39 < slippage < 0.41

    def test_calculate_rejection_rate(self):
        calculator = ExecutionQualityCalculator()
        orders = [
            {"status": "filled"},
            {"status": "rejected"},
            {"status": "filled"},
            {"status": "cancelled"},
            {"status": "filled"},
        ]
        rejection_rate = calculator.calculate_rejection_rate(orders)
        assert rejection_rate == 40.0  # 2/5 = 40%

    def test_calculate_cancel_rate(self):
        calculator = ExecutionQualityCalculator()
        orders = [
            {"status": "filled"},
            {"status": "cancelled"},
            {"status": "filled"},
            {"status": "cancelled"},
            {"status": "filled"},
        ]
        cancel_rate = calculator.calculate_cancel_rate(orders)
        assert cancel_rate == 40.0  # 2/5 = 40%

    def test_calculate_partial_fill_rate(self):
        calculator = ExecutionQualityCalculator()
        orders = [
            {"status": "filled", "filled_volume": 10, "volume": 10},
            {"status": "partial_filled", "filled_volume": 5, "volume": 10},
            {"status": "filled", "filled_volume": 10, "volume": 10},
        ]
        partial_rate = calculator.calculate_partial_fill_rate(orders)
        assert 33.0 < partial_rate < 34.0  # 1/3 ≈ 33.33%


class TestMarketMoverCalculator:
    """测试市场异动监控计算器"""

    def test_calculate_price_change_rate(self):
        calculator = MarketMoverCalculator()
        instruments = [
            {
                "instrument_id": "RB2505",
                "name": "螺纹钢",
                "last_price": 3850,
                "prev_close": 3800,
            },
            {
                "instrument_id": "HC2505",
                "name": "热卷",
                "last_price": 3600,
                "prev_close": 3700,
            },
        ]
        movers = calculator.calculate_price_change_rate(instruments, 10)
        assert len(movers) == 2
        # HC2505 变化率绝对值更大 (-2.7%) 所以排第一
        assert movers[0]["symbol"] == "HC2505"
        assert movers[1]["symbol"] == "RB2505"
        assert 1.3 < movers[1]["change_rate"] < 1.4  # (3850-3800)/3800 ≈ 1.32%

    def test_calculate_amplitude(self):
        calculator = MarketMoverCalculator()
        instruments = [
            {
                "instrument_id": "RB2505",
                "name": "螺纹钢",
                "highest_price": 3900,
                "lowest_price": 3800,
                "prev_close": 3850,
            },
        ]
        movers = calculator.calculate_amplitude(instruments, 10)
        assert len(movers) == 1
        assert 2.5 < movers[0]["amplitude"] < 2.7  # (3900-3800)/3850 ≈ 2.6%

    def test_calculate_volume_surge(self):
        calculator = MarketMoverCalculator()
        instruments = [
            {
                "instrument_id": "RB2505",
                "name": "螺纹钢",
                "volume": 150000,
                "avg_volume": 100000,
            },
        ]
        movers = calculator.calculate_volume_surge(instruments, 10)
        assert len(movers) == 1
        assert movers[0]["volume_ratio"] == 1.5
