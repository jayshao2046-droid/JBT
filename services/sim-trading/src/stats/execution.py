# Execution quality statistics calculator (SIMWEB-01 P1-2)

from typing import List, Dict, Any


class ExecutionQualityCalculator:
    """执行质量统计计算器"""

    def calculate_slippage(self, trades: List[Dict[str, Any]]) -> float:
        """计算平均滑点（实际成交价 vs 信号价格）"""
        if not trades:
            return 0.0

        slippages = []
        for trade in trades:
            signal_price = trade.get("signal_price") or trade.get("price")
            actual_price = trade.get("actual_price") or trade.get("price")
            if signal_price and actual_price:
                slippage = abs(actual_price - signal_price)
                slippages.append(slippage)

        if not slippages:
            return 0.0

        return round(sum(slippages) / len(slippages), 4)

    def calculate_rejection_rate(self, orders: List[Dict[str, Any]]) -> float:
        """计算订单拒绝率"""
        if not orders:
            return 0.0

        rejected_count = sum(
            1 for order in orders if order.get("status") in ["rejected", "cancelled", "error"]
        )
        return round(rejected_count / len(orders) * 100, 2)

    def calculate_latency(self, trades: List[Dict[str, Any]]) -> float:
        """计算平均成交延迟（毫秒）"""
        if not trades:
            return 0.0

        latencies = []
        for trade in trades:
            signal_time = trade.get("signal_time")
            trade_time = trade.get("trade_time") or trade.get("timestamp")
            if signal_time and trade_time:
                try:
                    from datetime import datetime

                    signal_dt = datetime.fromisoformat(signal_time.replace("Z", ""))
                    trade_dt = datetime.fromisoformat(trade_time.replace("Z", ""))
                    latency_ms = (trade_dt - signal_dt).total_seconds() * 1000
                    latencies.append(latency_ms)
                except (ValueError, AttributeError):
                    pass

        if not latencies:
            return 0.0

        return round(sum(latencies) / len(latencies), 2)

    def calculate_cancel_rate(self, orders: List[Dict[str, Any]]) -> float:
        """计算撤单率"""
        if not orders:
            return 0.0

        cancelled_count = sum(1 for order in orders if order.get("status") == "cancelled")
        return round(cancelled_count / len(orders) * 100, 2)

    def calculate_partial_fill_rate(self, orders: List[Dict[str, Any]]) -> float:
        """计算部分成交率"""
        if not orders:
            return 0.0

        partial_fill_count = sum(
            1
            for order in orders
            if order.get("status") == "partial_filled"
            or (
                order.get("filled_volume", 0) > 0
                and order.get("filled_volume", 0) < order.get("volume", 0)
            )
        )
        return round(partial_fill_count / len(orders) * 100, 2)

    def get_execution_stats(
        self, trades: List[Dict[str, Any]], orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """获取完整的执行质量统计"""
        return {
            "avg_slippage": self.calculate_slippage(trades),
            "rejection_rate": self.calculate_rejection_rate(orders),
            "avg_latency_ms": self.calculate_latency(trades),
            "cancel_rate": self.calculate_cancel_rate(orders),
            "partial_fill_rate": self.calculate_partial_fill_rate(orders),
        }
