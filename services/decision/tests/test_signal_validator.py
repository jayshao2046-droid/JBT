"""测试信号验证器和因子监控器 — TASK-0115"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.research.factor_monitor import FactorHealth, FactorMonitor
from src.research.signal_validator import SignalValidator, ValidationResult


class TestSignalValidator:
    """测试 SignalValidator。"""

    def test_validate_high_ic_signal(self):
        """测试高 IC 信号验证通过。"""
        validator = SignalValidator()

        # 构造高相关性的因子和收益
        factor_history = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        forward_returns = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]

        result = validator.validate(
            symbol="rb",
            signal_id="test_signal_1",
            signal_value=0.75,
            forward_returns=forward_returns,
            factor_history=factor_history,
            regime="trend",
        )

        assert result.symbol == "rb"
        assert result.valid is True
        assert result.ic > 0.5  # 高相关性
        assert result.anomaly is False
        assert result.regime_consistent is True

    def test_validate_low_ic_signal(self):
        """测试低 IC 信号验证失败。"""
        validator = SignalValidator()

        # 构造低相关性的因子和收益
        factor_history = [0.1, 0.2, 0.3, 0.4]
        forward_returns = [0.04, 0.03, 0.02, 0.01]  # 反向

        result = validator.validate(
            symbol="rb",
            signal_id="test_signal_2",
            signal_value=0.5,
            forward_returns=forward_returns,
            factor_history=factor_history,
            regime="trend",
        )

        assert result.valid is False
        assert "IC=" in result.reasons[0]
        assert "无信息量" in result.reasons[0]

    def test_validate_anomaly_signal(self):
        """测试异常信号检测。"""
        validator = SignalValidator()

        # 构造正常历史 + 异常当前值
        factor_history = [0.1, 0.15, 0.12, 0.18, 0.14, 0.16, 0.13, 0.17]
        forward_returns = [0.01] * len(factor_history)

        # 异常值：远超 3σ
        result = validator.validate(
            symbol="rb",
            signal_id="test_signal_3",
            signal_value=5.0,  # 异常大
            forward_returns=forward_returns,
            factor_history=factor_history,
            regime="trend",
        )

        assert result.anomaly is True
        assert result.valid is False
        assert any("超过" in r and "σ" in r for r in result.reasons)

    def test_validate_regime_inconsistency(self):
        """测试 regime 不一致检测。"""
        validator = SignalValidator()

        factor_history = [0.1, 0.2, 0.3, 0.4]
        forward_returns = [0.01, 0.02, 0.03, 0.04]

        # compression 期间强信号视为不一致
        result = validator.validate(
            symbol="rb",
            signal_id="test_signal_4",
            signal_value=0.9,  # 强信号
            forward_returns=forward_returns,
            factor_history=factor_history,
            regime="compression",
        )

        assert result.regime_consistent is False
        assert result.valid is False
        assert any("不一致" in r for r in result.reasons)

    def test_validate_ic_decay(self):
        """测试 IC 衰减检测。"""
        validator = SignalValidator()

        # 前半段高相关，后半段低相关
        factor_history = [0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5]
        forward_returns = [0.01, 0.02, 0.03, 0.04, 0.01, 0.01, 0.01, 0.01]

        result = validator.validate(
            symbol="rb",
            signal_id="test_signal_5",
            signal_value=0.5,
            forward_returns=forward_returns,
            factor_history=factor_history,
            regime="trend",
        )

        # IC 衰减应该被检测到
        assert result.ic_decay > 0.3
        assert any("衰减" in r for r in result.reasons)

    def test_validate_batch(self):
        """测试批量验证。"""
        validator = SignalValidator()

        signals = [
            {
                "symbol": "rb",
                "signal_id": "sig1",
                "signal_value": 0.5,
                "forward_returns": [0.01, 0.02, 0.03],
                "factor_history": [0.1, 0.2, 0.3],
                "regime": "trend",
            },
            {
                "symbol": "cu",
                "signal_id": "sig2",
                "signal_value": 0.6,
                "forward_returns": [0.02, 0.03, 0.04],
                "factor_history": [0.2, 0.3, 0.4],
                "regime": "oscillation",
            },
        ]

        results = validator.validate_batch(signals)

        assert len(results) == 2
        assert results[0].symbol == "rb"
        assert results[1].symbol == "cu"


class TestFactorMonitor:
    """测试 FactorMonitor。"""

    def test_record_and_check_healthy(self):
        """测试记录和检查健康因子。"""
        monitor = FactorMonitor()

        # 记录 30 个样本，保持稳定相关性
        for i in range(30):
            factor_value = 0.1 * i
            forward_return = 0.01 * i
            monitor.record("momentum_5d", "rb", factor_value, forward_return)

        health = monitor.check("momentum_5d", "rb")

        assert health is not None
        assert health.factor_name == "momentum_5d"
        assert health.symbol == "rb"
        assert health.healthy is True
        assert len(health.warnings) == 0

    def test_check_ic_decay(self):
        """测试 IC 衰减检测。"""
        monitor = FactorMonitor()

        # 前 60 个样本高相关
        for i in range(60):
            monitor.record("momentum_5d", "rb", 0.1 * i, 0.01 * i)

        # 后 30 个样本低相关
        for i in range(30):
            monitor.record("momentum_5d", "rb", 0.5, 0.0)

        health = monitor.check("momentum_5d", "rb")

        assert health is not None
        assert health.decay_rate > 0.3
        assert not health.healthy
        assert any("衰减" in w for w in health.warnings)

    def test_check_mean_shift(self):
        """测试均值漂移检测。"""
        monitor = FactorMonitor()

        # 前 60 个样本均值 0.5
        for i in range(60):
            monitor.record("momentum_5d", "rb", 0.5, 0.01)

        # 后 30 个样本均值 2.0（显著漂移）
        for i in range(30):
            monitor.record("momentum_5d", "rb", 2.0, 0.01)

        health = monitor.check("momentum_5d", "rb")

        assert health is not None
        assert abs(health.mean_shift) > 2.0
        assert not health.healthy
        assert any("均值漂移" in w for w in health.warnings)

    def test_check_std_ratio_anomaly(self):
        """测试方差异常检测。"""
        monitor = FactorMonitor()

        # 前 60 个样本方差小
        for i in range(60):
            monitor.record("momentum_5d", "rb", 0.5 + 0.01 * (i % 2), 0.01)

        # 后 30 个样本方差大
        for i in range(30):
            monitor.record("momentum_5d", "rb", 0.5 + 2.0 * (i % 2), 0.01)

        health = monitor.check("momentum_5d", "rb")

        assert health is not None
        assert health.std_ratio > 2.0
        assert not health.healthy
        assert any("方差比" in w for w in health.warnings)

    def test_check_insufficient_samples(self):
        """测试样本不足时返回 None。"""
        monitor = FactorMonitor()

        # 只记录 5 个样本（< MIN_SAMPLES=10）
        for i in range(5):
            monitor.record("momentum_5d", "rb", 0.1 * i, 0.01 * i)

        health = monitor.check("momentum_5d", "rb")

        assert health is None

    def test_check_all(self):
        """测试检查所有因子。"""
        monitor = FactorMonitor()

        # 记录两个因子
        for i in range(30):
            monitor.record("momentum_5d", "rb", 0.1 * i, 0.01 * i)
            monitor.record("volatility_20d", "cu", 0.2 * i, 0.02 * i)

        results = monitor.check_all()

        assert len(results) == 2
        assert {r.factor_name for r in results} == {"momentum_5d", "volatility_20d"}
        assert {r.symbol for r in results} == {"rb", "cu"}

    def test_get_unhealthy(self):
        """测试获取不健康因子。"""
        monitor = FactorMonitor()

        # 健康因子
        for i in range(30):
            monitor.record("momentum_5d", "rb", 0.1 * i, 0.01 * i)

        # 不健康因子（IC 衰减）
        for i in range(60):
            monitor.record("volatility_20d", "cu", 0.1 * i, 0.01 * i)
        for i in range(30):
            monitor.record("volatility_20d", "cu", 0.5, 0.0)

        unhealthy = monitor.get_unhealthy()

        assert len(unhealthy) >= 1
        assert any(h.factor_name == "volatility_20d" for h in unhealthy)

    def test_clear(self):
        """测试清除因子历史。"""
        monitor = FactorMonitor()

        for i in range(30):
            monitor.record("momentum_5d", "rb", 0.1 * i, 0.01 * i)

        # 清除前可以检查
        health = monitor.check("momentum_5d", "rb")
        assert health is not None

        # 清除
        monitor.clear("momentum_5d", "rb")

        # 清除后返回 None
        health = monitor.check("momentum_5d", "rb")
        assert health is None
