"""流式研究员调度器 — 24/7 持续爬取 + 逐条研报 + K线盘中分析 + 累计数据链"""

import asyncio
import os
import time
import json
import logging
from datetime import datetime, timedelta
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
from .health_monitor import HealthMonitor
from .crawler.engine import CodeCrawler, BrowserCrawler
from .crawler.source_registry import SourceRegistry
from .crawler.parsers import get_parser
from .crawler.anti_detect import AntiDetect
from .models import SymbolResearch, ReportBatch
from .dedup import ArticleDedup
from .kline_analyzer import KlineAnalyzer, is_trading_hours, get_trading_session, _extract_short_symbol, SYMBOL_CN_NAMES

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
            yaml_path=os.path.join(os.path.dirname(__file__), "..", "..", "configs", "researcher_sources.yaml")
        )
        self.daily_digest = DailyDigest()
        self.email_sender = ResearcherEmailSender()
        self.reviewer = ReportReviewer(
            feishu_webhook=self.notifier.feishu_webhook,
            stats_tracker=self.reporter.stats_tracker,
        )
        self.queue_manager = queue_manager
        self.dedup = ArticleDedup()
        self.anti_detect = AntiDetect()
        self.kline_analyzer = KlineAnalyzer()
        self._cycle_count = 0
        self._today_articles: List[Dict] = []  # 当日累计文章研报（内存缓存）
        self._today_kline_reports: List[Dict] = []  # 当日K线分析报告
        self._last_kline_time: Optional[datetime] = None  # 上次K线分析时间
        self._email_morning_sent: Optional[str] = None  # 最后一次发送早报的日期（YYYY-MM-DD）
        self._email_evening_sent: Optional[str] = None  # 最后一次发送晚报的日期（YYYY-MM-DD）
        # 4段日报发送记录（key: "08"/"13"/"20"/"00" → 最后发送日期）
        self._email_sent: Dict[str, Optional[str]] = {"08": None, "13": None, "20": None, "00": None}
        # 服务启动时记录到当日统计
        self.reporter.stats_tracker.record_startup()

        # 健康监控（飞书报警）
        self.health_monitor = HealthMonitor(
            alert_webhook=self.notifier.feishu_alert_webhook,
            info_webhook=self.notifier.feishu_webhook,
        )

        # 尝试注册 2h 健康度飞书报告（旧模块，兼容）
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
                self.queue_manager.add_to_queue(
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
        按当前时间和交易日历判断采集模式：
        - domestic:      内盘时段 — 国内交易时段（交易日 08:00-16:00），境内源为主
        - both:          夜盘时段（21:00-23:59，且明日为交易日），境内外全量
        - international: 其余时段（含周末/节假日白天、外盘时段），境外源为主

        注意：周末/节假日白天即使时刻在 08-16，也不返回 domestic，
        以避免爬取无意义的国内盘面源。
        """
        from .trading_calendar import is_trading_day, has_night_session
        now = datetime.now()
        h = now.hour
        # 内盘：交易日 08:00-16:00 → 优先境内源
        if is_trading_day(now) and 8 <= h < 16:
            return "domestic"
        # 夜盘：21:00-23:59，且明日为交易日（有夜盘）→ 境内外全量
        if h >= 21 and has_night_session(now):
            return "both"
        # 非交易日白天（周末/节假日 08:00-20:59）：新闻不停歇，境内外全量
        if not is_trading_day(now) and 8 <= h < 21:
            return "both"
        # 其余：交易日收盘后 17-20、深夜 0-7 → 境外源为主
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
        all_sources = self.source_registry.get_active_sources(None)
        logger.info(f"[CRAWL] market_mode={market_mode}, all_sources={len(all_sources)}")

        # 按时段过滤源
        if market_mode == "domestic":
            sources = [s for s in all_sources if getattr(s, "market", "both") in ("domestic", "both")]
        elif market_mode == "international":
            sources = [s for s in all_sources if getattr(s, "market", "both") in ("international", "both")]
        else:  # both（夜盘）— 全量
            sources = all_sources

        logger.info(f"[CRAWL] 过滤后 sources={len(sources)}, ids={[s.source_id for s in sources]}")

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
                    title = result.title or ''
                    content = result.content or ''
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

    # ═══════════════════════════════════════════════════════════════════════
    # 流式循环模式 — 替代 execute_hourly 的新调度入口
    # ═══════════════════════════════════════════════════════════════════════

    async def execute_stream_cycle(self) -> Dict[str, Any]:
        """
        执行一次流式循环：
        1. 爬取所有源 → 提取多文章 → 去重 → 逐条 LLM 分析 → 保存研报
        2. 盘中时段额外执行 K 线技术分析
        3. 汇总推送到 decision
        4. 每日零点重置累计缓存

        Returns:
            StreamCycleResult 风格的字典
        """
        self._cycle_count += 1
        start_time = time.time()
        now = datetime.now()
        errors = []

        # 跨日重置
        today = now.strftime("%Y-%m-%d")
        if self._today_articles and self._today_articles[0].get("date") != today:
            logger.info(f"[STREAM] 跨日重置: {self._today_articles[0].get('date')} → {today}")
            self._today_articles = []
            self._today_kline_reports = []
            self._last_kline_time = None

        # 资源检查
        if not self._check_resources():
            return {
                "cycle_id": self._cycle_count, "timestamp": now.isoformat(),
                "mode": "paused", "new_articles": 0, "kline_reports": 0,
                "pushed_to_decision": 0, "errors": ["资源不足，暂停"], "elapsed_seconds": 0,
            }

        # ── 阶段1: 流式新闻爬取 + 逐条分析 ──
        new_articles = await self._crawl_stream_with_dedup()
        logger.info(f"[STREAM] 周期 {self._cycle_count}: 新文章 {len(new_articles)} 条")

        # 逐条 LLM 分析
        analyzed = []
        total = len(new_articles)
        for idx, art in enumerate(new_articles, 1):
            try:
                src = art.get("source_id", "?")
                title_short = (art.get("title") or "")[:40]
                logger.info(f"[ANALYZE] ({idx}/{total}) [{src}] {title_short}...")
                report = await self._analyze_single_article(art)
                if report:
                    analyzed.append(report)
                    self._today_articles.append(report)
                    # 保存单篇研报
                    self._save_article_report(report, today)
            except Exception as e:
                errors.append(f"分析失败 {art.get('source_id','?')}: {e}")
                logger.warning(f"[STREAM] 文章分析异常: {e}")

        # ── 阶段2: 盘后日K分析（16:00 整点触发一次）──
        kline_reports = []
        hour_now = now.hour
        minute_now = now.minute
        should_daily_kline = (
            hour_now == ResearcherConfig.DAILY_KLINE_TRIGGER_HOUR
            and minute_now == 0
            and self._last_kline_time is not None
            and self._last_kline_time.date() < now.date()
        ) or (
            hour_now == ResearcherConfig.DAILY_KLINE_TRIGGER_HOUR
            and minute_now == 0
            and self._last_kline_time is None
        )

        if should_daily_kline:
            logger.info("[STREAM] 盘后日K分析启动（tushare 日线）")
            try:
                news_map = self._build_news_symbol_map()
                kline_reports = await self.kline_analyzer.analyze_batch(
                    symbols=ResearcherConfig.FUTURES_SYMBOLS,
                    related_news_map=news_map,
                )
                self._last_kline_time = now
                self._today_kline_reports = kline_reports  # 盘后覆盖，不累加
                for kr in kline_reports:
                    self._save_kline_report(kr, today)
                logger.info(f"[STREAM] 盘后日K分析完成: {len(kline_reports)} 个品种")
            except Exception as e:
                errors.append(f"日K分析失败: {e}")
                logger.error(f"[STREAM] 盘后日K分析异常: {e}", exc_info=True)

        # ── 阶段3: 推送到 decision（汇总研报）──
        pushed = 0
        if analyzed or kline_reports:
            try:
                pushed = await self._push_rich_report_to_decision(analyzed, kline_reports, today)
            except Exception as e:
                errors.append(f"推送失败: {e}")
                logger.error(f"[STREAM] 推送 decision 异常: {e}", exc_info=True)

        # ── 阶段4: 邮件日报钩子 — 4段/天（08/13/20/00，各触发一次）──
        hour = now.hour
        hkey = f"{hour:02d}"
        _email_slots = {
            "08": ("夜间报", self.daily_digest.generate_night_digest,      self.email_sender.send_night_report),
            "13": ("上午报", self.daily_digest.generate_morning_report_digest, self.email_sender.send_morning_session_report),
            "20": ("下午报", self.daily_digest.generate_afternoon_digest,   self.email_sender.send_afternoon_report),
            "00": ("夜盘报", self.daily_digest.generate_evening_session_digest, self.email_sender.send_evening_session_report),
        }
        # 夜盘报00点用前一天日期（汇总昨晚20-24点）
        digest_date = (now - __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d") if hour == 0 else today
        if hkey in _email_slots and self._email_sent.get(hkey) != today:
            label, gen_fn, send_fn = _email_slots[hkey]
            try:
                digest = gen_fn(digest_date)
                html   = build_morning_report_html(digest.get("reports", []), digest_date)
                send_fn(digest_date, html)
                self._email_sent[hkey] = today
                logger.info(f"[EMAIL] {label} 已发送: {digest_date}")
            except Exception as e:
                logger.warning(f"[EMAIL] {label} 发送失败: {e}")

        # ── 阶段5: 健康监控回调 ──
        elapsed = time.time() - start_time
        try:
            llm_slow = elapsed > 120 and len(analyzed) == 0  # 粗估 LLM 超时
            if errors:
                for err in errors:
                    module = "crawler" if "爬" in err else ("kline" if "K线" in err else "push" if "推送" in err else "llm")
                    await self.health_monitor.on_cycle_error(module, err)
            else:
                await self.health_monitor.on_cycle_success(
                    articles=len(analyzed),
                    cycle_secs=elapsed,
                    llm_timeout=llm_slow,
                )
        except Exception as hm_err:
            logger.debug(f"[HEALTH] 监控回调异常(不影响主流程): {hm_err}")
        mode = "both" if kline_reports else ("news" if analyzed else "idle")

        logger.info(
            f"[STREAM] 周期 {self._cycle_count} 完成: "
            f"mode={mode}, articles={len(analyzed)}, kline={len(kline_reports)}, "
            f"pushed={pushed}, errors={len(errors)}, elapsed={elapsed:.1f}s"
        )

        return {
            "cycle_id": self._cycle_count,
            "timestamp": now.isoformat(),
            "mode": mode,
            "new_articles": len(analyzed),
            "kline_reports": len(kline_reports),
            "pushed_to_decision": pushed,
            "errors": errors,
            "elapsed_seconds": elapsed,
            "today_total_articles": len(self._today_articles),
            "today_total_kline": len(self._today_kline_reports),
        }

    async def _crawl_stream_with_dedup(self) -> List[Dict]:
        """
        流式爬取所有源 → 提取多文章列表 → 去重 → 返回新文章

        Returns:
            新文章列表 [{source_id, title, content, url, published_at}, ...]
        """
        market_mode = self._get_market_mode()
        all_sources = self.source_registry.get_active_sources(None)

        # 按时段过滤
        if market_mode == "domestic":
            sources = [s for s in all_sources if getattr(s, "market", "both") in ("domestic", "both")]
        elif market_mode == "international":
            sources = [s for s in all_sources if getattr(s, "market", "both") in ("international", "both")]
        else:
            sources = all_sources

        # 按优先级排序
        sources.sort(key=lambda s: getattr(s, "priority", 5), reverse=True)

        new_articles = []

        for si, source in enumerate(sources, 1):
            try:
                logger.info(f"[CRAWL] ({si}/{len(sources)}) {source.source_id} [{source.mode}]")
                # 反爬限速
                wait = self.anti_detect.should_throttle(source.source_id, min_interval=3.0)
                if wait > 0:
                    await asyncio.sleep(wait)

                parser_func = get_parser(source.parser)
                if not parser_func:
                    continue

                # 爬取
                if source.mode == "code":
                    result = await self.code_crawler.crawl(
                        url=source.url_pattern,
                        source_id=source.source_id,
                        parser_func=parser_func,
                        timeout=source.timeout,
                    )
                else:
                    result = await self.browser_crawler.crawl(
                        url=source.url_pattern,
                        source_id=source.source_id,
                        parser_func=parser_func,
                        timeout=source.timeout,
                    )

                self.anti_detect.record_request(source.source_id, result.success)

                if not result.success:
                    logger.info(f"[CRAWL] {source.source_id} 失败: {result.error}")
                    continue

                # 提取多文章列表（兼容旧/新格式）
                articles = self._extract_articles_from_result(result, source)

                # 去重
                for art in articles:
                    title = art.get("title", "").strip()
                    if not title or len(title) < 3:
                        continue
                    if self.dedup.is_new(source.source_id, title):
                        self.dedup.mark_seen(source.source_id, title, art.get("url", ""))
                        art["source_id"] = source.source_id
                        art["source_name"] = getattr(source, "name", source.source_id)
                        new_articles.append(art)

                # 随机间隔
                interval = self.anti_detect.get_random_interval(2.0)
                await asyncio.sleep(interval)

            except Exception as e:
                logger.warning(f"[CRAWL] {source.source_id} 异常: {e}")
                self.anti_detect.record_request(source.source_id, False)

        logger.info(f"[CRAWL] 流式爬取完成: {len(sources)} 源, {len(new_articles)} 新文章")
        return new_articles

    def _extract_articles_from_result(self, result, source) -> List[Dict]:
        """从 CrawlResult 提取文章列表（兼容新旧格式）"""
        articles = []

        # 新格式：parser 返回的 data 字段包含 articles 列表
        if hasattr(result, 'data') and isinstance(result.data, dict):
            arts = result.data.get("articles", [])
            if arts:
                return arts

        # 旧格式：单条 title + content
        title = getattr(result, 'title', '') or ''
        content = getattr(result, 'content', '') or ''
        if title.strip():
            articles.append({
                "title": title.strip(),
                "content": content[:500] if content else title,
                "url": getattr(result, 'url', source.url_pattern),
                "published_at": getattr(result, 'published_at', None),
            })

        return articles

    async def _analyze_single_article(self, article: Dict) -> Optional[Dict]:
        """
        对单篇文章进行 LLM 分析，生成研报数据

        Returns:
            ArticleReport 风格的字典
        """
        title = (article.get("title") or "").strip()
        content = (article.get("content") or article.get("summary") or "").strip()
        source_id = article.get("source_id", "unknown")
        source_name = article.get("source_name", source_id)

        # 质量门槛：标题和内容必须有实质内容
        _placeholder_titles = {"无内容", "无金十快讯", "无标题", ""}
        if len(title) < 5 or title in _placeholder_titles:
            logger.warning(f"[QUALITY] 跳过低质量文章: title={title[:30]!r}")
            return None
        if len(content) < 20:
            logger.warning(f"[QUALITY] 内容过短，跳过LLM: title={title[:30]!r}, len={len(content)}")
            return None

        # 构建分析 prompt
        prompt = f"""你是期货市场分析师。请分析以下新闻对期货市场的影响。

新闻标题：{title}
新闻内容：{content[:500]}
来源：{source_name}

请用JSON格式回复：
{{"category":"futures/macro/energy/metals/agriculture/policy/general","relevance":0.0-1.0,"sentiment":"bullish/bearish/neutral","impact":"high/medium/low","symbols":["受影响品种代码"],"summary":"中文分析摘要(100字内)","key_points":["要点1","要点2"],"is_urgent":false}}"""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{ResearcherConfig.OLLAMA_URL}/api/generate",
                    json={
                        "model": ResearcherConfig.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_ctx": 4096,
                        },
                    },
                    timeout=ResearcherConfig.OLLAMA_TIMEOUT,
                )

                if resp.status_code != 200:
                    return None

                text = resp.json().get("response", "")
                # 移除 <think> 块
                if "<think>" in text and "</think>" in text:
                    text = text[text.index("</think>") + len("</think>"):]
                text = text.strip()

                # 解析 JSON
                analysis = {}
                if "{" in text:
                    try:
                        json_str = text[text.index("{"):text.rindex("}") + 1]
                        analysis = json.loads(json_str)
                    except (json.JSONDecodeError, ValueError):
                        pass

                now = datetime.now()
                return {
                    "article_id": f"ART-{now.strftime('%Y%m%d-%H%M%S')}-{source_id[:6]}",
                    "source_id": source_id,
                    "source_name": source_name,
                    "title": title,
                    "content": content[:500],
                    "url": article.get("url", ""),
                    "published_at": article.get("published_at"),
                    "crawled_at": now.isoformat(),
                    "date": now.strftime("%Y-%m-%d"),
                    "category": analysis.get("category", "general"),
                    "relevance": min(1.0, max(0.0, float(analysis.get("relevance", 0.3)))),
                    "sentiment": analysis.get("sentiment", "neutral"),
                    "impact_level": analysis.get("impact", "low"),
                    "affected_symbols": analysis.get("symbols", []),
                    "summary_cn": analysis.get("summary", title),
                    "key_points": analysis.get("key_points", []),
                    "is_urgent": bool(analysis.get("is_urgent", False)) or self._is_urgent(title, content),
                }

        except Exception as e:
            logger.warning(f"[ANALYZE] LLM 分析超时/失败 [{source_id}]: {e}")
            # 降级：返回不含 LLM 分析的基础研报
            now = datetime.now()
            return {
                "article_id": f"ART-{now.strftime('%Y%m%d-%H%M%S')}-{source_id[:6]}",
                "source_id": source_id,
                "source_name": source_name,
                "title": title,
                "content": content[:500],
                "url": article.get("url", ""),
                "crawled_at": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "category": "general",
                "relevance": 0.3,
                "sentiment": "neutral",
                "impact_level": "low",
                "affected_symbols": [],
                "summary_cn": title,
                "key_points": [],
                "is_urgent": self._is_urgent(title, content),
            }

    def _save_article_report(self, report: Dict, date: str):
        """保存单篇文章研报到 D:\\researcher_reports\\{date}\\articles\\"""
        try:
            # 质量标记：summary_cn 为空或过短则标 quality=low
            summary_cn = (report.get("summary_cn") or "").strip()
            if len(summary_cn) < 50:
                report["quality"] = "low"

            articles_dir = os.path.join(ResearcherConfig.REPORTS_DIR, date, "articles")
            os.makedirs(articles_dir, exist_ok=True)
            os.makedirs(articles_dir, exist_ok=True)
            filename = f"{report['article_id']}.json"
            filepath = os.path.join(articles_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"[SAVE] 文章研报已保存: {filepath}")
        except Exception as e:
            logger.warning(f"[SAVE] 保存文章研报失败: {e}")

    def _save_kline_report(self, report: Dict, date: str):
        """保存K线分析报告到 D:\\researcher_reports\\{date}\\kline\\"""
        try:
            kline_dir = os.path.join(ResearcherConfig.REPORTS_DIR, date, "kline")
            os.makedirs(kline_dir, exist_ok=True)
            filename = f"{report['report_id']}.json"
            filepath = os.path.join(kline_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"[SAVE] K线报告已保存: {filepath}")
        except Exception as e:
            logger.warning(f"[SAVE] 保存K线报告失败: {e}")

    def _build_news_symbol_map(self) -> Dict[str, List[str]]:
        """从当日文章研报中构建 品种→新闻标题 映射（供K线分析参考）"""
        news_map: Dict[str, List[str]] = {}
        for art in self._today_articles:
            for sym in art.get("affected_symbols", []):
                short = _extract_short_symbol(sym) if "." in sym else sym
                news_map.setdefault(short, []).append(art.get("title", ""))
        return news_map

    async def _push_rich_report_to_decision(
        self,
        article_reports: List[Dict],
        kline_reports: List[Dict],
        date: str,
    ) -> int:
        """推送研报到 decision — 适配 Studio ReportBatchRequest schema"""
        decision_url = os.getenv("DECISION_API_URL", "http://192.168.31.142:8104")
        evaluate_endpoint = f"{decision_url}/api/v1/evaluate"

        now = datetime.now()
        hour = now.hour

        # 构建 news_report（适配 Studio schema）
        news_report = None
        if article_reports:
            sorted_articles = sorted(
                article_reports,
                key=lambda a: a.get("relevance", 0),
                reverse=True,
            )
            news_report = {
                "report_id": f"NEWS-{date.replace('-','')}-{hour:02d}",
                "report_type": "news",
                "date": date,
                "hour": hour,
                "data": {
                    "total_items": len(sorted_articles),
                    "items": [
                        {
                            "source": a.get("source_name", ""),
                            "title": a.get("title", ""),
                            "summary": a.get("summary_cn", ""),
                            "sentiment": a.get("sentiment", "neutral"),
                            "impact": a.get("impact_level", "low"),
                            "symbols": a.get("affected_symbols", []),
                        }
                        for a in sorted_articles
                    ],
                },
                "confidence": 1.0,
            }

        # 构建 futures_report（适配 Studio schema）
        futures_report = None
        if kline_reports:
            futures_report = {
                "report_id": f"FUTURES-{date.replace('-','')}-{hour:02d}",
                "report_type": "futures",
                "date": date,
                "hour": hour,
                "data": {
                    "total_symbols": len(kline_reports),
                    "reports": [
                        {
                            "symbol": k.get("symbol", ""),
                            "trend": k.get("trend", ""),
                            "analysis": k.get("analysis", ""),
                            "change_pct": k.get("price_change_pct", 0),
                        }
                        for k in kline_reports
                    ],
                },
                "confidence": 1.0,
            }

        # 适配 ReportBatchRequest
        payload = {
            "batch_id": f"BATCH-{date.replace('-','')}-{hour:02d}",
            "date": date,
            "hour": hour,
            "generated_at": now.isoformat(),
            "news_report": news_report,
            "futures_report": futures_report,
            "total_reports": (1 if news_report else 0) + (1 if futures_report else 0),
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    evaluate_endpoint,
                    json=payload,
                    timeout=30.0,
                )
                success = resp.status_code in (200, 201)
                logger.info(f"[PUSH] decision 评级推送: status={resp.status_code}, body={resp.text[:200]}")
                return len(article_reports) + len(kline_reports) if success else 0
        except Exception as e:
            logger.error(f"[PUSH] decision 推送失败: {e}")
            return 0

    async def close(self):
        """关闭资源"""
        await self.browser_crawler.close()
        await self.kline_analyzer.close()
