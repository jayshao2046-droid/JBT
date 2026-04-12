"""PBO 检验器测试 — TASK-0075 CA7"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.research.pbo_validator import PBOValidator


# ------------------------------------------------------------------
# 测试 PBOValidator 初始化
# ------------------------------------------------------------------


def test_pbo_validator_init():
    """测试 PBOValidator 初始化。"""
    validator = PBOValidator(n_splits=16)
    assert validator.n_splits == 16


def test_pbo_validator_init_odd_splits():
    """测试 n_splits 为奇数时抛出异常。"""
    with pytest.raises(ValueError, match="n_splits must be even"):
        PBOValidator(n_splits=15)


# ------------------------------------------------------------------
# 测试 Sharpe 计算
# ------------------------------------------------------------------


def test_calculate_sharpe_positive():
    """测试正收益的 Sharpe 计算。"""
    validator = PBOValidator()
    returns = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01] * 50)  # 250 天
    sharpe = validator._calculate_sharpe(returns)
    assert sharpe > 0


def test_calculate_sharpe_zero_std():
    """测试零标准差时返回 0。"""
    validator = PBOValidator()
    returns = pd.Series([0.01] * 100)
    sharpe = validator._calculate_sharpe(returns)
    assert sharpe == 0.0


def test_calculate_sharpe_empty():
    """测试空序列返回 0。"""
    validator = PBOValidator()
    returns = pd.Series([])
    sharpe = validator._calculate_sharpe(returns)
    assert sharpe == 0.0


# ------------------------------------------------------------------
# 测试 PBO 检验
# ------------------------------------------------------------------


def test_validate_basic():
    """测试基本 PBO 检验流程。"""
    validator = PBOValidator(n_splits=4)

    # 生成 100 天的收益率数据
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    returns = pd.Series(np.random.randn(100) * 0.01, index=dates)

    # 生成 5 个参数配置
    param_configs = [
        {"returns": returns + np.random.randn(100) * 0.005} for _ in range(5)
    ]

    result = validator.validate(returns, param_configs)

    assert "pbo" in result
    assert "sharpe_is" in result
    assert "sharpe_oos" in result
    assert "rank_correlation" in result
    assert 0 <= result["pbo"] <= 1
    assert result["n_configs"] == 5
    assert result["n_splits"] == 4


def test_validate_insufficient_data():
    """测试数据不足时抛出异常。"""
    validator = PBOValidator(n_splits=16)
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    returns = pd.Series(np.random.randn(10) * 0.01, index=dates)

    with pytest.raises(ValueError, match="returns length .* < n_splits"):
        validator.validate(returns, [{"returns": returns}])


def test_validate_overfitting_scenario():
    """测试过拟合场景（样本内好，样本外差）。"""
    validator = PBOValidator(n_splits=4)

    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    returns = pd.Series(np.random.randn(100) * 0.01, index=dates)

    # 构造过拟合配置：样本内收益高，样本外收益低
    param_configs = []
    for i in range(5):
        config_returns = returns.copy()
        # 前 50 天（样本内）增加收益
        config_returns.iloc[:50] += 0.02
        # 后 50 天（样本外）减少收益
        config_returns.iloc[50:] -= 0.01
        param_configs.append({"returns": config_returns})

    result = validator.validate(returns, param_configs)

    # 过拟合场景下 PBO 应该较高
    assert result["pbo"] > 0.3


# ------------------------------------------------------------------
# 测试结果解释
# ------------------------------------------------------------------


def test_interpret_low_risk():
    """测试低风险场景的解释。"""
    validator = PBOValidator()
    result = {
        "pbo": 0.2,
        "sharpe_is": 1.5,
        "sharpe_oos": 1.3,
        "rank_correlation": 0.8,
    }
    interpretation = validator.interpret(result)
    assert "低风险" in interpretation
    assert "强相关" in interpretation


def test_interpret_high_risk():
    """测试高风险场景的解释。"""
    validator = PBOValidator()
    result = {
        "pbo": 0.7,
        "sharpe_is": 2.0,
        "sharpe_oos": 0.5,
        "rank_correlation": 0.2,
    }
    interpretation = validator.interpret(result)
    assert "高风险" in interpretation
    assert "弱相关" in interpretation


def test_interpret_medium_risk():
    """测试中等风险场景的解释。"""
    validator = PBOValidator()
    result = {
        "pbo": 0.4,
        "sharpe_is": 1.2,
        "sharpe_oos": 1.0,
        "rank_correlation": 0.5,
    }
    interpretation = validator.interpret(result)
    assert "中等风险" in interpretation
    assert "中等相关" in interpretation
