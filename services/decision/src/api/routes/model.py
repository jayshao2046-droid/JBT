from __future__ import annotations

import os
from collections import Counter
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from pydantic import BaseModel

from ...core.settings import get_settings
from ...model.router import route as model_route
from ...notifier.dispatcher import get_dispatcher
from ...persistence.state_store import get_state_store
from ...strategy.repository import get_repository

router = APIRouter(prefix="/models", tags=["model"])


class ModelRouteRequest(BaseModel):
    strategy_id: str
    backtest_certificate_id: Optional[str] = None
    research_snapshot_id: Optional[str] = None


def _research_window_state() -> dict:
    settings = get_settings()
    tz = ZoneInfo(settings.research_timezone)
    now_local = datetime.now(tz)
    now_hm = now_local.strftime("%H:%M")
    is_open = settings.research_window_start <= now_hm <= settings.research_window_end
    return {
        "timezone": settings.research_timezone,
        "start": settings.research_window_start,
        "end": settings.research_window_end,
        "current_time": now_local.strftime("%Y-%m-%d %H:%M:%S"),
        "is_open": is_open,
        "rule": "当前决策端只展示研究窗口规则；未接入独立调度器视图。",
    }


@router.get("/runtime")
def runtime_snapshot() -> dict:
    settings = get_settings()
    strategies = get_repository().list_all()
    state_store = get_state_store()
    dispatcher_snapshot = get_dispatcher().runtime_snapshot(recent_limit=10)

    from .signal import _L1_MODEL_PROFILE, _L2_MODEL_PROFILE, _decisions

    factor_sync = Counter(item.factor_sync_status for item in strategies)
    router_eligible = 0
    router_blocked = 0
    for item in strategies:
        result = model_route(
            strategy_id=item.strategy_id,
            backtest_certificate_id=item.backtest_certificate_id or None,
            research_snapshot_id=item.research_snapshot_id or None,
        )
        if result["allowed"]:
            router_eligible += 1
        else:
            router_blocked += 1

    return {
        "generated_at": datetime.now(ZoneInfo(settings.research_timezone)).isoformat(),
        "runtime_status": {
            "health": "ok",
            "state_store_path": str(state_store.file_path),
            "state_store_exists": state_store.file_path.exists(),
            "strategies_total": len(strategies),
            "approvals_total": len(state_store.list_records("approvals")),
            "backtest_certs_total": len(state_store.list_records("backtest_certs")),
            "research_snapshots_total": len(state_store.list_records("research_snapshots")),
            "decision_records_total": len(_decisions),
            "dispatcher_state": dispatcher_snapshot["dispatcher_state"],
        },
        "execution_gate": {
            "enabled": settings.execution_gate_enabled,
            "target": settings.execution_gate_target,
            "live_trading_locked": settings.live_trading_gate_locked,
            "summary": "当前仅模拟交易为可执行目标；实盘入口保持锁定可见。",
        },
        "model_router": {
            "require_backtest_cert": settings.model_router_require_backtest_cert,
            "require_research_snapshot": settings.model_router_require_research_snapshot,
            "eligible_strategies": router_eligible,
            "blocked_strategies": router_blocked,
        },
        "local_models": [
            {
                "profile_id": _L1_MODEL_PROFILE["profile_id"],
                "model_name": _L1_MODEL_PROFILE["model_name"],
                "deployment_class": _L1_MODEL_PROFILE["deployment_class"],
                "route_role": _L1_MODEL_PROFILE["route_role"],
                "status": "configured",
                "source": "signal review runtime profile",
            },
            {
                "profile_id": _L2_MODEL_PROFILE["profile_id"],
                "model_name": _L2_MODEL_PROFILE["model_name"],
                "deployment_class": _L2_MODEL_PROFILE["deployment_class"],
                "route_role": _L2_MODEL_PROFILE["route_role"],
                "status": "configured",
                "source": "signal review runtime profile",
            },
        ],
        "online_models": [
            {
                "model_id": "online-default",
                "name": os.getenv("ONLINE_MODEL_DEFAULT", "qwen-plus"),
                "type": "online",
                "status": "configured",
            },
            {
                "model_id": "online-upgrade",
                "name": os.getenv("ONLINE_MODEL_UPGRADE", "qwen-max"),
                "type": "online",
                "status": "configured",
            },
            {
                "model_id": "online-backup",
                "name": os.getenv("ONLINE_MODEL_BACKUP", "deepseek-chat"),
                "type": "online",
                "status": "configured",
            },
            {
                "model_id": "online-dispute",
                "name": os.getenv("ONLINE_MODEL_DISPUTE", "deepseek-reasoner"),
                "type": "online",
                "status": "configured",
            },
        ],
        "factor_sync": {
            "aligned": factor_sync.get("aligned", 0),
            "mismatch": factor_sync.get("mismatch", 0),
            "unknown": factor_sync.get("unknown", 0),
            "note": "当前未接入因子贡献度热图与漂移面板，只返回真实同步状态统计。",
        },
        "research_window": _research_window_state(),
        "service_integrations": [
            {
                "name": "data_api",
                "status": "configured",
                "url": settings.data_service_url,
                "timeout_seconds": settings.data_service_timeout,
                "note": "研究因子通过 data API 的 bars 接口生成。",
            },
            {
                "name": "backtest_service",
                "status": "not_used",
                "url": settings.backtest_service_url,
                "timeout_seconds": None,
                "note": "当前决策端不直接连接 backtest 服务。",
            },
        ],
    }


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


@router.get("/dashboard")
def dashboard_models() -> list[dict]:
    """模型注册表摘要（只读聚合，供临时看板使用）。"""
    from .signal import _L1_MODEL_PROFILE, _L2_MODEL_PROFILE

    now_iso = datetime.now(ZoneInfo(get_settings().research_timezone)).isoformat()
    return [
        {
            "model_id": _L1_MODEL_PROFILE["profile_id"],
            "name": _L1_MODEL_PROFILE["model_name"],
            "type": _L1_MODEL_PROFILE["deployment_class"],
            "status": "configured",
            "loaded_at": now_iso,
        },
        {
            "model_id": _L2_MODEL_PROFILE["profile_id"],
            "name": _L2_MODEL_PROFILE["model_name"],
            "type": _L2_MODEL_PROFILE["deployment_class"],
            "status": "configured",
            "loaded_at": now_iso,
        },
    ]
