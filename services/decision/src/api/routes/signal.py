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
from ...persistence.state_store import get_state_store

router = APIRouter(prefix="/signals", tags=["signal"])

_L1_MODEL_PROFILE = {
    "profile_id": "local-l1-phi4-reasoning",
    "model_name": "phi4-reasoning:14b",
    "deployment_class": "local",
    "route_role": "L1_gate_review",
}

_L2_MODEL_PROFILE = {
    "profile_id": "local-l2-phi4-reasoning",
    "model_name": "phi4-reasoning:14b",
    "deployment_class": "local",
    "route_role": "L2_deep_review",
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
    """从 state_store 读取所有决策记录并按时间排序。"""
    store = get_state_store()
    state = store.read_state()
    decisions = state.get("decisions", {})
    return sorted(
        decisions.values(),
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
async def review_signal(req: DecisionRequest) -> dict:
    """信号审查端点：资格门禁 + phi4 L1/L2 门控 + 发布流程判断。

    TASK-0112 Batch A: 接入真实 phi4-reasoning:14b L1/L2 门控。
    """
    decision_id = f"dd-{uuid.uuid4().hex[:12]}"

    # 前置资格门禁（model_router + PublishGate）
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

    # live-trading 锁定可见路径（不进入 LLM 审查）
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

    # 资格门禁阻塞路径（不进入 LLM 审查）
    elif not router_result["allowed"] or not publish_result.eligible:
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

    # signal=0 观望路径（不进入 LLM 审查）
    elif req.signal == 0:
        action = "hold"
        confidence = 0.0
        layer = "L1_rules"
        model_profile = dict(_L1_MODEL_PROFILE)
        eligibility_status = "eligible"
        publish_workflow_status = "none"
        reasoning_summary = "研究快照、回测证明与发布门禁均通过，但当前信号为 0，保持观望，不进入发布流程。"

    # 进入真实 LLM 门控审查路径
    else:
        from ...llm.gate_reviewer import GateReviewer
        from ...llm.context_loader import get_l1_context, get_l2_context

        gate_reviewer = GateReviewer()

        # L1 快审
        l1_context, l1_missing = await get_l1_context(req.symbol)
        l1_result = await gate_reviewer.l1_quick_review(
            strategy_id=req.strategy_id,
            symbol=req.symbol,
            signal=req.signal,
            signal_strength=req.signal_strength,
            factors=[f.model_dump() for f in req.factors],
            context=l1_context,
            missing_sources=l1_missing if l1_missing else None,
        )

        # L1 拒绝路径
        if not l1_result.get("pass", False):
            action = "hold"
            confidence = l1_result.get("confidence", 0.0)
            layer = "L1_gate_review"
            model_profile = dict(_L1_MODEL_PROFILE)
            eligibility_status = "eligible"
            publish_workflow_status = "none"
            reasoning_summary = f"L1 快审未通过: {l1_result.get('reasoning', 'unknown')}"
            if l1_result.get("degraded"):
                reasoning_summary += " [数据降级模式]"

        # L1 通过 → L2 深审
        else:
            l2_context, l2_missing = await get_l2_context(req.symbol)
            l2_result = await gate_reviewer.l2_deep_review(
                strategy_id=req.strategy_id,
                symbol=req.symbol,
                signal=req.signal,
                signal_strength=req.signal_strength,
                factors=[f.model_dump() for f in req.factors],
                market_context=req.market_context.model_dump(),
                l1_result=l1_result,
                context=l2_context,
                missing_sources=l2_missing if l2_missing else None,
            )

            # L2 批准 → 检查是否需要 L3 在线确认
            if l2_result.get("approve", False):
                from ...llm.online_confirmer import OnlineConfirmer

                online_confirmer = OnlineConfirmer()

                # 判断是否触发 L3
                should_trigger = online_confirmer.should_trigger_l3(
                    signal_strength=req.signal_strength,
                    l1_confidence=l1_result.get("confidence", 0.0),
                    l2_confidence=l2_result.get("confidence", 0.0),
                    risk_assessment=l2_result.get("risk_assessment", "unknown"),
                )

                if should_trigger:
                    # 调用 L3 在线确认
                    decision_context = {
                        "strategy_id": req.strategy_id,
                        "symbol": req.symbol,
                        "signal": req.signal,
                        "signal_strength": req.signal_strength,
                        "l1_result": l1_result,
                        "l2_result": l2_result,
                    }
                    l3_result = await online_confirmer.confirm(decision_context)

                    # L3 确认通过
                    if l3_result.get("confirmed", False):
                        action = "approve"
                        confidence = l2_result.get("confidence", 0.0)
                        layer = "L3_online_confirm"
                        model_profile = {
                            "profile_id": "online-l3-confirm",
                            "model_name": l3_result.get("model_used", "online"),
                            "deployment_class": "online",
                            "route_role": "L3_online_confirm",
                        }
                        eligibility_status = "eligible"
                        publish_workflow_status = "ready_for_publish"
                        reasoning_summary = f"L3 在线确认通过: {l3_result.get('reasoning', 'confirmed')}"
                        if l3_result.get("degraded"):
                            reasoning_summary += " [L3 降级为 L2]"

                    # L3 拒绝
                    else:
                        action = "hold"
                        confidence = l2_result.get("confidence", 0.0)
                        layer = "L3_online_reject" if not l3_result.get("degraded") else "L2_local_review_l3_degraded"
                        model_profile = {
                            "profile_id": "online-l3-reject",
                            "model_name": l3_result.get("model_used", "online"),
                            "deployment_class": "online",
                            "route_role": "L3_online_reject",
                        }
                        eligibility_status = "eligible"
                        publish_workflow_status = "none"
                        reasoning_summary = f"L3 在线确认未通过: {l3_result.get('reasoning', 'rejected')}"
                        if l3_result.get("degraded"):
                            reasoning_summary += " [L3 降级为 L2]"

                else:
                    # 不触发 L3，直接采用 L2 结论
                    action = "approve"
                    confidence = l2_result.get("confidence", 0.0)
                    layer = "L2_deep_review"
                    model_profile = dict(_L2_MODEL_PROFILE)
                    eligibility_status = "eligible"
                    publish_workflow_status = "ready_for_publish"
                    reasoning_summary = f"L1/L2 门控通过（未触发 L3）: {l2_result.get('reasoning', 'approved')}"
                    if l2_result.get("degraded"):
                        reasoning_summary += " [数据降级模式]"

            # L2 拒绝路径
            else:
                action = "hold"
                confidence = l2_result.get("confidence", 0.0)
                layer = "L2_deep_review"
                model_profile = dict(_L2_MODEL_PROFILE)
                eligibility_status = "eligible"
                publish_workflow_status = "none"
                reasoning_summary = f"L2 深审未通过: {l2_result.get('reasoning', 'rejected')}"
                if l2_result.get("degraded"):
                    reasoning_summary += " [数据降级模式]"

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

    # 写入 state_store
    store = get_state_store()
    decisions = store.get("decisions", {})
    decisions[decision_id] = result
    store.set("decisions", decisions)

    return result


@router.get("")
def list_decisions() -> list[dict]:
    return _sorted_decisions()


@router.get("/{decision_id}")
def get_decision(decision_id: str) -> dict:
    store = get_state_store()
    decisions = store.get("decisions", {})
    result = decisions.get(decision_id)
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
