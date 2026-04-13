"""
决策质量评估模块
"""
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class QualityCalculator:
    """决策质量计算器"""

    def calculate_signal_quality(self, signals: List[Dict]) -> float:
        """计算信号质量评分（0-100）"""
        if not signals:
            return 0.0

        scores = []
        for s in signals:
            score = 0.0
            # 信号强度权重 40%
            score += s.get("signal_strength", 0.0) * 40
            # 因子一致性权重 30%
            score += s.get("factor_consistency", 0.0) * 30
            # 市场环境匹配度权重 30%
            score += s.get("market_fit", 0.0) * 30
            scores.append(score)

        return round(sum(scores) / len(scores), 2)

    def calculate_factor_effectiveness(self, factors: List[Dict]) -> float:
        """计算因子有效性（0-100）"""
        if not factors:
            return 0.0

        effective = sum(1 for f in factors if f.get("is_effective", False))
        return round(effective / len(factors) * 100, 2)

    def calculate_strategy_stability(self, signals: List[Dict]) -> float:
        """计算策略稳定性（0-100）"""
        if not signals or len(signals) < 2:
            return 0.0

        returns = [s.get("return", 0.0) for s in signals if "return" in s]
        if not returns or len(returns) < 2:
            return 0.0

        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5

        # 稳定性 = 1 - (标准差 / (|平均收益| + 0.01))
        stability = 1 - (std_dev / (abs(avg_return) + 0.01))
        stability = max(0.0, min(1.0, stability))

        return round(stability * 100, 2)

    def calculate_risk_control_effectiveness(self, signals: List[Dict]) -> float:
        """计算风险控制有效性（0-100）"""
        if not signals:
            return 0.0

        # 检查止损触发率
        stop_loss_triggered = sum(1 for s in signals if s.get("stop_loss_triggered", False))
        # 检查风险限制遵守率
        risk_compliant = sum(1 for s in signals if s.get("risk_compliant", True))

        # 风控有效性 = 遵守率 * 0.7 + (1 - 止损率) * 0.3
        compliance_rate = risk_compliant / len(signals)
        stop_loss_rate = stop_loss_triggered / len(signals) if signals else 0.0

        effectiveness = compliance_rate * 0.7 + (1 - stop_loss_rate) * 0.3
        return round(effectiveness * 100, 2)

    def calculate_data_completeness(self, signals: List[Dict]) -> float:
        """计算数据完整性（0-100）"""
        if not signals:
            return 0.0

        required_fields = ["signal", "signal_strength", "factors", "market_context"]

        complete_count = 0
        for s in signals:
            if all(field in s for field in required_fields):
                complete_count += 1

        return round(complete_count / len(signals) * 100, 2)

    def calculate_all(self, signals: List[Dict], factors: Optional[List[Dict]] = None) -> Dict:
        """计算所有质量指标"""
        if factors is None:
            factors = []
            for s in signals:
                factors.extend(s.get("factors", []))

        return {
            "signal_quality": self.calculate_signal_quality(signals),
            "factor_effectiveness": self.calculate_factor_effectiveness(factors),
            "strategy_stability": self.calculate_strategy_stability(signals),
            "risk_control_effectiveness": self.calculate_risk_control_effectiveness(signals),
            "data_completeness": self.calculate_data_completeness(signals),
        }
