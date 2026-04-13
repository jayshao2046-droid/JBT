"""测试参数验证器"""
import pytest
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backtest.validator import ParameterValidator


def test_validate_type_success():
    """测试类型验证成功"""
    validator = ParameterValidator()
    assert validator.validate_type("test_param", 100, int) is True
    assert len(validator.errors) == 0


def test_validate_type_failure():
    """测试类型验证失败"""
    validator = ParameterValidator()
    assert validator.validate_type("test_param", "100", int) is False
    assert len(validator.errors) == 1
    assert "类型错误" in validator.errors[0]


def test_validate_range_success():
    """测试范围验证成功"""
    validator = ParameterValidator()
    assert validator.validate_range("test_param", 50, min_value=0, max_value=100) is True
    assert len(validator.errors) == 0


def test_validate_range_min_failure():
    """测试最小值验证失败"""
    validator = ParameterValidator()
    assert validator.validate_range("test_param", -10, min_value=0) is False
    assert len(validator.errors) == 1
    assert "小于最小值" in validator.errors[0]


def test_validate_range_max_failure():
    """测试最大值验证失败"""
    validator = ParameterValidator()
    assert validator.validate_range("test_param", 150, max_value=100) is False
    assert len(validator.errors) == 1
    assert "大于最大值" in validator.errors[0]


def test_validate_dependencies_success():
    """测试依赖验证成功"""
    validator = ParameterValidator()
    params = {"param_a": 1, "param_b": 2}
    dependencies = {"param_a": ["param_b"]}
    assert validator.validate_dependencies(params, dependencies) is True
    assert len(validator.errors) == 0


def test_validate_dependencies_failure():
    """测试依赖验证失败"""
    validator = ParameterValidator()
    params = {"param_a": 1}
    dependencies = {"param_a": ["param_b"]}
    assert validator.validate_dependencies(params, dependencies) is False
    assert len(validator.errors) == 1
    assert "依赖参数" in validator.errors[0]


def test_validate_strategy_params_initial_capital():
    """测试初始资金验证"""
    validator = ParameterValidator()

    # 成功案例
    valid, errors = validator.validate_strategy_params("generic", {"initial_capital": 100000})
    assert valid is True
    assert len(errors) == 0

    # 失败案例：小于最小值
    valid, errors = validator.validate_strategy_params("generic", {"initial_capital": 5000})
    assert valid is False
    assert len(errors) > 0


def test_validate_strategy_params_slippage():
    """测试滑点验证"""
    validator = ParameterValidator()

    # 成功案例
    valid, errors = validator.validate_strategy_params("generic", {"slippage_per_unit": 1.0})
    assert valid is True
    assert len(errors) == 0

    # 失败案例：负数
    valid, errors = validator.validate_strategy_params("generic", {"slippage_per_unit": -1.0})
    assert valid is False
    assert len(errors) > 0


def test_validate_strategy_params_timeframe():
    """测试时间周期验证"""
    validator = ParameterValidator()

    # 成功案例
    valid, errors = validator.validate_strategy_params("generic", {"timeframe_minutes": 60})
    assert valid is True
    assert len(errors) == 0

    # 失败案例：超出范围
    valid, errors = validator.validate_strategy_params("generic", {"timeframe_minutes": 2000})
    assert valid is False
    assert len(errors) > 0


def test_validate_strategy_params_multiple():
    """测试多个参数验证"""
    validator = ParameterValidator()

    params = {
        "initial_capital": 500000,
        "slippage_per_unit": 1.0,
        "commission_per_lot_round_turn": 8.0,
        "timeframe_minutes": 60,
    }

    valid, errors = validator.validate_strategy_params("generic", params)
    assert valid is True
    assert len(errors) == 0
