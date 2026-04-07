from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ...core.settings import get_settings
from ...model.router import route as model_route

router = APIRouter(prefix="/models", tags=["model"])


class ModelRouteRequest(BaseModel):
    strategy_id: str
    backtest_certificate_id: Optional[str] = None
    research_snapshot_id: Optional[str] = None


@router.get("/status")
def model_status() -> dict:
    settings = get_settings()
    return {
        "model_router_require_backtest_cert": settings.model_router_require_backtest_cert,
        "model_router_require_research_snapshot": settings.model_router_require_research_snapshot,
        "execution_gate_enabled": settings.execution_gate_enabled,
        "execution_gate_target": settings.execution_gate_target,
        "live_trading_gate_locked": settings.live_trading_gate_locked,
    }


@router.post("/route")
def trigger_model_route(req: ModelRouteRequest) -> dict:
    result = model_route(
        strategy_id=req.strategy_id,
        backtest_certificate_id=req.backtest_certificate_id,
        research_snapshot_id=req.research_snapshot_id,
    )
    return result
