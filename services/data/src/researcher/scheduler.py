"""每小时调度器 — 11个整点 + 早晚报邮件 + 突发检测 + decision推送"""

import asyncio
import os
import time
import logging
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
from .report_reviewer import ReportReviewer
from .notify import DailyDigest, ResearcherEmailSender, build_morning_report_html, build_evening_report_html
from .crawler.engine import CodeCrawler, BrowserCrawler
from .crawler.source_registry import SourceRegistry
from .crawler.parsers import get_parser
from .models import SymbolResearch, ReportBatch

logger = logging.getLogger(__name__)


class ResearcherScheduler:
    """研究员调度器（每小时执行）"""

    def __init__(self, queue_manager=None):
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
        self.reviewer = ReportReviewer(
            feishu_webhook=self.notifier.feishu_webhook,
            stats_tracker=self.reporter.stats_tracker,
        )
        self.queue_manager = queue_manager
        # 服务启动时记录到当日统计
        self.reporter.stats_tracker.record_startup()

        # 尝试注册 2h 健康度飞书报告
        try:
            from .researcher_health import ResearcherHealth
            self.health_reporter = ResearcherHealth(
                feishu_webhook=self.notifier.feishu_webhook,
                stats_tracker=self.reporter.stats_tracker,
            )
        except ImportError as e:
            # Bug-2 修复：捕获具体的导入错误
            logger.warning(f"ResearcherHealth module not available: {e}")
            self.health_reporter = None
        except (AttributeError, TypeError) as e:
            # Bug-2 修复：捕获初始化错误
            logger.error(f"Failed to initialize health reporter: {e}", exc_info=True)
            self.health_reporter = None

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

            # 5. 生成分类报告（按数据源）
            date = datetime.now().strftime("%Y-%m-%d")

            report_batch = self.reporter.generate_classified_reports(
                date=date,
                hour=hour,
                futures_researches=futures_researches,
                stocks_researches=stocks_researches,
                crawler_stats=crawler_stats
            )

            # 6. 推送飞书卡片（汇总通知）
            await self.notifier.notify_batch_done(report_batch)

            # 7. 推送到 Studio decision 触发 phi4 评级
            push_success = await self._push_to_decision(report_batch)

            # 8. 加入队列（供 decision 标记已读）
            if push_success and self.queue_manager:
                batch_file = os.path.join(
                    ResearcherConfig.REPORTS_DIR,
                    date,
                    f"{hour:02d}-00.json"
                )
                self.queue_manager.add_report(
                    report_id=report_batch.batch_id,
                    file_path=batch_file
                )
                logger.info(f"[QUEUE] 报告已加入队列: {report_batch.batch_id}")

            # 9. 报告已落盘到 D:\researcher_reports（phi4 直接读取，不推送 Mini）
            logger.info(f"[SAVE] 批次报告已保存: {report_batch.batch_id}, 共 {report_batch.total_reports} 份")

            # 9. 邮件日报钩子
            if hour == ResearcherConfig.EMAIL_MORNING_TRIGGER_HOUR:
                await self._send_morning_report(date)
            elif hour == ResearcherConfig.EMAIL_EVENING_TRIGGER_HOUR:
                await self._send_evening_report(date)

            # 9. 研究员健康度报告（每 HEALTH_INTERVAL_HOURS 整点触发）
            if self.health_reporter and hour % ResearcherConfig.HEALTH_INTERVAL_HOURS == 0:
                try:
                    await self.health_reporter.send_health_card()
                except (httpx.HTTPError, asyncio.TimeoutError) as e:
                    # Bug-2 修复：捕获具体的网络错误
                    logger.warning(f"Health report push failed (network): {e}")
                except Exception as e:
                    # Bug-2 修复：捕获其他异常并记录详情
                    logger.error(f"Health report push failed (unexpected): {e}", exc_info=True)

            elapsed = time.time() - start_time

            # 记录每日统计（成功路径）
            safe_seg = f"{hour:02d}-00"
            _json_path = os.path.join(
                ResearcherConfig.REPORTS_DIR,
                date,
                f"{safe_seg}.json",
            )
            self.reporter.stats_tracker.record_report(
                hour=hour,
                report_id=report_batch.batch_id,
                json_path=_json_path,
                elapsed_s=elapsed,
                success=True,
            )

            return {
                "success": True,
                "report_id": report_batch.batch_id,
                "hour": hour,
                "elapsed_seconds": elapsed,
                "futures_count": len(futures_researches),
                "stocks_count": len(stocks_researches),
                "crawler_stats": crawler_stats
            }

        except Exception as e:
            error_msg = str(e)
            await self.notifier.notify_report_fail(f"{hour:02d}", error_msg)
            # 记录每日统计（失败路径）
            self.reporter.stats_tracker.record_report(
                hour=hour,
                report_id="",
                json_path="",
                elapsed_s=time.time() - start_time,
                success=False,
            )
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

        except Exception as e:
            # 安全修复：P2-1 - 记录异常详情
            logger.error(f"Health check failed: {e}", exc_info=True)
            # 检查失败，保守起见暂停
            return False

    def _check_sim_trading_latency(self) -> float:
        """检查 sim-trading 延迟（毫秒）"""
        try:
            start = time.time()
            resp = httpx.get(f"{ResearcherConfig.DATA_API_URL}/api/v1/health", timeout=ResearcherConfig.HTTP_TIMEOUT_SHORT)
            latency_ms = (time.time() - start) * 1000
            return latency_ms if resp.status_code == 200 else 999.0
        except Exception as e:
            # 安全修复：P2-1 - 记录异常详情
            logger.warning(f"Latency check failed: {e}")
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

            except Exception as e:
                # 安全修复：P2-1 - 记录异常详情
                logger.error(f"Crawl failed for {source.source_id}: {e}", exc_info=True)
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
        推送报告到 Mini data API，供决策端消费。
        推送成功且 PUSH_RETENTION_LOCAL=False 时删除 Alienware 本地文件。

        Args:
            report: ResearchReport

        Returns:
            True 表示推送成功
        """
        try:
            logger.info(f"[PUSH] 开始推送报告到 Mini: {ResearcherConfig.DATA_API_PUSH_URL}")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    ResearcherConfig.DATA_API_PUSH_URL,
                    json=report.model_dump(mode='json'),
                    timeout=ResearcherConfig.HTTP_TIMEOUT_MEDIUM,
                )
                success = resp.status_code in (200, 201)
                logger.info(f"[PUSH] 推送响应: status={resp.status_code}, success={success}")

            if success and not ResearcherConfig.PUSH_RETENTION_LOCAL:
                # 推送成功后删除本地 JSON/MD 文件
                safe_segment = report.segment.replace(":", "-")
                date_dir = os.path.join(ResearcherConfig.REPORTS_DIR, report.date)
                for ext in (".json", ".md"):
                    local_path = os.path.join(date_dir, f"{safe_segment}{ext}")
                    try:
                        if os.path.exists(local_path):
                            os.remove(local_path)
                            logger.info(f"[PUSH] 删除本地文件: {local_path}")
                    except Exception:
                        pass  # 删除失败不影响主流程

            return success
        except Exception as e:
            # 推送失败不影响主流程，本地文件保留
            logger.error(f"[PUSH] 推送失败: {e}")
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
        logger.info(f"[SUMMARIZE] 开始归纳期货，共 {len(data)} 个品种")
        researches = []

        for symbol, bars in data.items():
            if not bars:
                logger.warning(f"[SUMMARIZE] 期货 {symbol} 数据为空，跳过")
                continue

            try:
                research = self.summarizer.summarize_symbol(
                    symbol=symbol,
                    incremental_data=bars,
                    previous_summary=None,  # TODO: 从上期报告获取
                    news_items=[]  # TODO: 从爬虫结果匹配
                )
                researches.append(research)
            except Exception as e:
                # 归纳失败，跳过该品种
                logger.error(f"[SUMMARIZE] 期货归纳失败 {symbol}: {e}", exc_info=True)
                continue

        return researches

    def _summarize_stocks(self, data: Dict[str, Any], hour_label: str) -> list[SymbolResearch]:
        """归纳股票"""
        logger.info(f"[SUMMARIZE] 开始归纳股票，共 {len(data)} 个标的")
        researches = []

        for symbol, bars in data.items():
            if not bars:
                logger.warning(f"[SUMMARIZE] 股票 {symbol} 数据为空，跳过")
                continue

            try:
                research = self.summarizer.summarize_symbol(
                    symbol=symbol,
                    incremental_data=bars,
                    previous_summary=None,
                    news_items=[]
                )
                researches.append(research)
            except Exception as e:
                # 归纳失败，跳过该品种
                logger.error(f"[SUMMARIZE] 股票归纳失败 {symbol}: {e}", exc_info=True)
                continue

        return researches

    async def _push_to_decision(self, batch: ReportBatch) -> bool:
        """
        推送报告批次到 Studio decision，触发 phi4 评级

        Args:
            batch: 报告批次

        Returns:
            True 表示推送成功
        """
        decision_url = os.getenv("DECISION_API_URL", "http://192.168.31.142:8104")
        evaluate_endpoint = f"{decision_url}/api/v1/evaluate"

        try:
            logger.info(f"[PUSH] 开始推送报告批次到 decision: {evaluate_endpoint}")

            # 使用 model_dump_json() 确保 datetime 正确序列化
            import json
            payload = json.loads(batch.model_dump_json())

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    evaluate_endpoint,
                    json=payload,
                    timeout=30.0,
                )
                success = resp.status_code in (200, 201)
                logger.info(f"[PUSH] decision 响应: status={resp.status_code}, success={success}")
                return success

        except Exception as e:
            logger.error(f"[PUSH] 推送到 decision 失败: {e}", exc_info=True)
            return False

    async def close(self):
        """关闭资源"""
        await self.browser_crawler.close()
