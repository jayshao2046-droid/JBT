"""本地 Sim 容灾引擎 — TASK-0076 CS1

当 sim-trading 服务不可用时，使用本地沙箱引擎模拟交易。
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from src.research.sandbox_engine import SandboxEngine, SandboxResult


@dataclass
class LocalSimOrder:
    """本地模拟订单。"""

    order_id: str
    symbol: str
    direction: str  # "buy" | "sell"
    quantity: int
    price: float
    status: str  # "pending" | "filled" | "rejected"
    created_at: str
    filled_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LocalSimEngine:
    """本地 Sim 容灾引擎。

    当 sim-trading 服务不可用时，使用本地沙箱引擎模拟交易。
    """

    def __init__(self, data_service_url: str = "http://localhost:8105"):
        """初始化本地 Sim 引擎。

        Args:
            data_service_url: data 服务 URL。
        """
        self.sandbox = SandboxEngine(data_service_url=data_service_url)
        self.orders: dict[str, LocalSimOrder] = {}
        self.positions: dict[str, float] = {}  # symbol -> quantity
        self.capital: float = 1_000_000.0

    def place_order(
        self,
        symbol: str,
        direction: str,
        quantity: int,
        price: float,
    ) -> LocalSimOrder:
        """下单（本地模拟）。

        Args:
            symbol: 合约代码。
            direction: 方向（buy/sell）。
            quantity: 数量。
            price: 价格。

        Returns:
            本地模拟订单。
        """
        order_id = f"local-sim-{uuid.uuid4().hex[:12]}"
        order = LocalSimOrder(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            price=price,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # 立即成交（简化逻辑）
        order.status = "filled"
        order.filled_at = datetime.now(timezone.utc).isoformat()

        # 更新持仓
        current_position = self.positions.get(symbol, 0.0)
        if direction == "buy":
            self.positions[symbol] = current_position + quantity
            self.capital -= price * quantity
        elif direction == "sell":
            self.positions[symbol] = current_position - quantity
            self.capital += price * quantity

        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[LocalSimOrder]:
        """查询订单。

        Args:
            order_id: 订单 ID。

        Returns:
            订单对象，不存在时返回 None。
        """
        return self.orders.get(order_id)

    def get_positions(self) -> dict[str, float]:
        """获取当前持仓。

        Returns:
            持仓字典（symbol -> quantity）。
        """
        return self.positions.copy()

    def get_capital(self) -> float:
        """获取当前资金。

        Returns:
            当前资金。
        """
        return self.capital

    async def run_strategy_backtest(
        self,
        strategy_config: dict,
        start_time: str,
        end_time: str,
        asset_type: str = "futures",
        initial_capital: float = 1_000_000,
        symbols: Optional[list[str]] = None,
    ) -> SandboxResult:
        """运行策略回测（委托给 SandboxEngine）。

        Args:
            strategy_config: 策略配置。
            start_time: 开始时间。
            end_time: 结束时间。
            asset_type: 资产类型（futures/stock）。
            initial_capital: 初始资金。
            symbols: 合约列表。

        Returns:
            回测结果。
        """
        return await self.sandbox.run_backtest(
            strategy_config=strategy_config,
            start_time=start_time,
            end_time=end_time,
            asset_type=asset_type,
            initial_capital=initial_capital,
            symbols=symbols,
        )

    def reset(self):
        """重置引擎状态。"""
        self.orders.clear()
        self.positions.clear()
        self.capital = 1_000_000.0
