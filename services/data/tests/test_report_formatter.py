"""测试报告格式化器"""
import pytest
from researcher.report_formatter import ReportFormatter
import json


def test_to_json():
    """测试 JSON 格式化"""
    report = {
        "report_id": "RPT-20260416-0845-001",
        "segment": "盘前",
        "generated_at": "2026-04-16T08:45:00"
    }

    json_str = ReportFormatter.to_json(report)

    # 验证是否为有效 JSON
    parsed = json.loads(json_str)
    assert parsed["report_id"] == "RPT-20260416-0845-001"


def test_to_markdown():
    """测试 Markdown 格式化"""
    report = {
        "report_id": "RPT-20260416-0845-001",
        "segment": "盘前",
        "generated_at": "2026-04-16T08:45:00",
        "model": "qwen3:14b",
        "futures_summary": {
            "market_overview": "市场平稳",
            "symbols_covered": 35
        },
        "stocks_summary": {
            "market_overview": "暂无数据",
            "symbols_covered": 0
        },
        "crawler_stats": {
            "sources_crawled": 3,
            "articles_processed": 10,
            "failed_sources": []
        }
    }

    md = ReportFormatter.to_markdown(report)

    # 验证 Markdown 内容
    assert "# 研究员报告" in md
    assert "盘前" in md
    assert "qwen3:14b" in md
