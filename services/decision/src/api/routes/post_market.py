"""
盘后评估 API 路由 (CB7)
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ...research.post_market import PostMarketEvaluator

router = APIRouter(prefix="/api/v1/stock/post-market", tags=["post-market"])

# 全局单例
_evaluator = PostMarketEvaluator()


class EvaluateRequest(BaseModel):
    symbol: str
    daily_data: dict


class BatchEvaluateRequest(BaseModel):
    symbols_data: list[dict]


@router.post("/evaluate")
async def evaluate_single(req: EvaluateRequest):
    """评估单只股票"""
    return _evaluator.evaluate(req.symbol, req.daily_data)


@router.post("/batch")
async def batch_evaluate(req: BatchEvaluateRequest):
    """批量评估"""
    return _evaluator.batch_evaluate(req.symbols_data)


@router.get("/report")
async def get_report():
    """获取最近一次报告"""
    return _evaluator.get_report()
