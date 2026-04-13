"""
决策服务单元测试
"""
import pytest
from src.decision.validator import ParameterValidator
from src.stats.performance import PerformanceCalculator
from src.stats.quality import QualityCalculator


class TestParameterValidator:
    """参数验证器测试"""

    def test_validate_type(self):
        validator = ParameterValidator()
        assert validator.validate_type("param1", 100, "int") is True
        assert validator.validate_type("param2", 100.5, "float") is True
        assert validator.validate_type("param3", "test", "str") is True
        assert validator.validate_type("param4", "test", "int") is False

    def test_validate_range(self):
        validator = ParameterValidator()
        assert validator.validate_range("param1", 50, 0, 100) is True
        assert validator.validate_range("param2", 150, 0, 100) is False
        assert validator.validate_range("param3", -10, 0, 100) is False

    def test_validate_all(self):
        validator = ParameterValidator()
        schema = {
            "required": ["initial_capital"],
            "properties": {
                "initial_capital": {"type": "float", "min": 10000},
                "max_position": {"type": "float", "min": 0, "max": 1},
            },
        }
        params = {"initial_capital": 100000, "max_position": 0.5}
        result = validator.validate_all(params, schema)
        assert result["valid"] is True
        assert len(result["errors"]) == 0


class TestPerformanceCalculator:
    """绩效计算器测试"""

    def test_calculate_signal_accuracy(self):
        calculator = PerformanceCalculator()
        signals = [
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": False},
        ]
        accuracy = calculator.calculate_signal_accuracy(signals)
        assert accuracy == 66.67

    def test_calculate_avg_return(self):
        calculator = PerformanceCalculator()
        signals = [
            {"return": 0.05},
            {"return": 0.03},
            {"return": -0.02},
        ]
        avg_return = calculator.calculate_avg_return(signals)
        assert avg_return == 2.0

    def test_calculate_max_drawdown(self):
        calculator = PerformanceCalculator()
        signals = [
            {"return": 0.1},
            {"return": -0.05},
            {"return": -0.03},
            {"return": 0.08},
        ]
        max_dd = calculator.calculate_max_drawdown(signals)
        assert max_dd > 0

    def test_calculate_sharpe_ratio(self):
        calculator = PerformanceCalculator()
        signals = [
            {"return": 0.05},
            {"return": 0.03},
            {"return": 0.04},
        ]
        sharpe = calculator.calculate_sharpe_ratio(signals)
        assert isinstance(sharpe, float)


class TestQualityCalculator:
    """质量计算器测试"""

    def test_calculate_signal_quality(self):
        calculator = QualityCalculator()
        signals = [
            {"signal_strength": 0.8, "factor_consistency": 0.7, "market_fit": 0.9},
            {"signal_strength": 0.6, "factor_consistency": 0.5, "market_fit": 0.7},
        ]
        quality = calculator.calculate_signal_quality(signals)
        assert 0 <= quality <= 100

    def test_calculate_factor_effectiveness(self):
        calculator = QualityCalculator()
        factors = [
            {"is_effective": True},
            {"is_effective": True},
            {"is_effective": False},
        ]
        effectiveness = calculator.calculate_factor_effectiveness(factors)
        assert effectiveness == 66.67

    def test_calculate_strategy_stability(self):
        calculator = QualityCalculator()
        signals = [
            {"return": 0.05},
            {"return": 0.04},
            {"return": 0.06},
        ]
        stability = calculator.calculate_strategy_stability(signals)
        assert 0 <= stability <= 100

    def test_calculate_data_completeness(self):
        calculator = QualityCalculator()
        signals = [
            {"signal": 1, "signal_strength": 0.8, "factors": [], "market_context": {}},
            {"signal": -1, "signal_strength": 0.6, "factors": [], "market_context": {}},
            {"signal": 0},
        ]
        completeness = calculator.calculate_data_completeness(signals)
        assert completeness == 66.67
