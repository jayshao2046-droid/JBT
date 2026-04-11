"""股票手动审核路由 — TASK-0058 CG3

提供股票手动回测提交、结果查询、审核确认的 HTTP 端点。
遵循 A 股 T+1、涨跌停限制、禁止做空。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

if __package__:
    from ...backtest.stock_runner import StockRunner
else:
    from backtest.stock_runner import StockRunner

stock_approval_router = APIRouter(
    prefix="/api/v1/stock-approval", tags=["stock-approval"]
)

# 模块级单例
_stock_runner = StockRunner()


def get_stock_runner() -> StockRunner:
    """返回模块级 StockRunner 单例（便于测试替换）。"""
    return _stock_runner


# ── Request / Response models ────────────────────────────────────────


class StockSubmitRequest(BaseModel):
    strategy_id: str = Field(..., min_length=1, max_length=128)
    symbol: str = Field(..., min_length=6, max_length=6, description="6 位股票代码")
    start_date: str = Field(..., min_length=8, max_length=10, description="YYYY-MM-DD")
    end_date: str = Field(..., min_length=8, max_length=10, description="YYYY-MM-DD")
    params: Optional[dict[str, Any]] = None


class StockApproveRequest(BaseModel):
    approved: bool
    note: str = ""


class StockResultResponse(BaseModel):
    run_id: str
    strategy_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    metrics: dict[str, Any] = {}
    approved: Optional[bool] = None
    reviewer_note: str = ""
    asset_type: str = "stock"
    price_limit_hits: int = 0
    t1_violations: int = 0


# ── Endpoints ─────────────────────────────────────────────────────────


@stock_approval_router.post(
    "/submit",
    response_model=StockResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_stock_backtest(body: StockSubmitRequest) -> StockResultResponse:
    """提交一次股票手动回测。"""
    runner = get_stock_runner()
    result = runner.submit(
        strategy_id=body.strategy_id,
        symbol=body.symbol,
        start_date=body.start_date,
        end_date=body.end_date,
        params=body.params,
    )
    return StockResultResponse(**result.to_dict())


@stock_approval_router.get("/results", response_model=list[StockResultResponse])
def list_stock_results(
    strategy_id: Optional[str] = Query(None),
) -> list[StockResultResponse]:
    """列出股票手动回测结果（可选按 strategy_id 过滤）。"""
    runner = get_stock_runner()
    items = runner.list_results(strategy_id=strategy_id)
    return [StockResultResponse(**r.to_dict()) for r in items]


@stock_approval_router.get(
    "/results/{run_id}", response_model=StockResultResponse
)
def get_stock_result(run_id: str) -> StockResultResponse:
    """获取单个股票手动回测结果。"""
    runner = get_stock_runner()
    result = runner.get_result(run_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run_id not found: {run_id}",
        )
    return StockResultResponse(**result.to_dict())


@stock_approval_router.post(
    "/results/{run_id}/approve", response_model=StockResultResponse
)
def approve_stock_result(
    run_id: str, body: StockApproveRequest
) -> StockResultResponse:
    """审核确认/拒绝一次股票手动回测结果。"""
    runner = get_stock_runner()
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
    return StockResultResponse(**result.to_dict())
