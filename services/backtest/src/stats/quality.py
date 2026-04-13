"""回测质量评估计算器"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from math import sqrt


class QualityCalculator:
    """回测质量评估计算器"""

    def calculate_out_of_sample_performance(
        self,
        in_sample_return: float,
        out_of_sample_return: float,
    ) -> float:
        """计算样本外表现（样本外收益率 / 样本内收益率）"""
        if in_sample_return == 0:
            return 0.0

        ratio = out_of_sample_return / in_sample_return
        # 转换为 0-100 分数，1.0 为满分
        score = min(100, max(0, ratio * 100))
        return round(score, 2)

    def detect_overfitting(
        self,
        in_sample_sharpe: float,
        out_of_sample_sharpe: float,
        param_count: int = 5,
    ) -> float:
        """检测过拟合（0-100分，分数越高越好）"""
        if in_sample_sharpe == 0:
            return 50.0

        # 样本内外夏普比率差异
        sharpe_degradation = (in_sample_sharpe - out_of_sample_sharpe) / in_sample_sharpe

        # 参数数量惩罚（参数越多，过拟合风险越高）
        param_penalty = min(0.3, param_count * 0.05)

        # 过拟合分数（差异越小越好）
        overfitting_score = max(0, 1 - sharpe_degradation - param_penalty)
        return round(overfitting_score * 100, 2)

    def calculate_stability_score(
        self,
        monthly_returns: List[float],
    ) -> float:
        """计算稳定性评分（基于月度收益率的变异系数）"""
        if not monthly_returns or len(monthly_returns) < 2:
            return 0.0

        mean_return = sum(monthly_returns) / len(monthly_returns)
        if mean_return == 0:
            return 0.0

        variance = sum((r - mean_return) ** 2 for r in monthly_returns) / len(monthly_returns)
        std_dev = sqrt(variance)

        # 变异系数（标准差 / 均值）
        cv = std_dev / abs(mean_return)

        # 转换为 0-100 分数（变异系数越小越稳定）
        stability_score = max(0, 100 - cv * 50)
        return round(stability_score, 2)

    def calculate_parameter_sensitivity(
        self,
        base_return: float,
        param_variations: List[float],
    ) -> float:
        """计算参数敏感度（参数变化对收益率的影响）"""
        if not param_variations or base_return == 0:
            return 50.0

        # 计算收益率变化的标准差
        return_changes = [(r - base_return) / base_return for r in param_variations]
        mean_change = sum(return_changes) / len(return_changes)
        variance = sum((c - mean_change) ** 2 for c in return_changes) / len(return_changes)
        std_dev = sqrt(variance)

        # 敏感度分数（标准差越小越好）
        sensitivity_score = max(0, 100 - std_dev * 200)
        return round(sensitivity_score, 2)

    def calculate_data_quality_score(
        self,
        total_bars: int,
        missing_bars: int = 0,
        outlier_bars: int = 0,
    ) -> float:
        """计算数据质量评分"""
        if total_bars == 0:
            return 0.0

        # 缺失数据比例
        missing_ratio = missing_bars / total_bars

        # 异常数据比例
        outlier_ratio = outlier_bars / total_bars

        # 数据质量分数
        quality_score = max(0, 100 - (missing_ratio + outlier_ratio) * 100)
        return round(quality_score, 2)

    def calculate_all_metrics(
        self,
        in_sample_return: float = 20.0,
        out_of_sample_return: float = 15.0,
        in_sample_sharpe: float = 1.5,
        out_of_sample_sharpe: float = 1.2,
        monthly_returns: Optional[List[float]] = None,
        param_variations: Optional[List[float]] = None,
        total_bars: int = 1000,
        missing_bars: int = 0,
        outlier_bars: int = 0,
    ) -> Dict[str, float]:
        """计算所有质量指标"""
        if monthly_returns is None:
            monthly_returns = [2.5, 3.0, -1.0, 4.0, 2.0, 3.5, -0.5, 2.8, 3.2, 2.1, 3.8, 2.6]

        if param_variations is None:
            param_variations = [18.0, 19.0, 20.0, 21.0, 22.0]

        return {
            "out_of_sample_performance": self.calculate_out_of_sample_performance(
                in_sample_return, out_of_sample_return
            ),
            "overfitting_score": self.detect_overfitting(
                in_sample_sharpe, out_of_sample_sharpe
            ),
            "stability_score": self.calculate_stability_score(monthly_returns),
            "parameter_sensitivity": self.calculate_parameter_sensitivity(
                in_sample_return, param_variations
            ),
            "data_quality_score": self.calculate_data_quality_score(
                total_bars, missing_bars, outlier_bars
            ),
        }
