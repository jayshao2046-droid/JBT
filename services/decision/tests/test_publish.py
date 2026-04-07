"""
test_publish.py — TASK-0021 G batch
单元测试：发布门禁、适配器、执行器
"""
import unittest.mock as mock
import urllib.error
import io
from typing import Optional

import pytest

from src.strategy.repository import StrategyPackage, StrategyRepository
from src.strategy.lifecycle import LifecycleStatus
from src.publish.gate import PublishGate, PublishEligibility
from src.publish.sim_adapter import SimTradingAdapter
from src.publish.executor import PublishExecutor, PublishStatus


# ── 测试固件 ──────────────────────────────────────────────────────────────────

def _make_pkg(strategy_id: str = "S001", factor_sync: str = "aligned", status: LifecycleStatus = LifecycleStatus.imported) -> StrategyPackage:
    pkg = StrategyPackage(
        strategy_id=strategy_id,
        strategy_name="Test Strategy",
        strategy_version="1.0",
        template_id="trend-v1",
        package_hash="pkg-hash-001",
        factor_version_hash="fac-hash-001",
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


# ── PublishGate 测试 ──────────────────────────────────────────────────────────

def test_gate_eligible_sim_trading(monkeypatch):
    """满足所有条件，sim-trading 应通过门禁。"""
    pkg = _make_pkg()
    repo = _make_repo(pkg)
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    # 设置环境变量让 execution_gate 通过
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    os.environ["LIVE_TRADING_GATE_LOCKED"] = "true"

    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is True
    assert len(result.reasons) == 0


def test_gate_rejects_unknown_strategy(monkeypatch):
    repo = _make_repo()  # empty
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    gate = PublishGate()
    result = gate.check("GHOST", "sim-trading")
    assert result.eligible is False
    assert "not found" in result.reasons[0]


def test_gate_rejects_archived_strategy(monkeypatch):
    pkg = _make_pkg(status=LifecycleStatus.archived)
    repo = _make_repo(pkg)
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is False
    assert any("archived" in r for r in result.reasons)


def test_gate_rejects_misaligned_factor(monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    pkg = _make_pkg(factor_sync="mismatch")
    repo = _make_repo(pkg)
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    gate = PublishGate()
    result = gate.check("S001", "sim-trading")
    assert result.eligible is False
    assert any("mismatch" in r for r in result.reasons)


def test_gate_rejects_target_not_allowed(monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    pkg = _make_pkg()
    pkg.allowed_targets = []
    repo = _make_repo(pkg)
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
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

def test_adapter_success(monkeypatch):
    import json, urllib.request

    class FakeResp:
        def getcode(self): return 200
        def read(self): return json.dumps({"status": "accepted"}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: FakeResp())

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is True
    assert result["status_code"] == 200


def test_adapter_404_degrades_to_success(monkeypatch):
    import urllib.request

    def fake_urlopen(req, timeout=10):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is True
    assert result["response"]["degraded"] is True


def test_adapter_500_fails(monkeypatch):
    import urllib.request

    def fake_urlopen(req, timeout=10):
        raise urllib.error.HTTPError(req.full_url, 500, "Internal Error", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    adapter = SimTradingAdapter()
    result = adapter.publish({"strategy_id": "S001"})
    assert result["success"] is False
    assert result["status_code"] == 500


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

def _build_executor(pkg: StrategyPackage, adapter_success: bool, monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    os.environ["NOTIFY_FEISHU_ENABLED"] = "false"
    os.environ["NOTIFY_EMAIL_ENABLED"] = "false"

    repo = _make_repo(pkg)
    monkeypatch.setattr("src.publish.gate.get_repository", lambda: repo)
    monkeypatch.setattr("src.publish.executor.get_repository", lambda: repo)

    gate = PublishGate()
    adapter = mock.MagicMock(spec=SimTradingAdapter)
    adapter.publish.return_value = {
        "success": adapter_success, "status_code": 200 if adapter_success else 500,
        "response": {} if adapter_success else "error"
    }
    # disable notifier
    monkeypatch.setattr("src.publish.executor.get_dispatcher", mock.MagicMock())

    executor = PublishExecutor(gate=gate, adapter=adapter)
    executor._dispatcher = mock.MagicMock()
    return executor, repo


def test_executor_publish_success(monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    pkg = _make_pkg()
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch)
    result = executor.execute("S001", "sim-trading")
    assert result.status == PublishStatus.SUCCESS
    updated = repo.get("S001")
    assert updated.lifecycle_status == LifecycleStatus.in_production


def test_executor_gate_rejected(monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    pkg = _make_pkg(factor_sync="mismatch")
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch)
    result = executor.execute("S001", "sim-trading")
    assert result.status == PublishStatus.GATE_REJECTED
    # executor notification was called
    executor._dispatcher.dispatch.assert_called()


def test_executor_adapter_failed(monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    pkg = _make_pkg()
    executor, repo = _build_executor(pkg, adapter_success=False, monkeypatch=monkeypatch)
    result = executor.execute("S001", "sim-trading")
    assert result.status == PublishStatus.ADAPTER_FAILED


def test_executor_strategy_not_found(monkeypatch):
    import os
    os.environ["EXECUTION_GATE_ENABLED"] = "true"
    pkg = _make_pkg()
    executor, repo = _build_executor(pkg, adapter_success=True, monkeypatch=monkeypatch)
    result = executor.execute("NONEXISTENT", "sim-trading")
    assert result.status == PublishStatus.STRATEGY_NOT_FOUND
