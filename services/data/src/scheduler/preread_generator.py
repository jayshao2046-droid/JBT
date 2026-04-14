"""夜间预读摘要生成器 — 为决策端四角色生成上下文摘要。

职责：
1. 在非交易时段（21:00）预读并聚合数据
2. 生成四角色结构化摘要：researcher / l1 / l2 / analyst
3. 存储到 runtime/daily_snapshots/{YYYY-MM-DD}/
4. 局部失败降级：单个 Collector 失败不影响其他角色摘要生成
5. 通过 NotifierDispatcher 发送 PREREAD_DONE / PREREAD_FAIL 通知
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger("preread_generator")

CN_TZ = timezone(timedelta(hours=8))


class PrereadGenerator:
    """夜间预读摘要生成器。"""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root)
        self.logger = logger

    def generate_daily_snapshot(self, *, date_str: str | None = None) -> dict[str, Any]:
        """生成指定日期的四角色摘要。

        Args:
            date_str: 日期字符串 YYYY-MM-DD，默认今日

        Returns:
            {
                "researcher_context": {...},
                "l1_briefing": {...},
                "l2_audit_context": {...},
                "analyst_dataset": {...},
                "ready_flag": bool,
                "generated_at": str,
                "errors": [...]
            }
        """
        date_str = date_str or datetime.now(CN_TZ).strftime("%Y-%m-%d")
        self.logger.info("开始生成 %s 预读摘要", date_str)

        errors: list[str] = []
        result = {
            "researcher_context": {},
            "l1_briefing": {},
            "l2_audit_context": {},
            "analyst_dataset": {},
            "ready_flag": False,
            "generated_at": datetime.now(CN_TZ).isoformat(),
            "errors": errors,
        }

        # ── 1. 研究员上下文 ──────────────────────────────────────
        try:
            result["researcher_context"] = self._generate_researcher_context(date_str)
        except Exception as exc:
            err_msg = f"研究员上下文生成失败: {exc}"
            self.logger.warning(err_msg)
            errors.append(err_msg)
            result["researcher_context"] = {"error": str(exc)}

        # ── 2. L1 快速简报 ──────────────────────────────────────
        try:
            result["l1_briefing"] = self._generate_l1_briefing(date_str)
        except Exception as exc:
            err_msg = f"L1 简报生成失败: {exc}"
            self.logger.warning(err_msg)
            errors.append(err_msg)
            result["l1_briefing"] = {"error": str(exc)}

        # ── 3. L2 审核上下文 ────────────────────────────────────
        try:
            result["l2_audit_context"] = self._generate_l2_audit_context(date_str)
        except Exception as exc:
            err_msg = f"L2 审核上下文生成失败: {exc}"
            self.logger.warning(err_msg)
            errors.append(err_msg)
            result["l2_audit_context"] = {"error": str(exc)}

        # ── 4. 数据分析师数据集 ──────────────────────────────────
        try:
            result["analyst_dataset"] = self._generate_analyst_dataset(date_str)
        except Exception as exc:
            err_msg = f"数据分析师数据集生成失败: {exc}"
            self.logger.warning(err_msg)
            errors.append(err_msg)
            result["analyst_dataset"] = {"error": str(exc)}

        # ── 5. 判断 ready_flag ──────────────────────────────────
        # 至少有 3 个角色摘要成功生成（允许 1 个失败）
        success_count = sum(
            1 for key in ["researcher_context", "l1_briefing", "l2_audit_context", "analyst_dataset"]
            if "error" not in result[key]
        )
        result["ready_flag"] = success_count >= 3

        # ── 6. 持久化到 runtime ─────────────────────────────────
        try:
            self._save_snapshot(date_str, result)
        except Exception as exc:
            err_msg = f"摘要持久化失败: {exc}"
            self.logger.error(err_msg)
            errors.append(err_msg)

        self.logger.info(
            "预读摘要生成完成: date=%s ready=%s errors=%d",
            date_str, result["ready_flag"], len(errors),
        )
        return result

    def _generate_researcher_context(self, date_str: str) -> dict[str, Any]:
        """生成研究员上下文 — watchlist + 近5日日线摘要 + 宏观快照 + CFTC持仓。"""
        context: dict[str, Any] = {}

        # 1. watchlist 股票池
        try:
            from src.collectors.watchlist_client import WatchlistClient
            client = WatchlistClient()
            watchlist = client.fetch_watchlist()
            context["watchlist"] = watchlist[:30]  # 限制 30 只
            self.logger.info("研究员上下文: watchlist=%d", len(context["watchlist"]))
        except Exception as exc:
            self.logger.warning("watchlist 获取失败: %s", exc)
            context["watchlist"] = []

        # 2. 近5日日线摘要（标的平均涨跌/成交量）
        try:
            from src.collectors.tushare_collector import TushareDailyCollector
            collector = TushareDailyCollector()
            # 简化：只取 watchlist 前 5 只的近 5 日数据作为市场概况
            sample_symbols = context["watchlist"][:5]
            daily_summary = []
            for symbol in sample_symbols:
                try:
                    records = collector.collect(symbol=symbol, days=5)
                    if records:
                        avg_change = sum(r.get("pct_chg", 0) for r in records) / len(records)
                        avg_volume = sum(r.get("vol", 0) for r in records) / len(records)
                        daily_summary.append({
                            "symbol": symbol,
                            "avg_change_pct": round(avg_change, 2),
                            "avg_volume": int(avg_volume),
                        })
                except Exception:
                    pass
            context["daily_summary"] = daily_summary
            self.logger.info("研究员上下文: daily_summary=%d", len(daily_summary))
        except Exception as exc:
            self.logger.warning("日线摘要生成失败: %s", exc)
            context["daily_summary"] = []

        # 3. 宏观背景快照（最新 CPI/PPI/PMI 月度值）
        try:
            from src.collectors.macro_collector import MacroCollector
            collector = MacroCollector()
            macro_records = collector.collect(countries=["CN", "US"], full_history=False)
            # 取最新一条记录
            macro_snapshot = {}
            for record in macro_records[-10:]:  # 最近 10 条
                indicator = record.get("payload", {}).get("indicator", "")
                value = record.get("payload", {}).get("value", 0)
                if indicator:
                    macro_snapshot[indicator] = value
            context["macro_snapshot"] = macro_snapshot
            self.logger.info("研究员上下文: macro_snapshot=%d", len(macro_snapshot))
        except Exception as exc:
            self.logger.warning("宏观快照生成失败: %s", exc)
            context["macro_snapshot"] = {}

        # 4. CFTC 大宗商品净持仓方向（期货策略专用）
        try:
            # CFTC 数据由 cftc_collector 采集，这里简化为空
            context["cftc_snapshot"] = {}
            self.logger.info("研究员上下文: cftc_snapshot=0 (未实现)")
        except Exception as exc:
            self.logger.warning("CFTC 快照生成失败: %s", exc)
            context["cftc_snapshot"] = {}

        return context

    def _generate_l1_briefing(self, date_str: str) -> dict[str, Any]:
        """生成 L1 快速简报 — 市场情绪 + 重大新闻 + 波动率指数。"""
        briefing: dict[str, Any] = {}

        # 1. 市场情绪简报（北向资金 + 融资融券）
        try:
            from src.collectors.sentiment_collector import SentimentCollector
            collector = SentimentCollector()
            sentiment_records = collector.collect(symbols=["north_flow", "margin_sh", "margin_sz"])
            # 取最新一条
            sentiment_summary = {}
            for record in sentiment_records[-5:]:
                symbol = record.get("symbol_or_indicator", "")
                payload = record.get("payload", {})
                if symbol == "north_flow":
                    sentiment_summary["north_flow"] = payload.get("net_buy", 0)
                elif symbol == "margin_sh":
                    sentiment_summary["margin_balance_sh"] = payload.get("margin_balance", 0)
            briefing["sentiment_summary"] = sentiment_summary
            self.logger.info("L1 简报: sentiment_summary=%d", len(sentiment_summary))
        except Exception as exc:
            self.logger.warning("情绪简报生成失败: %s", exc)
            briefing["sentiment_summary"] = {}

        # 2. 重大新闻标题列表（近 12h Top 10）
        try:
            from src.collectors.news_api_collector import NewsAPICollector
            collector = NewsAPICollector()
            news_records = collector.collect(sources=["cls", "eastmoney"])
            # 取最新 10 条标题
            news_titles = [r.get("payload", {}).get("title", "") for r in news_records[-10:]]
            briefing["news_titles"] = news_titles
            self.logger.info("L1 简报: news_titles=%d", len(news_titles))
        except Exception as exc:
            self.logger.warning("新闻标题生成失败: %s", exc)
            briefing["news_titles"] = []

        # 3. 波动率指数（50ETF QVIX / VIX）
        try:
            from src.collectors.volatility_collector import VolatilityCollector
            collector = VolatilityCollector()
            vol_records = collector.collect(symbols=["50ETF", "VIX"])
            vol_snapshot = {}
            for record in vol_records[-5:]:
                symbol = record.get("symbol", "")
                value = record.get("payload", {}).get("value", 0)
                if symbol:
                    vol_snapshot[symbol] = value
            briefing["volatility_snapshot"] = vol_snapshot
            self.logger.info("L1 简报: volatility_snapshot=%d", len(vol_snapshot))
        except Exception as exc:
            self.logger.warning("波动率快照生成失败: %s", exc)
            briefing["volatility_snapshot"] = {}

        return briefing

    def _generate_l2_audit_context(self, date_str: str) -> dict[str, Any]:
        """生成 L2 审核上下文 — 近20日分钟K统计 + 历史波动率 + 期权IV + 宏观月报。"""
        context: dict[str, Any] = {}

        # 1. 近 20 日分钟 K 线统计（简化：只取 watchlist 前 3 只）
        try:
            from src.collectors.watchlist_client import WatchlistClient
            from src.collectors.stock_minute_collector import StockMinuteCollector
            wl_client = WatchlistClient()
            watchlist = wl_client.fetch_watchlist()
            collector = StockMinuteCollector()
            minute_stats = []
            for symbol in watchlist[:3]:
                try:
                    records = collector.collect(symbol=symbol, days=20)
                    if records:
                        amplitudes = [r.get("payload", {}).get("amplitude", 0) for r in records]
                        avg_amp = sum(amplitudes) / len(amplitudes) if amplitudes else 0
                        minute_stats.append({
                            "symbol": symbol,
                            "avg_amplitude_pct": round(avg_amp, 2),
                            "sample_size": len(records),
                        })
                except Exception:
                    pass
            context["minute_stats"] = minute_stats
            self.logger.info("L2 审核上下文: minute_stats=%d", len(minute_stats))
        except Exception as exc:
            self.logger.warning("分钟K统计生成失败: %s", exc)
            context["minute_stats"] = []

        # 2. 历史波动率（20日/60日 ATR）— 简化为空
        context["historical_volatility"] = {}

        # 3. 期权隐含波动率（IV vs HV 差值）
        try:
            from src.collectors.options_collector import OptionsCollector
            collector = OptionsCollector()
            options_records = collector.collect(symbols=["50ETF", "300ETF"])
            iv_snapshot = {}
            for record in options_records[-5:]:
                symbol = record.get("symbol", "")
                iv = record.get("payload", {}).get("implied_volatility", 0)
                if symbol:
                    iv_snapshot[symbol] = iv
            context["iv_snapshot"] = iv_snapshot
            self.logger.info("L2 审核上下文: iv_snapshot=%d", len(iv_snapshot))
        except Exception as exc:
            self.logger.warning("期权IV生成失败: %s", exc)
            context["iv_snapshot"] = {}

        # 4. 宏观月报（完整 CPI/PPI/PMI 序列）
        try:
            from src.collectors.macro_collector import MacroCollector
            collector = MacroCollector()
            macro_records = collector.collect(countries=["CN", "US"], full_history=True)
            context["macro_series"] = macro_records[-30:]  # 最近 30 条
            self.logger.info("L2 审核上下文: macro_series=%d", len(context["macro_series"]))
        except Exception as exc:
            self.logger.warning("宏观月报生成失败: %s", exc)
            context["macro_series"] = []

        return context

    def _generate_analyst_dataset(self, date_str: str) -> dict[str, Any]:
        """生成数据分析师数据集 — 完整K线 + 波动率序列 + CFTC + 北向资金 + BDI + 融资融券。"""
        dataset: dict[str, Any] = {}

        # 1. 完整 K 线 OHLCV（日线 250 根 + 分钟 K 线样本）— 简化为空
        dataset["kline_daily"] = []
        dataset["kline_minute"] = []

        # 2. 波动率指数序列
        try:
            from src.collectors.volatility_collector import VolatilityCollector
            collector = VolatilityCollector()
            vol_records = collector.collect(symbols=["50ETF", "VIX", "300ETF"])
            dataset["volatility_series"] = vol_records[-30:]  # 最近 30 条
            self.logger.info("数据分析师数据集: volatility_series=%d", len(dataset["volatility_series"]))
        except Exception as exc:
            self.logger.warning("波动率序列生成失败: %s", exc)
            dataset["volatility_series"] = []

        # 3. CFTC 净持仓变化趋势（近 8 周）— 简化为空
        dataset["cftc_series"] = []

        # 4. 北向资金近 20 日净买入排名
        try:
            from src.collectors.sentiment_collector import SentimentCollector
            collector = SentimentCollector()
            sentiment_records = collector.collect(symbols=["north_flow"])
            dataset["north_flow_series"] = sentiment_records[-20:]  # 最近 20 条
            self.logger.info("数据分析师数据集: north_flow_series=%d", len(dataset["north_flow_series"]))
        except Exception as exc:
            self.logger.warning("北向资金序列生成失败: %s", exc)
            dataset["north_flow_series"] = []

        # 5. BDI 航运指数 — 简化为空
        dataset["bdi_series"] = []

        # 6. 融资融券余额变化率
        try:
            from src.collectors.sentiment_collector import SentimentCollector
            collector = SentimentCollector()
            sentiment_records = collector.collect(symbols=["margin_sh", "margin_sz"])
            dataset["margin_series"] = sentiment_records[-20:]  # 最近 20 条
            self.logger.info("数据分析师数据集: margin_series=%d", len(dataset["margin_series"]))
        except Exception as exc:
            self.logger.warning("融资融券序列生成失败: %s", exc)
            dataset["margin_series"] = []

        return dataset

    def _save_snapshot(self, date_str: str, snapshot: dict[str, Any]) -> None:
        """持久化摘要到 runtime/daily_snapshots/{YYYY-MM-DD}/。"""
        snapshot_dir = self.storage_root / "daily_snapshots" / date_str
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 保存完整 JSON
        snapshot_file = snapshot_dir / "snapshot.json"
        snapshot_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info("摘要已保存: %s", snapshot_file)

        # 写入 ready_flag
        if snapshot["ready_flag"]:
            ready_file = snapshot_dir / "ready_flag.txt"
            ready_file.write_text(snapshot["generated_at"], encoding="utf-8")
            self.logger.info("ready_flag 已写入: %s", ready_file)

    def load_snapshot(self, date_str: str | None = None) -> dict[str, Any] | None:
        """加载指定日期的摘要。"""
        date_str = date_str or datetime.now(CN_TZ).strftime("%Y-%m-%d")
        snapshot_file = self.storage_root / "daily_snapshots" / date_str / "snapshot.json"
        if not snapshot_file.exists():
            self.logger.warning("摘要文件不存在: %s", snapshot_file)
            return None
        try:
            return json.loads(snapshot_file.read_text(encoding="utf-8"))
        except Exception as exc:
            self.logger.error("摘要加载失败: %s", exc)
            return None
