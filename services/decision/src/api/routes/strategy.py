from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...publish.executor import PublishExecutor, PublishStatus
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


def _publish_response(strategy_id: str, status_name: str, message: str, target: str, adapter_response: dict) -> dict:
    latest_snapshot = get_repository().get(strategy_id)
    return {
        "status": status_name,
        "message": message,
        "target": target,
        "strategy": latest_snapshot.to_contract_dict() if latest_snapshot is not None else None,
        "adapter_response": adapter_response,
    }


@router.get("")
def list_strategies() -> list[dict]:
    repo = get_repository()
    return [p.to_contract_dict() for p in repo.list_all()]


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
