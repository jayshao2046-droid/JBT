"""研究员报告加载器 - 从 data 服务加载研究员报告

职责：
1. 从 data 服务 API 获取最新研究员报告
2. 解析报告内容
3. 提供给 LLM pipeline 使用
"""
import logging
import httpx
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
            segment: 时段筛选（如 "15-00"），None 表示最新

        Returns:
            报告字典，包含 futures_summary, stocks_summary, crawler_stats 等字段
        """
        try:
            # Alienware API: GET /reports/latest
            url = f"{self.data_service_url}/reports/latest"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()

                data = response.json()
                # Alienware API 直接返回报告对象，不是 {success, reports} 格式
                if data and data.get("report_id"):
                    return data

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
            # Alienware API 暂不支持时间范围查询，只返回最新报告
            latest = self.get_latest_report()
            if latest:
                return [latest]
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

        # 期货市场概况
        futures_summary = report.get("futures_summary", {})
        if futures_summary.get("symbols_covered", 0) > 0:
            overview = futures_summary.get("market_overview", "")
            key_points.append(f"期货市场: {overview}")

        # 股票市场概况
        stocks_summary = report.get("stocks_summary", {})
        if stocks_summary.get("symbols_covered", 0) > 0:
            overview = stocks_summary.get("market_overview", "")
            key_points.append(f"股票市场: {overview}")

            # 强势板块
            sector_rotation = stocks_summary.get("sector_rotation", {})
            strong_sectors = sector_rotation.get("强势板块", [])
            if strong_sectors:
                key_points.append(f"强势板块: {', '.join(strong_sectors[:3])}")

        # 爬虫新闻
        crawler_stats = report.get("crawler_stats", {})
        news_items = crawler_stats.get("news_items", [])
        for item in news_items[:3]:
            title = item.get("title", "")
            if title:
                key_points.append(f"新闻: {title[:100]}")

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
        report_id = report.get("report_id", "未知")
        generated_at = report.get("generated_at", "")
        lines.append(f"# 研究员报告 - {report_id}")
        lines.append(f"生成时间: {generated_at}")
        lines.append("")

        # 期货市场
        futures_summary = report.get("futures_summary", {})
        if futures_summary.get("symbols_covered", 0) > 0:
            lines.append("## 期货市场")
            lines.append(f"覆盖品种: {futures_summary.get('symbols_covered', 0)}")
            lines.append(f"市场概况: {futures_summary.get('market_overview', '')}")
            lines.append("")

        # 股票市场
        stocks_summary = report.get("stocks_summary", {})
        if stocks_summary.get("symbols_covered", 0) > 0:
            lines.append("## 股票市场")
            lines.append(f"覆盖股票: {stocks_summary.get('symbols_covered', 0)}")
            lines.append(f"市场概况: {stocks_summary.get('market_overview', '')}")

            # 板块轮动
            sector_rotation = stocks_summary.get("sector_rotation", {})
            if sector_rotation:
                lines.append("")
                lines.append("### 板块轮动")
                for category, sectors in sector_rotation.items():
                    if sectors:
                        lines.append(f"- {category}: {', '.join(sectors)}")
            lines.append("")

        # 爬虫新闻
        crawler_stats = report.get("crawler_stats", {})
        news_items = crawler_stats.get("news_items", [])
        if news_items:
            lines.append("## 重要新闻")
            for i, item in enumerate(news_items[:10], 1):
                title = item.get("title", "")
                source = item.get("source", "")
                lines.append(f"{i}. [{source}] {title}")
            lines.append("")

        return "\n".join(lines)
