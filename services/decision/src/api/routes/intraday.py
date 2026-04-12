"""
盘中跟踪 API 路由 (CB6)
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ...research.intraday_tracker import IntradayTracker

router = APIRouter(prefix="/api/v1/stock/intraday", tags=["intraday"])

# 全局单例
_tracker = IntradayTracker()


class UpdateRequest(BaseModel):
    symbol: str
    price: float
    volume: float
    ts: str | None = None


@router.get("/signals")
async def get_signals():
    """获取当前触发的信号"""
    return _tracker.get_signals()


@router.post("/update")
async def update_snapshot(req: UpdateRequest):
    """更新股票快照"""
    _tracker.update(req.symbol, req.price, req.volume, req.ts)
    return {"updated": True}


@router.get("/summary")
async def get_summary():
    """获取跟踪摘要"""
    return _tracker.get_summary()


@router.post("/clear")
async def clear_data():
    """清空当日数据"""
    _tracker.clear()
    return {"cleared": True}
