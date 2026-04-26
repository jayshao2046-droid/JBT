"""流式研究员调度器 — 24/7 持续爬取 + 逐条研报 + K线盘中分析 + 累计数据链"""

import asyncio
import os
import time
import json
import logging
import threading
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
from .crawler.engine import CodeCrawler, BrowserCrawler
from .crawler.source_registry import SourceRegistry
from .crawler.parsers import get_parser
from .crawler.anti_detect import AntiDetect
from .models import SymbolResearch, ReportBatch
from .dedup import ArticleDedup
from .kline_analyzer import KlineAnalyzer, is_trading_hours, get_trading_session, _extract_short_symbol, SYMBOL_CN_NAMES
from .mini_client import MiniClient

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
        # Mini 上下文数据缓存（宏观/波动率/航运/情绪）
        self.mini_client = MiniClient(ResearcherConfig.DATA_API_URL)
        self._context_cache: Dict[str, Any] = {}
        self._context_fetched_at: Optional[datetime] = None
        self._futures_minute_lookback_hours: int = 2
        self._pending_macro_report: Optional[Dict] = None
        self._last_macro_report_slot: Optional[str] = None
        self._last_futures_context_report_slot: Optional[str] = None
        self._stream_cycle_requested = threading.Event()
        self._stream_cycle_request_reason: Optional[str] = None
        self._stream_cycle_request_lock = threading.Lock()
        # 服务启动时记录到当日统计
        self.reporter.stats_tracker.record_startup()

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

    def request_stream_cycle(self, reason: str = "manual") -> None:
        """登记一次即时 stream cycle 请求，由持续运行主链消费。"""
        with self._stream_cycle_request_lock:
            self._stream_cycle_request_reason = reason
            self._stream_cycle_requested.set()

    def wait_for_stream_cycle_request(self, timeout_seconds: float) -> Optional[str]:
        """等待即时 stream cycle 请求；超时返回 None。"""
        if not self._stream_cycle_requested.wait(timeout_seconds):
            return None

        with self._stream_cycle_request_lock:
            reason = self._stream_cycle_request_reason or "manual"
            self._stream_cycle_request_reason = None
            self._stream_cycle_requested.clear()

        return reason

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

    # ═══════════════════════════════════════════════════════════════════════
    # Mini 上下文数据接入 — 宏观/波动率/航运/情绪全量数据注入研究员分析链路
    # ═══════════════════════════════════════════════════════════════════════

    async def _refresh_mini_context(self) -> bool:
        """刷新 Mini 采集数据上下文缓存（60 分钟 TTL）。

        Returns:
            True 表示发生了实际刷新，False 表示使用缓存。
        """
        now = datetime.now()
        if (
            self._context_fetched_at
            and (now - self._context_fetched_at).total_seconds() < 3600
        ):
            return False

        logger.info("[CONTEXT] 开始刷新 Mini 全量上下文数据（11类+期货分钟K）...")
        ctx: Dict[str, Any] = {}
        for data_type in (
            "macro", "volatility", "shipping", "sentiment", "rss",
            "cftc", "forex", "news_api", "weather", "options", "position",
        ):
            try:
                records = self.mini_client.get_context_data(data_type, days=7)
                ctx[data_type] = records
                logger.info("[CONTEXT] %s: %d 条", data_type, len(records))
            except Exception as exc:
                logger.warning("[CONTEXT] %s 获取失败: %s", data_type, exc)
                ctx[data_type] = []
        # 期货分钟K单独拉取（三级路径，聚合摘要格式与普通records不同）
        futures_minute_hours = 2 if is_trading_hours() else 8
        try:
            summaries = self.mini_client.get_futures_minute_context(hours=futures_minute_hours)
            ctx["futures_minute"] = summaries
            self._futures_minute_lookback_hours = futures_minute_hours
            logger.info("[CONTEXT] futures_minute: %d 个品种", len(summaries))
        except Exception as exc:
            logger.warning("[CONTEXT] futures_minute 获取失败: %s", exc)
            ctx["futures_minute"] = []
            self._futures_minute_lookback_hours = futures_minute_hours

        self._context_cache = ctx
        self._context_fetched_at = now
        total = sum(len(v) for v in ctx.values())
        logger.info("[CONTEXT] 刷新完成，共 %d 条/项: %s", total,
                    ", ".join(f"{k}={len(v)}" for k, v in ctx.items()))
        return True

    def _build_context_text(self) -> str:
        """将缓存的上下文数据格式化为 LLM 可读文本（最多 600 字）。"""
        if not self._context_cache:
            return ""
        parts: List[str] = []

        # 宏观指标
        macro = self._context_cache.get("macro", [])
        if macro:
            parts.append("【宏观指标】")
            seen: set = set()
            for r in macro[:15]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    val = r.get("value", "N/A")
                    ts = str(r.get("timestamp", ""))[:10]
                    parts.append(f"  {ind}: {val} ({ts})")

        # 波动率
        vol = self._context_cache.get("volatility", [])
        if vol:
            parts.append("【波动率指数】")
            seen = set()
            for r in vol[:6]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    close = r.get("close", r.get("value", "N/A"))
                    ts = str(r.get("timestamp", ""))[:10]
                    parts.append(f"  {ind.upper()}: {close} ({ts})")

        # 航运
        ship = self._context_cache.get("shipping", [])
        if ship:
            parts.append("【航运指数】")
            seen = set()
            for r in ship[:6]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    val = r.get("value", "N/A")
                    chg = r.get("change_pct", "")
                    ts = str(r.get("timestamp", ""))[:10]
                    chg_str = f" {chg:+.2f}%" if isinstance(chg, (int, float)) else ""
                    parts.append(f"  {ind.upper()}: {val}{chg_str} ({ts})")

        # 情绪
        sent = self._context_cache.get("sentiment", [])
        if sent:
            parts.append("【市场情绪】")
            seen = set()
            for r in sent[:4]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    ts = str(r.get("timestamp", ""))[:10]
                    if "margin" in ind:
                        bal = r.get("margin_balance", "N/A")
                        parts.append(f"  融资余额({ind}): {bal} ({ts})")
                    elif "north" in ind:
                        net = r.get("net_buy", "N/A")
                        parts.append(f"  北向净买入: {net} ({ts})")
                    else:
                        parts.append(f"  {ind}: {ts}")

        # CFTC 持仓
        cftc = self._context_cache.get("cftc", [])
        if cftc:
            parts.append("【CFTC持仓】")
            seen = set()
            for r in cftc[:4]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    net = r.get("net_long", r.get("net", r.get("value", "N/A")))
                    chg = r.get("change", "")
                    ts = str(r.get("timestamp", ""))[:10]
                    chg_str = f" 变动{chg:+.0f}" if isinstance(chg, (int, float)) else ""
                    parts.append(f"  {ind}: 净多{net}{chg_str} ({ts})")

        # 外汇
        forex = self._context_cache.get("forex", [])
        if forex:
            parts.append("【外汇】")
            seen = set()
            for r in forex[:4]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    val = r.get("value", r.get("close", "N/A"))
                    ts = str(r.get("timestamp", ""))[:10]
                    parts.append(f"  {ind}: {val} ({ts})")

        # 天气
        weather = self._context_cache.get("weather", [])
        if weather:
            parts.append("【主产区天气】")
            seen = set()
            for r in weather[:3]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    desc = r.get("description", r.get("condition", r.get("value", "N/A")))
                    ts = str(r.get("timestamp", ""))[:10]
                    parts.append(f"  {ind}: {desc} ({ts})")

        # 期权 PCR
        options = self._context_cache.get("options", [])
        if options:
            parts.append("【期权信号】")
            seen = set()
            for r in options[:3]:
                ind = r.get("indicator", "")
                if ind and ind not in seen:
                    seen.add(ind)
                    pcr = r.get("pcr", r.get("value", "N/A"))
                    ts = str(r.get("timestamp", ""))[:10]
                    parts.append(f"  {ind} PCR: {pcr} ({ts})")

        # 期货分钟K涨跌幅 Top5（按绝对值排序）
        futures_min = self._context_cache.get("futures_minute", [])
        if futures_min:
            parts.append(f"【期货近{self._futures_minute_lookback_hours}h涨跌 Top5】")
            top5 = sorted(futures_min, key=lambda x: abs(x.get("change_pct", 0)), reverse=True)[:5]
            for r in top5:
                sym = r.get("symbol", "").replace("KQ_m_", "")
                close = r.get("latest_close", "N/A")
                chg = r.get("change_pct", 0)
                parts.append(f"  {sym}: {close} ({chg:+.2f}%)")

        return "\n".join(parts)

    def _build_futures_context_report(self, today: str, hour: int) -> Optional[Dict]:
        """基于 Mini 分钟K上下文构建盘中数据研报。"""
        futures_min = self._context_cache.get("futures_minute", [])
        if not isinstance(futures_min, list) or not futures_min:
            return None

        normalized_items: List[Dict[str, Any]] = []
        for item in futures_min:
            if not isinstance(item, dict):
                continue

            symbol = str(item.get("symbol") or "").strip()
            if not symbol:
                continue

            try:
                change_pct = float(item.get("change_pct") or 0.0)
            except (TypeError, ValueError):
                change_pct = 0.0

            short_symbol = _extract_short_symbol(symbol).upper() if _extract_short_symbol(symbol) else symbol
            latest_close = item.get("latest_close")
            volume = item.get("volume", 0)
            if change_pct >= 0.6:
                trend = "偏多"
            elif change_pct <= -0.6:
                trend = "偏空"
            else:
                trend = "震荡"

            normalized_items.append({
                "symbol": symbol,
                "short_symbol": short_symbol,
                "change_pct": round(change_pct, 2),
                "latest_close": latest_close,
                "volume": volume,
                "trend": trend,
            })

        if not normalized_items:
            return None

        sorted_items = sorted(normalized_items, key=lambda row: abs(row["change_pct"]), reverse=True)
        rising = sum(1 for row in normalized_items if row["change_pct"] > 0.3)
        falling = sum(1 for row in normalized_items if row["change_pct"] < -0.3)
        neutral = len(normalized_items) - rising - falling

        if rising > falling + max(2, len(normalized_items) // 10):
            bias = "整体偏强"
        elif falling > rising + max(2, len(normalized_items) // 10):
            bias = "整体偏弱"
        else:
            bias = "多空分化"

        top_movers = [
            f"{row['short_symbol']} {row['change_pct']:+.2f}%"
            for row in sorted_items[:5]
        ]
        market_overview = (
            f"Mini 近{self._futures_minute_lookback_hours}小时分钟K覆盖 {len(normalized_items)} 个期货主连，{bias}；"
            f"上涨 {rising} 个，下跌 {falling} 个，震荡 {neutral} 个。"
        )

        futures_summary = {
            "symbols_covered": len(normalized_items),
            "market_overview": market_overview,
            "top_movers": top_movers,
            "symbols": {
                row["short_symbol"]: {
                    "trend": row["trend"],
                    "change_pct": row["change_pct"],
                    "confidence": 0.72,
                }
                for row in sorted_items[:10]
            },
        }

        report_rows = []
        for row in sorted_items[:10]:
            latest_close = row["latest_close"]
            latest_text = latest_close if latest_close is not None else "N/A"
            report_rows.append({
                "symbol": row["symbol"],
                "trend": row["trend"],
                "analysis": (
                    f"{row['short_symbol']} 近2小时涨跌 {row['change_pct']:+.2f}%，"
                    f"最新价 {latest_text}，当前判断为 {row['trend']}。"
                ),
                "change_pct": row["change_pct"],
                "latest_close": latest_close,
                "volume": row["volume"],
            })

        content = market_overview
        if top_movers:
            content = f"{content} 重点波动：{'；'.join(top_movers[:3])}。"

        return {
            "report_id": f"FUTURES-{today.replace('-', '')}-{hour:02d}",
            "report_type": "futures",
            "date": today,
            "hour": hour,
            "title": "Mini 分钟K数据研报",
            "summary": market_overview,
            "content": content,
            "symbols": [row["short_symbol"] for row in sorted_items[:10]],
            "symbols_covered": len(normalized_items),
            "market_overview": market_overview,
            "top_movers": top_movers,
            "futures_summary": futures_summary,
            "data": {
                "total_symbols": len(normalized_items),
                "reports": report_rows,
            },
            "confidence": 0.95,
        }

    def _build_macro_report_payload(
        self,
        today: str,
        hour: int,
        context_text: str,
        analysis: Optional[Dict[str, Any]] = None,
        fallback_reason: Optional[str] = None,
    ) -> Dict:
        """构建 Decision 可直接消费的宏观情报研报。"""
        analysis = analysis or {}
        coverage = {key: len(value) for key, value in self._context_cache.items() if value}
        futures_min = self._context_cache.get("futures_minute", [])

        movers: List[Dict[str, Any]] = []
        if isinstance(futures_min, list):
            for item in futures_min:
                if not isinstance(item, dict):
                    continue
                symbol = str(item.get("symbol") or "").strip()
                if not symbol:
                    continue
                try:
                    change_pct = float(item.get("change_pct") or 0.0)
                except (TypeError, ValueError):
                    change_pct = 0.0
                short_symbol = _extract_short_symbol(symbol).upper() if _extract_short_symbol(symbol) else symbol
                movers.append({
                    "symbol": short_symbol,
                    "change_pct": round(change_pct, 2),
                })

        movers.sort(key=lambda row: abs(row["change_pct"]), reverse=True)
        top_movers = [row["symbol"] for row in movers[:5]]
        avg_change = sum(row["change_pct"] for row in movers) / len(movers) if movers else 0.0
        max_abs_change = max((abs(row["change_pct"]) for row in movers), default=0.0)

        macro_trend = str(analysis.get("macro_trend") or "").strip()
        if not macro_trend:
            if avg_change >= 0.4:
                macro_trend = "偏多"
            elif avg_change <= -0.4:
                macro_trend = "偏空"
            else:
                macro_trend = "震荡"

        risk_level = str(analysis.get("risk_level") or "").strip()
        if risk_level not in {"high", "medium", "low"}:
            risk_level = "high" if max_abs_change >= 2.0 else "medium"

        default_drivers: List[str] = []
        if coverage.get("macro"):
            default_drivers.append(f"宏观指标样本 {coverage['macro']} 条")
        if coverage.get("sentiment"):
            default_drivers.append(f"市场情绪样本 {coverage['sentiment']} 条")
        if coverage.get("futures_minute"):
            default_drivers.append(f"期货分钟K覆盖 {coverage['futures_minute']} 个品种")
        if coverage.get("shipping"):
            default_drivers.append(f"航运指标样本 {coverage['shipping']} 条")
        if not default_drivers:
            default_drivers.append("Mini 上下文已刷新")

        key_drivers = analysis.get("key_drivers") or default_drivers[:3]
        volatility_signal = analysis.get("volatility_signal") or ("上升" if max_abs_change >= 2.0 else "稳定")
        shipping_signal = analysis.get("shipping_signal") or ("扩张" if coverage.get("shipping") else "稳定")
        cftc_signal = analysis.get("cftc_signal") or ""
        forex_signal = analysis.get("forex_signal") or ""
        sentiment = analysis.get("sentiment") or (
            "乐观" if macro_trend == "偏多" else "悲观" if macro_trend == "偏空" else "中性"
        )
        recommended_sectors = analysis.get("recommended_sectors") or []
        weather_impact = analysis.get("weather_impact") or "无"
        impact_on_futures = analysis.get("impact_on_futures") or (
            f"当前宏观研判为 {macro_trend}，风险等级 {risk_level}。"
            f"Mini 上下文显示近端波动主要集中在 {'/'.join(top_movers[:3]) if top_movers else '主要期货品种'}。"
        )
        risk_note = analysis.get("risk_note") or (
            f"LLM 宏观分析不可用，当前采用 Mini 上下文回退摘要。原因: {fallback_reason}"
            if fallback_reason
            else ""
        )

        summary_parts = [
            f"宏观趋势 {macro_trend}",
            f"风险 {risk_level}",
        ]
        summary_parts.extend(str(driver) for driver in key_drivers[:2])
        summary = "；".join(part for part in summary_parts if part)

        return {
            "report_id": f"MACRO-{today.replace('-', '')}-{hour:02d}",
            "report_type": "macro",
            "date": today,
            "hour": hour,
            "title": "Mini 宏观情报研报",
            "summary": summary,
            "content": impact_on_futures,
            "macro_trend": macro_trend,
            "risk_level": risk_level,
            "key_drivers": key_drivers,
            "volatility_signal": volatility_signal,
            "shipping_signal": shipping_signal,
            "cftc_signal": cftc_signal,
            "forex_signal": forex_signal,
            "sentiment": sentiment,
            "top_movers": top_movers,
            "weather_impact": weather_impact,
            "impact_on_futures": impact_on_futures,
            "recommended_sectors": recommended_sectors,
            "risk_note": risk_note,
            "data_coverage": coverage,
            "data": {
                "macro_trend": macro_trend,
                "risk_level": risk_level,
                "key_drivers": key_drivers,
                "volatility_signal": volatility_signal,
                "shipping_signal": shipping_signal,
                "cftc_signal": cftc_signal,
                "forex_signal": forex_signal,
                "sentiment": sentiment,
                "top_movers": top_movers,
                "weather_impact": weather_impact,
                "impact_on_futures": impact_on_futures,
                "recommended_sectors": recommended_sectors,
                "risk_note": risk_note,
                "data_coverage": coverage,
                "context_summary": context_text[:800],
            },
            "confidence": 0.9 if fallback_reason else 1.0,
        }

    async def _analyze_mini_context(self, today: str, hour: int) -> Optional[Dict]:
        """对 Mini 上下文数据进行 LLM 宏观分析，生成 macro_report 报告。"""
        context_text = self._build_context_text()
        if not context_text:
            logger.info("[CONTEXT] 上下文为空，跳过宏观 LLM 分析")
            return None

        prompt = (
            "你是期货市场宏观分析师。以下是来自 Mini 数据端采集的最新全量市场指标数据：\n\n"
            f"{context_text}\n\n"
            "请综合分析以上宏观/波动率/航运/情绪/CFTC持仓/外汇/天气/期权/期货行情等全量指标，"
            "生成期货市场宏观研报，用JSON格式回复：\n"
            '{"macro_trend":"偏多/偏空/震荡","risk_level":"high/medium/low",'
            '"key_drivers":["驱动1","驱动2","驱动3"],'
            '"volatility_signal":"上升/下降/稳定","shipping_signal":"扩张/收缩/稳定",'
            '"cftc_signal":"净多持续增加/净多减少/净空增加/震荡",'
            '"forex_signal":"美元偏强/美元偏弱/震荡",'
            '"sentiment":"乐观/悲观/中性",'
            '"top_movers":["涨幅最大品种代码","跌幅最大品种代码"],'
            '"weather_impact":"天气对农产品期货的影响(50字,无影响填无)",'
            '"impact_on_futures":"对期货市场的综合影响分析(200字以内)",'
            '"recommended_sectors":["推荐板块1","板块2"],'
            '"risk_note":"主要风险提示"}'
        )

        analysis: Dict[str, Any] = {}
        fallback_reason: Optional[str] = None

        try:
            # F1（2026-04-24）：宏观 LLM 参数收紧 — /no_think + num_predict + keep_alive
            tightened_prompt = "/no_think\n" + prompt
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{ResearcherConfig.OLLAMA_URL}/api/generate",
                    json={
                        "model": ResearcherConfig.OLLAMA_MODEL,
                        "prompt": tightened_prompt,
                        "stream": False,
                        "keep_alive": ResearcherConfig.OLLAMA_KEEP_ALIVE,
                        "options": {
                            "temperature": 0.3,
                            "num_ctx": 4096,
                            "num_predict": ResearcherConfig.OLLAMA_NUM_PREDICT,
                        },
                    },
                    timeout=ResearcherConfig.OLLAMA_NEWS_TIMEOUT,
                )
            if resp.status_code != 200:
                fallback_reason = f"ollama_status_{resp.status_code}"
            else:
                text = resp.json().get("response", "")
                if "<think>" in text and "</think>" in text:
                    text = text[text.index("</think>") + len("</think>"):]
                text = text.strip()

                if "{" in text:
                    try:
                        json_str = text[text.index("{"):text.rindex("}") + 1]
                        analysis = json.loads(json_str)
                    except Exception:
                        fallback_reason = "invalid_macro_json"
                else:
                    fallback_reason = "missing_macro_json"
        except Exception as exc:
            fallback_reason = str(exc)

        if fallback_reason:
            logger.warning("[CONTEXT] 宏观 LLM 分析失败，使用回退摘要: %s", fallback_reason)

        return self._build_macro_report_payload(
            today,
            hour,
            context_text,
            analysis=analysis,
            fallback_reason=fallback_reason,
        )

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
                    # 安全修复：P0-8 - 添加文件删除错误日志
                    try:
                        if os.path.exists(local_path):
                            os.remove(local_path)
                            logger.info(f"[PUSH] 删除本地文件: {local_path}")
                    except OSError as e:
                        logger.warning(f"[PUSH] 删除文件失败 {local_path}: {e}")

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

        futures_context_report: Optional[Dict[str, Any]] = None

        # ── 阶段0: 刷新 Mini 上下文数据（60分钟 TTL）──
        try:
            context_refreshed = await self._refresh_mini_context()
            slot_key = f"{today}-{now.hour:02d}"
            if any(self._context_cache.values()):
                if self._last_futures_context_report_slot != slot_key:
                    futures_context_report = self._build_futures_context_report(today, now.hour)
                    if futures_context_report:
                        self._last_futures_context_report_slot = slot_key
                        logger.info("[CONTEXT] 数据研报已生成: %s", futures_context_report["report_id"])

                if self._last_macro_report_slot != slot_key:
                    macro_rpt = await self._analyze_mini_context(today, now.hour)
                    if macro_rpt:
                        self._pending_macro_report = macro_rpt
                        self._last_macro_report_slot = slot_key
                        logger.info("[CONTEXT] 宏观研报已生成: %s", macro_rpt["report_id"])
            elif context_refreshed:
                logger.warning("[CONTEXT] Mini 上下文刷新完成但内容为空")
        except Exception as exc:
            errors.append(f"context_refresh: {exc}")
            logger.warning("[CONTEXT] 刷新/分析异常: %s", exc)

        # ── 阶段0.5: 把 Mini news_api/rss 缓存记录转为文章对象，注入分析队列 ──
        mini_news_articles: List[Dict] = []
        try:
            for src_key, source_id, title_field, content_field in (
                ("news_api", "mini_news_api", "title", "content"),
                ("rss",      "mini_rss",      "title", "summary"),
            ):
                cached = self._context_cache.get(src_key, [])
                if not cached:
                    continue
                # 只取最近 30 条，避免重复分析
                for rec in cached[:30]:
                    title = str(rec.get(title_field) or rec.get("title") or "").strip()
                    content = str(rec.get(content_field) or rec.get("full_text") or "").strip()
                    source_name = str(rec.get("feed") or rec.get("source") or src_key)
                    if not title or len(title) < 5:
                        continue
                    # 用 ArticleDedup 去重
                    if not self.dedup.is_new(source_id, title):
                        continue
                    self.dedup.mark_seen(source_id, title, rec.get("link") or rec.get("url") or "")
                    mini_news_articles.append({
                        "source_id": source_id,
                        "source_name": source_name,
                        "title": title,
                        "content": content,
                        "url": rec.get("link") or rec.get("url") or "",
                        "published_at": str(rec.get("timestamp") or rec.get("time") or ""),
                    })
            if mini_news_articles:
                logger.info("[CONTEXT] Mini 新闻注入分析队列: %d 条", len(mini_news_articles))
        except Exception as exc:
            logger.warning("[CONTEXT] Mini 新闻转换异常: %s", exc)

        # ── 阶段1: 流式新闻爬取 + 逐条分析 ──
        new_articles = await self._crawl_stream_with_dedup()
        new_articles = mini_news_articles + new_articles  # Mini 新闻优先置前
        logger.info(f"[STREAM] 周期 {self._cycle_count}: 新文章 {len(new_articles)} 条")

        # ── F1（2026-04-24）：两段式管线第一段 — 7B 小模型前置筛选 ──
        # 仅 score >= OLLAMA_PREFILTER_THRESHOLD 的新闻才进入 14B 深分析。
        # 通过 OLLAMA_PREFILTER_ENABLED=false 可一键回滚单段式。
        try:
            from .news_prefilter import prefilter_news
            _raw_count = len(new_articles)
            new_articles = await prefilter_news(new_articles)
            logger.info(
                f"[STREAM] 前置筛选: {_raw_count} → {len(new_articles)} 条进入 14B"
            )
        except Exception as _pf_err:
            errors.append(f"prefilter: {_pf_err}")
            logger.warning(f"[PREFILTER] 异常，按全量放行: {_pf_err}")

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

        # ── 阶段3: 推送到 decision（汇总研报 + 宏观上下文报告）──
        pushed = 0
        macro_report = self._pending_macro_report
        self._pending_macro_report = None  # 取出后清除，避免重复推送
        if analyzed or kline_reports or macro_report or futures_context_report:
            try:
                pushed = await self._push_rich_report_to_decision(
                    analyzed,
                    kline_reports,
                    today,
                    macro_report=macro_report,
                    futures_report=futures_context_report,
                )
            except Exception as e:
                errors.append(f"推送失败: {e}")
                logger.error(f"[STREAM] 推送 decision 异常: {e}", exc_info=True)

        if pushed == 0:
            if macro_report:
                self._pending_macro_report = macro_report
                self._last_macro_report_slot = None
            if futures_context_report:
                self._last_futures_context_report_slot = None

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
        # 安全修复：P0-3 - 移除不安全的 __import__ 动态导入
        digest_date = (now - timedelta(days=1)).strftime("%Y-%m-%d") if hour == 0 else today
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
        elapsed = time.time() - start_time
        mode = "both" if kline_reports else ("news" if analyzed else "idle")

        logger.info(
            f"[STREAM] 周期 {self._cycle_count} 完成: "
            f"mode={mode}, articles={len(analyzed)}, kline={len(kline_reports)}, "
            f"pushed={pushed}, errors={len(errors)}, elapsed={elapsed:.1f}s"
        )

        # daily_stats 埋点（不阻断主链）
        try:
            report_id_for_stats = f"STREAM-{now.strftime('%H%M%S')}-{self._cycle_count}"
            self.reporter.stats_tracker.record_report(
                hour=now.hour,
                report_id=report_id_for_stats,
                json_path="",
                elapsed_s=elapsed,
                success=(len(errors) == 0),
            )
        except Exception as _stats_err:
            logger.debug(f"[STREAM] daily_stats 埋点失败（非阻断）: {_stats_err}")

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

        # 注入 Mini 宏观上下文（如有缓存）
        context_text = self._build_context_text()
        context_section = (
            f"\n\n当前市场宏观背景（来自 Mini 全量采集）：\n{context_text[:800]}"
            if context_text else ""
        )

        # 构建分析 prompt
        prompt = f"""你是期货市场分析师。请分析以下新闻对期货市场的影响。{context_section}

新闻标题：{title}
新闻内容：{content[:500]}
来源：{source_name}

请用JSON格式回复：
{{"category":"futures/macro/energy/metals/agriculture/policy/general","relevance":0.0-1.0,"sentiment":"bullish/bearish/neutral","impact":"high/medium/low","symbols":["受影响品种代码"],"summary":"中文分析摘要(100字内)","key_points":["要点1","要点2"],"is_urgent":false}}"""

        try:
            # F1（2026-04-24）：新闻 LLM 参数收紧 — /no_think + num_predict + keep_alive + 短 timeout
            tightened_prompt = "/no_think\n" + prompt
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{ResearcherConfig.OLLAMA_URL}/api/generate",
                    json={
                        "model": ResearcherConfig.OLLAMA_MODEL,
                        "prompt": tightened_prompt,
                        "stream": False,
                        "keep_alive": ResearcherConfig.OLLAMA_KEEP_ALIVE,
                        "options": {
                            "temperature": 0.3,
                            "num_ctx": 4096,
                            "num_predict": ResearcherConfig.OLLAMA_NUM_PREDICT,
                        },
                    },
                    timeout=ResearcherConfig.OLLAMA_NEWS_TIMEOUT,
                )

                if resp.status_code != 200:
                    logger.warning(f"[ANALYZE] LLM 分析失败 [{source_id}]: HTTP {resp.status_code}, body={resp.text[:200]}")
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
        *,
        macro_report: Optional[Dict] = None,
        futures_report: Optional[Dict] = None,
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
            news_items = [
                {
                    "source": a.get("source_name", ""),
                    "title": a.get("title", ""),
                    "summary": a.get("summary_cn", ""),
                    "sentiment": a.get("sentiment", "neutral"),
                    "impact": a.get("impact_level", "low"),
                    "symbols": a.get("affected_symbols", []),
                }
                for a in sorted_articles
            ]
            unique_symbols = sorted({
                symbol
                for article in sorted_articles
                for symbol in (article.get("affected_symbols") or [])
                if symbol
            })
            summary = f"本轮共分析 {len(sorted_articles)} 条新闻，涉及 {len(unique_symbols)} 个重点品种。"
            news_report = {
                "report_id": f"NEWS-{date.replace('-','')}-{hour:02d}",
                "report_type": "news",
                "date": date,
                "hour": hour,
                "title": "市场新闻情绪研报",
                "summary": summary,
                "content": "\n".join(
                    f"[{item['source']}] {item['title']} - {item['summary']}"
                    for item in news_items[:8]
                )[:1600],
                "symbols": unique_symbols,
                "news_items": news_items,
                "crawler_stats": {
                    "articles_processed": len(sorted_articles),
                    "news_items": news_items,
                },
                "data": {
                    "total_items": len(sorted_articles),
                    "items": news_items,
                },
                "confidence": 1.0,
            }

        # 构建 futures_report（适配 Studio schema）
        if futures_report is None and kline_reports:
            sorted_kline = sorted(
                kline_reports,
                key=lambda item: abs(float(item.get("price_change_pct") or 0.0)),
                reverse=True,
            )
            top_movers = [
                f"{_extract_short_symbol(item.get('symbol', '')).upper() if _extract_short_symbol(item.get('symbol', '')) else item.get('symbol', '')} {float(item.get('price_change_pct') or 0.0):+.2f}%"
                for item in sorted_kline[:5]
            ]
            market_overview = f"盘后日K覆盖 {len(kline_reports)} 个期货品种。"
            futures_report = {
                "report_id": f"FUTURES-{date.replace('-','')}-{hour:02d}",
                "report_type": "futures",
                "date": date,
                "hour": hour,
                "title": "盘后期货数据研报",
                "summary": market_overview,
                "content": f"{market_overview} 重点波动：{'；'.join(top_movers[:3])}" if top_movers else market_overview,
                "symbols": [
                    _extract_short_symbol(item.get("symbol", "")).upper() if _extract_short_symbol(item.get("symbol", "")) else item.get("symbol", "")
                    for item in sorted_kline[:10]
                ],
                "symbols_covered": len(kline_reports),
                "market_overview": market_overview,
                "top_movers": top_movers,
                "futures_summary": {
                    "symbols_covered": len(kline_reports),
                    "market_overview": market_overview,
                    "top_movers": top_movers,
                    "symbols": {
                        (
                            _extract_short_symbol(item.get("symbol", "")).upper()
                            if _extract_short_symbol(item.get("symbol", ""))
                            else item.get("symbol", "")
                        ): {
                            "trend": item.get("trend", ""),
                            "change_pct": float(item.get("price_change_pct") or 0.0),
                            "confidence": 0.8,
                        }
                        for item in sorted_kline[:10]
                    },
                },
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
            "macro_report": macro_report,
            "total_reports": (1 if news_report else 0) + (1 if futures_report else 0) + (1 if macro_report else 0),
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
                return payload["total_reports"] if success else 0
        except Exception as e:
            logger.error(f"[PUSH] decision 推送失败: {e}")
            return 0

    async def close(self):
        """关闭资源"""
        await self.browser_crawler.close()
        await self.kline_analyzer.close()
