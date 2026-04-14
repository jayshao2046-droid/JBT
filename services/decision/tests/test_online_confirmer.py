"""Tests for TASK-0112 Batch B: L3 online confirmer.

测试覆盖：
- 触发条件满足 → 调 L3 → confirmed
- 触发条件满足 → 调 L3 → not confirmed → hold
- 触发条件不满足 → 跳过 L3 → 直接 L2 结论
- DashScope 超时 → 降级为 L2
- 全部失败 → 降级 + 标记 l3_degraded
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.online_confirmer import OnlineConfirmer


@pytest.fixture
def online_confirmer():
    """Create OnlineConfirmer instance."""
    return OnlineConfirmer()


def test_should_trigger_l3_high_signal_strength(online_confirmer):
    """测试触发条件 1: signal_strength > 0.8。"""
    should_trigger = online_confirmer.should_trigger_l3(
        signal_strength=0.85,
        l1_confidence=0.7,
        l2_confidence=0.75,
        risk_assessment="medium",
    )
    assert should_trigger is True


def test_should_trigger_l3_confidence_diff(online_confirmer):
    """测试触发条件 2: L1/L2 confidence 差异 > 0.3。"""
    should_trigger = online_confirmer.should_trigger_l3(
        signal_strength=0.6,
        l1_confidence=0.5,
        l2_confidence=0.85,
        risk_assessment="low",
    )
    assert should_trigger is True


def test_should_trigger_l3_high_risk(online_confirmer):
    """测试触发条件 3: risk_assessment = high。"""
    should_trigger = online_confirmer.should_trigger_l3(
        signal_strength=0.6,
        l1_confidence=0.7,
        l2_confidence=0.75,
        risk_assessment="high",
    )
    assert should_trigger is True


def test_should_not_trigger_l3(online_confirmer):
    """测试不触发 L3：所有条件均不满足。"""
    should_trigger = online_confirmer.should_trigger_l3(
        signal_strength=0.6,
        l1_confidence=0.7,
        l2_confidence=0.75,
        risk_assessment="medium",
    )
    assert should_trigger is False


@pytest.mark.asyncio
async def test_l3_confirmed(online_confirmer):
    """测试 L3 确认通过路径。"""
    # Mock API key
    online_confirmer.api_key = "test-api-key"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "confirmed": True,
                            "reasoning": "L3 综合评估通过",
                        })
                    }
                }
            ]
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        decision_context = {
            "strategy_id": "test-strategy",
            "symbol": "RB2505",
            "signal": 1,
            "signal_strength": 0.85,
            "l1_result": {"pass": True, "confidence": 0.8},
            "l2_result": {"approve": True, "confidence": 0.85},
        }

        result = await online_confirmer.confirm(decision_context)

        assert result["confirmed"] is True
        assert result["degraded"] is False
        assert "通过" in result["reasoning"]


@pytest.mark.asyncio
async def test_l3_rejected(online_confirmer):
    """测试 L3 拒绝路径。"""
    # Mock API key
    online_confirmer.api_key = "test-api-key"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "confirmed": False,
                            "reasoning": "L3 综合评估未通过",
                        })
                    }
                }
            ]
        }
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        decision_context = {
            "strategy_id": "test-strategy",
            "symbol": "RB2505",
            "signal": 1,
            "signal_strength": 0.85,
            "l1_result": {"pass": True, "confidence": 0.8},
            "l2_result": {"approve": True, "confidence": 0.85},
        }

        result = await online_confirmer.confirm(decision_context)

        assert result["confirmed"] is False
        assert result["degraded"] is False
        assert "未通过" in result["reasoning"]


@pytest.mark.asyncio
async def test_l3_timeout_degrade_to_l2(online_confirmer):
    """测试 DashScope 超时 → 降级为 L2。"""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=Exception("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        decision_context = {
            "strategy_id": "test-strategy",
            "symbol": "RB2505",
            "signal": 1,
            "signal_strength": 0.85,
            "l1_result": {"pass": True, "confidence": 0.8},
            "l2_result": {"approve": True, "confidence": 0.85},
        }

        result = await online_confirmer.confirm(decision_context)

        assert result["degraded"] is True
        assert result["model_used"] == "L2_degraded"
        assert result["confirmed"] is True  # 采用 L2 的 approve=True
        assert "降级" in result["reasoning"]


@pytest.mark.asyncio
async def test_l3_all_fail_degrade_to_l2(online_confirmer):
    """测试全部模型失败 → 降级为 L2。"""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=Exception("All models failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        decision_context = {
            "strategy_id": "test-strategy",
            "symbol": "RB2505",
            "signal": 1,
            "signal_strength": 0.85,
            "l1_result": {"pass": True, "confidence": 0.8},
            "l2_result": {"approve": False, "confidence": 0.65},
        }

        result = await online_confirmer.confirm(decision_context)

        assert result["degraded"] is True
        assert result["model_used"] == "L2_degraded"
        assert result["confirmed"] is False  # 采用 L2 的 approve=False
        assert "降级" in result["reasoning"]


@pytest.mark.asyncio
async def test_l3_no_api_key_degrade(online_confirmer):
    """测试 API key 未配置 → 直接降级。"""
    # 临时清空 API key
    original_api_key = online_confirmer.api_key
    online_confirmer.api_key = ""

    decision_context = {
        "strategy_id": "test-strategy",
        "symbol": "RB2505",
        "signal": 1,
        "signal_strength": 0.85,
        "l1_result": {"pass": True, "confidence": 0.8},
        "l2_result": {"approve": True, "confidence": 0.85},
    }

    result = await online_confirmer.confirm(decision_context)

    assert result["degraded"] is True
    assert result["model_used"] == "L2_degraded"
    assert "API key" in result["reasoning"]

    # 恢复 API key
    online_confirmer.api_key = original_api_key
