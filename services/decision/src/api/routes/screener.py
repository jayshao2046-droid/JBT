"""选股路由 — TASK-0062 CB3"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...research.stock_screener import StockScreener

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])

_screener = StockScreener()


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

class ScreenRequest(BaseModel):
    symbols: list[str]
    top_n: int = 20
    lookback_days: int = 20
    benchmark_symbol: Optional[str] = None


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.post("/run")
def run_screen(req: ScreenRequest):
    """执行选股（同步），返回 TOP-N 排名列表。"""
    result = _screener.screen(
        symbols=req.symbols,
        top_n=req.top_n,
        lookback_days=req.lookback_days,
        benchmark_symbol=req.benchmark_symbol,
    )
    return result.to_dict()


@router.get("/results")
def list_results():
    """列出选股历史。"""
    results = _screener.list_results()
    return [r.to_dict() for r in results]


@router.get("/results/{screen_id}")
def get_result(screen_id: str):
    """获取单个选股结果。"""
    result = _screener.get_result(screen_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"screen {screen_id} not found")
    return result.to_dict()
