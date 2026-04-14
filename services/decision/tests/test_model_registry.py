"""测试品种级模型注册表 — TASK-0114"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
import xgboost as xgb

from src.research.model_registry import ModelEntry, ModelRegistry
from src.research.regime_detector import Regime, RegimeDetector, RegimeResult
from src.research.trainer import XGBoostTrainer


class TestModelRegistry:
    """测试 ModelRegistry 核心功能。"""

    def test_register_and_get(self):
        """测试注册和获取模型。"""
        registry = ModelRegistry()

        # 创建模型
        model = xgb.XGBClassifier(n_estimators=10)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # 注册
        entry = registry.register(
            symbol="rb",
            regime="trend",
            model=model,
            best_params={"n_estimators": 10},
            sharpe=1.5,
        )

        assert entry.symbol == "rb"
        assert entry.regime == "trend"
        assert entry.sharpe == 1.5
        assert entry.version == 1

        # 获取
        retrieved = registry.get("rb", "trend")
        assert retrieved is not None
        assert retrieved.symbol == "rb"
        assert retrieved.sharpe == 1.5

    def test_two_symbols_isolated(self):
        """测试两个品种互不干扰。"""
        registry = ModelRegistry()

        # 创建两个模型
        model_rb = xgb.XGBClassifier(n_estimators=10)
        model_cu = xgb.XGBClassifier(n_estimators=20)

        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)

        model_rb.fit(X, y)
        model_cu.fit(X, y)

        # 注册 rb
        registry.register(
            symbol="rb",
            regime="trend",
            model=model_rb,
            best_params={"n_estimators": 10},
            sharpe=1.5,
        )

        # 注册 cu
        registry.register(
            symbol="cu",
            regime="oscillation",
            model=model_cu,
            best_params={"n_estimators": 20},
            sharpe=2.0,
        )

        # 验证隔离
        rb_entry = registry.get("rb", "trend")
        cu_entry = registry.get("cu", "oscillation")

        assert rb_entry is not None
        assert cu_entry is not None
        assert rb_entry.symbol == "rb"
        assert cu_entry.symbol == "cu"
        assert rb_entry.best_params["n_estimators"] == 10
        assert cu_entry.best_params["n_estimators"] == 20

        # rb 不应该有 oscillation
        assert registry.get("rb", "oscillation") is None

    def test_version_increment(self):
        """测试版本号递增。"""
        registry = ModelRegistry()

        model = xgb.XGBClassifier(n_estimators=10)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # 第一次注册
        entry1 = registry.register(
            symbol="rb",
            regime="trend",
            model=model,
            best_params={},
            sharpe=1.0,
        )
        assert entry1.version == 1

        # 第二次注册（更新）
        entry2 = registry.register(
            symbol="rb",
            regime="trend",
            model=model,
            best_params={},
            sharpe=1.5,
        )
        assert entry2.version == 2

    def test_retire(self):
        """测试注销模型。"""
        registry = ModelRegistry()

        model = xgb.XGBClassifier(n_estimators=10)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # 注册
        registry.register(
            symbol="rb",
            regime="trend",
            model=model,
            best_params={},
            sharpe=1.5,
        )

        # 验证存在
        assert registry.get("rb", "trend") is not None

        # 注销
        success = registry.retire("rb", "trend")
        assert success is True

        # 验证已删除
        assert registry.get("rb", "trend") is None

        # 再次注销应该失败
        success = registry.retire("rb", "trend")
        assert success is False

    def test_get_best_regime(self):
        """测试获取 Sharpe 最高的 regime。"""
        registry = ModelRegistry()

        model = xgb.XGBClassifier(n_estimators=10)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # 注册三个 regime
        registry.register("rb", "trend", model, {}, sharpe=1.5)
        registry.register("rb", "oscillation", model, {}, sharpe=2.5)
        registry.register("rb", "high_vol", model, {}, sharpe=1.0)

        # 获取最佳
        best = registry.get_best_regime("rb")
        assert best is not None
        assert best.regime == "oscillation"
        assert best.sharpe == 2.5

    def test_list_symbols(self):
        """测试列出所有品种。"""
        registry = ModelRegistry()

        model = xgb.XGBClassifier(n_estimators=10)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # 注册多个品种
        registry.register("rb", "trend", model, {}, sharpe=1.5)
        registry.register("cu", "oscillation", model, {}, sharpe=2.0)
        registry.register("au", "high_vol", model, {}, sharpe=1.8)

        symbols = registry.list_symbols()
        assert len(symbols) == 3
        assert "rb" in symbols
        assert "cu" in symbols
        assert "au" in symbols

    def test_persistence(self):
        """测试持久化和加载。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_dir = Path(tmpdir)

            # 创建注册表并注册模型
            registry1 = ModelRegistry(persist_dir=str(persist_dir))

            model = xgb.XGBClassifier(n_estimators=10)
            X = np.random.rand(100, 5)
            y = np.random.randint(0, 2, 100)
            model.fit(X, y)

            registry1.register(
                symbol="rb",
                regime="trend",
                model=model,
                best_params={"n_estimators": 10},
                sharpe=1.5,
            )

            # 创建新注册表，应该自动加载
            registry2 = ModelRegistry(persist_dir=str(persist_dir))

            entry = registry2.get("rb", "trend")
            assert entry is not None
            assert entry.symbol == "rb"
            assert entry.sharpe == 1.5
            assert entry.best_params["n_estimators"] == 10


class TestRegimeDetector:
    """测试 RegimeDetector。"""

    @pytest.mark.asyncio
    async def test_detect_success(self):
        """测试正常检测流程。"""
        detector = RegimeDetector()

        bars_5d = [
            {"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
            {"open": 104, "high": 108, "low": 103, "close": 107, "volume": 1100},
            {"open": 107, "high": 110, "low": 106, "close": 109, "volume": 1200},
            {"open": 109, "high": 112, "low": 108, "close": 111, "volume": 1300},
            {"open": 111, "high": 115, "low": 110, "close": 114, "volume": 1400},
        ]

        bars_20d = bars_5d * 4  # 简化

        # Mock httpx 响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"regime": "trend", "confidence": 0.85, "reasoning": "明显上涨趋势"}'
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await detector.detect("rb", bars_5d, bars_20d)

            assert result.symbol == "rb"
            assert result.regime == Regime.TREND
            assert result.confidence == 0.85
            assert result.source == "phi4"

    @pytest.mark.asyncio
    async def test_detect_timeout_fallback(self):
        """测试超时降级。"""
        detector = RegimeDetector()

        bars_5d = [{"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000}]
        bars_20d = bars_5d * 4

        # Mock 超时
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=TimeoutError("timeout")
            )

            result = await detector.detect("rb", bars_5d, bars_20d)

            assert result.symbol == "rb"
            assert result.regime == Regime.TREND  # fallback
            assert result.source == "fallback"
            assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_detect_parse_error_fallback(self):
        """测试解析错误降级。"""
        detector = RegimeDetector()

        bars_5d = [{"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000}]
        bars_20d = bars_5d * 4

        # Mock 无效 JSON 响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "invalid json"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await detector.detect("rb", bars_5d, bars_20d)

            assert result.symbol == "rb"
            assert result.regime == Regime.TREND  # fallback
            assert result.source == "fallback"


class TestTrainerIntegration:
    """测试 Trainer 与 ModelRegistry 集成。"""

    def test_train_for_symbol_incremental(self):
        """测试增量训练。"""
        trainer = XGBoostTrainer()
        registry = ModelRegistry()

        # 准备数据
        X = np.random.rand(200, 5)
        y = np.random.randint(0, 2, 200)

        params = {"n_estimators": 10, "max_depth": 3}

        # 第一次训练
        model1, metrics1 = trainer.train_for_symbol(
            symbol="rb",
            regime="trend",
            X=X,
            y=y,
            params=params,
            existing_model=None,
        )

        sharpe1 = metrics1["sharpe"]

        # 注册
        registry.register("rb", "trend", model1, params, sharpe1)

        # 第二次训练（增量）
        X_new = np.random.rand(200, 5)
        y_new = np.random.randint(0, 2, 200)

        existing = registry.get("rb", "trend")
        model2, metrics2 = trainer.train_for_symbol(
            symbol="rb",
            regime="trend",
            X=X_new,
            y=y_new,
            params=params,
            existing_model=existing.model if existing else None,
        )

        # 验证增量训练执行
        assert model2 is not None
        assert "sharpe" in metrics2

    def test_train_for_symbol_no_cross_contamination(self):
        """测试增量训练不跨品种污染。"""
        trainer = XGBoostTrainer()
        registry = ModelRegistry()

        X = np.random.rand(200, 5)
        y = np.random.randint(0, 2, 200)
        params = {"n_estimators": 10, "max_depth": 3}

        # 训练 rb
        model_rb, metrics_rb = trainer.train_for_symbol(
            symbol="rb", regime="trend", X=X, y=y, params=params
        )
        registry.register("rb", "trend", model_rb, params, metrics_rb["sharpe"])

        # 训练 cu（独立）
        model_cu, metrics_cu = trainer.train_for_symbol(
            symbol="cu", regime="trend", X=X, y=y, params=params
        )
        registry.register("cu", "trend", model_cu, params, metrics_cu["sharpe"])

        # 验证两个模型独立存在
        rb_entry = registry.get("rb", "trend")
        cu_entry = registry.get("cu", "trend")

        assert rb_entry is not None
        assert cu_entry is not None
        assert rb_entry.symbol == "rb"
        assert cu_entry.symbol == "cu"
