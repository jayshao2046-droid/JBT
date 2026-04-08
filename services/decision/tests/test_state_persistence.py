import json

from src.api.routes import approval as approval_mod
from src.api.routes.approval import ApprovalCompleteRequest, ApprovalSubmitRequest
from src.persistence.state_store import FileStateStore
from src.strategy.repository import StrategyPackage, StrategyRepository


def _make_strategy(strategy_id: str = "persist-strategy-001") -> StrategyPackage:
    return StrategyPackage(
        strategy_id=strategy_id,
        strategy_name="Persistent Strategy",
        strategy_version="2026.04.08",
        template_id="trend-template-v1",
        package_hash="pkg-hash-001",
        factor_version_hash="factor-hash-001",
        factor_sync_status="aligned",
        research_snapshot_id="rs-001",
        backtest_certificate_id="bc-001",
        risk_profile_hash="risk-001",
        config_snapshot_ref="cfg-001",
        allowed_targets=["sim-trading"],
    )


def test_strategy_and_approval_share_same_file_state_store(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "decision-state.json"
    store = FileStateStore(state_file)
    repo = StrategyRepository(state_store=store)
    pkg = _make_strategy()

    repo.create(pkg)
    monkeypatch.setattr(approval_mod, "get_state_store", lambda: store)
    approval = approval_mod.submit_approval(
        ApprovalSubmitRequest(
            strategy_id=pkg.strategy_id,
            target="sim-trading",
            requester="tester",
            notes="persist me",
        )
    )

    raw_state = json.loads(state_file.read_text(encoding="utf-8"))
    assert raw_state["version"] == 1
    assert raw_state["strategies"][pkg.strategy_id]["strategy_name"] == pkg.strategy_name
    assert raw_state["approvals"][approval["approval_id"]]["strategy_id"] == pkg.strategy_id

    restarted_repo = StrategyRepository(state_store=FileStateStore(state_file))
    restored_pkg = restarted_repo.get(pkg.strategy_id)
    assert restored_pkg is not None
    assert restored_pkg.strategy_name == pkg.strategy_name

    monkeypatch.setattr(approval_mod, "get_state_store", lambda: FileStateStore(state_file))
    restored_approval = approval_mod.get_approval(approval["approval_id"])
    assert restored_approval["approval_status"] == "pending"
    assert restored_approval["notes"] == "persist me"


def test_completed_approval_survives_restart(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "decision-state.json"
    first_store = FileStateStore(state_file)

    monkeypatch.setattr(approval_mod, "get_state_store", lambda: first_store)
    submitted = approval_mod.submit_approval(
        ApprovalSubmitRequest(
            strategy_id="persist-strategy-002",
            target="sim-trading",
            requester="tester",
        )
    )

    restarted_store = FileStateStore(state_file)
    monkeypatch.setattr(approval_mod, "get_state_store", lambda: restarted_store)
    completed = approval_mod.complete_approval(
        submitted["approval_id"],
        ApprovalCompleteRequest(result="approve", notes="looks good"),
    )

    assert completed["approval_status"] == "completed"
    assert completed["result"] == "approve"
    assert completed["completed_at"] is not None

    final_store = FileStateStore(state_file)
    monkeypatch.setattr(approval_mod, "get_state_store", lambda: final_store)
    restored = approval_mod.get_approval(submitted["approval_id"])
    assert restored["approval_status"] == "completed"
    assert restored["result"] == "approve"
    assert restored["notes"] == "looks good"
    assert restored["completed_at"] is not None