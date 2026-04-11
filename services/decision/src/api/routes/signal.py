from __future__ import annotations

from collections import Counter
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ...model.router import route
from ...notifier.dispatcher import get_dispatcher
from ...publish.gate import PublishGate
from ...reporting.daily import get_daily_reporter

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


def _sorted_decisions() -> list[dict]:
    return sorted(
        _decisions.values(),
        key=lambda item: item.get("generated_at") or "",
        reverse=True,
    )


def _stage_counts(decisions: list[dict]) -> list[dict]:
    total = len(decisions)
    eligible = sum(1 for item in decisions if item.get("eligibility_status") == "eligible")
    blocked = sum(1 for item in decisions if item.get("eligibility_status") in {"blocked", "expired"})
    ready = sum(1 for item in decisions if item.get("publish_workflow_status") == "ready_for_publish")
    locked = sum(1 for item in decisions if item.get("publish_workflow_status") == "locked_visible")
    held = sum(1 for item in decisions if item.get("action") == "hold")
    return [
        {"key": "generated", "label": "已生成", "count": total},
        {"key": "eligible", "label": "资格通过", "count": eligible},
        {"key": "blocked", "label": "资格阻塞", "count": blocked},
        {"key": "ready_for_publish", "label": "待发布", "count": ready},
        {"key": "locked_visible", "label": "实盘锁定可见", "count": locked},
        {"key": "held", "label": "保持观望", "count": held},
    ]


@router.get("/overview")
def get_signal_overview() -> dict:
    decisions = _sorted_decisions()
    dispatcher_snapshot = get_dispatcher().runtime_snapshot(recent_limit=20)
    daily_snapshot = get_daily_reporter().runtime_snapshot(limit=7)

    total = len(decisions)
    ready = sum(1 for item in decisions if item.get("publish_workflow_status") == "ready_for_publish")
    approved = sum(1 for item in decisions if item.get("action") == "approve")
    blocked = sum(1 for item in decisions if item.get("eligibility_status") in {"blocked", "expired"})
    locked = sum(1 for item in decisions if item.get("publish_workflow_status") == "locked_visible")
    hold = sum(1 for item in decisions if item.get("action") == "hold")

    timeline = [
        {
            "decision_id": item.get("decision_id"),
            "generated_at": item.get("generated_at"),
            "strategy_id": item.get("strategy_id"),
            "symbol": item.get("symbol"),
            "action": item.get("action"),
            "eligibility_status": item.get("eligibility_status"),
            "publish_workflow_status": item.get("publish_workflow_status"),
            "summary": item.get("reasoning_summary"),
        }
        for item in decisions[:12]
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "total": total,
            "approved": approved,
            "hold": hold,
            "blocked": blocked,
            "ready_for_publish": ready,
            "locked_visible": locked,
        },
        "stage_counts": _stage_counts(decisions),
        "timeline": timeline,
        "recent_signals": decisions[:20],
        "notification_channels": dispatcher_snapshot["channels"],
        "recent_events": dispatcher_snapshot["recent_events"],
        "dispatcher_state": dispatcher_snapshot["dispatcher_state"],
        "daily_report": daily_snapshot,
        "empty_states": {
            "signals": total == 0,
            "events": len(dispatcher_snapshot["recent_events"]) == 0,
            "daily_history": not daily_snapshot["has_sent_history"],
        },
    }


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
        "requested_target": req.requested_target,
        "symbol": req.symbol,
        "requested_signal": req.signal,
        "requested_signal_strength": req.signal_strength,
        "factor_count": len(req.factors),
        "factor_names": [factor.name for factor in req.factors],
        "market_context": req.market_context.model_dump(),
        "action": action,
        "confidence": confidence,
        "layer": layer,
        "model_profile": model_profile,
        "eligibility_status": eligibility_status,
        "publish_target": req.requested_target,
        "publish_gate_eligible": publish_result.eligible,
        "publish_workflow_status": publish_workflow_status,
        "gate_reasons": reasons,
        "decision_stage": (
            "ready_for_publish"
            if publish_workflow_status == "ready_for_publish"
            else "locked_visible"
            if publish_workflow_status == "locked_visible"
            else eligibility_status
        ),
        "reasoning_summary": reasoning_summary,
        "notification_event_id": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _decisions[decision_id] = result
    return result


@router.get("")
def list_decisions() -> list[dict]:
    return _sorted_decisions()


@router.get("/{decision_id}")
def get_decision(decision_id: str) -> dict:
    result = _decisions.get(decision_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Decision {decision_id} not found")
    return result


@router.get("/dashboard/signals")
def dashboard_signals() -> list[dict]:
    """最近信号摘要（只读聚合，供临时看板使用）。"""
    return [
        {
            "strategy_id": item.get("strategy_id"),
            "signal": item.get("requested_signal"),
            "signal_strength": item.get("requested_signal_strength"),
            "timestamp": item.get("generated_at"),
        }
        for item in _sorted_decisions()[:50]
    ]


@router.get("/dashboard/notifications")
def dashboard_notifications() -> list[dict]:
    """最近通知列表（只读聚合，供临时看板使用）。"""
    return get_dispatcher().dashboard_notifications()


@router.get("/dashboard/reports")
def dashboard_reports() -> list[dict]:
    """最近日报摘要（只读聚合，供临时看板使用）。"""
    return get_daily_reporter().dashboard_reports()


# ---------------------------------------------------------------------------
# CA6 信号分发端点 (TASK-0059-D)
# 延迟 import shared.contracts 与 signal_dispatcher 以兼容服务内 PYTHONPATH
# ---------------------------------------------------------------------------

_signal_dispatcher = None


def _get_signal_dispatcher():
    global _signal_dispatcher
    if _signal_dispatcher is None:
        from ...core.signal_dispatcher import SignalDispatcher
        from ...core.settings import get_settings

        settings = get_settings()
        sim_url = getattr(settings, "sim_trading_url", "http://localhost:8101")
        _signal_dispatcher = SignalDispatcher(sim_trading_url=sim_url)
    return _signal_dispatcher


@router.post("/dispatch", status_code=status.HTTP_200_OK)
async def dispatch_signal(request: Request):
    """将决策信号分发到 sim-trading 服务。"""
    from shared.contracts.decision.signal_dispatch import SignalDispatchRequest

    body = await request.json()
    parsed = SignalDispatchRequest(**body)
    dispatcher = _get_signal_dispatcher()
    return await dispatcher.dispatch(parsed)


@router.get("/status/{signal_id}")
def get_signal_status(signal_id: str):
    """查询信号分发状态。"""
    dispatcher = _get_signal_dispatcher()
    result = dispatcher.get_status(signal_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal {signal_id} not found",
        )
    return result
