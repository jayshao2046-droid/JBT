"""研究员报告加载器 - 从 data 服务加载研究员报告

职责：
1. 从 data 服务 API 获取最新研究员报告
2. 解析报告内容
3. 提供给 LLM pipeline 使用
"""
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResearcherLoader:
    """研究员报告加载器"""

    def __init__(self, data_service_url: str = "http://192.168.31.76:8105"):
        self.data_service_url = data_service_url
        self.api_endpoint = f"{data_service_url}/api/v1/researcher/reports"

    def get_latest_report(self, segment: Optional[str] = None) -> Optional[Dict]:
        """获取最新报告

        Args:
            segment: 时段筛选（盘前/午间/盘后/夜盘收盘），None 表示最新

        Returns:
            报告字典，包含 summary, analyses, timestamp 等字段
        """
        try:
            params = {}
            if segment:
                params["segment"] = segment

            response = requests.get(
                self.api_endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            if data.get("success") and data.get("reports"):
                return data["reports"][0]  # 返回最新的一份

            return None

        except Exception as e:
            logger.error(f"Failed to load researcher report: {e}")
            return None

    def get_reports_since(self, hours: int = 24) -> List[Dict]:
        """获取最近 N 小时的所有报告

        Args:
            hours: 时间范围（小时）

        Returns:
            报告列表
        """
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            params = {
                "since": since_time.isoformat(),
                "limit": 100
            }

            response = requests.get(
                self.api_endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                return data.get("reports", [])

            return []

        except Exception as e:
            logger.error(f"Failed to load researcher reports: {e}")
            return []

    def extract_key_points(self, report: Dict) -> List[str]:
        """从报告中提取关键要点

        Args:
            report: 报告字典

        Returns:
            关键要点列表
        """
        key_points = []

        # 从摘要中提取
        summary = report.get("summary", "")
        if summary:
            key_points.append(f"市场概况: {summary}")

        # 从分析列表中提取
        analyses = report.get("analyses", [])
        for analysis in analyses[:5]:  # 最多取前 5 条
            event_type = analysis.get("event_type", "")
            content = analysis.get("content", "")
            if content:
                key_points.append(f"{event_type}: {content[:200]}")

        return key_points

    def format_for_llm(self, report: Dict) -> str:
        """格式化报告供 LLM 使用

        Args:
            report: 报告字典

        Returns:
            格式化后的文本
        """
        lines = []

        # 标题
        segment = report.get("segment", "未知时段")
        timestamp = report.get("timestamp", "")
        lines.append(f"# 研究员报告 - {segment}")
        lines.append(f"时间: {timestamp}")
        lines.append("")

        # 摘要
        summary = report.get("summary", "")
        if summary:
            lines.append("## 市场概况")
            lines.append(summary)
            lines.append("")

        # 关键分析
        analyses = report.get("analyses", [])
        if analyses:
            lines.append("## 关键事件")
            for i, analysis in enumerate(analyses[:10], 1):
                event_type = analysis.get("event_type", "")
                symbol = analysis.get("symbol", "")
                content = analysis.get("content", "")

                lines.append(f"{i}. [{event_type}] {symbol}")
                lines.append(f"   {content}")
                lines.append("")

        return "\n".join(lines)
