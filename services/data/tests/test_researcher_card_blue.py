"""测试飞书卡片三类分流（blue/orange/red）"""

import pytest
import sys
import os
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.notify.card_templates import (
    build_report_card,
    build_failure_card,
    build_urgent_card,
    build_daily_digest_card,
)


@pytest.fixture
def mock_report():
    """模拟研究报告数据"""
    return {
        "report_id": "rep-001",
        "date": "2026-04-15",
        "hour": "08",
        "minute": "05",
        "futures_summary": {
            "market_overview": "市场平稳运行",
            "symbols": {
                "rb": {"trend": "偏空", "change_pct": -0.5, "confidence": 0.7},
                "au": {"trend": "偏多", "change_pct": 0.3, "confidence": 0.8},
                "cu": {"trend": "震荡", "change_pct": 0.0, "confidence": 0.5},
            }
        },
        "stocks_summary": {"symbols_covered": 20},
        "crawler_stats": {
            "sources_crawled": 5,
            "articles_processed": 15,
            "news_items": [
                {"source": "金十", "title": "美联储维持利率", "summary": "...", "time": "08:30"},
                {"source": "东财", "title": "螺纹钢库存下降", "summary": "...", "time": "08:35"},
            ]
        },
        "change_highlights": ["螺纹钢库存大幅下降"],
        "elapsed_seconds": 45.0
    }


def test_report_card_is_blue(mock_report):
    """测试研究报告卡片用 blue 模板"""
    card = build_report_card(mock_report)

    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["template"] == "blue"


def test_report_card_icon_is_chart(mock_report):
    """测试研究报告卡片图标是 📈"""
    card = build_report_card(mock_report)

    title = card["card"]["header"]["title"]["content"]
    assert "📈" in title
    assert "📊" not in title  # 不是旧的图标


def test_report_card_title_format(mock_report):
    """测试研究报告卡片标题格式"""
    card = build_report_card(mock_report)

    title = card["card"]["header"]["title"]["content"]
    assert "JBT 数据研究员" in title
    assert "08:00" in title  # 小时制
    assert "2026-04-15" in title


def test_report_card_has_footer(mock_report):
    """测试研究报告卡片有 note footer"""
    card = build_report_card(mock_report)

    elements = card["card"]["elements"]
    # 最后一个元素应该是 note
    last_element = elements[-1]
    assert last_element["tag"] == "note"

    footer_text = last_element["elements"][0]["content"]
    assert "JBT 数据研究员" in footer_text
    assert "Alienware" in footer_text
    assert "采集" in footer_text  # 采集统计


def test_report_card_is_concise(mock_report):
    """测试研究报告卡片精炼（不冗长）"""
    card = build_report_card(mock_report)

    elements = card["card"]["elements"]
    # 应该有：期货研判 + hr + 要闻摘要 + hr + 综合研判 + hr + note = 7 个元素
    assert len(elements) == 7

    # 检查期货研判是否精炼（按偏多/偏空/震荡分组）
    futures_elem = elements[0]
    futures_content = futures_elem["text"]["content"]
    assert "期货研判" in futures_content
    assert ("🔴" in futures_content or "🟢" in futures_content or "⚪" in futures_content)


def test_failure_card_is_orange():
    """测试失败卡片用 orange 模板"""
    card = build_failure_card("08", "网络超时")

    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["template"] == "orange"


def test_failure_card_title():
    """测试失败卡片标题"""
    card = build_failure_card("08", "网络超时")

    title = card["card"]["header"]["title"]["content"]
    assert "⚠️" in title
    assert "JBT 数据研究员" in title
    assert "报警" in title
    assert "执行失败" in title


def test_failure_card_has_footer():
    """测试失败卡片有 note footer"""
    card = build_failure_card("08", "网络超时")

    elements = card["card"]["elements"]
    last_element = elements[-1]
    assert last_element["tag"] == "note"

    footer_text = last_element["elements"][0]["content"]
    assert "JBT 数据研究员" in footer_text
    assert "Alienware" in footer_text


def test_urgent_card_is_red():
    """测试突发卡片用 red 模板"""
    card = build_urgent_card(
        headline="交易所紧急通知：暂停交易",
        source="上期所",
        url="https://www.shfe.com.cn/notice/123",
        detected_at="2026-04-15 10:30:00"
    )

    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["template"] == "red"


def test_urgent_card_has_headline():
    """测试突发卡片包含 headline + source + url"""
    card = build_urgent_card(
        headline="交易所紧急通知：暂停交易",
        source="上期所",
        url="https://www.shfe.com.cn/notice/123",
        detected_at="2026-04-15 10:30:00"
    )

    title = card["card"]["header"]["title"]["content"]
    assert "🚨" in title
    assert "紧急" in title

    # 检查内容
    content_elem = card["card"]["elements"][0]
    content = content_elem["text"]["content"]
    assert "交易所紧急通知" in content
    assert "上期所" in content
    assert "https://www.shfe.com.cn/notice/123" in content
    assert "2026-04-15 10:30:00" in content


def test_urgent_card_has_footer():
    """测试突发卡片有 note footer"""
    card = build_urgent_card(
        headline="重大政策调整",
        source="金十",
        url="https://www.jin10.com/123",
        detected_at="2026-04-15 10:30:00"
    )

    elements = card["card"]["elements"]
    last_element = elements[-1]
    assert last_element["tag"] == "note"

    footer_text = last_element["elements"][0]["content"]
    assert "JBT 数据研究员" in footer_text
    assert "突发紧急" in footer_text
    assert "Alienware" in footer_text


def test_daily_digest_card_is_blue():
    """测试每日日报卡片用 blue 模板"""
    digest = {
        "date": "2026-04-15",
        "success_count": 4,
        "total_count": 4,
        "total_elapsed": 180.0,
        "futures_total": 40,
        "stocks_total": 80,
        "articles_total": 60,
        "suggestions": ["市场平稳", "无重大变化"]
    }

    card = build_daily_digest_card(digest)

    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["template"] == "blue"


def test_all_cards_have_footer():
    """测试所有卡片都有 note footer"""
    mock_report = {
        "report_id": "rep-001",
        "date": "2026-04-15",
        "hour": "08",
        "minute": "05",
        "futures_summary": {"market_overview": "平稳", "symbols": {}},
        "stocks_summary": {"symbols_covered": 0},
        "crawler_stats": {"sources_crawled": 0, "articles_processed": 0, "news_items": []},
    }

    cards = [
        build_report_card(mock_report),
        build_failure_card("08", "错误"),
        build_urgent_card("标题", "来源", "url", "时间"),
        build_daily_digest_card({
            "date": "2026-04-15",
            "success_count": 0,
            "total_count": 0,
            "total_elapsed": 0,
            "futures_total": 0,
            "stocks_total": 0,
            "articles_total": 0,
            "suggestions": []
        })
    ]

    for card in cards:
        elements = card["card"]["elements"]
        last_element = elements[-1]
        assert last_element["tag"] == "note"
        footer_text = last_element["elements"][0]["content"]
        assert "JBT 数据研究员" in footer_text
        assert "Alienware" in footer_text


def test_report_card_futures_brief_grouping(mock_report):
    """测试期货研判按偏多/偏空/震荡分组"""
    card = build_report_card(mock_report)

    futures_elem = card["card"]["elements"][0]
    futures_content = futures_elem["text"]["content"]

    # 应该包含分组标记
    assert "🔴 偏空" in futures_content or "偏空" in futures_content
    assert "🟢 偏多" in futures_content or "偏多" in futures_content
    assert "⚪ 震荡" in futures_content or "震荡" in futures_content


def test_report_card_news_brief_with_source(mock_report):
    """测试要闻摘要标注来源"""
    card = build_report_card(mock_report)

    news_elem = card["card"]["elements"][2]  # 第3个元素是要闻摘要
    news_content = news_elem["text"]["content"]

    assert "要闻摘要" in news_content
    # 应该标注来源
    assert "金十" in news_content or "东财" in news_content
