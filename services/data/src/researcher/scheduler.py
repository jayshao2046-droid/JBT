"""每小时调度器 — 11个整点 + 早晚报邮件 + 突发检测 + Mini推送"""

import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx

# psutil 改为 lazy import（可选依赖）
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .config import ResearcherConfig
from .staging import StagingManager
from .summarizer import Summarizer
from .reporter import Reporter
from .notifier import ResearcherNotifier
from .notify import DailyDigest, ResearcherEmailSender, build_morning_report_html, build_evening_report_html
from .crawler.engine import CodeCrawler, BrowserCrawler
from .crawler.source_registry import SourceRegistry
from .crawler.parsers import get_parser
from .models import SymbolResearch


class ResearcherScheduler:
    """研究员调度器（每小时执行）"""

    def __init__(self):
        self.staging_manager = StagingManager()
        self.summarizer = Summarizer()
        self.reporter = Reporter()
        self.notifier = ResearcherNotifier()
        self.code_crawler = CodeCrawler()
        self.browser_crawler = BrowserCrawler()
        self.source_registry = SourceRegistry(
            yaml_path=ResearcherConfig.REPORTS_DIR.replace("reports", "../configs/researcher_sources.yaml")
        )
        self.daily_digest = DailyDigest()
        self.email_sender = ResearcherEmailSender()

    async def execute_hourly(self, hour: int) -> Dict[str, Any]:
        """
        执行单个整点的研究

        Args:
            hour: 小时（8, 9, 10, ...）

        Returns:
            执行结果
        """
        start_time = time.time()
        hour_label = f"{hour:02d}:00"

        try:
            # 1. 资源监控
            if not self._check_resources():
                error_msg = "资源不足，暂停研究"
                await self.notifier.notify_report_fail(f"{hour:02d}", error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "hour": hour
                }

            # 2. 增量读取数据
            futures_data = self.staging_manager.get_incremental(
                ResearcherConfig.FUTURES_SYMBOLS,
                lookback_hours=24
            )

            stocks_data = self.staging_manager.get_incremental(
                ResearcherConfig.get_all_stock_symbols(),
                lookback_hours=24
            )

            # 3. 爬虫采集（带突发检测）
            crawler_stats = await self._crawl_news_with_urgent_detection(hour_label)

            # 4. LLM 归纳
            futures_researches = self._summarize_futures(futures_data, hour_label)
            stocks_researches = self._summarize_stocks(stocks_data, hour_label)

            # 5. 生成报告
            date = datetime.now().strftime("%Y-%m-%d")
            previous_summary = None  # 每小时调度不使用 previous_summary
            previous_report_id = None  # TODO: 从上期报告获取

            report = self.reporter.generate_report(
                date=date,
                segment=hour_label,
                futures_researches=futures_researches,
                stocks_researches=stocks_researches,
                crawler_stats=crawler_stats,
                previous_report_id=previous_report_id,
                previous_summary=previous_summary
            )

            # 6. 推送飞书卡片
            await self.notifier.notify_report_done(report)

            # 7. 推送到 Mini data API
            await self._push_to_data_api(report)

            # 8. 邮件日报钩子
            if hour == ResearcherConfig.EMAIL_MORNING_TRIGGER_HOUR:
                await self._send_morning_report(date)
            elif hour == ResearcherConfig.EMAIL_EVENING_TRIGGER_HOUR:
                await self._send_evening_report(date)

            elapsed = time.time() - start_time

            return {
                "success": True,
                "report_id": report.report_id,
                "hour": hour,
                "elapsed_seconds": elapsed,
                "futures_count": len(futures_researches),
                "stocks_count": len(stocks_researches),
                "crawler_stats": crawler_stats
            }

        except Exception as e:
            error_msg = str(e)
            await self.notifier.notify_report_fail(f"{hour:02d}", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "hour": hour,
                "elapsed_seconds": time.time() - start_time
            }

    async def execute_segment(self, segment: str) -> Dict[str, Any]:
        """
        LEGACY: 执行单个时段的研究（向后兼容）

        Args:
            segment: 时段（盘前/午间/盘后/夜盘）

        Returns:
            执行结果
        """
        # 映射到小时
        segment_to_hour = {
            "盘前": 8,
            "午间": 11,
            "盘后": 15,
            "夜盘": 23,
        }
        hour = segment_to_hour.get(segment, 8)
        return await self.execute_hourly(hour)

    def _check_resources(self) -> bool:
        """
        检查 Alienware 资源状态

        Returns:
            True 表示资源充足，可以继续；False 表示资源不足，暂停
        """
        if not PSUTIL_AVAILABLE:
            # psutil 未安装，跳过资源检查
            return True

        try:
            # CPU + 内存检查
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            if memory_percent > ResearcherConfig.RESOURCE_THRESHOLDS["memory_usage_max"]:
                return False

            # TODO: 检查 sim-trading 延迟（通过 Mini API）
            # sim_latency = self._check_sim_trading_latency()
            # if sim_latency > ResearcherConfig.RESOURCE_THRESHOLDS["sim_trading_latency_max"]:
            #     return False

            return True

        except Exception:
            # 检查失败，保守起见暂停
            return False

    def _check_sim_trading_latency(self) -> float:
        """检查 sim-trading 延迟（毫秒）"""
        try:
            start = time.time()
            resp = httpx.get(f"{ResearcherConfig.DATA_API_URL}/api/v1/health", timeout=5.0)
            latency_ms = (time.time() - start) * 1000
            return latency_ms if resp.status_code == 200 else 999.0
        except Exception:
            return 999.0

    @staticmethod
    def _get_market_mode() -> str:
        """
        按当前小时判断采集模式：
        - international: 外盘时段 — 境外深夜/凌晨（0-7, 20-23），以国际源为主
        - domestic:      内盘时段 — 国内交易时段（8-16），以境内源为主
        - both:          夜盘（21-23）jim10 + 国际均覆盖
        """
        h = datetime.now().hour
        # 内盘：08:00-16:00
        if 8 <= h < 16:
            return "domestic"
        # 夜盘：21:00-23:59（内外均活跃）
        if h >= 21:
            return "both"
        # 其余（0-7, 17-20）：外盘为主
        return "international"

    async def _crawl_news_with_urgent_detection(self, hour_label: str) -> Dict[str, Any]:
        """
        爬取新闻（带突发检测 + 时段智能过滤）

        - 内盘时段（08-16）: 优先境内源（domestic + both）
        - 外盘时段（0-7, 17-20）: 优先境外源（international + both）
        - 夜盘（21-23）: 境内外全量

        Args:
            hour_label: 小时标签（如 "08:00"）

        Returns:
            爬虫统计
        """
        market_mode = self._get_market_mode()
        all_sources = self.source_registry.get_active_sources("all")

        # 按时段过滤源
        if market_mode == "domestic":
            sources = [s for s in all_sources if getattr(s, "market", "both") in ("domestic", "both")]
        elif market_mode == "international":
            sources = [s for s in all_sources if getattr(s, "market", "both") in ("international", "both")]
        else:  # both（夜盘）— 全量
            sources = all_sources

        sources_crawled = 0
        articles_processed = 0
        failed_sources = []
        news_items = []

        for source in sources:
            try:
                parser_func = get_parser(source.parser)
                if not parser_func:
                    failed_sources.append(source.source_id)
                    continue

                # 根据模式选择爬虫
                if source.mode == "code":
                    result = await self.code_crawler.crawl(
                        url=source.url_pattern,
                        source_id=source.source_id,
                        parser_func=parser_func,
                        timeout=source.timeout
                    )
                else:  # browser
                    result = await self.browser_crawler.crawl(
                        url=source.url_pattern,
                        source_id=source.source_id,
                        parser_func=parser_func,
                        timeout=source.timeout
                    )

                if result.success:
                    sources_crawled += 1
                    articles_processed += 1

                    # 突发检测
                    title = result.data.get('title', '')
                    content = result.data.get('content', '')
                    if self._is_urgent(title, content):
                        # 立即推送突发卡片
                        await self.notifier.notify_urgent(
                            headline=title,
                            source=source.source_id,
                            url=source.url_pattern
                        )

                    # 收集新闻条目
                    news_items.append({
                        'source': source.source_id,
                        'title': title,
                        'summary': content[:100],
                        'time': datetime.now().strftime('%H:%M')
                    })
                else:
                    failed_sources.append(source.source_id)

            except Exception:
                failed_sources.append(source.source_id)

        return {
            "sources_crawled": sources_crawled,
            "articles_processed": articles_processed,
            "failed_sources": failed_sources,
            "news_items": news_items
        }

    def _is_urgent(self, title: str, content: str) -> bool:
        """
        检测是否为突发紧急事件

        Args:
            title: 标题
            content: 内容

        Returns:
            True 表示突发
        """
        text = (title + " " + content).lower()
        for keyword in ResearcherConfig.URGENT_KEYWORDS:
            if keyword.lower() in text:
                return True
        return False

    async def _push_to_data_api(self, report) -> bool:
        """
        推送报告到 Mini data API，供决策端消费

        Args:
            report: ResearchReport

        Returns:
            True 表示推送成功
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    ResearcherConfig.DATA_API_PUSH_URL,
                    json=report.dict(),
                    timeout=10.0
                )
                return resp.status_code == 200
        except Exception:
            # 推送失败不影响主流程
            return False

    async def _send_morning_report(self, date: str):
        """
        发送早报邮件（汇总 08:00~16:00）

        Args:
            date: 日期 YYYY-MM-DD
        """
        try:
            digest = self.daily_digest.generate_morning_digest(date)
            html = build_morning_report_html(digest['reports'], date)
            self.email_sender.send_morning_report(date, html)
        except Exception:
            pass  # 邮件发送失败不影响主流程

    async def _send_evening_report(self, date: str):
        """
        发送晚报邮件（汇总 21:00~23:00）

        Args:
            date: 日期 YYYY-MM-DD
        """
        try:
            digest = self.daily_digest.generate_evening_digest(date)
            html = build_evening_report_html(digest['reports'], date)
            self.email_sender.send_evening_report(date, html)
        except Exception:
            pass  # 邮件发送失败不影响主流程

    def _summarize_futures(self, data: Dict[str, Any], hour_label: str) -> list[SymbolResearch]:
        """归纳期货品种"""
        researches = []

        for symbol, bars in data.items():
            if not bars:
                continue

            try:
                research = self.summarizer.summarize_symbol(
                    symbol=symbol,
                    incremental_data=bars,
                    previous_summary=None,  # TODO: 从上期报告获取
                    news_items=[]  # TODO: 从爬虫结果匹配
                )
                researches.append(research)
            except Exception:
                # 归纳失败，跳过该品种
                continue

        return researches

    def _summarize_stocks(self, data: Dict[str, Any], hour_label: str) -> list[SymbolResearch]:
        """归纳股票"""
        researches = []

        for symbol, bars in data.items():
            if not bars:
                continue

            try:
                research = self.summarizer.summarize_symbol(
                    symbol=symbol,
                    incremental_data=bars,
                    previous_summary=None,
                    news_items=[]
                )
                researches.append(research)
            except Exception:
                continue

        return researches

    async def close(self):
        """关闭资源"""
        await self.browser_crawler.close()
