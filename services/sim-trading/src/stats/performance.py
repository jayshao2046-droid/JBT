# Performance statistics calculator (SIMWEB-01 P1-1)

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class PerformanceCalculator:
    """交易绩效统计计算器"""

    def calculate_win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """计算胜率"""
        if not trades:
            return 0.0
        winning_trades = [t for t in trades if (t.get("pnl") or 0) > 0]
        return round(len(winning_trades) / len(trades) * 100, 2)

    def calculate_profit_loss_ratio(self, trades: List[Dict[str, Any]]) -> float:
        """计算盈亏比"""
        winning_trades = [t for t in trades if (t.get("pnl") or 0) > 0]
        losing_trades = [t for t in trades if (t.get("pnl") or 0) < 0]

        if not winning_trades or not losing_trades:
            return 0.0

        avg_profit = sum(t.get("pnl", 0) for t in winning_trades) / len(winning_trades)
        avg_loss = abs(sum(t.get("pnl", 0) for t in losing_trades) / len(losing_trades))

        return round(avg_profit / avg_loss, 2) if avg_loss > 0 else 0.0

    def calculate_max_drawdown(self, equity_history: List[Dict[str, Any]]) -> float:
        """计算最大回撤百分比"""
        if len(equity_history) < 2:
            return 0.0

        peak = equity_history[0].get("equity", 0)
        max_dd = 0.0

        for point in equity_history:
            equity = point.get("equity", 0)
            if equity > peak:
                peak = equity
            if peak > 0:
                dd = (peak - equity) / peak * 100
                if dd > max_dd:
                    max_dd = dd

        return round(max_dd, 2)

    def calculate_sharpe_ratio(
        self, equity_history: List[Dict[str, Any]], risk_free_rate: float = 0.03
    ) -> float:
        """计算夏普比率（年化）"""
        if len(equity_history) < 2:
            return 0.0

        # 计算日收益率
        returns = []
        for i in range(1, len(equity_history)):
            prev_equity = equity_history[i - 1].get("equity", 0)
            curr_equity = equity_history[i].get("equity", 0)
            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)

        if not returns:
            return 0.0

        # 计算平均收益率和标准差
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 0.0

        # 年化夏普比率（假设 252 个交易日）
        sharpe = (avg_return * 252 - risk_free_rate) / (std_dev * (252 ** 0.5))
        return round(sharpe, 2)

    def calculate_period_pnl(
        self, trades: List[Dict[str, Any]], period: str = "today"
    ) -> float:
        """计算指定周期的盈亏"""
        now = datetime.now()

        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = now - timedelta(days=now.weekday())
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return 0.0

        period_trades = []
        for trade in trades:
            trade_time_str = trade.get("timestamp") or trade.get("time")
            if trade_time_str:
                try:
                    trade_time = datetime.fromisoformat(trade_time_str.replace("Z", ""))
                    if trade_time >= start_time:
                        period_trades.append(trade)
                except (ValueError, AttributeError):
                    pass

        return round(sum(t.get("pnl", 0) for t in period_trades), 2)

    def get_performance_stats(
        self, trades: List[Dict[str, Any]], equity_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """获取完整的绩效统计"""
        return {
            "win_rate": self.calculate_win_rate(trades),
            "profit_loss_ratio": self.calculate_profit_loss_ratio(trades),
            "max_drawdown": self.calculate_max_drawdown(equity_history),
            "sharpe_ratio": self.calculate_sharpe_ratio(equity_history),
            "today_pnl": self.calculate_period_pnl(trades, "today"),
            "week_pnl": self.calculate_period_pnl(trades, "week"),
            "month_pnl": self.calculate_period_pnl(trades, "month"),
        }
