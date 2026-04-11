"""人工审核确认路由 — TASK-0055 CG2

提供手动回测提交、结果查询、审核确认的 HTTP 端点。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

if __package__:
    from ...backtest.manual_runner import ManualRunner
else:
    from backtest.manual_runner import ManualRunner

approval_router = APIRouter(prefix="/api/v1/approval", tags=["approval"])

# 模块级单例
_runner = ManualRunner()


def get_runner() -> ManualRunner:
    """返回模块级 ManualRunner 单例（便于测试替换）。"""
    return _runner


# ── Request / Response models ────────────────────────────────────────


class SubmitRequest(BaseModel):
    strategy_id: str = Field(..., min_length=1, max_length=128)
    start_date: str = Field(..., min_length=8, max_length=10, description="YYYY-MM-DD")
    end_date: str = Field(..., min_length=8, max_length=10, description="YYYY-MM-DD")
    params: Optional[dict[str, Any]] = None


class ApproveRequest(BaseModel):
    approved: bool
    note: str = ""


class ManualResultResponse(BaseModel):
    run_id: str
    strategy_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    metrics: dict[str, Any] = {}
    approved: Optional[bool] = None
    reviewer_note: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────


@approval_router.post(
    "/submit",
    response_model=ManualResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_manual_backtest(body: SubmitRequest) -> ManualResultResponse:
    """提交一次手动回测。"""
    runner = get_runner()
    result = runner.submit(
        strategy_id=body.strategy_id,
        start_date=body.start_date,
        end_date=body.end_date,
        params=body.params,
    )
    return ManualResultResponse(**result.to_dict())


@approval_router.get("/results", response_model=list[ManualResultResponse])
def list_results(
    strategy_id: Optional[str] = Query(None),
) -> list[ManualResultResponse]:
    """列出手动回测结果（可选按 strategy_id 过滤）。"""
    runner = get_runner()
    items = runner.list_results(strategy_id=strategy_id)
    return [ManualResultResponse(**r.to_dict()) for r in items]


@approval_router.get("/results/{run_id}", response_model=ManualResultResponse)
def get_result(run_id: str) -> ManualResultResponse:
    """获取单个手动回测结果。"""
    runner = get_runner()
    result = runner.get_result(run_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run_id not found: {run_id}",
        )
    return ManualResultResponse(**result.to_dict())


@approval_router.post(
    "/results/{run_id}/approve", response_model=ManualResultResponse
)
def approve_result(run_id: str, body: ApproveRequest) -> ManualResultResponse:
    """审核确认/拒绝一次手动回测结果。"""
    runner = get_runner()
    try:
        result = runner.approve(
            run_id=run_id, approved=body.approved, note=body.note
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run_id not found: {run_id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    return ManualResultResponse(**result.to_dict())
