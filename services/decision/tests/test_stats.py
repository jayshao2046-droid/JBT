"""
统计模块单元测试
"""
import pytest
from src.stats.performance import PerformanceCalculator
from src.stats.quality import QualityCalculator


class TestPerformanceStats:
    """绩效统计测试"""

    def test_empty_signals(self):
        calculator = PerformanceCalculator()
        result = calculator.calculate_all([])
        assert result["signal_accuracy"] == 0.0
        assert result["avg_return"] == 0.0
        assert result["signal_count"] == 0

    def test_full_calculation(self):
        calculator = PerformanceCalculator()
        signals = [
            {"is_correct": True, "return": 0.05, "executed": True, "response_time_ms": 50},
            {"is_correct": False, "return": -0.02, "executed": True, "response_time_ms": 60},
            {"is_correct": True, "return": 0.03, "executed": False, "response_time_ms": 45},
        ]
        result = calculator.calculate_all(signals)
        assert result["signal_count"] == 3
        assert result["signal_accuracy"] == 66.67
        assert result["execution_success_rate"] == 66.67
        assert result["avg_response_time"] == 51.67


class TestQualityStats:
    """质量统计测试"""

    def test_empty_signals(self):
        calculator = QualityCalculator()
        result = calculator.calculate_all([])
        assert result["signal_quality"] == 0.0
        assert result["data_completeness"] == 0.0

    def test_full_calculation(self):
        calculator = QualityCalculator()
        signals = [
            {
                "signal": 1,
                "signal_strength": 0.8,
                "factor_consistency": 0.7,
                "market_fit": 0.9,
                "factors": [],
                "market_context": {},
                "return": 0.05,
                "risk_compliant": True,
            },
            {
                "signal": -1,
                "signal_strength": 0.6,
                "factor_consistency": 0.5,
                "market_fit": 0.7,
                "factors": [],
                "market_context": {},
                "return": -0.02,
                "risk_compliant": True,
            },
        ]
        result = calculator.calculate_all(signals)
        assert result["signal_quality"] > 0
        assert result["data_completeness"] == 100.0
        assert result["risk_control_effectiveness"] > 0
