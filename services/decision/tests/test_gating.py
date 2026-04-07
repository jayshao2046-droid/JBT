from __future__ import annotations

from datetime import timedelta, timezone, datetime

import pytest

from src.gating.backtest_gate import BacktestGate, CertStatus
from src.gating.research_gate import ResearchGate


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
