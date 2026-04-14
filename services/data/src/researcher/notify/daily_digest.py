"""每日日报生成器 — 早报（16:00后）+ 晚报（23:00后）"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path


class DailyDigest:
    """每日日报生成器"""

    def __init__(self):
        self.reports_dir = Path("runtime/researcher/reports")

    def generate_digest(self, date: str) -> Dict[str, Any]:
        """
        生成指定日期的日报（全天汇总）

        Args:
            date: 日期 YYYY-MM-DD

        Returns:
            日报数据
        """
        segments = ["盘前", "午间", "盘后", "夜盘"]
        reports = []

        # 读取当日所有报告
        date_dir = self.reports_dir / date
        if not date_dir.exists():
            return self._empty_digest(date)

        for segment in segments:
            report_path = date_dir / f"{segment}.json"
            if report_path.exists():
                with open(report_path, "r", encoding="utf-8") as f:
                    reports.append(json.load(f))

        if not reports:
            return self._empty_digest(date)

        # 统计执行概况
        success_count = len(reports)
        total_count = 4  # 四段
        total_elapsed = sum([r.get("elapsed_seconds", 0) for r in reports])

        # 统计分析数据
        futures_total = sum([r["futures_summary"]["symbols_covered"] for r in reports])
        stocks_total = sum([r["stocks_summary"]["symbols_covered"] for r in reports])
        articles_total = sum([r["crawler_stats"]["articles_processed"] for r in reports])

        # 提取关键建议
        suggestions = self._extract_suggestions(reports)

        return {
            "date": date,
            "success_count": success_count,
            "total_count": total_count,
            "total_elapsed": total_elapsed,
            "futures_total": futures_total,
            "stocks_total": stocks_total,
            "articles_total": articles_total,
            "suggestions": suggestions,
            "reports": reports
        }

    def generate_morning_digest(self, date: str) -> Dict[str, Any]:
        """
        生成早报（汇总 08:00~16:00 所有整点报告）

        Args:
            date: 日期 YYYY-MM-DD

        Returns:
            早报数据（包含 reports 列表）
        """
        morning_hours = [8, 9, 10, 11, 13, 14, 15, 16]
        return self._generate_hourly_digest(date, morning_hours, "早报")

    def generate_evening_digest(self, date: str) -> Dict[str, Any]:
        """
        生成晚报（汇总 21:00~23:00 所有整点报告）

        Args:
            date: 日期 YYYY-MM-DD

        Returns:
            晚报数据（包含 reports 列表）
        """
        evening_hours = [21, 22, 23]
        return self._generate_hourly_digest(date, evening_hours, "晚报")

    def _generate_hourly_digest(self, date: str, hours: List[int], digest_type: str) -> Dict[str, Any]:
        """
        生成指定小时范围的日报

        Args:
            date: 日期 YYYY-MM-DD
            hours: 小时列表（如 [8, 9, 10, ...]）
            digest_type: 日报类型（"早报" 或 "晚报"）

        Returns:
            日报数据
        """
        reports = []

        # 读取指定小时的报告
        date_dir = self.reports_dir / date
        if not date_dir.exists():
            return self._empty_hourly_digest(date, digest_type)

        for hour in hours:
            report_path = date_dir / f"{hour:02d}00.json"
            if report_path.exists():
                with open(report_path, "r", encoding="utf-8") as f:
                    report = json.load(f)
                    report['hour'] = f"{hour:02d}"  # 添加小时字段
                    reports.append(report)

        if not reports:
            return self._empty_hourly_digest(date, digest_type)

        # 统计执行概况
        success_count = len(reports)
        total_count = len(hours)
        total_elapsed = sum([r.get("elapsed_seconds", 0) for r in reports])

        # 统计分析数据
        futures_total = sum([r.get("futures_summary", {}).get("symbols_covered", 0) for r in reports])
        stocks_total = sum([r.get("stocks_summary", {}).get("symbols_covered", 0) for r in reports])
        articles_total = sum([r.get("crawler_stats", {}).get("articles_processed", 0) for r in reports])

        # 提取关键建议
        suggestions = self._extract_suggestions(reports)

        # 提取信息来源（供邮件使用）
        news_sources = self._extract_news_sources(reports)

        # 提取策略建议（供邮件使用）
        strategy_suggestions = self._extract_strategy_suggestions(reports)

        return {
            "date": date,
            "digest_type": digest_type,
            "success_count": success_count,
            "total_count": total_count,
            "total_elapsed": total_elapsed,
            "futures_total": futures_total,
            "stocks_total": stocks_total,
            "articles_total": articles_total,
            "suggestions": suggestions,
            "news_sources": news_sources,
            "strategy_suggestions": strategy_suggestions,
            "reports": reports
        }

    def _empty_digest(self, date: str) -> Dict[str, Any]:
        """空日报"""
        return {
            "date": date,
            "success_count": 0,
            "total_count": 4,
            "total_elapsed": 0.0,
            "futures_total": 0,
            "stocks_total": 0,
            "articles_total": 0,
            "suggestions": ["当日无研究报告"],
            "reports": []
        }

    def _empty_hourly_digest(self, date: str, digest_type: str) -> Dict[str, Any]:
        """空的小时日报"""
        return {
            "date": date,
            "digest_type": digest_type,
            "success_count": 0,
            "total_count": 0,
            "total_elapsed": 0.0,
            "futures_total": 0,
            "stocks_total": 0,
            "articles_total": 0,
            "suggestions": [f"{digest_type}无研究报告"],
            "news_sources": [],
            "strategy_suggestions": [],
            "reports": []
        }

    def _extract_suggestions(self, reports: List[Dict[str, Any]]) -> List[str]:
        """
        从报告中提取关键建议

        Args:
            reports: 报告列表

        Returns:
            建议列表
        """
        suggestions = []

        # 1. 提取所有变化要点
        all_changes = []
        for report in reports:
            all_changes.extend(report.get("change_highlights", []))

        if all_changes:
            suggestions.append(f"关键变化：{', '.join(all_changes[:3])}")

        # 2. 提取高信心品种
        high_conf_symbols = []
        for report in reports:
            symbols = report.get("futures_summary", {}).get("symbols", {})
            for sym, detail in symbols.items():
                if detail.get("confidence", 0) >= 0.8:
                    high_conf_symbols.append(f"{sym}({detail['trend']})")

        if high_conf_symbols:
            suggestions.append(f"高信心品种：{', '.join(high_conf_symbols[:5])}")

        # 3. 爬虫失败源
        failed_sources = []
        for report in reports:
            failed_sources.extend(report.get("crawler_stats", {}).get("failed_sources", []))

        if failed_sources:
            unique_failed = list(set(failed_sources))
            suggestions.append(f"爬虫失败源：{', '.join(unique_failed[:3])}")

        # 4. 默认建议
        if not suggestions:
            suggestions.append("当日市场平稳，无重大变化")

        return suggestions[:5]  # 最多 5 条

    def _extract_news_sources(self, reports: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        提取所有新闻来源（供邮件使用）

        Args:
            reports: 报告列表

        Returns:
            新闻来源列表 [{"source": "金十", "title": "...", "summary": "...", "time": "..."}]
        """
        news_items = []
        for report in reports:
            items = report.get("crawler_stats", {}).get("news_items", [])
            news_items.extend(items)

        return news_items[:20]  # 最多20条

    def _extract_strategy_suggestions(self, reports: List[Dict[str, Any]]) -> List[str]:
        """
        提取重大策略建议（供邮件使用）

        Args:
            reports: 报告列表

        Returns:
            策略建议列表
        """
        # TODO: 从报告中提取实际策略建议
        # 当前版本返回占位符
        return [
            "黑色系：库存拐点临近，螺纹钢短线偏弱但中期关注补库驱动",
            "贵金属：美联储鸽派信号明确，黄金维持偏多配置",
            "能源化工：原油受地缘支撑但需求端偏弱，建议观望",
        ]

    def should_send_digest(self) -> bool:
        """
        判断是否应该发送日报

        夜盘收盘后（约 02:50）发送

        Returns:
            True 表示应该发送
        """
        now = datetime.now()
        # 夜盘收盘时间：02:40，延迟 10 分钟发送
        return now.hour == 2 and 50 <= now.minute < 55
