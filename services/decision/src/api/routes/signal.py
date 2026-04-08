import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...model.router import route
from ...publish.gate import PublishGate

router = APIRouter(prefix="/signals", tags=["signal"])

_decisions: dict[str, dict] = {}

_L1_MODEL_PROFILE = {
    "profile_id": "local-l1-qwen2.5-series",
    "model_name": "Qwen2.5",
    "deployment_class": "local",
    "route_role": "gate_review",
}

_L2_MODEL_PROFILE = {
    "profile_id": "local-primary-qwen3-14b",
    "model_name": "Qwen3 14B",
    "deployment_class": "local",
    "route_role": "primary_local_review",
}


def _dedupe_reasons(*groups: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for reason in group:
            if not reason or reason in seen:
                continue
            seen.add(reason)
            ordered.append(reason)
    return ordered


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _has_expired_reason(reasons: list[str]) -> bool:
    return any("expired" in reason for reason in reasons)


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
    router_result = route(
        strategy_id=req.strategy_id,
        backtest_certificate_id=req.backtest_certificate_id,
        research_snapshot_id=req.research_snapshot_id,
    )
    publish_result = PublishGate().check(req.strategy_id, req.requested_target)
    reasons = _dedupe_reasons(
        [] if router_result["allowed"] else [router_result["reason"]],
        publish_result.reasons,
    )

    if req.requested_target == "live-trading":
        action = "hold"
        confidence = 0.0
        layer = "L1_rules"
        model_profile = dict(_L1_MODEL_PROFILE)
        eligibility_status = "locked_visible"
        publish_workflow_status = "locked_visible"
        reasoning_summary = "当前发布目标为 live-trading，第一阶段仅锁定可见，不进入发布流程。"
        if reasons:
            reasoning_summary = f"{reasoning_summary} 详情: {'; '.join(reasons)}"
    elif router_result["allowed"] and publish_result.eligible and req.signal != 0:
        action = "approve"
        confidence = _clamp_confidence(req.signal_strength)
        layer = "L2_local_review"
        model_profile = dict(_L2_MODEL_PROFILE)
        eligibility_status = "eligible"
        publish_workflow_status = "ready_for_publish"
        reasoning_summary = "研究快照、回测证明与发布门禁均通过，当前允许进入模拟交易发布流程。"
    elif router_result["allowed"] and publish_result.eligible:
        action = "hold"
        confidence = 0.0
        layer = "L1_rules"
        model_profile = dict(_L1_MODEL_PROFILE)
        eligibility_status = "eligible"
        publish_workflow_status = "none"
        reasoning_summary = "研究快照、回测证明与发布门禁均通过，但当前信号为 0，保持观望，不进入发布流程。"
    else:
        action = "hold"
        confidence = 0.0 if req.signal == 0 else min(_clamp_confidence(req.signal_strength), 0.49)
        layer = "L1_rules"
        model_profile = dict(_L1_MODEL_PROFILE)
        eligibility_status = "expired" if _has_expired_reason(reasons) else "blocked"
        publish_workflow_status = "none"
        reasoning_summary = (
            "资格门禁未通过，当前暂不进入发布流程。"
            f" 详情: {'; '.join(reasons) if reasons else 'gate evaluation failed'}"
        )

    result = {
        "decision_id": decision_id,
        "request_id": req.request_id,
        "trace_id": req.trace_id,
        "strategy_id": req.strategy_id,
        "action": action,
        "confidence": confidence,
        "layer": layer,
        "model_profile": model_profile,
        "eligibility_status": eligibility_status,
        "publish_target": req.requested_target,
        "publish_workflow_status": publish_workflow_status,
        "reasoning_summary": reasoning_summary,
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
