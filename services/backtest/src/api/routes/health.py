from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

if __package__:
    from ...core.settings import get_settings
else:
    from core.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mode: str
    asset_type: str
    risk_config_source: str


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version="0.1.0",
        mode=settings.backtest_mode,
        asset_type="futures",
        risk_config_source="yaml",
    )