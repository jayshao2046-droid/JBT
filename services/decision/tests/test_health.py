import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import app


@pytest.mark.asyncio
async def test_health_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "decision"


@pytest.mark.asyncio
async def test_ready_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
