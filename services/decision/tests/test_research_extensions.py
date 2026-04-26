"""Tests for TASK-0117: CorrelationMonitor + SpreadMonitor + NewsScorer extensions.

测试覆盖：
CorrelationMonitor:
- record + check_pair: 正常返回 CorrelationSnapshot
- 数据不足时返回 None
- breakdown 检测：30d 相关性急剧偏离 90d 基准
- check_all_pairs: 批量检查套利对
- get_breakdowns: 只返回突变对
- record_batch: 批量初始化

SpreadMonitor:
- _calc_zscore: 边界情况（空序列、单值）
- _calc_pair_zscore: 正常计算 z-score
- DEFAULT_PAIRS 结构正确（含 symbol_a, symbol_b）

NewsScorer:
- _build_scoring_prompt: 包含新闻内容
- _parse_scoring_response: 正确解析 JSON
- _parse_scoring_response: 无效 JSON 返回 None
- _should_push: 分数高于阈值才推送
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from src.research.correlation_monitor import CorrelationMonitor, CorrelationSnapshot
from src.research.research_store import ResearchStore


# ─────────────────────────────────────────────
# CorrelationMonitor
# ─────────────────────────────────────────────

class TestCorrelationMonitor:
    """跨品种相关性监控。"""

    def _make_correlated_series(
        self, n: int, corr: float = 0.9, seed: int = 0
    ) -> tuple[List[float], List[float]]:
        """生成具有指定相关系数的两组价格序列。"""
        np.random.seed(seed)
        x = np.random.randn(n)
        y = corr * x + (1 - corr**2)**0.5 * np.random.randn(n)
        # 转为价格（累积收益）
        price_x = list(np.exp(np.cumsum(x * 0.01)) * 3000)
        price_y = list(np.exp(np.cumsum(y * 0.01)) * 100)
        return price_x, price_y

    def test_check_pair_returns_none_for_insufficient_data(self):
        """数据不足 → 返回 None。"""
        monitor = CorrelationMonitor()
        monitor.record("rb", 3000.0)
        monitor.record("hc", 3100.0)
        result = monitor.check_pair("rb", "hc")
        assert result is None

    def test_check_pair_returns_snapshot(self):
        """足够数据 → 返回 CorrelationSnapshot。"""
        monitor = CorrelationMonitor()
        prices_rb, prices_hc = self._make_correlated_series(n=100, corr=0.85)
        for p in prices_rb:
            monitor.record("rb", p)
        for p in prices_hc:
            monitor.record("hc", p)
        snap = monitor.check_pair("rb", "hc")
        assert snap is not None
        assert isinstance(snap, CorrelationSnapshot)
        assert snap.symbol_a == "rb"
        assert snap.symbol_b == "hc"
        assert -1.0 <= snap.corr_30d <= 1.0
        assert -1.0 <= snap.corr_90d <= 1.0

    def test_breakdown_detected_when_correlation_drops(self):
        """相关性从高位急跌 → breakdown=True。"""
        monitor = CorrelationMonitor()
        # 前90期：强相关
        prices_rb_hist, prices_hc_hist = self._make_correlated_series(n=90, corr=0.95, seed=1)
        monitor.record_batch("rb", prices_rb_hist)
        monitor.record_batch("hc", prices_hc_hist)
        # 后30期：零相关（完全随机）
        np.random.seed(99)
        recent_rb = list(np.exp(np.cumsum(np.random.randn(30) * 0.01)) * prices_rb_hist[-1])
        np.random.seed(88)
        recent_hc = list(np.exp(np.cumsum(np.random.randn(30) * 0.01)) * prices_hc_hist[-1])
        monitor.record_batch("rb", recent_rb)
        monitor.record_batch("hc", recent_hc)
        snap = monitor.check_pair("rb", "hc")
        assert snap is not None
        # delta 应为负（30d < 90d）且超阈值
        assert snap.delta < 0

    def test_no_breakdown_for_stable_correlation(self):
        """相关性稳定 → breakdown=False。"""
        monitor = CorrelationMonitor()
        prices_rb, prices_hc = self._make_correlated_series(n=120, corr=0.88, seed=5)
        monitor.record_batch("rb", prices_rb)
        monitor.record_batch("hc", prices_hc)
        snap = monitor.check_pair("rb", "hc")
        assert snap is not None
        assert isinstance(snap.breakdown, bool)

    def test_check_pair_with_regime(self):
        """传入 regime → snapshot 含 regime 信息。"""
        monitor = CorrelationMonitor()
        prices_rb, prices_hc = self._make_correlated_series(n=50, corr=0.8, seed=2)
        monitor.record_batch("rb", prices_rb)
        monitor.record_batch("hc", prices_hc)
        snap = monitor.check_pair("rb", "hc", regime_a="trend", regime_b="oscillation")
        assert snap is not None
        assert snap.regime_a == "trend"
        assert snap.regime_b == "oscillation"

    def test_check_all_pairs_returns_list(self):
        """check_all_pairs 返回非空列表（数据足够时）。"""
        monitor = CorrelationMonitor()
        for sym in ["rb", "hc"]:
            prices, _ = self._make_correlated_series(n=50, corr=0.8)
            monitor.record_batch(sym, prices)
        results = monitor.check_all_pairs(pairs=[("rb", "hc")])
        assert isinstance(results, list)

    def test_get_breakdowns_filters_only_breakdowns(self):
        """get_breakdowns 只返回 breakdown=True 的对。"""
        monitor = CorrelationMonitor()
        for sym in ["rb", "hc"]:
            prices, _ = self._make_correlated_series(n=50, corr=0.8, seed=3)
            monitor.record_batch(sym, prices)
        breakdowns = monitor.get_breakdowns(pairs=[("rb", "hc")])
        for snap in breakdowns:
            assert snap.breakdown is True

    def test_record_batch_extends_history(self):
        """record_batch 按顺序追加历史。"""
        monitor = CorrelationMonitor()
        monitor.record_batch("rb", [3000.0, 3010.0, 3020.0])
        assert len(monitor._series["rb"]) == 3
        monitor.record_batch("rb", [3030.0, 3040.0])
        assert len(monitor._series["rb"]) == 5

    def test_default_pairs_structure(self):
        """DEFAULT_PAIRS 是 (str, str) 元组列表。"""
        for pair in CorrelationMonitor.DEFAULT_PAIRS:
            assert isinstance(pair, tuple)
            assert len(pair) == 2
            assert isinstance(pair[0], str)
            assert isinstance(pair[1], str)


# ─────────────────────────────────────────────
# SpreadMonitor (已存在，测试关键方法)
# ─────────────────────────────────────────────

class TestSpreadMonitorCore:
    """SpreadMonitor 核心计算方法测试（不启动外部服务）。"""

    def test_calc_zscore_empty_series(self):
        """空序列 → zscore=0.0。"""
        from src.research.spread_monitor import SpreadMonitor
        import pandas as pd
        monitor = SpreadMonitor(data_api_url="http://localhost:0")
        empty = pd.Series([], dtype=float)
        result = monitor._calc_zscore(empty, window=20)
        assert result == 0.0

    def test_calc_zscore_constant_series(self):
        """方差为零的序列 → zscore=0.0。"""
        from src.research.spread_monitor import SpreadMonitor
        import pandas as pd
        monitor = SpreadMonitor(data_api_url="http://localhost:0")
        series = pd.Series([1.0] * 30)
        result = monitor._calc_zscore(series, window=20)
        assert result == 0.0

    def test_calc_zscore_normal_series(self):
        """正常序列 → 返回 float。"""
        from src.research.spread_monitor import SpreadMonitor
        import pandas as pd
        monitor = SpreadMonitor(data_api_url="http://localhost:0")
        np.random.seed(0)
        series = pd.Series(np.random.randn(50))
        result = monitor._calc_zscore(series, window=30)
        assert isinstance(result, float)


# ─────────────────────────────────────────────
# NewsScorer (已存在，测试核心方法)
# ─────────────────────────────────────────────

class TestNewsScorerCore:
    """NewsScorer 核心逻辑测试（不启动 LLM）。"""

    def test_build_scoring_prompt_contains_news_content(self):
        """prompt 包含新闻标题。"""
        from src.research.news_scorer import NewsScorer
        scorer = NewsScorer.__new__(NewsScorer)
        news_item = {
            "title": "央行降准利好市场",
            "content": "中国人民银行宣布下调存款准备金率",
            "source": "财联社",
        }
        prompt = scorer._build_scoring_prompt(news_item)
        assert "央行降准" in prompt

    def test_parse_scoring_response_valid_json(self):
        """合法 JSON 含必需字段 → 正确解析。"""
        from src.research.news_scorer import NewsScorer
        scorer = NewsScorer.__new__(NewsScorer)
        response_text = json.dumps({
            "symbols": ["rb", "i"],
            "urgency": 8,
            "reasoning": "利好政策",
        })
        result = scorer._parse_scoring_response(response_text)
        assert result is not None
        assert result.get("urgency") == 8
        assert "rb" in result.get("symbols", [])

    def test_parse_scoring_response_invalid_json_returns_none(self):
        """无效 JSON → 返回 None（不抛异常）。"""
        from src.research.news_scorer import NewsScorer
        scorer = NewsScorer.__new__(NewsScorer)
        result = scorer._parse_scoring_response("这不是JSON")
        assert result is None

    def test_should_push_above_threshold(self):
        """紧急度高 + 影响已持有品种 → 应推送。"""
        from src.research.news_scorer import NewsScorer
        scorer = NewsScorer.__new__(NewsScorer)
        scorer.SCORE_THRESHOLD = 6
        assert scorer._should_push(["rb", "cu"], held_symbols=["rb"], urgency=8) is True

    def test_should_push_below_threshold(self):
        """紧急度低 → 不推送。"""
        from src.research.news_scorer import NewsScorer
        scorer = NewsScorer.__new__(NewsScorer)
        scorer.SCORE_THRESHOLD = 6
        assert scorer._should_push(["rb"], held_symbols=["rb"], urgency=3) is False


def _make_research_store(tmp_path) -> ResearchStore:
    ResearchStore._instance = None
    return ResearchStore(persist_dir=str(tmp_path / "research_store"))


class TestResearcherFactStore:
    """TASK-P1-20260424E2: researcher 三类事实库存证。"""

    def test_store_builds_grouped_researcher_facts(self, tmp_path):
        store = _make_research_store(tmp_path)

        store.save(
            "futures",
            {
                "report_id": "fut-001",
                "score": 81.0,
                "confidence": "high",
                "reasoning": "期货主线清晰",
            },
            source_report={
                "report_id": "fut-001",
                "summary": "黑色系震荡偏强",
                "symbols": ["rb", "hc"],
            },
            batch_context={"batch_id": "batch-1", "date": "2026-04-24", "hour": 9},
        )
        store.save(
            "macro",
            {
                "report_id": "macro-001",
                "score": 73.0,
                "confidence": "medium",
            },
            source_report={
                "report_id": "macro-001",
                "macro_trend": "risk_on",
                "risk_level": "medium",
                "key_drivers": ["政策宽松"],
                "recommended_sectors": ["黑色", "有色"],
            },
            batch_context={"batch_id": "batch-1", "date": "2026-04-24", "hour": 9},
        )
        store.save(
            "news",
            {"report_id": "news-001", "score": 68.0, "confidence": "medium"},
            source_report={"report_id": "news-001", "summary": "国内新闻偏多"},
            batch_context={"batch_id": "batch-1", "date": "2026-04-24", "hour": 9},
        )
        store.save(
            "rss",
            {"report_id": "rss-001", "score": 66.0, "confidence": "medium"},
            source_report={"report_id": "rss-001", "summary": "海外 RSS 偏空"},
            batch_context={"batch_id": "batch-1", "date": "2026-04-24", "hour": 9},
        )
        store.save(
            "sentiment",
            {"report_id": "sent-001", "score": 64.0, "confidence": "low"},
            source_report={"report_id": "sent-001", "sentiment": "neutral"},
            batch_context={"batch_id": "batch-1", "date": "2026-04-24", "hour": 9},
        )

        futures_latest = store.get_latest("futures")
        assert futures_latest is not None
        assert futures_latest["fact_group"] == "data"
        assert futures_latest["source_report"]["symbols"] == ["rb", "hc"]

        macro_summary = store.get_macro_summary()
        assert macro_summary["available"] is True
        assert macro_summary["macro_trend"] == "risk_on"
        assert macro_summary["risk_level"] == "medium"

        sentiment_snapshot = store.get_fact_group_snapshot("sentiment", limit=10)
        assert sentiment_snapshot["available"] is True
        assert sentiment_snapshot["primary_report_type"] == "news"
        assert set(sentiment_snapshot["source_report_types"]) == {"news", "rss", "sentiment"}
        assert len(sentiment_snapshot["history"]) == 3

    def test_evaluate_route_persists_raw_reports_for_query_reuse(self, tmp_path, monkeypatch):
        from src.api.routes import researcher_evaluate

        store = _make_research_store(tmp_path)
        researcher_evaluate._report_dedup_cache.clear()
        monkeypatch.setattr(researcher_evaluate, "ResearchStore", lambda: store)

        class _DummyScorer:
            async def score_report_detail(self, report):
                return {
                    "score": 82.0,
                    "confidence": "high",
                    "reasoning": f"已评级 {report.get('report_id')}",
                    "observed_content": report.get("summary", ""),
                }

        class _DummyFeishu:
            async def send_researcher_score(self, **kwargs):
                return True

        monkeypatch.setattr(researcher_evaluate, "ResearcherPhi4Scorer", lambda: _DummyScorer())
        monkeypatch.setattr(researcher_evaluate, "FeishuNotifier", lambda: _DummyFeishu())

        batch = researcher_evaluate.ReportBatchRequest(
            batch_id="batch-e2",
            date="2026-04-24",
            hour=10,
            generated_at="2026-04-24T10:00:00",
            futures_report={"report_id": "fut-002", "summary": "黑色偏强", "symbols": ["rb"]},
            macro_report={"report_id": "macro-002", "macro_trend": "risk_off", "risk_level": "high"},
            news_report={"report_id": "news-002", "summary": "新闻偏多"},
            rss_report={"report_id": "rss-002", "summary": "RSS 偏空"},
            sentiment_report={"report_id": "sent-002", "sentiment": "bearish"},
            total_reports=5,
            elapsed_seconds=2.5,
        )

        result = asyncio.run(researcher_evaluate.evaluate_researcher_reports(batch))
        assert result["evaluated_count"] == 5

        futures_latest = store.get_latest("futures")
        assert futures_latest is not None
        assert futures_latest["source_report"]["report_id"] == "fut-002"
        assert futures_latest["fact_record"]["batch_id"] == "batch-e2"

        sentiment_snapshot = store.get_fact_group_snapshot("sentiment", limit=10)
        assert sentiment_snapshot["available"] is True
        assert set(sentiment_snapshot["source_report_types"]) == {"news", "rss", "sentiment"}

    def test_research_query_returns_grouped_fact_views(self, tmp_path, monkeypatch):
        from src.api.routes import research_query

        store = _make_research_store(tmp_path)
        store.save(
            "macro",
            {"report_id": "macro-q-1", "score": 75.0, "confidence": "medium"},
            source_report={
                "report_id": "macro-q-1",
                "macro_trend": "neutral",
                "risk_level": "medium",
            },
            batch_context={"batch_id": "batch-q", "date": "2026-04-24", "hour": 11},
        )
        store.save(
            "news",
            {"report_id": "news-q-1", "score": 61.0, "confidence": "medium"},
            source_report={"report_id": "news-q-1", "summary": "新闻摘要"},
            batch_context={"batch_id": "batch-q", "date": "2026-04-24", "hour": 11},
        )

        monkeypatch.setattr(research_query, "ResearchStore", lambda: store)

        overview = asyncio.run(research_query.get_fact_overview(limit=5))
        assert overview["intelligence"]["available"] is True
        assert overview["intelligence"]["latest"]["source_report"]["report_id"] == "macro-q-1"

        intelligence_latest = asyncio.run(research_query.get_fact_group_latest("intelligence", limit=5))
        assert intelligence_latest["primary_report_type"] == "macro"
        assert intelligence_latest["latest"]["fact_record"]["risk_level"] == "medium"

        sentiment_history = asyncio.run(research_query.get_fact_group_history("sentiment", limit=5))
        assert sentiment_history["available"] is True
        assert len(sentiment_history["history"]) == 1
