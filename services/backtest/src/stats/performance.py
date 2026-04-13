"""绩效统计计算器"""
from __future__ import annotations

from datetime import date, timedelta
from math import sqrt
from typing import Any, Dict, List, Optional


class PerformanceCalculator:
    """绩效统计计算器"""

    def calculate_annual_return(
        self,
        initial_capital: float,
        final_capital: float,
        start_date: date,
        end_date: date,
    ) -> float:
        """计算年化收益率"""
        if initial_capital <= 0:
            return 0.0

        total_days = max((end_date - start_date).days, 1)
        total_return = (final_capital - initial_capital) / initial_capital

        # 年化收益率 = (1 + 总收益率) ^ (365 / 总天数) - 1
        annual_return = ((1 + total_return) ** (365.0 / total_days)) - 1
        return round(annual_return * 100, 2)

    def calculate_max_drawdown(self, equity_curve: List[Dict[str, Any]]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0.0

        max_dd = 0.0
        peak = equity_curve[0].get("equity", 0.0)

        for point in equity_curve:
            equity = point.get("equity", 0.0)
            peak = max(peak, equity)

            if peak > 0:
                drawdown = (peak - equity) / peak
                max_dd = max(max_dd, drawdown)

        return round(max_dd * 100, 2)

    def calculate_sharpe_ratio(
        self,
        equity_curve: List[Dict[str, Any]],
        risk_free_rate: float = 0.03,
    ) -> float:
        """计算夏普比率"""
        if len(equity_curve) < 2:
            return 0.0

        # 计算每日收益率
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i - 1].get("equity", 0.0)
            curr_equity = equity_curve[i].get("equity", 0.0)

            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)

        if not returns:
            return 0.0

        # 计算平均收益率和标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = sqrt(variance) if variance > 0 else 0.0

        if std_dev == 0:
            return 0.0

        # 年化夏普比率
        daily_rf = risk_free_rate / 252
        sharpe = (mean_return - daily_rf) / std_dev * sqrt(252)

        return round(sharpe, 2)

    def calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float,
    ) -> float:
        """计算卡玛比率（年化收益率 / 最大回撤）"""
        if max_drawdown == 0:
            return 0.0

        calmar = annual_return / max_drawdown
        return round(calmar, 2)

    def calculate_win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """计算胜率"""
        if not trades:
            return 0.0

        winning_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
        total_trades = len(trades)

        if total_trades == 0:
            return 0.0

        win_rate = (winning_trades / total_trades) * 100
        return round(win_rate, 2)

    def calculate_profit_loss_ratio(self, trades: List[Dict[str, Any]]) -> float:
        """计算盈亏比（平均盈利 / 平均亏损）"""
        if not trades:
            return 0.0

        winning_trades = [trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) > 0]
        losing_trades = [abs(trade.get("pnl", 0)) for trade in trades if trade.get("pnl", 0) < 0]

        if not winning_trades or not losing_trades:
            return 0.0

        avg_win = sum(winning_trades) / len(winning_trades)
        avg_loss = sum(losing_trades) / len(losing_trades)

        if avg_loss == 0:
            return 0.0

        profit_loss_ratio = avg_win / avg_loss
        return round(profit_loss_ratio, 2)

    def calculate_total_trades(self, trades: List[Dict[str, Any]]) -> int:
        """计算总交易次数"""
        return len(trades)

    def calculate_all_metrics(
        self,
        initial_capital: float,
        final_capital: float,
        start_date: date,
        end_date: date,
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """计算所有绩效指标"""
        annual_return = self.calculate_annual_return(
            initial_capital, final_capital, start_date, end_date
        )
        max_drawdown = self.calculate_max_drawdown(equity_curve)

        return {
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": self.calculate_sharpe_ratio(equity_curve),
            "calmar_ratio": self.calculate_calmar_ratio(annual_return, max_drawdown),
            "win_rate": self.calculate_win_rate(trades),
            "profit_loss_ratio": self.calculate_profit_loss_ratio(trades),
            "total_trades": self.calculate_total_trades(trades),
        }
