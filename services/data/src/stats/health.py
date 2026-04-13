"""数据源健康评估器"""
from __future__ import annotations

import time
from typing import Any, Optional


class DataSourceHealthCalculator:
    """数据源健康评估器"""

    def calculate_availability(self, source_records: list[dict[str, Any]]) -> float:
        """计算数据源可用性

        Args:
            source_records: 数据源记录列表

        Returns:
            可用性百分比 (0-100)
        """
        if not source_records:
            return 0.0

        available_count = sum(1 for r in source_records if r.get("status") == "available")
        return round((available_count / len(source_records)) * 100, 2)

    def calculate_response_time(self, source_records: list[dict[str, Any]]) -> float:
        """计算平均响应时间

        Args:
            source_records: 数据源记录列表

        Returns:
            平均响应时间（毫秒）
        """
        if not source_records:
            return 0.0

        response_times = [r.get("response_time", 0) for r in source_records if r.get("response_time", 0) > 0]

        if not response_times:
            return 0.0

        return round(sum(response_times) / len(response_times), 2)

    def calculate_error_rate(self, source_records: list[dict[str, Any]]) -> float:
        """计算错误率

        Args:
            source_records: 数据源记录列表

        Returns:
            错误率百分比 (0-100)
        """
        if not source_records:
            return 0.0

        error_count = sum(1 for r in source_records if r.get("status") == "error")
        return round((error_count / len(source_records)) * 100, 2)

    def calculate_freshness(self, source_records: list[dict[str, Any]]) -> float:
        """计算数据新鲜度

        Args:
            source_records: 数据源记录列表

        Returns:
            新鲜度分数 (0-100)，基于最近更新时间
        """
        if not source_records:
            return 0.0

        now = time.time()
        freshness_scores = []

        for record in source_records:
            last_update = record.get("last_update_time", 0)
            if last_update > 0:
                age_hours = (now - last_update) / 3600
                threshold_hours = record.get("freshness_threshold", 24)

                # 计算新鲜度分数：在阈值内为100，超过阈值线性衰减
                if age_hours <= threshold_hours:
                    score = 100.0
                else:
                    score = max(0, 100 - ((age_hours - threshold_hours) / threshold_hours) * 100)

                freshness_scores.append(score)

        if not freshness_scores:
            return 0.0

        return round(sum(freshness_scores) / len(freshness_scores), 2)

    def calculate_coverage(self, source_records: list[dict[str, Any]]) -> float:
        """计算数据覆盖率

        Args:
            source_records: 数据源记录列表

        Returns:
            覆盖率百分比 (0-100)
        """
        if not source_records:
            return 0.0

        total_expected = sum(r.get("expected_symbols", 0) for r in source_records)
        total_actual = sum(r.get("actual_symbols", 0) for r in source_records)

        if total_expected == 0:
            return 100.0

        return round((total_actual / total_expected) * 100, 2)

    def calculate_all_metrics(self, source_records: list[dict[str, Any]]) -> dict[str, float]:
        """计算所有健康指标

        Args:
            source_records: 数据源记录列表

        Returns:
            所有指标的字典
        """
        return {
            "availability": self.calculate_availability(source_records),
            "response_time": self.calculate_response_time(source_records),
            "error_rate": self.calculate_error_rate(source_records),
            "freshness": self.calculate_freshness(source_records),
            "coverage": self.calculate_coverage(source_records),
        }
