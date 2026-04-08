from __future__ import annotations

import importlib
import sys

import httpx
import numpy as np
import pytest

import src.research.factor_loader as factor_loader_mod
from src.gating.backtest_gate import BacktestGate
from src.persistence.state_store import FileStateStore
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


def test_factor_loader_load_prefers_executed_data_symbol_from_backtest_cert(
    tmp_path,
    monkeypatch,
) -> None:
    """load() 应优先使用回测证书中的 executed_data_symbol 访问 data service。"""
    monkeypatch.setenv("DATA_SERVICE_URL", "http://data-service:8105")
    state_file = tmp_path / "decision-state.json"
    monkeypatch.setenv("DECISION_STATE_FILE", str(state_file))

    BacktestGate(state_store=FileStateStore(state_file)).register_cert(
        cert_id="bc-research-001",
        strategy_id="strategy-alpha-001",
        sharpe=1.4,
        drawdown=0.08,
        requested_symbol="DCE.p2605",
        executed_data_symbol="KQ_m_DCE_p",
    )

    def fake_get(url: str, *, params: dict[str, object], timeout: float) -> httpx.Response:
        assert url == "http://data-service:8105/api/v1/bars"
        assert params == {
            "symbol": "KQ_m_DCE_p",
            "timeframe_minutes": 1,
            "start": "2024-04-03",
            "end": "2024-04-08",
        }
        assert timeout == 30
        payload = {
            "requested_symbol": "KQ_m_DCE_p",
            "resolved_symbol": "KQ_m_DCE_p",
            "source_kind": "continuous",
            "timeframe_minutes": 1,
            "count": 5,
            "bars": [
                {"datetime": "2024-04-03T09:00:00", "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.0, "volume": 100.0, "open_interest": 1000.0},
                {"datetime": "2024-04-03T09:01:00", "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0, "volume": 110.0, "open_interest": 1005.0},
                {"datetime": "2024-04-03T09:02:00", "open": 11.0, "high": 12.0, "low": 10.0, "close": 12.0, "volume": 121.0, "open_interest": 1010.0},
                {"datetime": "2024-04-03T09:03:00", "open": 12.0, "high": 13.0, "low": 11.0, "close": 11.0, "volume": 133.1, "open_interest": 1008.0},
                {"datetime": "2024-04-03T09:04:00", "open": 11.0, "high": 14.0, "low": 10.0, "close": 13.0, "volume": 146.41, "open_interest": 1015.0},
            ],
        }
        return httpx.Response(
            200,
            request=httpx.Request("GET", url, params=params),
            json=payload,
        )

    monkeypatch.setattr(factor_loader_mod.httpx, "get", fake_get)

    loader = FactorLoader()
    X, y = loader.load("strategy-alpha-001", "2024-04-03", "2024-04-08", n_features=5)

    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.dtype == np.float32
    assert y.dtype == np.int64
    assert X.shape == (3, 5)
    assert y.shape == (3,)
    np.testing.assert_allclose(
        X[0],
        np.array([0.1, 3.0 / 11.0, 0.1, 0.1, 0.005], dtype=np.float32),
        rtol=1e-6,
    )
    np.testing.assert_array_equal(y, np.array([1, 0, 1], dtype=np.int64))


def test_factor_loader_load_raises_when_no_valid_symbol_source(
    tmp_path,
    monkeypatch,
) -> None:
    """无证书 symbol 且 strategy_id 不是合法标的格式时，应显式失败。"""
    monkeypatch.setenv("DATA_SERVICE_URL", "http://data-service:8105")
    monkeypatch.setenv("DECISION_STATE_FILE", str(tmp_path / "decision-state.json"))

    def fake_get(url: str, *, params: dict[str, object], timeout: float) -> httpx.Response:
        raise AssertionError("httpx.get should not be called without a valid data symbol")

    monkeypatch.setattr(factor_loader_mod.httpx, "get", fake_get)

    loader = FactorLoader()
    with pytest.raises(RuntimeError, match="No valid data symbol available for strategy strategy-alpha-001"):
        loader.load("strategy-alpha-001", "2024-04-03", "2024-04-08")


def test_factor_loader_load_raises_when_data_service_unavailable(monkeypatch) -> None:
    """上游 bars API 不可用时，应显式失败而不是静默回退到 mock 数据。"""
    monkeypatch.setenv("DATA_SERVICE_URL", "http://data-service:8105")

    def fake_get(url: str, *, params: dict[str, object], timeout: float) -> httpx.Response:
        raise httpx.ConnectError(
            "connection refused",
            request=httpx.Request("GET", url, params=params),
        )

    monkeypatch.setattr(factor_loader_mod.httpx, "get", fake_get)

    loader = FactorLoader()
    with pytest.raises(RuntimeError, match="Failed to load bars from data service"):
        loader.load("DCE.p2605", "2024-04-03", "2024-04-08")


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
