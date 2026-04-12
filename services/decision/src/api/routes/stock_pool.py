"""
股票池管理 API 路由 (CB4)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...research.stock_pool import StockPool

router = APIRouter(prefix="/api/v1/stock/pool", tags=["stock-pool"])

# 全局单例
_pool = StockPool()


class AddSymbolRequest(BaseModel):
    symbol: str


class RotateRequest(BaseModel):
    to_add: list[str]
    to_remove: list[str]


@router.get("")
async def get_pool():
    """获取当前股票池"""
    return _pool.to_dict()


@router.post("")
async def add_symbol(req: AddSymbolRequest):
    """添加股票到池中"""
    added = _pool.add(req.symbol)
    return {
        "added": added,
        "pool_size": _pool.size()
    }


@router.delete("/{symbol}")
async def remove_symbol(symbol: str):
    """从池中移除股票"""
    removed = _pool.remove(symbol)
    return {
        "removed": removed,
        "pool_size": _pool.size()
    }


@router.post("/rotate")
async def rotate_pool(req: RotateRequest):
    """批量轮换股票池"""
    result = _pool.rotate(req.to_add, req.to_remove)
    return result
