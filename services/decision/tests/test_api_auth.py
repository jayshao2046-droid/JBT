"""DECISION_API_KEY authentication tests."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.decision.src.api.app import create_app


def _make_client(monkeypatch) -> TestClient:
    return TestClient(create_app())


def test_no_key_allows_access(monkeypatch) -> None:
    """DECISION_API_KEY 为空时所有端点可访问"""
    monkeypatch.setattr("services.decision.src.api.app._DECISION_API_KEY", "")
    client = _make_client(monkeypatch)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_key_blocks_unauthenticated(monkeypatch) -> None:
    """设置 API Key 后，无 Key 访问业务端点返回 403"""
    monkeypatch.setattr("services.decision.src.api.app._DECISION_API_KEY", "secret-123")
    client = _make_client(monkeypatch)
    resp = client.get("/strategies")
    assert resp.status_code == 403


def test_key_allows_authenticated(monkeypatch) -> None:
    """正确 API Key 可正常访问"""
    monkeypatch.setattr("services.decision.src.api.app._DECISION_API_KEY", "secret-123")
    client = _make_client(monkeypatch)
    resp = client.get("/strategies", headers={"X-API-Key": "secret-123"})
    assert resp.status_code == 200


def test_health_always_accessible(monkeypatch) -> None:
    """即使设置 API Key，/health 始终可访问"""
    monkeypatch.setattr("services.decision.src.api.app._DECISION_API_KEY", "secret-123")
    client = _make_client(monkeypatch)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_wrong_key_rejected(monkeypatch) -> None:
    """错误的 API Key 返回 403"""
    monkeypatch.setattr("services.decision.src.api.app._DECISION_API_KEY", "correct-key")
    client = _make_client(monkeypatch)
    resp = client.get("/strategies", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403
