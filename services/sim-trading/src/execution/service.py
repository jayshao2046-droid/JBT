# SimNow execution adapter — delegates to SimNowGateway

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from src.gateway.simnow import SimNowGateway

logger = logging.getLogger(__name__)


class ExecutionService:
    """交易执行服务 — 委托到 SimNowGateway 真实执行。

    router.py 中的下单/撤单端点已直接调用 gateway，本类作为
    独立模块提供相同能力，供未来策略引擎或信号消费者使用。
    """

    def __init__(self, gateway: Optional["SimNowGateway"] = None) -> None:
        self._gateway = gateway

    def bind_gateway(self, gateway: "SimNowGateway") -> None:
        """延迟绑定网关（CTP 连接后调用）。"""
        self._gateway = gateway

    def _ensure_gateway(self) -> "SimNowGateway":
        if self._gateway is None:
            raise RuntimeError("ExecutionService: gateway not bound")
        return self._gateway

    def submit_order(
        self,
        instrument_id: str,
        direction: str,
        offset: str,
        price: float,
        volume: int,
    ) -> Dict:
        """提交限价单到 CTP。

        direction: '0'=买, '1'=卖
        offset:    '0'=开仓, '1'=平仓, '3'=平今
        """
        gw = self._ensure_gateway()
        result = gw.insert_order(instrument_id, direction, offset, price, volume)
        logger.info(
            "[execution] order submitted: %s %s%s@%.2f vol=%d → %s",
            instrument_id, direction, offset, price, volume, result,
        )
        return result

    def cancel_order(self, order_ref: str) -> Dict:
        """撤单。"""
        gw = self._ensure_gateway()
        result = gw.cancel_order(order_ref)
        logger.info("[execution] cancel submitted: ref=%s → %s", order_ref, result)
        return result

    def get_order_status(self, order_ref: str) -> Dict:
        """查询订单状态。"""
        gw = self._ensure_gateway()
        orders = gw.get_orders()
        return orders.get(order_ref, {"order_ref": order_ref, "status": "unknown"})
