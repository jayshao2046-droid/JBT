from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...core.settings import get_settings
from ...gating.backtest_gate import get_backtest_gate
from ...gating.research_gate import get_research_gate
from ...persistence.state_store import get_state_store
from ...publish.executor import PublishExecutor, PublishStatus
from ...publish.gate import PublishGate
from ...strategy.repository import get_repository, StrategyPackage
from ...strategy.lifecycle import LifecycleStatus, to_contract_state

router = APIRouter(prefix="/strategies", tags=["strategy"])


class StrategyCreateRequest(BaseModel):
    strategy_id: str
    strategy_name: str
    strategy_version: str
    template_id: str
    package_hash: str
    factor_version_hash: str
    factor_sync_status: str
    research_snapshot_id: str
    backtest_certificate_id: str
    risk_profile_hash: str
    config_snapshot_ref: str
    allowed_targets: list[str]
    publish_target: Optional[str] = None
    live_visibility_mode: str = "locked_visible"
    reserved_at: Optional[str] = None
    published_at: Optional[str] = None
    retired_at: Optional[str] = None


class StrategyPublishRequest(BaseModel):
    target: str = "sim-trading"


def _localize_reason(reason: str) -> str:
    if reason == "backtest certificate missing":
        return "回测证书未接入"
    if reason == "backtest certificate expired":
        return "回测证书已过期"
    if reason == "backtest certificate id mismatch":
        return "回测证书与策略登记不一致"
    if reason.startswith("backtest certificate status="):
        return f"回测证书状态异常: {reason.split('=', 1)[1]}"
    if reason == "backtest certificate factor_version_hash mismatch":
        return "回测证书与策略因子版本不一致"
    if reason == "research snapshot missing":
        return "研究快照未接入"
    if reason == "research snapshot expired":
        return "研究快照已过期"
    if reason == "research snapshot id mismatch":
        return "研究快照与策略登记不一致"
    if reason.startswith("research snapshot status="):
        return f"研究快照状态异常: {reason.split('=', 1)[1]}"
    if reason == "research snapshot factor_version_hash mismatch":
        return "研究快照与策略因子版本不一致"
    if reason == "eligibility factor_version_hash mismatch":
        return "研究与回测资格的因子版本不一致"
    if reason.startswith("factor_sync_status="):
        return "因子同步状态未对齐"
    if reason.startswith("target "):
        return "策略未开放当前发布目标"
    if reason.startswith("execution gate:"):
        suffix = reason.split(":", 1)[1].strip()
        if suffix == "live-trading gate locked":
            return "实盘门禁锁定"
        if suffix == "execution gate disabled":
            return "执行门禁已关闭"
        return f"执行门禁阻塞: {suffix}"
    if reason.startswith("lifecycle_status="):
        return "生命周期尚未进入可发布阶段"
    if reason.startswith("strategy ") and reason.endswith(" not found"):
        return "策略不存在"
    return reason


def _approval_groups() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for approval in get_state_store().list_records("approvals"):
        strategy_id = approval.get("strategy_id")
        if strategy_id:
            grouped[str(strategy_id)].append(approval)

    for items in grouped.values():
        items.sort(key=lambda item: item.get("submitted_at") or "", reverse=True)
    return grouped


def _serialize_strategy(pkg: StrategyPackage, approvals_by_strategy: dict[str, list[dict[str, Any]]], target: str) -> dict:
    backtest_cert = get_backtest_gate().get_cert(pkg.strategy_id)
    research_snapshot = get_research_gate().get_snapshot(pkg.strategy_id)
    publish_readiness = PublishGate().check(pkg.strategy_id, target)
    approvals = approvals_by_strategy.get(pkg.strategy_id, [])
    pending_approvals = sum(1 for item in approvals if item.get("approval_status") == "pending")
    reasons = [_localize_reason(reason) for reason in publish_readiness.reasons]

    contract = pkg.to_contract_dict()
    contract.update(
        {
            "backtest_cert_id": backtest_cert.certificate_id if backtest_cert is not None else None,
            "backtest_cert_status": backtest_cert.review_status if backtest_cert is not None else "missing",
            "backtest_cert_expires_at": backtest_cert.expires_at.isoformat() if backtest_cert is not None else None,
            "research_snapshot_status": research_snapshot.research_status if research_snapshot is not None else "missing",
            "research_snapshot_valid_until": research_snapshot.valid_until.isoformat() if research_snapshot is not None else None,
            "pending_approvals": pending_approvals,
            "latest_approval": approvals[0] if approvals else None,
            "publish_readiness": {
                "target": target,
                "eligible": publish_readiness.eligible,
                "reasons": list(dict.fromkeys(reasons)),
            },
        }
    )
    return contract


def _build_strategy_overview() -> dict:
    settings = get_settings()
    target = settings.execution_gate_target
    state_store = get_state_store()
    approvals = state_store.list_records("approvals")
    approvals_by_strategy = _approval_groups()
    strategies = sorted(
        get_repository().list_all(),
        key=lambda item: item.updated_at,
        reverse=True,
    )
    strategy_rows = [_serialize_strategy(item, approvals_by_strategy, target) for item in strategies]

    lifecycle_counts = Counter(row["lifecycle_status"] for row in strategy_rows)
    blockers = Counter(
        reason
        for row in strategy_rows
        for reason in row["publish_readiness"]["reasons"]
    )

    pending_actions: list[dict[str, Any]] = []
    for row in strategy_rows:
        reasons = row["publish_readiness"]["reasons"]
        if row["publish_readiness"]["eligible"] and row["lifecycle_status"] != "published":
            pending_actions.append(
                {
                    "type": "ready",
                    "strategy_id": row["strategy_id"],
                    "strategy_name": row["strategy_name"],
                    "lifecycle_status": row["lifecycle_status"],
                    "detail": f"当前已满足 {target} 发布前置条件",
                    "updated_at": row["updated_at"],
                }
            )
        elif row["pending_approvals"]:
            pending_actions.append(
                {
                    "type": "approval",
                    "strategy_id": row["strategy_id"],
                    "strategy_name": row["strategy_name"],
                    "lifecycle_status": row["lifecycle_status"],
                    "detail": f"存在 {row['pending_approvals']} 条待处理审批",
                    "updated_at": row["updated_at"],
                }
            )
        elif reasons:
            pending_actions.append(
                {
                    "type": "blocked",
                    "strategy_id": row["strategy_id"],
                    "strategy_name": row["strategy_name"],
                    "lifecycle_status": row["lifecycle_status"],
                    "detail": reasons[0],
                    "updated_at": row["updated_at"],
                }
            )

    research_ready = sum(1 for row in strategy_rows if row["research_snapshot_status"] == "completed")
    backtest_ready = sum(1 for row in strategy_rows if row["backtest_cert_status"] == "approved")
    factor_aligned = sum(1 for row in strategy_rows if row["factor_sync_status"] == "aligned")
    publish_ready = sum(
        1
        for row in strategy_rows
        if row["publish_readiness"]["eligible"] and row["lifecycle_status"] != "published"
    )
    published = sum(1 for row in strategy_rows if row["lifecycle_status"] == "published")
    approval_pending = sum(1 for item in approvals if item.get("approval_status") == "pending")
    live_locked = sum(
        1
        for row in strategy_rows
        if "live-trading" in (row.get("allowed_targets") or []) and settings.live_trading_gate_locked
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_store": {
            "path": str(state_store.file_path),
            "exists": state_store.file_path.exists(),
        },
        "runtime": {
            "strategy_count": len(strategy_rows),
            "approval_count": len(approvals),
            "execution_target": target,
            "live_trading_gate_locked": settings.live_trading_gate_locked,
        },
        "kpis": {
            "total": len(strategy_rows),
            "publish_ready": publish_ready,
            "published": published,
            "research_ready": research_ready,
            "backtest_ready": backtest_ready,
            "factor_aligned": factor_aligned,
            "pending_approvals": approval_pending,
        },
        "lifecycle_counts": [
            {"key": key, "label": key, "count": count}
            for key, count in sorted(lifecycle_counts.items())
        ],
        "pipeline": [
            {"key": "strategies", "label": "策略登记", "count": len(strategy_rows)},
            {"key": "factor_aligned", "label": "因子对齐", "count": factor_aligned},
            {"key": "research_ready", "label": "研究通过", "count": research_ready},
            {"key": "backtest_ready", "label": "回测通过", "count": backtest_ready},
            {"key": "approval_pending", "label": "审批待处理", "count": approval_pending},
            {"key": "publish_ready", "label": "可发布到模拟交易", "count": publish_ready},
            {"key": "published", "label": "已发布", "count": published},
        ],
        "blockers": [
            {
                "key": label,
                "label": label,
                "count": count,
                "severity": "warning" if "锁定" in label else "alert",
            }
            for label, count in blockers.most_common()
        ] + (
            [{"key": "live_locked", "label": "实盘目标继续锁定", "count": live_locked, "severity": "warning"}]
            if live_locked
            else []
        ),
        "pending_actions": pending_actions[:10],
        "research_readiness": {
            "research_ready": research_ready,
            "research_missing": len(strategy_rows) - research_ready,
            "backtest_ready": backtest_ready,
            "backtest_missing": len(strategy_rows) - backtest_ready,
            "factor_aligned": factor_aligned,
            "factor_mismatch": len(strategy_rows) - factor_aligned,
            "live_locked": live_locked,
        },
        "strategies": strategy_rows,
    }


def _publish_response(strategy_id: str, status_name: str, message: str, target: str, adapter_response: dict) -> dict:
    latest_snapshot = get_repository().get(strategy_id)
    return {
        "status": status_name,
        "message": message,
        "target": target,
        "strategy": latest_snapshot.to_contract_dict() if latest_snapshot is not None else None,
        "adapter_response": adapter_response,
    }


@router.get("/overview")
def get_strategy_overview() -> dict:
    return _build_strategy_overview()


@router.get("")
def list_strategies() -> list[dict]:
    repo = get_repository()
    return [p.to_contract_dict() for p in repo.list_all()]


@router.get("/dashboard")
def dashboard_strategies() -> list[dict]:
    """策略仓库摘要列表（只读聚合，供临时看板使用）。"""
    repo = get_repository()
    strategies = repo.list_all()
    return [
        {
            "strategy_id": pkg.strategy_id,
            "name": pkg.strategy_name,
            "status": to_contract_state(pkg.lifecycle_status),
            "symbols": pkg.allowed_targets,
            "last_updated": pkg.updated_at,
        }
        for pkg in sorted(strategies, key=lambda s: s.updated_at, reverse=True)
    ]


@router.get("/watchlist")
def get_watchlist() -> list[str]:
    """返回当前活跃策略的去重股票代码列表（供数据端 watchlist 采集使用）。

    TASK-0054-E CB5: 方案 A — watchlist 编入同批 Token。
    """
    repo = get_repository()
    symbols: set[str] = set()
    for pkg in repo.list_all():
        if pkg.lifecycle_status in (
            LifecycleStatus.backtest_confirmed,
            LifecycleStatus.pending_execution,
            LifecycleStatus.in_production,
        ):
            for target in pkg.allowed_targets:
                stripped = target.strip()
                if stripped:
                    symbols.add(stripped)
    return sorted(symbols)


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str) -> dict:
    repo = get_repository()
    pkg = repo.get(strategy_id)
    if pkg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found")
    return pkg.to_contract_dict()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_strategy(req: StrategyCreateRequest) -> dict:
    repo = get_repository()
    pkg = StrategyPackage(
        strategy_id=req.strategy_id,
        strategy_name=req.strategy_name,
        strategy_version=req.strategy_version,
        template_id=req.template_id,
        package_hash=req.package_hash,
        factor_version_hash=req.factor_version_hash,
        factor_sync_status=req.factor_sync_status,
        research_snapshot_id=req.research_snapshot_id,
        backtest_certificate_id=req.backtest_certificate_id,
        risk_profile_hash=req.risk_profile_hash,
        config_snapshot_ref=req.config_snapshot_ref,
        allowed_targets=req.allowed_targets,
        publish_target=req.publish_target,
        live_visibility_mode=req.live_visibility_mode,
        reserved_at=req.reserved_at,
        published_at=req.published_at,
        retired_at=req.retired_at,
    )
    repo.create(pkg)
    return pkg.to_contract_dict()


@router.get("/{strategy_id}/lifecycle")
def get_strategy_lifecycle(strategy_id: str) -> dict:
    repo = get_repository()
    pkg = repo.get(strategy_id)
    if pkg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found")
    return {
        "strategy_id": strategy_id,
        "lifecycle_status": to_contract_state(pkg.lifecycle_status),
        "updated_at": pkg.updated_at,
    }


@router.post("/{strategy_id}/publish")
def publish_strategy(strategy_id: str, req: StrategyPublishRequest) -> JSONResponse:
    result = PublishExecutor().execute(strategy_id, req.target)
    body = _publish_response(
        strategy_id=strategy_id,
        status_name=result.status.value,
        message=result.message,
        target=result.target,
        adapter_response=result.adapter_response,
    )

    if result.status == PublishStatus.SUCCESS:
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)
    if result.status == PublishStatus.STRATEGY_NOT_FOUND:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=body)
    if result.status == PublishStatus.GATE_REJECTED:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body)
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=body)
