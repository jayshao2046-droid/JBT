from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.gating.backtest_gate import BacktestGate, CertStatus
from src.gating.research_gate import ResearchGate
from src.model import router as router_mod
from src.persistence.state_store import FileStateStore
from src.strategy.repository import StrategyPackage, StrategyRepository


def _make_strategy_package(
    strategy_id: str = "alpha-router-001",
    factor_version_hash: str = "factor-hash-001",
    research_snapshot_id: str = "rs-001",
    backtest_certificate_id: str = "bc-001",
) -> StrategyPackage:
    return StrategyPackage(
        strategy_id=strategy_id,
        strategy_name="Router Strategy",
        strategy_version="2026.04.08",
        template_id="trend-v1",
        package_hash="pkg-hash-001",
        factor_version_hash=factor_version_hash,
        factor_sync_status="aligned",
        research_snapshot_id=research_snapshot_id,
        backtest_certificate_id=backtest_certificate_id,
        risk_profile_hash="risk-hash-001",
        config_snapshot_ref="cfg-001",
        allowed_targets=["sim-trading"],
    )


def _patch_router_dependencies(monkeypatch, repo, backtest_gate, research_gate) -> None:
    monkeypatch.setattr(
        router_mod,
        "get_settings",
        lambda: SimpleNamespace(
            model_router_require_backtest_cert=True,
            model_router_require_research_snapshot=True,
        ),
    )
    monkeypatch.setattr(router_mod, "get_repository", lambda: repo)
    monkeypatch.setattr(router_mod, "get_backtest_gate", lambda: backtest_gate)
    monkeypatch.setattr(router_mod, "get_research_gate", lambda: research_gate)


# ---------------------------------------------------------------------------
# BacktestGate
# ---------------------------------------------------------------------------


def test_backtest_gate_register_and_valid() -> None:
    """register_cert 后 is_valid 应返回 True。"""
    gate = BacktestGate()
    gate.register_cert(
        cert_id="bc-test-001",
        strategy_id="alpha-001",
        sharpe=1.5,
        drawdown=0.08,
        expires_days=90,
    )
    assert gate.is_valid("alpha-001") is True


def test_backtest_gate_unknown_strategy() -> None:
    """未注册策略的 is_valid 应返回 False。"""
    gate = BacktestGate()
    assert gate.is_valid("unknown-strategy") is False


def test_backtest_gate_invalidate() -> None:
    """invalidate 后 is_valid 应返回 False；review_status 变为 rejected。"""
    gate = BacktestGate()
    gate.register_cert(
        cert_id="bc-test-002",
        strategy_id="alpha-002",
        sharpe=1.2,
        drawdown=0.1,
    )
    assert gate.is_valid("alpha-002") is True

    gate.invalidate("bc-test-002")

    assert gate.is_valid("alpha-002") is False
    cert = gate.get_cert("alpha-002")
    assert cert is not None
    assert cert.review_status == CertStatus.REJECTED


def test_cert_expiry() -> None:
    """过期证书（expires_days=-1）is_valid 应返回 False，状态应为 expired。"""
    gate = BacktestGate()
    gate.register_cert(
        cert_id="bc-test-003",
        strategy_id="alpha-003",
        sharpe=0.9,
        drawdown=0.15,
        expires_days=-1,  # 立即过期
    )
    assert gate.is_valid("alpha-003") is False
    cert = gate.get_cert("alpha-003")
    assert cert is not None
    assert cert.review_status == CertStatus.EXPIRED


def test_cert_get_cert_returns_none_for_unknown() -> None:
    """get_cert 对未注册策略应返回 None。"""
    gate = BacktestGate()
    assert gate.get_cert("nonexistent") is None


def test_backtest_gate_persists_record_across_restart(tmp_path) -> None:
    state_file = tmp_path / "decision-state.json"

    first_gate = BacktestGate(state_store=FileStateStore(state_file))
    first_gate.register_cert(
        cert_id="bc-persist-001",
        strategy_id="alpha-persist-001",
        sharpe=1.7,
        drawdown=0.06,
        factor_version_hash="factor-hash-001",
        expires_days=90,
        requested_symbol="DCE.p2605",
        executed_data_symbol="KQ_m_DCE_p",
    )

    raw_state = json.loads(state_file.read_text(encoding="utf-8"))
    stored = raw_state["backtest_certs"]["alpha-persist-001"]
    assert stored["requested_symbol"] == "DCE.p2605"
    assert stored["executed_data_symbol"] == "KQ_m_DCE_p"

    restarted_gate = BacktestGate(state_store=FileStateStore(state_file))
    restored = restarted_gate.get_cert("alpha-persist-001")

    assert restored is not None
    assert restored.certificate_id == "bc-persist-001"
    assert restored.factor_version_hash == "factor-hash-001"
    assert restored.requested_symbol == "DCE.p2605"
    assert restored.executed_data_symbol == "KQ_m_DCE_p"
    assert restarted_gate.is_valid("alpha-persist-001") is True


# ---------------------------------------------------------------------------
# ResearchGate
# ---------------------------------------------------------------------------


def test_research_gate_register_and_complete() -> None:
    """register_snapshot 后 is_complete 应返回 True。"""
    gate = ResearchGate()
    gate.register_snapshot(
        session_id="sess-001",
        strategy_id="alpha-001",
        factor_hash="hash-abc123",
        best_params={"n_estimators": 200, "max_depth": 5},
        metrics={"sharpe": 1.4, "drawdown": 0.09, "accuracy": 0.62},
        shap_summary_path="/tmp/shap_alpha001.json",
        onnx_artifact_path="/tmp/alpha001.onnx",
    )
    assert gate.is_complete("alpha-001") is True


def test_research_gate_unknown_strategy() -> None:
    """未注册策略的 is_complete 应返回 False。"""
    gate = ResearchGate()
    assert gate.is_complete("unknown-strategy") is False


def test_research_gate_snapshot_fields() -> None:
    """register_snapshot 返回的快照字段应对齐契约。"""
    gate = ResearchGate()
    snap = gate.register_snapshot(
        session_id="sess-002",
        strategy_id="alpha-002",
        factor_hash="hash-xyz789",
        best_params={"n_estimators": 300},
        metrics={"sharpe": 1.1},
    )
    assert snap.research_snapshot_id == "sess-002"
    assert snap.strategy_id == "alpha-002"
    assert snap.factor_version_hash == "hash-xyz789"
    assert snap.research_status == "completed"


def test_research_gate_get_snapshot() -> None:
    """get_snapshot 应返回最新注册的快照对象。"""
    gate = ResearchGate()
    assert gate.get_snapshot("alpha-004") is None

    gate.register_snapshot(
        session_id="sess-003",
        strategy_id="alpha-004",
        factor_hash="hash-xxx",
        best_params={},
        metrics={},
    )
    snap = gate.get_snapshot("alpha-004")
    assert snap is not None
    assert snap.research_snapshot_id == "sess-003"


def test_research_gate_persists_record_across_restart(tmp_path) -> None:
    state_file = tmp_path / "decision-state.json"

    first_gate = ResearchGate(state_store=FileStateStore(state_file))
    first_gate.register_snapshot(
        session_id="rs-persist-001",
        strategy_id="alpha-persist-002",
        factor_hash="factor-hash-001",
        best_params={"n_estimators": 200},
        metrics={"sharpe": 1.3},
    )

    restarted_gate = ResearchGate(state_store=FileStateStore(state_file))
    restored = restarted_gate.get_snapshot("alpha-persist-002")

    assert restored is not None
    assert restored.research_snapshot_id == "rs-persist-001"
    assert restored.factor_version_hash == "factor-hash-001"
    assert restarted_gate.is_complete("alpha-persist-002") is True


def test_model_router_rejects_missing_persisted_research_snapshot(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "decision-state.json"
    initial_store = FileStateStore(state_file)

    repo = StrategyRepository(state_store=initial_store)
    repo.create(_make_strategy_package())

    backtest_gate = BacktestGate(state_store=initial_store)
    backtest_gate.register_cert(
        cert_id="bc-001",
        strategy_id="alpha-router-001",
        sharpe=1.4,
        drawdown=0.08,
        factor_version_hash="factor-hash-001",
    )

    restarted_store = FileStateStore(state_file)
    _patch_router_dependencies(
        monkeypatch,
        StrategyRepository(state_store=restarted_store),
        BacktestGate(state_store=restarted_store),
        ResearchGate(state_store=restarted_store),
    )

    result = router_mod.route(
        strategy_id="alpha-router-001",
        backtest_certificate_id="bc-001",
        research_snapshot_id="rs-001",
    )

    assert result["allowed"] is False
    assert "research snapshot" in result["reason"]


def test_model_router_rejects_mismatched_eligibility_ids(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "decision-state.json"
    initial_store = FileStateStore(state_file)

    repo = StrategyRepository(state_store=initial_store)
    repo.create(_make_strategy_package())

    backtest_gate = BacktestGate(state_store=initial_store)
    backtest_gate.register_cert(
        cert_id="bc-001",
        strategy_id="alpha-router-001",
        sharpe=1.4,
        drawdown=0.08,
        factor_version_hash="factor-hash-001",
    )
    research_gate = ResearchGate(state_store=initial_store)
    research_gate.register_snapshot(
        session_id="rs-001",
        strategy_id="alpha-router-001",
        factor_hash="factor-hash-001",
        best_params={"max_depth": 4},
        metrics={"sharpe": 1.2},
    )

    restarted_store = FileStateStore(state_file)
    _patch_router_dependencies(
        monkeypatch,
        StrategyRepository(state_store=restarted_store),
        BacktestGate(state_store=restarted_store),
        ResearchGate(state_store=restarted_store),
    )

    result = router_mod.route(
        strategy_id="alpha-router-001",
        backtest_certificate_id="bc-wrong",
        research_snapshot_id="rs-001",
    )

    assert result["allowed"] is False
    assert "backtest certificate" in result["reason"]


def test_model_router_allows_valid_persisted_eligibility(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "decision-state.json"
    initial_store = FileStateStore(state_file)

    repo = StrategyRepository(state_store=initial_store)
    repo.create(_make_strategy_package())

    backtest_gate = BacktestGate(state_store=initial_store)
    backtest_gate.register_cert(
        cert_id="bc-001",
        strategy_id="alpha-router-001",
        sharpe=1.4,
        drawdown=0.08,
        factor_version_hash="factor-hash-001",
    )
    research_gate = ResearchGate(state_store=initial_store)
    research_gate.register_snapshot(
        session_id="rs-001",
        strategy_id="alpha-router-001",
        factor_hash="factor-hash-001",
        best_params={"max_depth": 4},
        metrics={"sharpe": 1.2},
    )

    restarted_store = FileStateStore(state_file)
    _patch_router_dependencies(
        monkeypatch,
        StrategyRepository(state_store=restarted_store),
        BacktestGate(state_store=restarted_store),
        ResearchGate(state_store=restarted_store),
    )

    result = router_mod.route(
        strategy_id="alpha-router-001",
        backtest_certificate_id="bc-001",
        research_snapshot_id="rs-001",
    )

    assert result == {
        "allowed": True,
        "reason": "all gate checks passed",
    }
