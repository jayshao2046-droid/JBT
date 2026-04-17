"""稳定性过滤器 — TASK-U0-20260417-004

用于数据清洗，只保留高质量的训练数据。

过滤标准:
1. actual_improvement == True（有改进）
2. IS Sharpe ≥ 1.0（样本内表现良好）
3. OOS Sharpe ≥ 0.8（样本外表现良好）
4. OOS/IS Sharpe ≥ 70%（防止过拟合）
5. OOS 交易次数 ≥ 10（样本充足）

目的:
- 防止模型学会"运气好"的坏模式
- 确保训练数据的稳定性和泛化能力
- 排除异常样本
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRecord:
    """优化记录"""
    strategy_id: str
    iteration: int

    # 样本内指标
    is_sharpe: float
    is_trades: int
    is_win_rate: float
    is_max_dd: float

    # 样本外指标
    oos_sharpe: float
    oos_trades: int
    oos_win_rate: float
    oos_max_dd: float

    # 改进标记
    actual_improvement: bool

    # 参数调整
    parameter_changes: dict

    # 诊断信息
    diagnosis: Optional[dict] = None


class StabilityFilter:
    """稳定性过滤器

    只保留高质量的训练数据，防止模型学会"过度拟合"的坏毛病。
    """

    # 过滤标准
    MIN_IS_SHARPE = 1.0
    MIN_OOS_SHARPE = 0.8
    MIN_OOS_IS_RATIO = 0.7  # OOS/IS ≥ 70%
    MIN_OOS_TRADES = 10

    def __init__(self):
        self.filtered_count = 0
        self.total_count = 0

    def is_high_quality(self, record: OptimizationRecord) -> bool:
        """判断是否为高质量训练数据

        Args:
            record: 优化记录

        Returns:
            True 表示高质量，False 表示应过滤
        """
        self.total_count += 1

        # 检查所有条件
        checks = {
            "actual_improvement": record.actual_improvement,
            "is_sharpe": record.is_sharpe >= self.MIN_IS_SHARPE,
            "oos_sharpe": record.oos_sharpe >= self.MIN_OOS_SHARPE,
            "oos_trades": record.oos_trades >= self.MIN_OOS_TRADES,
        }

        # OOS/IS Sharpe 比例检查（防止过拟合）
        if record.is_sharpe > 0:
            oos_is_ratio = record.oos_sharpe / record.is_sharpe
            checks["oos_is_ratio"] = oos_is_ratio >= self.MIN_OOS_IS_RATIO
        else:
            checks["oos_is_ratio"] = False

        # 所有条件必须满足
        is_quality = all(checks.values())

        if not is_quality:
            self.filtered_count += 1
            failed_checks = [k for k, v in checks.items() if not v]
            logger.debug(
                f"过滤记录 {record.strategy_id} 迭代{record.iteration}: "
                f"未通过检查 {failed_checks}"
            )

        return is_quality

    def get_filter_stats(self) -> dict:
        """获取过滤统计"""
        return {
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
            "passed_count": self.total_count - self.filtered_count,
            "filter_rate": (
                self.filtered_count / self.total_count
                if self.total_count > 0
                else 0.0
            ),
        }

    def filter_batch(self, records: list[OptimizationRecord]) -> list[OptimizationRecord]:
        """批量过滤

        Args:
            records: 优化记录列表

        Returns:
            高质量记录列表
        """
        high_quality_records = [r for r in records if self.is_high_quality(r)]

        stats = self.get_filter_stats()
        logger.info(
            f"📊 稳定性过滤完成: "
            f"总数 {stats['total_count']}, "
            f"通过 {stats['passed_count']}, "
            f"过滤 {stats['filtered_count']} ({stats['filter_rate']:.1%})"
        )

        return high_quality_records
