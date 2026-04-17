"""双格式报告生成 — JSON 决策版 + Markdown Jay 版"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .config import ResearcherConfig
from .daily_stats import DailyStatsTracker
from .queue_manager import QueueManager
from .models import (
    ResearchReport, SymbolResearch,
    ClassifiedReport, ReportBatch
)

logger = logging.getLogger(__name__)


class Reporter:
    """报告生成器"""

    def __init__(self):
        ResearcherConfig.ensure_dirs()
        self.stats_tracker = DailyStatsTracker(ResearcherConfig.LOGS_DIR)

        # 初始化队列管理器
        queue_dir = os.path.join(ResearcherConfig.REPORTS_DIR, ".queue")
        self.queue_manager = QueueManager(queue_dir)

        self._init_report_index()

    def _init_report_index(self):
        """初始化报告索引表（减量化，只存可检索字段）"""
        # P1-2 修复：使用 with 语句确保连接自动关闭
        with sqlite3.connect(ResearcherConfig.REPORTS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_index (
                    report_id              TEXT PRIMARY KEY,
                    date                   TEXT NOT NULL,
                    hour                   INTEGER NOT NULL,
                    segment                TEXT,
                    symbols                TEXT,
                    market_view            TEXT,
                    sources_count          INTEGER DEFAULT 0,
                    articles_count         INTEGER DEFAULT 0,
                    model                  TEXT,
                    json_path              TEXT NOT NULL,
                    created_at             TEXT NOT NULL,
                    decision_confidence    REAL DEFAULT NULL,
                    decision_reviewed_at   TEXT DEFAULT NULL,
                    decision_reason        TEXT DEFAULT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_date ON report_index(date, hour)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_symbol ON report_index(date, symbols)")
            # 迁移：为已存在的旧表补充 decision 列
            for col_def in [
                "ADD COLUMN decision_confidence  REAL DEFAULT NULL",
                "ADD COLUMN decision_reviewed_at TEXT DEFAULT NULL",
                "ADD COLUMN decision_reason      TEXT DEFAULT NULL",
            ]:
                try:
                    cursor.execute(f"ALTER TABLE report_index {col_def}")
                except Exception:
                    pass  # 列已存在
            conn.commit()

    def generate_report(
        self,
        date: str,
        segment: str,
        futures_researches: List[SymbolResearch],
        stocks_researches: List[SymbolResearch],
        crawler_stats: Dict[str, Any],
        previous_report_id: Optional[str] = None,
        previous_summary: Optional[Dict[str, Any]] = None
    ) -> ResearchReport:
        """
        生成研究报告（LEGACY - 向后兼容）

        Args:
            date: 日期 YYYY-MM-DD
            segment: 时段
            futures_researches: 期货研究列表
            stocks_researches: 股票研究列表
            crawler_stats: 爬虫统计
            previous_report_id: 上期报告ID
            previous_summary: 上期摘要

        Returns:
            ResearchReport
        """
        # 生成报告ID
        report_id = self._generate_report_id(date, segment)

        # 构建期货综述
        futures_summary = self._build_futures_summary(futures_researches)

        # 构建股票综述
        stocks_summary = self._build_stocks_summary(stocks_researches)

        # 计算变化要点
        change_highlights = self._compute_changes(
            futures_researches,
            previous_summary
        )

        # 创建报告对象
        report = ResearchReport(
            report_id=report_id,
            date=date,
            segment=segment,
            generated_at=datetime.now(),
            model="qwen3:14b",
            futures_summary=futures_summary,
            stocks_summary=stocks_summary,
            crawler_stats=crawler_stats,
            previous_report_id=previous_report_id,
            change_highlights=change_highlights
        )

        # 保存报告
        self._save_report(report)

        return report

    def generate_classified_reports(
        self,
        date: str,
        hour: int,
        futures_researches: List[SymbolResearch],
        stocks_researches: List[SymbolResearch],
        crawler_stats: Dict[str, Any]
    ) -> ReportBatch:
        """
        生成分类报告批次（按数据源分类）

        Args:
            date: 日期 YYYY-MM-DD
            hour: 小时 0-23
            futures_researches: 期货研究列表
            stocks_researches: 股票研究列表
            crawler_stats: 爬虫统计

        Returns:
            ReportBatch
        """
        batch_id = f"BATCH-{date.replace('-', '')}-{hour:02d}"
        batch = ReportBatch(
            batch_id=batch_id,
            date=date,
            hour=hour,
            generated_at=datetime.now()
        )

        # 1. 生成期货报告
        if futures_researches:
            futures_report = self._generate_futures_report(date, hour, futures_researches)
            batch.futures_report = futures_report
            batch.total_reports += 1

        # 2. 生成股票报告
        if stocks_researches:
            stocks_report = self._generate_stocks_report(date, hour, stocks_researches)
            batch.stocks_report = stocks_report
            batch.total_reports += 1

        # 3. 生成新闻报告
        news_items = crawler_stats.get("news_items", [])
        if news_items:
            news_report = self._generate_news_report(date, hour, news_items)
            batch.news_report = news_report
            batch.total_reports += 1

        # 4. 生成 RSS 报告（暂时合并到新闻）
        # TODO: 分离 RSS 数据源

        # 5. 生成情绪报告（暂时从新闻中提取）
        # TODO: 独立情绪分析

        return batch

    def _generate_futures_report(
        self,
        date: str,
        hour: int,
        researches: List[SymbolResearch]
    ) -> ClassifiedReport:
        """生成期货报告"""
        report_id = f"FUT-{date.replace('-', '')}-{hour:02d}"

        # 构建期货数据
        symbols_dict = {}
        for sr in researches:
            symbols_dict[sr.symbol] = {
                "trend": sr.trend,
                "confidence": sr.confidence,
                "key_factors": sr.key_factors,
                "overnight_context": sr.overnight_context,
                "news_highlights": sr.news_highlights,
                "position_change": sr.position_change
            }

        market_overview = self._generate_market_overview(researches, "期货")

        data = {
            "market_overview": market_overview,
            "symbols": symbols_dict,
            "trend_distribution": self._get_trend_distribution(researches)
        }

        report = ClassifiedReport(
            report_id=report_id,
            report_type="futures",
            date=date,
            hour=hour,
            generated_at=datetime.now(),
            model="qwen3:14b",
            data=data,
            symbols_covered=len(researches),
            data_points=sum(len(sr.key_factors) for sr in researches),
            confidence=sum(sr.confidence for sr in researches) / len(researches) if researches else 0.0
        )

        # 保存报告
        self._save_classified_report(report)
        return report

    def _generate_stocks_report(
        self,
        date: str,
        hour: int,
        researches: List[SymbolResearch]
    ) -> ClassifiedReport:
        """生成股票报告"""
        report_id = f"STK-{date.replace('-', '')}-{hour:02d}"

        # 提取 top movers
        top_movers = sorted(
            researches,
            key=lambda x: abs(x.confidence - 0.5),
            reverse=True
        )[:10]

        data = {
            "market_overview": self._generate_market_overview(researches, "股票"),
            "top_movers": [
                {
                    "symbol": sr.symbol,
                    "trend": sr.trend,
                    "confidence": sr.confidence,
                    "key_factors": sr.key_factors
                }
                for sr in top_movers
            ],
            "trend_distribution": self._get_trend_distribution(researches)
        }

        report = ClassifiedReport(
            report_id=report_id,
            report_type="stocks",
            date=date,
            hour=hour,
            generated_at=datetime.now(),
            model="qwen3:14b",
            data=data,
            symbols_covered=len(researches),
            data_points=len(researches),
            confidence=sum(sr.confidence for sr in researches) / len(researches) if researches else 0.0
        )

        self._save_classified_report(report)
        return report

    def _generate_news_report(
        self,
        date: str,
        hour: int,
        news_items: List[Dict[str, Any]]
    ) -> ClassifiedReport:
        """生成新闻报告"""
        report_id = f"NEWS-{date.replace('-', '')}-{hour:02d}"

        # 按来源分组
        sources_breakdown = {}
        for item in news_items:
            source = item.get("source", "unknown")
            if source not in sources_breakdown:
                sources_breakdown[source] = []
            sources_breakdown[source].append(item)

        data = {
            "total_items": len(news_items),
            "sources_breakdown": {
                source: len(items) for source, items in sources_breakdown.items()
            },
            "items": news_items[:50],  # 最多保存 50 条
            "urgent_items": [item for item in news_items if item.get("is_urgent", False)]
        }

        report = ClassifiedReport(
            report_id=report_id,
            report_type="news",
            date=date,
            hour=hour,
            generated_at=datetime.now(),
            model="crawler",
            data=data,
            symbols_covered=0,
            data_points=len(news_items),
            confidence=1.0 if news_items else 0.0
        )

        self._save_classified_report(report)
        return report

    def _get_trend_distribution(self, researches: List[SymbolResearch]) -> Dict[str, int]:
        """获取趋势分布"""
        trend_counts = {}
        for sr in researches:
            trend_counts[sr.trend] = trend_counts.get(sr.trend, 0) + 1
        return trend_counts

    def _save_classified_report(self, report: ClassifiedReport):
        """保存分类报告到文件"""
        # 创建日期目录
        date_dir = os.path.join(ResearcherConfig.REPORTS_DIR, report.date)
        os.makedirs(date_dir, exist_ok=True)

        # 保存 JSON 文件：futures.json, stocks.json, news.json
        filename = f"{report.report_type}_{report.hour}.json"
        json_path = os.path.join(date_dir, filename)

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            # 记录文件路径
            report.file_path = json_path

            # 添加到待读队列
            metadata = {
                "report_type": report.report_type,
                "date": report.date,
                "hour": report.hour,
                "symbols_covered": report.symbols_covered,
                "confidence": report.confidence
            }
            self.queue_manager.add_to_queue(report.report_id, json_path, metadata)

            logger.info(
                f"[REPORT_SAVE] 报告已保存: {report.report_id} -> {json_path} "
                f"(类型={report.report_type}, 品种数={report.symbols_covered})"
            )

        except Exception as e:
            logger.error(f"[REPORT_SAVE] 保存失败: {report.report_id}, {e}", exc_info=True)
            raise

    def _generate_report_id(self, date: str, segment: str) -> str:
        """生成报告ID（segment 保留原始格式如 '12:00'，文件名中用 '-' 替换 ':'）"""
        date_str = date.replace("-", "")
        safe_segment = segment.replace(":", "-")  # Windows 文件名不允许 ':'
        report_dir = os.path.join(ResearcherConfig.REPORTS_DIR, date)
        seq = 1
        if os.path.exists(report_dir):
            # 按安全文件名计数已存在的同时段报告
            existing = [
                f for f in os.listdir(report_dir)
                if f.startswith(safe_segment) and f.endswith(".json")
            ]
            if existing:
                seq = len(existing) + 1

        return f"RPT-{date_str}-{segment}-{seq:03d}"

    def _build_futures_summary(self, researches: List[SymbolResearch]) -> Dict[str, Any]:
        """构建期货综述"""
        symbols_dict = {}
        for sr in researches:
            symbols_dict[sr.symbol] = {
                "trend": sr.trend,
                "confidence": sr.confidence,
                "key_factors": sr.key_factors,
                "overnight_context": sr.overnight_context,
                "news_highlights": sr.news_highlights,
                "position_change": sr.position_change
            }

        # 市场综述
        market_overview = self._generate_market_overview(researches, "期货")

        return {
            "symbols_covered": len(researches),
            "market_overview": market_overview,
            "symbols": symbols_dict
        }

    def _build_stocks_summary(self, researches: List[SymbolResearch]) -> Dict[str, Any]:
        """构建股票综述"""
        # 提取 top movers
        top_movers = sorted(
            researches,
            key=lambda x: abs(x.confidence - 0.5),
            reverse=True
        )[:10]

        # 板块轮动（简化版，实际需要板块分类）
        sector_rotation = {
            "强势板块": [],
            "弱势板块": []
        }

        return {
            "symbols_covered": len(researches),
            "market_overview": self._generate_market_overview(researches, "股票"),
            "top_movers": [
                {
                    "symbol": sr.symbol,
                    "trend": sr.trend,
                    "confidence": sr.confidence
                }
                for sr in top_movers
            ],
            "sector_rotation": sector_rotation
        }

    def _generate_market_overview(self, researches: List[SymbolResearch], asset_type: str) -> str:
        """生成市场综述"""
        if not researches:
            return f"{asset_type}市场无新增数据"

        # 统计趋势分布
        trend_counts = {}
        for sr in researches:
            trend_counts[sr.trend] = trend_counts.get(sr.trend, 0) + 1

        # 构建综述
        overview_parts = [
            f"{asset_type}市场共覆盖 {len(researches)} 个品种。",
            f"趋势分布：{', '.join([f'{k} {v}个' for k, v in trend_counts.items()])}。"
        ]

        # 高信心品种
        high_conf = [sr for sr in researches if sr.confidence >= 0.7]
        if high_conf:
            overview_parts.append(f"高信心品种（≥0.7）：{', '.join([sr.symbol for sr in high_conf])}。")

        return " ".join(overview_parts)

    def _compute_changes(
        self,
        current_researches: List[SymbolResearch],
        previous_summary: Optional[Dict[str, Any]]
    ) -> List[str]:
        """计算变化要点"""
        if not previous_summary:
            return []

        changes = []
        prev_symbols = previous_summary.get("symbols", {})

        for sr in current_researches:
            if sr.symbol in prev_symbols:
                prev = prev_symbols[sr.symbol]
                prev_trend = prev.get("trend")

                if prev_trend and prev_trend != sr.trend:
                    changes.append(f"{sr.symbol} 从 {prev_trend} 转 {sr.trend}")

        return changes[:10]  # 最多 10 条

    def _save_report(self, report: ResearchReport):
        """保存报告到文件（safe_segment 避免 Windows 路径中 ':' 非法字符）"""
        safe_segment = report.segment.replace(":", "-")  # e.g. "12:00" → "12-00"

        # 创建日期目录
        date_dir = os.path.join(ResearcherConfig.REPORTS_DIR, report.date)
        os.makedirs(date_dir, exist_ok=True)

        # 保存 JSON 决策版
        json_path = os.path.join(date_dir, f"{safe_segment}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.dict(), f, ensure_ascii=False, indent=2, default=str)

        # 保存 Markdown Jay 版
        md_path = os.path.join(date_dir, f"{safe_segment}.md")
        md_content = self._generate_markdown(report)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 写入减量化索引
        self._index_report(report, json_path)

    def _index_report(self, report: ResearchReport, json_path: str):
        """将报告可检索字段写入 report_index 表"""
        symbols_list = list(report.futures_summary.get("symbols", {}).keys())
        symbols_json = json.dumps(symbols_list, ensure_ascii=False)
        market_view = report.futures_summary.get("market_overview", "")[:200]
        sources_count = report.crawler_stats.get("sources_crawled", 0)
        articles_count = report.crawler_stats.get("articles_processed", 0)

        # 从 segment 解析小时（segment 格式如 "06" 或 "盘前"）
        try:
            hour = int(report.segment)
        except (ValueError, TypeError):
            hour = report.generated_at.hour

        try:
            # P1-2 修复：使用 with 语句确保连接自动关闭
            with sqlite3.connect(ResearcherConfig.REPORTS_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO report_index
                        (report_id, date, hour, segment, symbols, market_view,
                         sources_count, articles_count, model, json_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id,
                    report.date,
                    hour,
                    report.segment,
                    symbols_json,
                    market_view,
                    sources_count,
                    articles_count,
                    report.model,
                    json_path,
                    report.generated_at.isoformat(),
                ))
                conn.commit()
        except Exception:
            pass  # 索引写入失败不阻断主流程

    def _generate_markdown(self, report: ResearchReport) -> str:
        """生成 Markdown Jay 版"""
        lines = [
            f"# 研究员报告 — {report.date} {report.segment}",
            f"",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**模型**: {report.model}",
            f"",
            f"## 期货市场",
            f"",
            f"{report.futures_summary.get('market_overview', '')}",
            f"",
        ]

        # 期货品种详情（只展示高信心品种）
        futures_symbols = report.futures_summary.get("symbols", {})
        high_conf_futures = [
            (sym, detail) for sym, detail in futures_symbols.items()
            if detail.get("confidence", 0) >= 0.7
        ]

        if high_conf_futures:
            lines.append("### 高信心品种")
            lines.append("")
            for sym, detail in high_conf_futures:
                lines.append(f"**{sym}**: {detail['trend']} (信心 {detail['confidence']:.2f})")
                if detail.get("key_factors"):
                    lines.append(f"- 关键因素: {', '.join(detail['key_factors'])}")
                if detail.get("overnight_context"):
                    lines.append(f"- 隔夜背景: {detail['overnight_context']}")
                lines.append("")

        # 股票市场
        lines.append("## 股票市场")
        lines.append("")
        lines.append(report.stocks_summary.get("market_overview", ""))
        lines.append("")

        # Top movers
        top_movers = report.stocks_summary.get("top_movers", [])
        if top_movers:
            lines.append("### Top Movers")
            lines.append("")
            for mover in top_movers[:5]:
                lines.append(f"- {mover['symbol']}: {mover['trend']} (信心 {mover['confidence']:.2f})")
            lines.append("")

        # 变化要点
        if report.change_highlights:
            lines.append("## 变化要点")
            lines.append("")
            for change in report.change_highlights:
                lines.append(f"- {change}")
            lines.append("")

        # 爬虫统计
        lines.append("## 爬虫统计")
        lines.append("")
        lines.append(f"- 采集源数: {report.crawler_stats.get('sources_crawled', 0)}")
        lines.append(f"- 文章数: {report.crawler_stats.get('articles_processed', 0)}")
        if report.crawler_stats.get("failed_sources"):
            lines.append(f"- 失败源: {', '.join(report.crawler_stats['failed_sources'])}")
        lines.append("")

        return "\n".join(lines)

    def get_latest_report(self) -> Optional[ResearchReport]:
        """获取最新报告"""
        # 遍历 reports 目录，找到最新的报告
        if not os.path.exists(ResearcherConfig.REPORTS_DIR):
            return None

        all_reports = []
        for date_dir in os.listdir(ResearcherConfig.REPORTS_DIR):
            date_path = os.path.join(ResearcherConfig.REPORTS_DIR, date_dir)
            if os.path.isdir(date_path):
                for segment_file in os.listdir(date_path):
                    if segment_file.endswith(".json"):
                        report_path = os.path.join(date_path, segment_file)
                        with open(report_path, "r", encoding="utf-8") as f:
                            report_data = json.load(f)
                            all_reports.append(report_data)

        if not all_reports:
            return None

        # 按生成时间排序
        all_reports.sort(key=lambda x: x["generated_at"], reverse=True)
        latest = all_reports[0]

        return ResearchReport(**latest)
