"""采集参数优化器"""
from __future__ import annotations

import itertools
from typing import Any, Optional


class CollectionOptimizer:
    """采集参数优化器"""

    def grid_search(
        self,
        param_grid: dict[str, list[Any]],
        objective: str = "success_rate",
    ) -> list[dict[str, Any]]:
        """参数网格搜索

        Args:
            param_grid: 参数网格，例如 {"interval": [60, 300, 600], "timeout": [10, 30, 60]}
            objective: 优化目标 (success_rate/latency/error_rate)

        Returns:
            参数组合列表，按优化目标排序
        """
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        combinations = []
        for values in itertools.product(*param_values):
            param_dict = dict(zip(param_names, values))
            # 模拟评估分数（实际应该运行采集任务）
            score = self._evaluate_params(param_dict, objective)
            combinations.append({
                "params": param_dict,
                "score": score,
                "objective": objective,
            })

        # 按分数排序（success_rate 越高越好，latency/error_rate 越低越好）
        reverse = objective == "success_rate"
        combinations.sort(key=lambda x: x["score"], reverse=reverse)

        return combinations

    def auto_tune(
        self,
        current_params: dict[str, Any],
        objective: str = "success_rate",
    ) -> dict[str, Any]:
        """自动调优

        Args:
            current_params: 当前参数
            objective: 优化目标

        Returns:
            推荐的参数配置
        """
        # 基于当前参数生成候选参数
        candidates = self._generate_candidates(current_params)

        # 评估所有候选参数
        best_params = current_params
        best_score = self._evaluate_params(current_params, objective)

        for candidate in candidates:
            score = self._evaluate_params(candidate, objective)
            if self._is_better(score, best_score, objective):
                best_score = score
                best_params = candidate

        return {
            "recommended_params": best_params,
            "expected_score": best_score,
            "improvement": self._calculate_improvement(
                self._evaluate_params(current_params, objective),
                best_score,
                objective,
            ),
        }

    def recommend_best_practice(self, source_type: str) -> dict[str, Any]:
        """推荐最佳实践

        Args:
            source_type: 数据源类型

        Returns:
            最佳实践参数
        """
        best_practices = {
            "futures_minute": {
                "interval": 60,
                "timeout": 30,
                "retry_count": 3,
                "retry_delay": 5,
                "batch_size": 100,
            },
            "stock_minute": {
                "interval": 60,
                "timeout": 30,
                "retry_count": 3,
                "retry_delay": 5,
                "batch_size": 50,
            },
            "news_rss": {
                "interval": 600,
                "timeout": 15,
                "retry_count": 2,
                "retry_delay": 3,
                "batch_size": 20,
            },
            "macro_global": {
                "interval": 14400,
                "timeout": 60,
                "retry_count": 3,
                "retry_delay": 10,
                "batch_size": 10,
            },
        }

        params = best_practices.get(source_type, {
            "interval": 300,
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 5,
            "batch_size": 50,
        })

        return {
            "source_type": source_type,
            "recommended_params": params,
            "description": self._get_best_practice_description(source_type),
        }

    def _evaluate_params(self, params: dict[str, Any], objective: str) -> float:
        """评估参数配置（模拟）

        实际应该运行采集任务并测量指标
        """
        # 模拟评估逻辑
        interval = params.get("interval", 300)
        timeout = params.get("timeout", 30)
        retry_count = params.get("retry_count", 3)

        if objective == "success_rate":
            # 更多重试次数 -> 更高成功率
            # 更长超时 -> 更高成功率
            score = min(100, 70 + retry_count * 5 + timeout * 0.3)
        elif objective == "latency":
            # 更短超时 -> 更低延迟
            # 更少重试 -> 更低延迟
            score = timeout + retry_count * 2
        elif objective == "error_rate":
            # 更多重试 -> 更低错误率
            # 更长超时 -> 更低错误率
            score = max(0, 30 - retry_count * 5 - timeout * 0.2)
        else:
            score = 50.0

        return round(score, 2)

    def _generate_candidates(self, current_params: dict[str, Any]) -> list[dict[str, Any]]:
        """生成候选参数"""
        candidates = []

        # 调整 interval
        interval = current_params.get("interval", 300)
        for factor in [0.5, 0.75, 1.25, 1.5]:
            candidate = current_params.copy()
            candidate["interval"] = int(interval * factor)
            candidates.append(candidate)

        # 调整 timeout
        timeout = current_params.get("timeout", 30)
        for delta in [-10, -5, 5, 10]:
            candidate = current_params.copy()
            candidate["timeout"] = max(5, timeout + delta)
            candidates.append(candidate)

        # 调整 retry_count
        retry_count = current_params.get("retry_count", 3)
        for delta in [-1, 1]:
            candidate = current_params.copy()
            candidate["retry_count"] = max(0, retry_count + delta)
            candidates.append(candidate)

        return candidates

    def _is_better(self, new_score: float, old_score: float, objective: str) -> bool:
        """判断新分数是否更好"""
        if objective == "success_rate":
            return new_score > old_score
        else:  # latency, error_rate
            return new_score < old_score

    def _calculate_improvement(self, old_score: float, new_score: float, objective: str) -> float:
        """计算改进幅度"""
        if old_score == 0:
            return 0.0

        if objective == "success_rate":
            improvement = ((new_score - old_score) / old_score) * 100
        else:  # latency, error_rate
            improvement = ((old_score - new_score) / old_score) * 100

        return round(improvement, 2)

    def _get_best_practice_description(self, source_type: str) -> str:
        """获取最佳实践描述"""
        descriptions = {
            "futures_minute": "期货分钟数据：高频采集，短超时，适度重试",
            "stock_minute": "股票分钟数据：高频采集，短超时，适度重试",
            "news_rss": "RSS新闻：中频采集，短超时，少量重试",
            "macro_global": "宏观数据：低频采集，长超时，适度重试",
        }
        return descriptions.get(source_type, "通用配置：平衡频率、超时和重试")
