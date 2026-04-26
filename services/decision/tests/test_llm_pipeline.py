"""Tests for LLM pipeline.

TASK-0083: 补充集成测试（data 拉取、auto_backtest）。
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.client import OllamaClient
from src.llm.pipeline import LLMPipeline


@pytest.mark.asyncio
async def test_ollama_client_timeout():
    """Test OllamaClient handles timeout correctly."""
    client = OllamaClient()

    with patch.object(client, "_client") as mock_client:
        mock_client.post = AsyncMock(side_effect=Exception("Timeout"))

        result = await client.chat("test-model", [{"role": "user", "content": "test"}])

        assert "error" in result
        assert result["model"] == "test-model"
        assert result["content"] == ""


@pytest.mark.asyncio
async def test_ollama_client_normal_response():
    """Test OllamaClient parses normal response correctly."""
    client = OllamaClient()

    mock_response = AsyncMock()
    mock_response.json = lambda: {
        "message": {"content": "Generated code here"},
        "model": "deepcoder:14b",
        "total_duration": 1000000000,
        "eval_count": 100,
        "eval_duration": 500000000,
    }
    mock_response.raise_for_status = lambda: None

    with patch.object(client, "_client") as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await client.chat("deepcoder:14b", [{"role": "user", "content": "test"}])

        assert "error" not in result
        assert result["content"] == "Generated code here"
        assert result["model"] == "deepcoder:14b"
        assert result["total_duration"] == 1000000000
        assert result["eval_count"] == 100


@pytest.mark.asyncio
async def test_pipeline_research_normal():
    """Test LLMPipeline.research normal execution."""
    mock_client = AsyncMock(spec=OllamaClient)
    mock_client.chat = AsyncMock(
        return_value={
            "content": "def strategy():\n    pass",
            "model": "deepcoder:14b",
            "total_duration": 1000000000,
            "eval_count": 50,
            "eval_duration": 500000000,
        }
    )

    pipeline = LLMPipeline(client=mock_client)
    result = await pipeline.research("Create a momentum strategy")

    assert "error" not in result
    assert "def strategy()" in result["code"]
    assert result["model"] == "deepcoder:14b"
    assert result["duration_seconds"] > 0


@pytest.mark.asyncio
async def test_pipeline_audit_normal():
    """Test LLMPipeline.audit normal execution."""
    mock_client = AsyncMock(spec=OllamaClient)
    audit_response = {
        "passed": True,
        "issues": [],
        "risk_level": "low",
        "summary": "Code looks good",
    }
    mock_client.chat = AsyncMock(
        return_value={
            "content": json.dumps(audit_response),
            "model": "qwen3:14b",
            "total_duration": 1000000000,
            "eval_count": 50,
            "eval_duration": 500000000,
        }
    )

    pipeline = LLMPipeline(client=mock_client)
    result = await pipeline.audit("def strategy():\n    pass")

    assert "error" not in result
    assert result["passed"] is True
    assert result["risk_level"] == "low"
    assert result["model"] == "qwen3:14b"
    assert result["duration_seconds"] > 0


@pytest.mark.asyncio
async def test_pipeline_full_audit_failed_skips_analyze():
    """Test full_pipeline skips analyze when audit fails."""
    mock_client = AsyncMock(spec=OllamaClient)

    # Mock research response
    research_response = {
        "content": "def strategy():\n    pass",
        "model": "deepcoder:14b",
        "total_duration": 1000000000,
        "eval_count": 50,
        "eval_duration": 500000000,
    }

    # Mock audit response (failed)
    audit_response = {
        "passed": False,
        "issues": ["Missing stop loss"],
        "risk_level": "high",
        "summary": "Code has issues",
    }

    mock_client.chat = AsyncMock(
        side_effect=[
            research_response,
            {"content": json.dumps(audit_response), "model": "qwen3:14b"},
        ]
    )

    pipeline = LLMPipeline(client=mock_client)
    result = await pipeline.full_pipeline(
        "Create a momentum strategy", performance_data={"sharpe": 1.5}
    )

    assert "research_result" in result
    assert "audit_result" in result
    assert result["audit_result"]["passed"] is False
    assert "analysis_result" in result
    assert result["analysis_result"]["skipped"] is True
    assert result["analysis_result"]["reason"] == "Audit did not pass"
    assert result["total_duration_seconds"] > 0


@pytest.mark.asyncio
async def test_pipeline_full_normal_execution():
    """Test full_pipeline completes all steps successfully."""
    mock_client = AsyncMock(spec=OllamaClient)

    # Mock research response
    research_response = {
        "content": "def strategy():\n    pass",
        "model": "deepcoder:14b",
        "total_duration": 1000000000,
        "eval_count": 50,
        "eval_duration": 500000000,
    }

    # Mock audit response (passed)
    audit_response = {
        "passed": True,
        "issues": [],
        "risk_level": "low",
        "summary": "Code looks good",
    }

    # Mock analysis response
    analysis_response = {
        "content": "Strategy shows good momentum characteristics",
        "model": "phi4-reasoning:14b",
        "total_duration": 1000000000,
        "eval_count": 50,
        "eval_duration": 500000000,
    }

    mock_client.chat = AsyncMock(
        side_effect=[
            research_response,
            {"content": json.dumps(audit_response), "model": "qwen3:14b"},
            analysis_response,
        ]
    )

    pipeline = LLMPipeline(client=mock_client)
    result = await pipeline.full_pipeline(
        "Create a momentum strategy", performance_data={"sharpe": 1.5, "max_drawdown": -0.15}
    )

    assert "research_result" in result
    assert "audit_result" in result
    assert "analysis_result" in result
    assert result["audit_result"]["passed"] is True
    assert "skipped" not in result["analysis_result"]
    assert "Strategy shows good momentum" in result["analysis_result"]["analysis"]
    assert result["total_duration_seconds"] > 0


@pytest.mark.asyncio
async def test_pipeline_auto_backtest():
    """Test full_pipeline with auto_backtest=True.

    TASK-0083: 测试自动沙箱回测功能。
    """
    mock_client = AsyncMock(spec=OllamaClient)

    # Mock research response
    research_response = {
        "content": "def strategy():\n    pass",
        "model": "deepcoder:14b",
        "total_duration": 1000000000,
        "eval_count": 50,
        "eval_duration": 500000000,
    }

    # Mock audit response (passed)
    audit_response = {
        "passed": True,
        "issues": [],
        "risk_level": "low",
        "summary": "Code looks good",
    }

    mock_client.chat = AsyncMock(
        side_effect=[
            research_response,
            {"content": json.dumps(audit_response), "model": "qwen3:14b"},
        ]
    )

    pipeline = LLMPipeline(client=mock_client)
    result = await pipeline.full_pipeline(
        "Create a momentum strategy", auto_backtest=True
    )

    assert "research_result" in result
    assert "audit_result" in result
    assert result["audit_result"]["passed"] is True
    assert "backtest_result" in result
    # 当前返回占位结果
    assert result["backtest_result"]["status"] == "not_implemented"


@pytest.mark.asyncio
async def test_pipeline_analyze_with_symbol():
    """Test analyze with symbol and timeframe for auto data fetching.

    TASK-0083: 测试自动拉取 K 线数据功能。
    """
    mock_client = AsyncMock(spec=OllamaClient)

    analysis_response = {
        "content": "Strategy shows good momentum characteristics",
        "model": "phi4-reasoning:14b",
        "total_duration": 1000000000,
        "eval_count": 50,
        "eval_duration": 500000000,
    }

    mock_client.chat = AsyncMock(return_value=analysis_response)

    pipeline = LLMPipeline(client=mock_client)

    # Mock _fetch_kline_data
    with patch.object(pipeline, "_fetch_kline_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [
            {"open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000},
            {"open": 103, "high": 107, "low": 102, "close": 106, "volume": 1200},
        ]

        result = await pipeline.analyze(
            {"sharpe": 1.5}, symbol="000001.SZ", timeframe="1m"
        )

        assert "error" not in result
        assert "analysis" in result
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_kline_data_fallback_uses_current_api_params():
    """Mini fallback 应使用当前 data API 的 start/end/timeframe_minutes 口径。"""
    mock_client = AsyncMock(spec=OllamaClient)
    pipeline = LLMPipeline(client=mock_client)

    with patch.object(pipeline, "_fetch_kline_via_tqsdk", new_callable=AsyncMock) as mock_tqsdk:
        with patch("src.llm.pipeline.httpx.AsyncClient") as mock_client_class:
            mock_tqsdk.return_value = []

            mock_http = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"bars": [{"close": 1.0}]}

            mock_http.get = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_http

            bars = await pipeline._fetch_kline_data(
                "http://localhost:8105",
                "RB2505",
                "1m",
            )

            assert bars == [{"close": 1.0}]
            params = mock_http.get.call_args[1]["params"]
            assert params["symbol"] == "RB2505"
            assert params["timeframe_minutes"] == 1
            assert "start" in params
            assert "end" in params


@pytest.mark.asyncio
async def test_evaluate_researcher_report_uses_local_research_store():
    """pipeline 后段 researcher 消费应走本地 ResearchStore，而不是远端 latest。"""
    mock_client = AsyncMock(spec=OllamaClient)
    pipeline = LLMPipeline(client=mock_client)

    histories = {
        "futures": [
            {
                "report_id": "fut-0900",
                "source_report": {"summary": "早盘震荡", "symbols": ["rb"]},
                "batch_context": {"hour": 9},
                "fact_record": {"generated_at": "2026-04-24T09:00:00"},
            },
            {
                "report_id": "fut-1500",
                "source_report": {"summary": "午盘黑色偏强", "symbols": ["rb", "hc"]},
                "batch_context": {"hour": 15},
                "fact_record": {"generated_at": "2026-04-24T15:00:00"},
            },
        ],
        "stocks": [],
        "news": [
            {
                "report_id": "news-1500",
                "source_report": {
                    "news": [
                        {"title": "钢厂去库", "content": "库存继续下降", "source": "财联社"},
                    ]
                },
                "batch_context": {"hour": 15},
                "fact_record": {"generated_at": "2026-04-24T15:00:00"},
            }
        ],
        "rss": [],
        "sentiment": [],
    }

    store = MagicMock()
    store.get_history.side_effect = lambda report_type, limit=50: histories.get(report_type, [])

    with patch("src.llm.pipeline.ResearchStore", return_value=store):
        with patch.object(pipeline.researcher_phi4_scorer, "_score_report_full", new_callable=AsyncMock) as mock_score:
            with patch.object(pipeline, "_send_feishu_notification", new_callable=AsyncMock) as mock_notify:
                mock_score.return_value = {
                    "score": 82.0,
                    "confidence": "high",
                    "reasoning": "本地库存证完整",
                    "improvements": [],
                    "model": "qwen3:14b-q4_K_M",
                }
                mock_notify.return_value = {"success": True}

                result = await pipeline.evaluate_researcher_report(segment="15:00")

    assert result["notification_sent"] is True
    assert result["score"] == 82.0
    assert result["report"]["source"] == "research_store"
    assert result["report"]["futures_summary"]["market_overview"] == "午盘黑色偏强"
    assert result["report"]["crawler_stats"]["articles_processed"] == 1

    scored_report = mock_score.await_args.kwargs["report"]
    assert scored_report["futures_summary"]["symbols_covered"] == 2
    assert scored_report["crawler_stats"]["news_items"][0]["title"] == "钢厂去库"
    mock_notify.assert_awaited_once()

