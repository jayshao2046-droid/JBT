"""数据质量计算器"""
from __future__ import annotations

import time
from typing import Any, Optional


class DataQualityCalculator:
    """数据质量计算器"""

    def calculate_completeness(self, collections: list[dict[str, Any]]) -> float:
        """计算数据完整性

        Args:
            collections: 采集记录列表

        Returns:
            完整性百分比 (0-100)
        """
        if not collections:
            return 0.0

        total_expected = sum(c.get("expected_count", 0) for c in collections)
        total_actual = sum(c.get("actual_count", 0) for c in collections)

        if total_expected == 0:
            return 100.0

        return round((total_actual / total_expected) * 100, 2)

    def calculate_timeliness(self, collections: list[dict[str, Any]]) -> float:
        """计算数据及时性

        Args:
            collections: 采集记录列表

        Returns:
            及时性百分比 (0-100)
        """
        if not collections:
            return 0.0

        on_time_count = 0
        for collection in collections:
            scheduled_time = collection.get("scheduled_time", 0)
            actual_time = collection.get("actual_time", 0)
            delay_threshold = collection.get("delay_threshold", 300)  # 默认5分钟

            if actual_time > 0 and scheduled_time > 0:
                delay = actual_time - scheduled_time
                if delay <= delay_threshold:
                    on_time_count += 1

        return round((on_time_count / len(collections)) * 100, 2)

    def calculate_accuracy(self, collections: list[dict[str, Any]]) -> float:
        """计算数据准确性

        Args:
            collections: 采集记录列表

        Returns:
            准确性百分比 (0-100)
        """
        if not collections:
            return 0.0

        accurate_count = 0
        for collection in collections:
            validation_errors = collection.get("validation_errors", 0)
            if validation_errors == 0:
                accurate_count += 1

        return round((accurate_count / len(collections)) * 100, 2)

    def calculate_consistency(self, collections: list[dict[str, Any]]) -> float:
        """计算数据一致性

        Args:
            collections: 采集记录列表

        Returns:
            一致性百分比 (0-100)
        """
        if not collections:
            return 0.0

        consistent_count = 0
        for collection in collections:
            schema_violations = collection.get("schema_violations", 0)
            if schema_violations == 0:
                consistent_count += 1

        return round((consistent_count / len(collections)) * 100, 2)

    def calculate_success_rate(self, collections: list[dict[str, Any]]) -> float:
        """计算采集成功率

        Args:
            collections: 采集记录列表

        Returns:
            成功率百分比 (0-100)
        """
        if not collections:
            return 0.0

        success_count = sum(1 for c in collections if c.get("status") == "success")
        return round((success_count / len(collections)) * 100, 2)

    def calculate_avg_latency(self, collections: list[dict[str, Any]]) -> float:
        """计算平均延迟

        Args:
            collections: 采集记录列表

        Returns:
            平均延迟（秒）
        """
        if not collections:
            return 0.0

        latencies = []
        for collection in collections:
            start_time = collection.get("start_time", 0)
            end_time = collection.get("end_time", 0)
            if start_time > 0 and end_time > 0:
                latencies.append(end_time - start_time)

        if not latencies:
            return 0.0

        return round(sum(latencies) / len(latencies), 2)

    def calculate_error_rate(self, collections: list[dict[str, Any]]) -> float:
        """计算错误率

        Args:
            collections: 采集记录列表

        Returns:
            错误率百分比 (0-100)
        """
        if not collections:
            return 0.0

        error_count = sum(1 for c in collections if c.get("status") == "failed")
        return round((error_count / len(collections)) * 100, 2)

    def calculate_all_metrics(self, collections: list[dict[str, Any]]) -> dict[str, float]:
        """计算所有质量指标

        Args:
            collections: 采集记录列表

        Returns:
            所有指标的字典
        """
        return {
            "completeness": self.calculate_completeness(collections),
            "timeliness": self.calculate_timeliness(collections),
            "accuracy": self.calculate_accuracy(collections),
            "consistency": self.calculate_consistency(collections),
            "success_rate": self.calculate_success_rate(collections),
            "avg_latency": self.calculate_avg_latency(collections),
            "error_rate": self.calculate_error_rate(collections),
        }
