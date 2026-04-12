"""本地 Sim 容灾 API 路由 — TASK-0076 CS1"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.research.local_sim_engine import LocalSimEngine


router = APIRouter(prefix="/local-sim", tags=["local-sim"])

# 全局引擎实例
_engine = LocalSimEngine()


class PlaceOrderRequest(BaseModel):
    """下单请求。"""

    symbol: str = Field(..., description="合约代码")
    direction: str = Field(..., description="方向（buy/sell）")
    quantity: int = Field(..., description="数量", gt=0)
    price: float = Field(..., description="价格", gt=0)


class PlaceOrderResponse(BaseModel):
    """下单响应。"""

    order_id: str
    symbol: str
    direction: str
    quantity: int
    price: float
    status: str
    created_at: str
    filled_at: str | None


class GetPositionsResponse(BaseModel):
    """持仓响应。"""

    positions: dict[str, float]
    capital: float


class BacktestRequest(BaseModel):
    """回测请求。"""

    strategy_config: dict = Field(..., description="策略配置")
    start_time: str = Field(..., description="开始时间（ISO 格式）")
    end_time: str = Field(..., description="结束时间（ISO 格式）")
    asset_type: str = Field("futures", description="资产类型（futures/stock）")
    initial_capital: float = Field(1_000_000, description="初始资金")
    symbols: list[str] | None = Field(None, description="合约列表")


@router.post("/order", response_model=PlaceOrderResponse)
async def place_order(request: PlaceOrderRequest):
    """下单（本地模拟）。

    Args:
        request: 下单请求。

    Returns:
        订单信息。
    """
    try:
        if request.direction not in ("buy", "sell"):
            raise HTTPException(
                status_code=400, detail="direction must be 'buy' or 'sell'"
            )

        order = _engine.place_order(
            symbol=request.symbol,
            direction=request.direction,
            quantity=request.quantity,
            price=request.price,
        )

        return PlaceOrderResponse(
            order_id=order.order_id,
            symbol=order.symbol,
            direction=order.direction,
            quantity=order.quantity,
            price=order.price,
            status=order.status,
            created_at=order.created_at,
            filled_at=order.filled_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Place order failed: {e}")


@router.get("/order/{order_id}", response_model=PlaceOrderResponse)
async def get_order(order_id: str):
    """查询订单。

    Args:
        order_id: 订单 ID。

    Returns:
        订单信息。
    """
    order = _engine.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return PlaceOrderResponse(
        order_id=order.order_id,
        symbol=order.symbol,
        direction=order.direction,
        quantity=order.quantity,
        price=order.price,
        status=order.status,
        created_at=order.created_at,
        filled_at=order.filled_at,
    )


@router.get("/positions", response_model=GetPositionsResponse)
async def get_positions():
    """获取当前持仓。

    Returns:
        持仓信息。
    """
    positions = _engine.get_positions()
    capital = _engine.get_capital()

    return GetPositionsResponse(positions=positions, capital=capital)


@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """运行策略回测。

    Args:
        request: 回测请求。

    Returns:
        回测结果。
    """
    try:
        result = await _engine.run_strategy_backtest(
            strategy_config=request.strategy_config,
            start_time=request.start_time,
            end_time=request.end_time,
            asset_type=request.asset_type,
            initial_capital=request.initial_capital,
            symbols=request.symbols,
        )

        return result.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}")


@router.post("/reset")
async def reset_engine():
    """重置引擎状态。

    Returns:
        重置结果。
    """
    _engine.reset()
    return {"status": "ok", "message": "Engine reset successfully"}


@router.get("/health")
async def health():
    """健康检查。"""
    return {"status": "ok", "module": "local_sim_engine"}
