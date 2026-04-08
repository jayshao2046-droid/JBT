from __future__ import annotations

"""
test_publish.py — TASK-0021-H4
单元测试：发布门禁、适配器、执行器、signal review 与 strategy publish 路由
"""
import io
import unittest.mock as mock
import urllib.error
from typing import Optional

import pytest
from fastapi.testclient import TestClient

import src.api.routes.signal as signal_route
import src.api.routes.strategy as strategy_route
from src.api.app import create_app
from src.gating.backtest_gate import BacktestGate
from src.gating.research_gate import ResearchGate
from src.persistence.state_store import FileStateStore
from src.publish.executor import PublishExecutor, PublishResult, PublishStatus
from src.strategy.repository import StrategyPackage, StrategyRepository
from src.strategy.lifecycle import LifecycleStatus
from src.publish.gate import PublishGate, PublishEligibility
from src.publish.sim_adapter import SimTradingAdapter


# ── 测试固件 ──────────────────────────────────────────────────────────────────

def _make_pkg(
    strategy_id: str = "S001",
    factor_sync: str = "aligned",
    factor_hash: str = "fac-hash-001",
    status: LifecycleStatus = LifecycleStatus.backtest_confirmed,
) -> StrategyPackage:
    pkg = StrategyPackage(
        strategy_id=strategy_id,
        strategy_name="Test Strategy",
        strategy_version="1.0",
        template_id="trend-v1",
        package_hash="pkg-hash-001",
        factor_version_hash=factor_hash,
        factor_sync_status=factor_sync,
        research_snapshot_id="rs-001",
        backtest_certificate_id="bc-001",
        risk_profile_hash="risk-001",
        config_snapshot_ref="config-001",
        allowed_targets=["sim-trading"],
    )
    pkg.lifecycle_status = status
    return pkg


def _make_repo(pkg: Optional[StrategyPackage] = None) -> StrategyRepository:
    repo = StrategyRepository()
    if pkg is not None:
        repo.create(pkg)
    return repo


def _persist_strategy_state(
    state_file,
    pkg: StrategyPackage,
    *,
    register_backtest: bool = True,
    backtest_expires_days: int = 90,
    backtest_factor_hash: str | None = None,
    package_backtest_id: str | None = None,
    register_research: bool = True,
    research_valid_days: int = 30,
    research_factor_hash: str | None = None,
    research_status: str | None = None,
    package_research_id: str | None = None,
) -> None:
    store = FileStateStore(state_file)
    repo = StrategyRepository(state_store=store)
    repo.create(pkg)

    if package_backtest_id is not None:
        repo.update(pkg.strategy_id, {"backtest_certificate_id": package_backtest_id})
    if package_research_id is not None:
        repo.update(pkg.strategy_id, {"research_snapshot_id": package_research_id})

    if register_backtest:
        cert = BacktestGate(state_store=store).register_cert(
            cert_id="bc-001",
            strategy_id=pkg.strategy_id,
            sharpe=1.3,
            drawdown=0.08,
            expires_days=backtest_expires_days,
            factor_version_hash=backtest_factor_hash or pkg.factor_version_hash,
            requested_symbol="DCE.p2605",
            executed_data_symbol="KQ_m_DCE_p",
        )
        store.upsert_record("backtest_certs", pkg.strategy_id, cert.to_dict())

    if register_research:
        snapshot = ResearchGate(state_store=store).register_snapshot(
            session_id="rs-001",
            strategy_id=pkg.strategy_id,
            factor_hash=research_factor_hash or pkg.factor_version_hash,
            best_params={"max_depth": 4},
            metrics={"sharpe": 1.1},
            valid_days=research_valid_days,
        )
        record = snapshot.to_dict()
        if research_status is not None:
            record["research_status"] = research_status
        store.upsert_record("research_snapshots", pkg.strategy_id, record)


def _patch_gate_dependencies(monkeypatch, state_file, *, execution_eligible: bool = True, execution_reason: str = "sim-trading gate open") -> StrategyRepository:
    store = FileStateStore(state_file)
    repo = StrategyRepository(state_store=store)
    backtest_gate = BacktestGate(state_store=store)
    research_gate = ResearchGate(state_store=store)

    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    monkeypatch.setattr("src.publish.gate.get_backtest_gate", lambda: backtest_gate)
    monkeypatch.setattr("src.publish.gate.get_research_gate", lambda: research_gate)
    monkeypatch.setattr(
        "src.publish.gate.check_execution_eligibility",
        lambda strategy_id, target: {
            "eligible": execution_eligible,
            "target": target,
            "reason": execution_reason,
        },
    )
    return repo


_DECISION_REQUEST = {
    "request_id": "dr-001",
    "trace_id": "tr-001",
    "strategy_id": "S001",
    "strategy_version": "1.0",
    "symbol": "DCE.p2605",
    "requested_target": "sim-trading",
    "signal": 1,
    "signal_strength": 0.82,
    "factors": [
        {
            "name": "momentum_score",
            "value": 0.71,
            "version": "v3",
            "updated_at": "2026-04-08T09:00:00+08:00",
        }
    ],
    "factor_version_hash": "fac-hash-001",
    "market_context": {
        "market_session": "day",
        "volatility_regime": "normal",
        "liquidity_regime": "stable",
        "headline_risk_level": "low",
    },
    "research_snapshot_id": "rs-001",
    "backtest_certificate_id": "bc-001",
    "submitted_at": "2026-04-08T09:00:00+08:00",
}


# ── PublishGate 测试 ──────────────────────────────────────────────────────────

def test_gate_eligible_sim_trading(monkeypatch, tmp_path):
    """满足所有条件，sim-trading 应通过门禁。"""
    pkg = _make_pkg()
    state_file = tmp_path / "eligible.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is True
    assert len(result.reasons) == 0


def test_gate_revalidates_persisted_eligibility(monkeypatch, tmp_path):
    pkg = _make_pkg()
    state_file = tmp_path / "decision-state.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is True
    assert len(result.reasons) == 0


def test_gate_rejects_invalid_lifecycle_state(monkeypatch, tmp_path):
    pkg = _make_pkg(status=LifecycleStatus.imported)
    state_file = tmp_path / "invalid-lifecycle.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    result = PublishGate().check("S001", "sim-trading")
    assert result.eligible is False
    assert any("lifecycle_status=imported cannot enter publish flow" in reason for reason in result.reasons)


def test_gate_allows_pending_execution_retry(monkeypatch, tmp_path):
    pkg = _make_pkg(status=LifecycleStatus.pending_execution)
    state_file = tmp_path / "publish-retry.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    result = PublishGate().check("S001", "sim-trading")
    assert result.eligible is True
    assert len(result.reasons) == 0


@pytest.mark.parametrize(
    ("scenario", "config", "expected_reason"),
    [
        ("missing_backtest_cert", {"register_backtest": False}, "backtest certificate missing"),
        ("backtest_expired", {"backtest_expires_days": -1}, "backtest certificate expired"),
        ("backtest_id_mismatch", {"package_backtest_id": "bc-other"}, "backtest certificate id mismatch"),
        ("research_status_failed", {"research_status": "failed"}, "research snapshot status=failed"),
        ("research_expired", {"research_valid_days": -1}, "research snapshot expired"),
        ("research_id_mismatch", {"package_research_id": "rs-other"}, "research snapshot id mismatch"),
        ("factor_hash_mismatch", {"research_factor_hash": "fac-other"}, "research snapshot factor_version_hash mismatch"),
    ],
)
def test_gate_rejects_invalid_persisted_eligibility(monkeypatch, tmp_path, scenario, config, expected_reason):
    pkg = _make_pkg()
    state_file = tmp_path / f"{scenario}.json"
    _persist_strategy_state(state_file, pkg, **config)
    _patch_gate_dependencies(monkeypatch, state_file)

    result = PublishGate().check("S001", "sim-trading")
    assert result.eligible is False
    assert expected_reason in result.reasons


def test_gate_rejects_unknown_strategy(monkeypatch):
    repo = _make_repo()  # empty
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    monkeypatch.setattr("src.publish.gate.get_backtest_gate", lambda: mock.MagicMock())
    monkeypatch.setattr("src.publish.gate.get_research_gate", lambda: mock.MagicMock())
    gate = PublishGate()
    result = gate.check("GHOST", "sim-trading")
    assert result.eligible is False
    assert "not found" in result.reasons[0]


def test_gate_rejects_archived_strategy(monkeypatch, tmp_path):
    pkg = _make_pkg(status=LifecycleStatus.archived)
    state_file = tmp_path / "archived.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is False
    assert any("archived" in r for r in result.reasons)


def test_gate_rejects_misaligned_factor(monkeypatch, tmp_path):
    pkg = _make_pkg(factor_sync="mismatch")
    state_file = tmp_path / "misaligned.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is False
    assert any("mismatch" in r for r in result.reasons)


def test_gate_rejects_target_not_allowed(monkeypatch, tmp_path):
    pkg = _make_pkg()
    pkg.allowed_targets = []
    state_file = tmp_path / "target-not-allowed.json"
    _persist_strategy_state(state_file, pkg)
    _patch_gate_dependencies(monkeypatch, state_file)

    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is False
    assert any("allowed_targets" in r for r in result.reasons)


def test_gate_eligibility_primary_reason():
    e = PublishEligibility(
        eligible=False, strategy_id="S001", target="sim-trading",
        reasons=["reason A", "reason B"],
    )
    assert e.primary_reason == "reason A; reason B"

    e2 = PublishEligibility(eligible=True, strategy_id="S001", target="sim-trading", reasons=[])
    assert e2.primary_reason == "ok"


# ── SimTradingAdapter 测试 ────────────────────────────────────────────────────

def test_adapter_202_accepted_is_success(monkeypatch):
    import json, urllib.request

    class FakeResp:
        def getcode(self): return 202
        def read(self): return json.dumps({"status": "accepted"}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: FakeResp())

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is True
    assert result["status_code"] == 202


def test_adapter_404_fails(monkeypatch):
    import urllib.request

    def fake_urlopen(req, timeout=10):
        raise urllib.error.HTTPError(
            req.full_url,
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"detail":"not found"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is False
    assert result["status_code"] == 404
    assert result["response"]["detail"] == "not found"


def test_adapter_500_fails(monkeypatch):
    import urllib.request

    def fake_urlopen(req, timeout=10):
        raise urllib.error.HTTPError(
            req.full_url,
            500,
            "Internal Error",
            {},
            io.BytesIO(b'{"detail":"boom"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is False
    assert result["status_code"] == 500
    assert result["response"]["detail"] == "boom"


def test_adapter_connection_error(monkeypatch):
    import urllib.request

    def fake_urlopen(req, timeout=10):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is False
    assert result["status_code"] == 0


# ── PublishExecutor 测试 ──────────────────────────────────────────────────────

def _build_executor(pkg: StrategyPackage, adapter_success: bool, monkeypatch, tmp_path):
    state_file = tmp_path / f"{pkg.strategy_id}.json"
    _persist_strategy_state(state_file, pkg)
    repo = _patch_gate_dependencies(monkeypatch, state_file)
    monkeypatch.setattr("src.publish.executor.get_repository", lambda: repo)

    gate = PublishGate()
    adapter = mock.MagicMock(spec=SimTradingAdapter)
    adapter.publish.return_value = {
        "success": adapter_success, "status_code": 202 if adapter_success else 500,
        "response": {} if adapter_success else "error"
    }
    # disable notifier
    monkeypatch.setattr("src.publish.executor.get_dispatcher", lambda: mock.MagicMock())

    executor = PublishExecutor(gate=gate, adapter=adapter)
    executor._dispatcher = mock.MagicMock()
    return executor, repo


def test_executor_publish_success(monkeypatch, tmp_path):
    pkg = _make_pkg()
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch, tmp_path=tmp_path)
    result = executor.execute("S001", "sim-trading")
    assert result.status == PublishStatus.SUCCESS
    updated = repo.get("S001")
    assert updated.lifecycle_status == LifecycleStatus.in_production


def test_executor_publish_retry_from_pending_execution(monkeypatch, tmp_path):
    pkg = _make_pkg(status=LifecycleStatus.pending_execution)
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch, tmp_path=tmp_path)

    result = executor.execute("S001", "sim-trading")

    assert result.status == PublishStatus.SUCCESS
    updated = repo.get("S001")
    assert updated.lifecycle_status == LifecycleStatus.in_production


def test_executor_gate_rejected(monkeypatch, tmp_path):
    pkg = _make_pkg(factor_sync="mismatch")
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch, tmp_path=tmp_path)
    result = executor.execute("S001", "sim-trading")
    assert result.status == PublishStatus.GATE_REJECTED
    # executor notification was called
    executor._dispatcher.dispatch.assert_called()


def test_executor_adapter_failed(monkeypatch, tmp_path):
    pkg = _make_pkg()
    executor, repo = _build_executor(pkg, adapter_success=False, monkeypatch=monkeypatch, tmp_path=tmp_path)
    result = executor.execute("S001", "sim-trading")
    assert result.status == PublishStatus.ADAPTER_FAILED


def test_executor_strategy_not_found(monkeypatch, tmp_path):
    pkg = _make_pkg()
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch, tmp_path=tmp_path)
    result = executor.execute("NONEXISTENT", "sim-trading")
    assert result.status == PublishStatus.STRATEGY_NOT_FOUND


class _StubSignalGate:
    def __init__(self, eligibility: PublishEligibility) -> None:
        self._eligibility = eligibility

    def check(self, strategy_id: str, target: str = "sim-trading") -> PublishEligibility:
        return self._eligibility


@pytest.fixture
def client():
    return TestClient(create_app())


def test_signal_review_ready_for_publish(monkeypatch, client):
    monkeypatch.setattr(
        signal_route,
        "route",
        lambda strategy_id, backtest_certificate_id, research_snapshot_id: {
            "allowed": True,
            "reason": "all gate checks passed",
        },
    )
    monkeypatch.setattr(
        signal_route,
        "PublishGate",
        lambda: _StubSignalGate(
            PublishEligibility(True, "S001", "sim-trading", [])
        ),
    )

    response = client.post("/signals/review", json=_DECISION_REQUEST)

    assert response.status_code == 201
    data = response.json()
    assert data["action"] == "approve"
    assert data["eligibility_status"] == "eligible"
    assert data["publish_workflow_status"] == "ready_for_publish"
    assert data["publish_target"] == "sim-trading"


def test_signal_review_live_trading_locked_visible(monkeypatch, client):
    payload = dict(_DECISION_REQUEST)
    payload["requested_target"] = "live-trading"

    monkeypatch.setattr(
        signal_route,
        "route",
        lambda strategy_id, backtest_certificate_id, research_snapshot_id: {
            "allowed": True,
            "reason": "all gate checks passed",
        },
    )
    monkeypatch.setattr(
        signal_route,
        "PublishGate",
        lambda: _StubSignalGate(
            PublishEligibility(
                False,
                "S001",
                "live-trading",
                ["execution gate: live-trading gate locked"],
            )
        ),
    )

    response = client.post("/signals/review", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["action"] == "hold"
    assert data["eligibility_status"] == "locked_visible"
    assert data["publish_workflow_status"] == "locked_visible"
    assert data["publish_target"] == "live-trading"


def test_strategy_publish_route_success(monkeypatch, client):
    pkg = _make_pkg()
    repo = _make_repo(pkg)

    class _StubExecutor:
        def execute(self, strategy_id: str, target: str = "sim-trading") -> PublishResult:
            repo.update(strategy_id, {"lifecycle_status": LifecycleStatus.in_production, "publish_target": target})
            return PublishResult(
                status=PublishStatus.SUCCESS,
                strategy_id=strategy_id,
                target=target,
                message="published",
                adapter_response={"accepted": True},
            )

    monkeypatch.setattr(strategy_route, "get_repository", lambda: repo)
    monkeypatch.setattr(strategy_route, "PublishExecutor", lambda: _StubExecutor())

    response = client.post("/strategies/S001/publish", json={"target": "sim-trading"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["strategy"]["lifecycle_status"] == "published"


def test_strategy_publish_route_gate_rejected(monkeypatch, client):
    pkg = _make_pkg()
    repo = _make_repo(pkg)

    class _StubExecutor:
        def execute(self, strategy_id: str, target: str = "sim-trading") -> PublishResult:
            return PublishResult(
                status=PublishStatus.GATE_REJECTED,
                strategy_id=strategy_id,
                target=target,
                message="backtest certificate expired",
            )

    monkeypatch.setattr(strategy_route, "get_repository", lambda: repo)
    monkeypatch.setattr(strategy_route, "PublishExecutor", lambda: _StubExecutor())

    response = client.post("/strategies/S001/publish", json={"target": "sim-trading"})

    assert response.status_code == 409
    data = response.json()
    assert data["status"] == "gate_rejected"
    assert data["strategy"]["strategy_id"] == "S001"


def test_strategy_publish_route_adapter_failed(monkeypatch, client):
    pkg = _make_pkg()
    repo = _make_repo(pkg)

    class _StubExecutor:
        def execute(self, strategy_id: str, target: str = "sim-trading") -> PublishResult:
            repo.update(strategy_id, {"lifecycle_status": LifecycleStatus.pending_execution, "publish_target": target})
            return PublishResult(
                status=PublishStatus.ADAPTER_FAILED,
                strategy_id=strategy_id,
                target=target,
                message="Adapter failed",
                adapter_response={"status_code": 500},
            )

    monkeypatch.setattr(strategy_route, "get_repository", lambda: repo)
    monkeypatch.setattr(strategy_route, "PublishExecutor", lambda: _StubExecutor())

    response = client.post("/strategies/S001/publish", json={"target": "sim-trading"})

    assert response.status_code == 502
    data = response.json()
    assert data["status"] == "adapter_failed"
    assert data["strategy"]["lifecycle_status"] == "publish_pending"


def test_strategy_publish_route_strategy_not_found(monkeypatch, client):
    repo = _make_repo()

    class _StubExecutor:
        def execute(self, strategy_id: str, target: str = "sim-trading") -> PublishResult:
            return PublishResult(
                status=PublishStatus.STRATEGY_NOT_FOUND,
                strategy_id=strategy_id,
                target=target,
                message="Strategy missing",
            )

    monkeypatch.setattr(strategy_route, "get_repository", lambda: repo)
    monkeypatch.setattr(strategy_route, "PublishExecutor", lambda: _StubExecutor())

    response = client.post("/strategies/UNKNOWN/publish", json={"target": "sim-trading"})

    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "strategy_not_found"
    assert data["strategy"] is None
