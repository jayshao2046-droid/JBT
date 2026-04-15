"""研究员报告评分器 - 评估报告对交易决策的价值

职责：
1. 评估报告的时效性
2. 评估报告的相关性（与当前持仓/关注品种）
3. 评估报告的重要性（事件级别）
4. 计算综合评分
"""
import logging
from typing import Dict, List, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResearcherScorer:
    """研究员报告评分器"""

    def __init__(self):
        # 事件类型权重
        self.event_weights = {
            "K线异动": 0.9,
            "重大新闻": 0.8,
            "库存变化": 0.7,
            "仓单变化": 0.6,
            "一般新闻": 0.4,
        }

    def score_report(
        self,
        report: Dict,
        watched_symbols: Set[str] = None,
        current_positions: Set[str] = None
    ) -> float:
        """综合评分

        Args:
            report: 报告字典
            watched_symbols: 关注的品种集合
            current_positions: 当前持仓品种集合

        Returns:
            评分 (0-1)
        """
        if watched_symbols is None:
            watched_symbols = set()
        if current_positions is None:
            current_positions = set()

        # 时效性评分 (0-1)
        timeliness_score = self._score_timeliness(report)

        # 相关性评分 (0-1)
        relevance_score = self._score_relevance(
            report, watched_symbols, current_positions
        )

        # 重要性评分 (0-1)
        importance_score = self._score_importance(report)

        # 加权综合
        final_score = (
            timeliness_score * 0.3 +
            relevance_score * 0.4 +
            importance_score * 0.3
        )

        return final_score

    def _score_timeliness(self, report: Dict) -> float:
        """评估时效性

        Args:
            report: 报告字典

        Returns:
            时效性评分 (0-1)
        """
        try:
            timestamp_str = report.get("timestamp", "")
            if not timestamp_str:
                return 0.5  # 无时间戳，给中等分

            report_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.now(report_time.tzinfo)
            age_hours = (now - report_time).total_seconds() / 3600

            # 1 小时内: 1.0
            # 3 小时内: 0.8
            # 6 小时内: 0.6
            # 12 小时内: 0.4
            # 24 小时内: 0.2
            # 超过 24 小时: 0.1
            if age_hours < 1:
                return 1.0
            elif age_hours < 3:
                return 0.8
            elif age_hours < 6:
                return 0.6
            elif age_hours < 12:
                return 0.4
            elif age_hours < 24:
                return 0.2
            else:
                return 0.1

        except Exception as e:
            logger.warning(f"Failed to score timeliness: {e}")
            return 0.5

    def _score_relevance(
        self,
        report: Dict,
        watched_symbols: Set[str],
        current_positions: Set[str]
    ) -> float:
        """评估相关性

        Args:
            report: 报告字典
            watched_symbols: 关注的品种集合
            current_positions: 当前持仓品种集合

        Returns:
            相关性评分 (0-1)
        """
        analyses = report.get("analyses", [])
        if not analyses:
            return 0.0

        total_weight = 0.0
        relevant_weight = 0.0

        for analysis in analyses:
            symbol = analysis.get("symbol", "")
            event_type = analysis.get("event_type", "")
            weight = self.event_weights.get(event_type, 0.5)

            total_weight += weight

            # 持仓品种权重 x2
            if symbol in current_positions:
                relevant_weight += weight * 2.0
            # 关注品种权重 x1
            elif symbol in watched_symbols:
                relevant_weight += weight * 1.0

        if total_weight == 0:
            return 0.0

        # 归一化到 0-1
        score = min(relevant_weight / total_weight, 1.0)
        return score

    def _score_importance(self, report: Dict) -> float:
        """评估重要性

        Args:
            report: 报告字典

        Returns:
            重要性评分 (0-1)
        """
        analyses = report.get("analyses", [])
        if not analyses:
            return 0.0

        # 统计各类事件数量
        event_counts = {}
        for analysis in analyses:
            event_type = analysis.get("event_type", "")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # 加权求和
        total_score = 0.0
        for event_type, count in event_counts.items():
            weight = self.event_weights.get(event_type, 0.5)
            total_score += weight * count

        # 归一化（假设 10 个高权重事件为满分）
        normalized_score = min(total_score / 10.0, 1.0)
        return normalized_score

    def filter_high_value_reports(
        self,
        reports: List[Dict],
        watched_symbols: Set[str] = None,
        current_positions: Set[str] = None,
        threshold: float = 0.6
    ) -> List[Dict]:
        """筛选高价值报告

        Args:
            reports: 报告列表
            watched_symbols: 关注的品种集合
            current_positions: 当前持仓品种集合
            threshold: 评分阈值

        Returns:
            高价值报告列表（带评分）
        """
        scored_reports = []

        for report in reports:
            score = self.score_report(report, watched_symbols, current_positions)
            if score >= threshold:
                report_with_score = report.copy()
                report_with_score["_score"] = score
                scored_reports.append(report_with_score)

        # 按评分降序排序
        scored_reports.sort(key=lambda x: x["_score"], reverse=True)
        return scored_reports
