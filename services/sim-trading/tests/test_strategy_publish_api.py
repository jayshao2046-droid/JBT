from copy import deepcopy

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

_BASE_PAYLOAD = {
    "strategy_id": "S001",
    "strategy_version": "1.0",
    "package_hash": "pkg-hash-001",
    "publish_target": "sim-trading",
    "allowed_targets": ["sim-trading"],
    "lifecycle_status": "publish_pending",
    "published_at": "2026-04-08T09:00:00+08:00",
    "live_visibility_mode": "locked_visible",
}


def _payload(**overrides):
    payload = deepcopy(_BASE_PAYLOAD)
    payload.update(overrides)
    return payload


def test_strategy_publish_accepts_valid_package():
    response = client.post("/api/v1/strategy/publish", json=_payload())

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] is True
    assert data["target"] == "sim-trading"
    assert data["strategy_id"] == "S001"
    assert data["strategy_version"] == "1.0"
    assert data["package_hash"] == "pkg-hash-001"
    assert data["message"] == "strategy package accepted"
    assert data["received_at"].endswith("Z")


def test_strategy_publish_rejects_mismatched_publish_target():
    response = client.post(
        "/api/v1/strategy/publish",
        json=_payload(publish_target="live-trading"),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "publish_target must be sim-trading"}


def test_strategy_publish_rejects_missing_allowed_target():
    response = client.post(
        "/api/v1/strategy/publish",
        json=_payload(allowed_targets=["live-trading"]),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "allowed_targets must include sim-trading"}


def test_strategy_publish_rejects_invalid_lifecycle_status():
    response = client.post(
        "/api/v1/strategy/publish",
        json=_payload(lifecycle_status="published"),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "lifecycle_status must be publish_pending"}


def test_strategy_publish_rejects_invalid_visibility_mode():
    response = client.post(
        "/api/v1/strategy/publish",
        json=_payload(live_visibility_mode="public"),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "live_visibility_mode must be locked_visible"}


def test_strategy_publish_requires_contract_fields():
    payload = _payload()
    payload.pop("package_hash")

    response = client.post("/api/v1/strategy/publish", json=payload)

    assert response.status_code == 422


def test_strategy_publish_requires_valid_published_at():
    response = client.post(
        "/api/v1/strategy/publish",
        json=_payload(published_at="not-a-timestamp"),
    )

    assert response.status_code == 422