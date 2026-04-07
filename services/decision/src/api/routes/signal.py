import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/signals", tags=["signal"])

_decisions: dict[str, dict] = {}


class FactorItem(BaseModel):
    name: str
    value: float
    version: str
    updated_at: str


class MarketContext(BaseModel):
    market_session: str
    volatility_regime: str
    liquidity_regime: str
    headline_risk_level: str


class DecisionRequest(BaseModel):
    request_id: str
    trace_id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    requested_target: str
    signal: int
    signal_strength: float
    factors: list[FactorItem]
    factor_version_hash: str
    market_context: MarketContext
    research_snapshot_id: str
    backtest_certificate_id: str
    submitted_at: str


@router.post("/review", status_code=status.HTTP_201_CREATED)
def review_signal(req: DecisionRequest) -> dict:
    decision_id = f"dd-{uuid.uuid4().hex[:12]}"
    result = {
        "decision_id": decision_id,
        "request_id": req.request_id,
        "trace_id": req.trace_id,
        "strategy_id": req.strategy_id,
        "action": "hold",
        "confidence": 0.0,
        "layer": "L1_rules",
        "model_profile": {
            "profile_id": "pending",
            "model_name": "pending",
            "deployment_class": "local",
            "route_role": "pending",
        },
        "eligibility_status": "manual_review",
        "publish_target": req.requested_target if req.requested_target == "sim-trading" else None,
        "publish_workflow_status": "none",
        "reasoning_summary": "Signal received, pending full gate evaluation.",
        "notification_event_id": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _decisions[decision_id] = result
    return result


@router.get("")
def list_decisions() -> list[dict]:
    return list(_decisions.values())


@router.get("/{decision_id}")
def get_decision(decision_id: str) -> dict:
    result = _decisions.get(decision_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Decision {decision_id} not found")
    return result
