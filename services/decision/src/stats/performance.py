"""
决策绩效计算模块
"""
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """决策绩效计算器"""

    def calculate_signal_accuracy(self, signals: List[Dict]) -> float:
        """计算信号准确率"""
        if not signals:
            return 0.0

        correct = sum(1 for s in signals if s.get("is_correct", False))
        return round(correct / len(signals) * 100, 2)

    def calculate_avg_return(self, signals: List[Dict]) -> float:
        """计算平均收益率"""
        if not signals:
            return 0.0

        returns = [s.get("return", 0.0) for s in signals if "return" in s]
        if not returns:
            return 0.0

        return round(sum(returns) / len(returns) * 100, 2)

    def calculate_max_drawdown(self, signals: List[Dict]) -> float:
        """计算最大回撤"""
        if not signals:
            return 0.0

        equity_curve = []
        cumulative = 0.0

        for s in signals:
            cumulative += s.get("return", 0.0)
            equity_curve.append(cumulative)

        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak != 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return round(max_dd * 100, 2)

    def calculate_sharpe_ratio(self, signals: List[Dict], risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        if not signals:
            return 0.0

        returns = [s.get("return", 0.0) for s in signals if "return" in s]
        if not returns:
            return 0.0

        avg_return = sum(returns) / len(returns)

        if len(returns) < 2:
            return 0.0

        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 0.0

        sharpe = (avg_return - risk_free_rate / 252) / std_dev
        return round(sharpe, 2)

    def calculate_signal_count(self, signals: List[Dict]) -> int:
        """计算信号数量"""
        return len(signals)

    def calculate_execution_success_rate(self, signals: List[Dict]) -> float:
        """计算执行成功率"""
        if not signals:
            return 0.0

        executed = sum(1 for s in signals if s.get("executed", False))
        return round(executed / len(signals) * 100, 2)

    def calculate_avg_response_time(self, signals: List[Dict]) -> float:
        """计算平均响应时间（毫秒）"""
        if not signals:
            return 0.0

        times = [s.get("response_time_ms", 0.0) for s in signals if "response_time_ms" in s]
        if not times:
            return 0.0

        return round(sum(times) / len(times), 2)

    def calculate_all(self, signals: List[Dict]) -> Dict:
        """计算所有绩效指标"""
        return {
            "signal_accuracy": self.calculate_signal_accuracy(signals),
            "avg_return": self.calculate_avg_return(signals),
            "max_drawdown": self.calculate_max_drawdown(signals),
            "sharpe_ratio": self.calculate_sharpe_ratio(signals),
            "signal_count": self.calculate_signal_count(signals),
            "execution_success_rate": self.calculate_execution_success_rate(signals),
            "avg_response_time": self.calculate_avg_response_time(signals),
        }
