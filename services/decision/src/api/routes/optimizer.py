"""调优路由 — TASK-0061 CA4"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...research.trade_optimizer import TradeOptimizer

router = APIRouter(prefix="/api/v1/optimizer", tags=["optimizer"])

_optimizer = TradeOptimizer()


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    strategy_id: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: dict[str, list]
    objective: str = "sharpe"
    asset_type: str = "futures"


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.post("/run")
def run_optimization(req: OptimizeRequest):
    """启动调优（同步执行，返回完整结果）。"""
    result = _optimizer.optimize(
        strategy_id=req.strategy_id,
        symbol=req.symbol,
        start_date=req.start_date,
        end_date=req.end_date,
        param_grid=req.param_grid,
        objective=req.objective,
        asset_type=req.asset_type,
    )
    return result.to_dict()


@router.get("/results")
def list_results(strategy_id: Optional[str] = None):
    """列出调优历史。"""
    results = _optimizer.list_results(strategy_id=strategy_id)
    return [r.to_dict() for r in results]


@router.get("/results/{opt_id}")
def get_result(opt_id: str):
    """获取单个调优结果。"""
    result = _optimizer.get_result(opt_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"optimization {opt_id} not found")
    return result.to_dict()
