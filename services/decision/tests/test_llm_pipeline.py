"""Tests for LLM pipeline."""

import json
from unittest.mock import AsyncMock, patch

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
