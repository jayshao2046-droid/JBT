"""
参数验证器单元测试
"""
import pytest
from src.decision.validator import ParameterValidator


class TestValidator:
    """验证器测试"""

    def test_type_validation(self):
        validator = ParameterValidator()
        assert validator.validate_type("test", 123, "int") is True
        assert validator.validate_type("test", 123.45, "float") is True
        assert validator.validate_type("test", "hello", "str") is True
        assert validator.validate_type("test", True, "bool") is True
        assert validator.validate_type("test", [], "list") is True
        assert validator.validate_type("test", {}, "dict") is True

    def test_type_validation_failure(self):
        validator = ParameterValidator()
        assert validator.validate_type("test", "123", "int") is False
        assert validator.validate_type("test", 123, "str") is False

    def test_range_validation(self):
        validator = ParameterValidator()
        assert validator.validate_range("test", 50, 0, 100) is True
        assert validator.validate_range("test", 0, 0, 100) is True
        assert validator.validate_range("test", 100, 0, 100) is True
        assert validator.validate_range("test", -1, 0, 100) is False
        assert validator.validate_range("test", 101, 0, 100) is False

    def test_dependencies_validation(self):
        validator = ParameterValidator()
        params = {"stop_loss": 0.05, "take_profit": 0.10}
        rules = [{"param": "take_profit", "depends_on": "stop_loss", "condition": "greater_than"}]
        assert validator.validate_dependencies(params, rules) is True

        params2 = {"stop_loss": 0.10, "take_profit": 0.05}
        assert validator.validate_dependencies(params2, rules) is False

    def test_full_validation(self):
        validator = ParameterValidator()
        schema = {
            "required": ["initial_capital", "max_position"],
            "properties": {
                "initial_capital": {"type": "float", "min": 10000},
                "max_position": {"type": "float", "min": 0.01, "max": 1.0},
                "stop_loss": {"type": "float", "min": 0.01, "max": 0.5},
            },
            "dependencies": [],
        }

        # 有效参数
        params = {"initial_capital": 100000, "max_position": 0.5, "stop_loss": 0.05}
        result = validator.validate_all(params, schema)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # 缺少必填参数
        params2 = {"initial_capital": 100000}
        result2 = validator.validate_all(params2, schema)
        assert result2["valid"] is False
        assert len(result2["errors"]) > 0

        # 参数超出范围
        params3 = {"initial_capital": 5000, "max_position": 0.5}
        result3 = validator.validate_all(params3, schema)
        assert result3["valid"] is False
