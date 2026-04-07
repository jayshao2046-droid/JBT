from __future__ import annotations

import importlib
import sys

import numpy as np
import pytest

from src.research.session import ResearchSession, ResearchStatus, ResearchArtifacts
from src.research.factor_loader import FactorLoader


# ---------------------------------------------------------------------------
# ResearchSession — 初始化与状态流转
# ---------------------------------------------------------------------------


def test_research_session_init() -> None:
    """新建会话默认状态为 PENDING，session_id 自动生成。"""
    session = ResearchSession(strategy_id="alpha-001")
    assert session.status == ResearchStatus.PENDING
    assert session.session_id != ""
    assert session.strategy_id == "alpha-001"
    assert session.best_params == {}
    assert session.metrics == {}
    assert session.completed_at is None


def test_research_session_start() -> None:
    """start() 将状态从 PENDING 变为 RUNNING。"""
    session = ResearchSession(strategy_id="alpha-002")
    session.start()
    assert session.status == ResearchStatus.RUNNING


def test_research_session_complete() -> None:
    """complete() 将状态从 RUNNING 变为 COMPLETED，记录参数与指标。"""
    session = ResearchSession(strategy_id="alpha-003")
    session.start()
    params = {"n_estimators": 200, "max_depth": 5}
    metrics = {"sharpe": 1.3, "drawdown": 0.08, "accuracy": 0.61}
    session.complete(best_params=params, metrics=metrics)
    assert session.status == ResearchStatus.COMPLETED
    assert session.best_params == params
    assert session.metrics == metrics
    assert session.completed_at is not None


def test_research_session_fail() -> None:
    """fail() 将状态切换为 FAILED 并记录 completed_at。"""
    session = ResearchSession(strategy_id="alpha-004")
    session.start()
    session.fail(reason="训练数据不足")
    assert session.status == ResearchStatus.FAILED
    assert session.completed_at is not None


def test_research_session_invalid_transition() -> None:
    """从非 PENDING 状态调用 start() 应抛出 ValueError。"""
    session = ResearchSession(strategy_id="alpha-005")
    session.start()
    with pytest.raises(ValueError):
        session.start()


def test_research_session_complete_invalid() -> None:
    """从非 RUNNING 状态调用 complete() 应抛出 ValueError。"""
    session = ResearchSession(strategy_id="alpha-006")
    with pytest.raises(ValueError):
        session.complete(best_params={}, metrics={})


def test_research_session_artifacts_default() -> None:
    """artifacts 默认为空路径的 ResearchArtifacts。"""
    session = ResearchSession(strategy_id="alpha-007")
    assert isinstance(session.artifacts, ResearchArtifacts)
    assert session.artifacts.shap_path == ""
    assert session.artifacts.onnx_path == ""


# ---------------------------------------------------------------------------
# FactorLoader — compute_hash
# ---------------------------------------------------------------------------


def test_factor_loader_compute_hash_deterministic() -> None:
    """相同数组的 hash 应一致。"""
    rng = np.random.default_rng(seed=42)
    X = rng.random((100, 10)).astype(np.float32)
    h1 = FactorLoader.compute_hash(X)
    h2 = FactorLoader.compute_hash(X)
    assert h1 == h2


def test_factor_loader_compute_hash_distinct() -> None:
    """不同数组的 hash 应不同。"""
    rng = np.random.default_rng(seed=42)
    X1 = rng.random((100, 10)).astype(np.float32)
    X2 = rng.random((100, 10)).astype(np.float32)
    assert FactorLoader.compute_hash(X1) != FactorLoader.compute_hash(X2)


def test_factor_loader_mock_load() -> None:
    """mock load 应返回 (X, y) numpy 数组，形状正确。"""
    loader = FactorLoader()
    X, y = loader.load("alpha-001", "2025-01-01", "2025-12-31")
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.ndim == 2
    assert y.ndim == 1
    assert X.shape[0] == y.shape[0]


# ---------------------------------------------------------------------------
# XGBoostTrainer — ImportError 抛出（mock xgboost = None）
# ---------------------------------------------------------------------------


def test_xgboost_trainer_import_error() -> None:
    """当 xgboost 不可用时，导入 trainer 模块应抛出 ImportError。"""
    original_xgb = sys.modules.get("xgboost")
    # 将 xgboost 标记为不可用
    sys.modules["xgboost"] = None  # type: ignore[assignment]

    # 清除已缓存的 trainer 模块（强制重新导入）
    trainer_key = "src.research.trainer"
    original_trainer = sys.modules.pop(trainer_key, None)

    try:
        with pytest.raises(ImportError):
            importlib.import_module(trainer_key)
    finally:
        # 恢复 sys.modules
        if original_xgb is None:
            sys.modules.pop("xgboost", None)
        else:
            sys.modules["xgboost"] = original_xgb

        if original_trainer is not None:
            sys.modules[trainer_key] = original_trainer
        else:
            sys.modules.pop(trainer_key, None)


# ---------------------------------------------------------------------------
# OptunaSearch — ImportError 抛出（mock optuna = None）
# ---------------------------------------------------------------------------


def test_optuna_search_import_error() -> None:
    """当 optuna 不可用时，导入 optuna_search 模块应抛出 ImportError。"""
    original_optuna = sys.modules.get("optuna")
    sys.modules["optuna"] = None  # type: ignore[assignment]

    search_key = "src.research.optuna_search"
    original_search = sys.modules.pop(search_key, None)

    try:
        with pytest.raises(ImportError):
            importlib.import_module(search_key)
    finally:
        if original_optuna is None:
            sys.modules.pop("optuna", None)
        else:
            sys.modules["optuna"] = original_optuna

        if original_search is not None:
            sys.modules[search_key] = original_search
        else:
            sys.modules.pop(search_key, None)
