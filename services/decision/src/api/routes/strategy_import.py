"""
策略导入路由 — TASK-0051 C0-3
POST /strategy-import/import → 导入或验证策略定义。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...publish.strategy_importer import import_strategy, get_import_repository

router = APIRouter(prefix="/strategy-import", tags=["strategy-import"])


class StrategyImportRequest(BaseModel):
    name: str
    symbol: str
    exchange: str
    direction: str = "long"
    entry_rules: Dict[str, Any] = {}
    exit_rules: Dict[str, Any] = {}
    risk_params: Dict[str, Any] = {}
    source_type: str = "manual"
    content: str = ""


class StrategyImportResponse(BaseModel):
    strategy_id: Optional[str] = None
    status: str
    message: str
    validation_errors: List[str] = []
    strategy_data: Optional[Dict[str, Any]] = None


@router.post(
    "/import",
    response_model=StrategyImportResponse,
    status_code=status.HTTP_200_OK,
    summary="导入策略定义",
)
def strategy_import_endpoint(
    body: StrategyImportRequest,
    validate_only: bool = False,
) -> StrategyImportResponse:
    """
    导入或仅验证策略定义。

    - **validate_only=true**：仅校验，不保存
    - 正常导入：验证 → 生成 ID → 保存
    """
    data = body.model_dump()

    try:
        result = import_strategy(data, validate_only=validate_only)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略导入内部错误: {exc}",
        ) from exc

    if result["status"] == "validation_failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "strategy_id": result["strategy_id"],
                "status": result["status"],
                "message": result["message"],
                "validation_errors": result["validation_errors"],
            },
        )

    if result["status"] == "conflict":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "strategy_id": result["strategy_id"],
                "status": result["status"],
                "message": result["message"],
            },
        )

    if result["status"] == "imported":
        return StrategyImportResponse(
            strategy_id=result["strategy_id"],
            status=result["status"],
            message=result["message"],
            validation_errors=[],
            strategy_data=result["strategy_data"],
        )

    # validated (validate_only=true)
    return StrategyImportResponse(
        strategy_id=result["strategy_id"],
        status=result["status"],
        message=result["message"],
        validation_errors=[],
        strategy_data=result["strategy_data"],
    )
