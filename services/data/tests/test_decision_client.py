"""测试决策客户端"""
import pytest
from researcher.decision_client import DecisionClient


def test_decision_client_init():
    """测试决策客户端初始化"""
    client = DecisionClient()

    assert client.mini_api == "http://192.168.31.76:8105/api/v1/researcher/reports"
    assert client.email_to is not None


def test_format_feishu_message():
    """测试飞书消息格式化"""
    client = DecisionClient()

    report = {
        "segment": "盘前",
        "generated_at": "2026-04-16T08:45:00",
        "futures_summary": {
            "symbols_covered": 35
        }
    }

    message = client._format_feishu_message(report)

    assert "盘前" in message
    assert "35" in message
