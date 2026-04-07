import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app
from src.strategy.lifecycle import LifecycleStatus, transition, to_contract_state, _INTERNAL_TO_CONTRACT


@pytest.fixture
def app():
    return create_app()


_STRATEGY_PAYLOAD = {
    "strategy_id": "test-strategy-001",
    "strategy_name": "Test Strategy",
    "strategy_version": "2026.04.07",
    "template_id": "trend-template-v1",
    "package_hash": "pkg-test-001",
    "factor_version_hash": "fac-test-001",
    "factor_sync_status": "aligned",
    "research_snapshot_id": "rs-test-001",
    "backtest_certificate_id": "bc-test-001",
    "risk_profile_hash": "risk-test-001",
    "config_snapshot_ref": "cfg-test-001",
    "allowed_targets": ["sim-trading"],
    "live_visibility_mode": "locked_visible",
}


@pytest.mark.asyncio
async def test_create_strategy(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/strategies", json=_STRATEGY_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["strategy_id"] == _STRATEGY_PAYLOAD["strategy_id"]
    # API 响应使用契约规范值：imported → imported（与内部值相同）
    assert data["lifecycle_status"] == "imported"


@pytest.mark.asyncio
async def test_get_nonexistent_strategy(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/strategies/nonexistent-999")
    assert response.status_code == 404


def test_lifecycle_transition_valid() -> None:
    result = transition(LifecycleStatus.imported, LifecycleStatus.reserved)
    assert result == LifecycleStatus.reserved


def test_lifecycle_transition_invalid() -> None:
    with pytest.raises(ValueError):
        transition(LifecycleStatus.reserved, LifecycleStatus.in_production)


def test_to_contract_state_terminal_states() -> None:
    """终态映射：内部值与契约规范值不同，必须正确转换。"""
    assert to_contract_state(LifecycleStatus.pending_execution) == "publish_pending"
    assert to_contract_state(LifecycleStatus.in_production) == "published"
    assert to_contract_state(LifecycleStatus.archived) == "retired"


def test_to_contract_state_passthrough_states() -> None:
    """中间态与导入态透传：内部值与契约值相同。"""
    assert to_contract_state(LifecycleStatus.imported) == "imported"
    assert to_contract_state(LifecycleStatus.reserved) == "reserved"
    assert to_contract_state(LifecycleStatus.researching) == "researching"
    assert to_contract_state(LifecycleStatus.research_complete) == "research_complete"
    assert to_contract_state(LifecycleStatus.backtest_confirmed) == "backtest_confirmed"


def test_internal_to_contract_covers_all_statuses() -> None:
    """_INTERNAL_TO_CONTRACT 必须覆盖全部 8 个枚举值，不允许遗漏。"""
    for status in LifecycleStatus:
        assert status.value in _INTERNAL_TO_CONTRACT, (
            f"LifecycleStatus.{status.name} ({status.value!r}) 不在 _INTERNAL_TO_CONTRACT 中"
        )
