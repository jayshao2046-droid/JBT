"""
KPI 计算引擎
计算交易绩效 KPI 和执行质量 KPI
"""
import math
from typing import List, Dict, Any
from datetime import datetime, timedelta


class KpiCalculator:
    """KPI 计算引擎"""

    @staticmethod
    def calculate_trading_kpis(trades: List[Dict], account: Dict) -> Dict[str, float]:
        """计算交易绩效 KPI

        Args:
            trades: 成交记录列表
            account: 账户信息

        Returns:
            包含 7 个交易绩效指标的字典
        """
        if not trades:
            return {
                "win_rate": 0.0,
                "profit_loss_ratio": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "daily_pnl": 0.0,
                "weekly_pnl": 0.0,
                "monthly_pnl": 0.0
            }

        # 胜率
        win_trades = [t for t in trades if t.get("pnl", 0) > 0]
        loss_trades = [t for t in trades if t.get("pnl", 0) < 0]
        win_rate = len(win_trades) / len(trades) * 100 if trades else 0.0

        # 盈亏比
        avg_win = sum(t["pnl"] for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = abs(sum(t["pnl"] for t in loss_trades) / len(loss_trades)) if loss_trades else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0

        # 最大回撤（基于账户余额）
        max_drawdown = KpiCalculator._calculate_max_drawdown(account)

        # 夏普比率（简化版）
        sharpe_ratio = KpiCalculator._calculate_sharpe_ratio(trades)

        # 今日/本周/本月盈亏
        daily_pnl = account.get("close_pnl", 0) + account.get("floating_pnl", 0)
        weekly_pnl = KpiCalculator._calculate_period_pnl(trades, days=7)
        monthly_pnl = KpiCalculator._calculate_period_pnl(trades, days=30)

        return {
            "win_rate": round(win_rate, 2),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "daily_pnl": round(daily_pnl, 2),
            "weekly_pnl": round(weekly_pnl, 2),
            "monthly_pnl": round(monthly_pnl, 2)
        }

    @staticmethod
    def calculate_execution_kpis(orders: List[Dict]) -> Dict[str, float]:
        """计算执行质量 KPI

        Args:
            orders: 订单列表

        Returns:
            包含 5 个执行质量指标的字典
        """
        if not orders:
            return {
                "avg_slippage": 0.0,
                "order_reject_rate": 0.0,
                "avg_fill_latency": 0.0,
                "cancel_rate": 0.0,
                "partial_fill_rate": 0.0
            }

        total = len(orders)
        rejected = len([o for o in orders if o.get("status") == "废单"])
        cancelled = len([o for o in orders if o.get("status") == "已撤单"])
        partial = len([o for o in orders if o.get("status") == "部分成交"])
        filled = [o for o in orders if o.get("status") == "已成交"]

        # 平均滑点（tick）
        avg_slippage = sum(o.get("slippage", 0) for o in filled) / len(filled) if filled else 0.0

        # 订单拒绝率
        order_reject_rate = rejected / total * 100 if total > 0 else 0.0

        # 平均成交延迟（ms）
        avg_fill_latency = sum(o.get("latency_ms", 0) for o in filled) / len(filled) if filled else 0.0

        # 撤单率
        cancel_rate = cancelled / total * 100 if total > 0 else 0.0

        # 部分成交率
        partial_fill_rate = partial / total * 100 if total > 0 else 0.0

        return {
            "avg_slippage": round(avg_slippage, 2),
            "order_reject_rate": round(order_reject_rate, 2),
            "avg_fill_latency": round(avg_fill_latency, 0),
            "cancel_rate": round(cancel_rate, 2),
            "partial_fill_rate": round(partial_fill_rate, 2)
        }

    @staticmethod
    def _calculate_max_drawdown(account: Dict) -> float:
        """计算最大回撤（简化版）

        基于当前账户余额与初始余额的比较
        """
        balance = account.get("balance", 0)
        pre_balance = account.get("pre_balance", 0) or account.get("initial_balance", 0)

        if pre_balance <= 0:
            return 0.0

        drawdown = (pre_balance - balance) / pre_balance * 100
        return max(0, drawdown)

    @staticmethod
    def _calculate_sharpe_ratio(trades: List[Dict]) -> float:
        """计算夏普比率（简化版）

        使用日收益率的均值除以标准差
        """
        if len(trades) < 2:
            return 0.0

        # 提取每笔交易的收益率
        returns = [t.get("pnl", 0) for t in trades]

        # 计算均值和标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance) if variance > 0 else 1

        # 夏普比率（假设无风险利率为 0）
        sharpe = mean_return / std_return if std_return > 0 else 0.0

        return sharpe

    @staticmethod
    def _calculate_period_pnl(trades: List[Dict], days: int) -> float:
        """计算指定周期内的盈亏

        Args:
            trades: 成交记录列表
            days: 天数

        Returns:
            周期内总盈亏
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        period_trades = [
            t for t in trades
            if t.get("timestamp", "") >= cutoff or t.get("saved_at", "") >= cutoff
        ]
        return sum(t.get("pnl", 0) for t in period_trades)


# 便捷函数
def calculate_trading_kpis(trades: List[Dict], account: Dict) -> Dict[str, float]:
    """计算交易绩效 KPI（便捷函数）"""
    return KpiCalculator.calculate_trading_kpis(trades, account)


def calculate_execution_kpis(orders: List[Dict]) -> Dict[str, float]:
    """计算执行质量 KPI（便捷函数）"""
    return KpiCalculator.calculate_execution_kpis(orders)
