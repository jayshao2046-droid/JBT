"""TASK-0104-D2 LLM 上下文注入测试"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_daily_context():
    """Mock 预读上下文数据。"""
    return {
        "researcher_context": {
            "watchlist": ["000001", "000002", "600000"],
            "daily_summary": [
                {"symbol": "000001", "avg_change_pct": 1.5, "avg_volume": 1000000},
                {"symbol": "000002", "avg_change_pct": -0.8, "avg_volume": 800000},
            ],
            "macro_snapshot": {"CN.cpi_yoy": 2.1, "US.cpi_yoy": 3.2},
            "cftc_snapshot": {},
        },
        "l1_briefing": {
            "sentiment_summary": {"north_flow": 1000000, "margin_balance_sh": 5000000},
            "news_titles": ["重大新闻1", "重大新闻2"],
            "volatility_snapshot": {"50ETF": 0.25, "VIX": 18.5},
        },
        "l2_audit_context": {
            "minute_stats": [
                {"symbol": "000001", "avg_amplitude_pct": 2.5, "sample_size": 100},
            ],
            "historical_volatility": {},
            "iv_snapshot": {"50ETF": 0.28, "300ETF": 0.22},
            "macro_series": [],
        },
        "analyst_dataset": {
            "kline_daily": [],
            "kline_minute": [],
            "volatility_series": [{"symbol": "50ETF", "value": 0.25}],
            "cftc_series": [],
            "north_flow_series": [{"date": "2026-04-15", "net_buy": 1000000}],
            "bdi_series": [],
            "margin_series": [{"date": "2026-04-15", "balance": 5000000}],
        },
        "ready_flag": True,
        "generated_at": "2026-04-15T21:00:00+08:00",
        "errors": [],
    }


def test_context_loader_returns_none_when_data_unavailable():
    """data 服务不可用时，get_daily_context() 应返回 None，不抛异常。"""
    from src.llm.context_loader import DailyContextLoader

    with patch("httpx.get") as mock_get:
        mock_get.side_effect = ConnectionError("Connection refused")

        loader = DailyContextLoader()
        result = loader.get()

        assert result is None, "data 服务不可用时应返回 None"


def test_context_loader_caches_within_ttl(mock_daily_context):
    """TTL 内第二次调用不发 HTTP 请求，直接返回缓存。"""
    from src.llm.context_loader import DailyContextLoader

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_daily_context
        mock_get.return_value = mock_response

        loader = DailyContextLoader()

        # 第一次调用
        result1 = loader.get()
        assert result1 == mock_daily_context
        assert mock_get.call_count == 1

        # 第二次调用（TTL 内）
        result2 = loader.get()
        assert result2 == mock_daily_context
        assert mock_get.call_count == 1, "TTL 内不应发起第二次 HTTP 请求"


def test_context_loader_refreshes_after_ttl(mock_daily_context):
    """TTL 过期后强制刷新。"""
    from src.llm.context_loader import DailyContextLoader

    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_daily_context
        mock_get.return_value = mock_response

        loader = DailyContextLoader()

        # 第一次调用
        result1 = loader.get()
        assert result1 == mock_daily_context
        assert mock_get.call_count == 1

        # 模拟 TTL 过期
        loader._loaded_at = time.time() - (loader.TTL_SECONDS + 1)

        # 第二次调用（TTL 过期）
        result2 = loader.get()
        assert result2 == mock_daily_context
        assert mock_get.call_count == 2, "TTL 过期后应发起第二次 HTTP 请求"


@pytest.mark.asyncio
async def test_pipeline_research_with_context(mock_daily_context):
    """有上下文时，LLM 调用的 messages 中包含 researcher_context。"""
    from src.llm.pipeline import LLMPipeline

    with patch("src.llm.pipeline.get_daily_context") as mock_get_ctx:
        mock_get_ctx.return_value = mock_daily_context

        with patch("src.llm.client.OllamaClient.chat") as mock_chat:
            mock_chat.return_value = {"content": "# Generated code", "model": "deepcoder:14b"}

            pipeline = LLMPipeline()
            result = await pipeline.research("生成一个均线策略")

            assert "error" not in result
            assert result["code"] == "# Generated code"

            # 验证 messages 中包含上下文
            call_args = mock_chat.call_args
            messages = call_args[0][1]  # 第二个参数是 messages
            user_content = messages[1]["content"]

            assert "[今日市场预读]" in user_content, "应包含研究员上下文标记"
            assert "000001" in user_content or "000002" in user_content, "应包含 watchlist"


@pytest.mark.asyncio
async def test_pipeline_research_without_context():
    """无上下文（ctx=None）时，LLM 调用行为与原有一致。"""
    from src.llm.pipeline import LLMPipeline

    with patch("src.llm.pipeline.get_daily_context") as mock_get_ctx:
        mock_get_ctx.return_value = None  # 模拟 data 服务不可用

        with patch("src.llm.client.OllamaClient.chat") as mock_chat:
            mock_chat.return_value = {"content": "# Generated code", "model": "deepcoder:14b"}

            pipeline = LLMPipeline()
            result = await pipeline.research("生成一个均线策略")

            assert "error" not in result
            assert result["code"] == "# Generated code"

            # 验证 messages 中不包含上下文标记
            call_args = mock_chat.call_args
            messages = call_args[0][1]
            user_content = messages[1]["content"]

            assert "[今日市场预读]" not in user_content, "无上下文时不应包含上下文标记"
            assert user_content == "生成一个均线策略", "无上下文时 user content 应与 intent 一致"


@pytest.mark.asyncio
async def test_pipeline_audit_without_context():
    """无上下文时，audit() 行为不变。"""
    from src.llm.pipeline import LLMPipeline

    with patch("src.llm.pipeline.get_daily_context") as mock_get_ctx:
        mock_get_ctx.return_value = None

        with patch("src.llm.client.OllamaClient.chat") as mock_chat:
            mock_chat.return_value = {
                "content": '{"passed": true, "issues": [], "risk_level": "low", "summary": "OK"}',
                "model": "qwen3:14b",
            }

            pipeline = LLMPipeline()
            result = await pipeline.audit("# Strategy code")

            assert "error" not in result
            assert result["passed"] is True

            # 验证 messages 中不包含上下文标记
            call_args = mock_chat.call_args
            messages = call_args[0][1]
            user_content = messages[1]["content"]

            assert "[今日审核参考]" not in user_content, "无上下文时不应包含上下文标记"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
