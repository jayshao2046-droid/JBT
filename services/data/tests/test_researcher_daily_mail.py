"""测试早报/晚报生成"""

import pytest
import sys
import os
from datetime import datetime
from pathlib import Path
import json
import tempfile
import shutil

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.notify.daily_digest import DailyDigest
from researcher.notify.card_templates import build_morning_report_html, build_evening_report_html


@pytest.fixture
def temp_reports_dir():
    """创建临时报告目录"""
    temp_dir = tempfile.mkdtemp()
    reports_dir = Path(temp_dir) / "runtime" / "researcher" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    yield reports_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_hourly_reports():
    """模拟整点报告数据"""
    return [
        {
            "report_id": "rep-08-001",
            "date": "2026-04-15",
            "hour": "08",
            "futures_summary": {
                "symbols_covered": 10,
                "market_overview": "开盘平稳",
                "symbols": {
                    "rb": {"trend": "偏空", "change_pct": -0.5, "confidence": 0.7}
                }
            },
            "stocks_summary": {"symbols_covered": 20},
            "crawler_stats": {
                "sources_crawled": 5,
                "articles_processed": 15,
                "news_items": [
                    {"source": "金十", "title": "美联储维持利率", "summary": "...", "time": "08:30"}
                ]
            },
            "change_highlights": ["螺纹钢库存下降"],
            "elapsed_seconds": 45.0
        },
        {
            "report_id": "rep-09-001",
            "date": "2026-04-15",
            "hour": "09",
            "futures_summary": {
                "symbols_covered": 12,
                "market_overview": "震荡上行",
                "symbols": {}
            },
            "stocks_summary": {"symbols_covered": 25},
            "crawler_stats": {
                "sources_crawled": 6,
                "articles_processed": 18,
                "news_items": []
            },
            "change_highlights": [],
            "elapsed_seconds": 50.0
        }
    ]


def test_generate_morning_digest(temp_reports_dir, mock_hourly_reports, monkeypatch):
    """测试早报生成（汇总 08:00~16:00）"""
    # 修改 DailyDigest 的 reports_dir
    digest = DailyDigest()
    monkeypatch.setattr(digest, 'reports_dir', temp_reports_dir)

    # 创建模拟报告文件
    date = "2026-04-15"
    date_dir = temp_reports_dir / date
    date_dir.mkdir(exist_ok=True)

    for report in mock_hourly_reports:
        hour = report["hour"]
        report_path = date_dir / f"{hour}00.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False)

    # 生成早报
    morning_digest = digest.generate_morning_digest(date)

    assert morning_digest["date"] == date
    assert morning_digest["digest_type"] == "早报"
    assert len(morning_digest["reports"]) == 2  # 08:00 和 09:00
    assert morning_digest["success_count"] == 2
    assert "news_sources" in morning_digest
    assert "strategy_suggestions" in morning_digest


def test_generate_evening_digest(temp_reports_dir, monkeypatch):
    """测试晚报生成（汇总 21:00~23:00）"""
    digest = DailyDigest()
    monkeypatch.setattr(digest, 'reports_dir', temp_reports_dir)

    date = "2026-04-15"
    date_dir = temp_reports_dir / date
    date_dir.mkdir(exist_ok=True)

    # 创建夜盘报告
    evening_report = {
        "report_id": "rep-21-001",
        "date": date,
        "hour": "21",
        "futures_summary": {"symbols_covered": 8, "market_overview": "夜盘平稳", "symbols": {}},
        "stocks_summary": {"symbols_covered": 0},
        "crawler_stats": {"sources_crawled": 4, "articles_processed": 10, "news_items": []},
        "change_highlights": [],
        "elapsed_seconds": 40.0
    }

    report_path = date_dir / "2100.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(evening_report, f, ensure_ascii=False)

    # 生成晚报
    evening_digest = digest.generate_evening_digest(date)

    assert evening_digest["date"] == date
    assert evening_digest["digest_type"] == "晚报"
    assert len(evening_digest["reports"]) == 1  # 只有 21:00
    assert evening_digest["success_count"] == 1


def test_morning_html_is_chinese(mock_hourly_reports):
    """测试早报 HTML 全中文"""
    html = build_morning_report_html(mock_hourly_reports, "2026-04-15")

    assert "早报" in html
    assert "市场总览" in html
    assert "信息来源与要闻" in html
    assert "重大策略建议" in html
    assert "变化要点" in html
    assert "采集统计" in html
    assert "JBT 数据研究员" in html
    assert "Alienware" in html


def test_evening_html_is_chinese(mock_hourly_reports):
    """测试晚报 HTML 全中文"""
    html = build_evening_report_html(mock_hourly_reports, "2026-04-15")

    assert "晚报" in html
    assert "市场总览" in html
    assert "信息来源与要闻" in html
    assert "重大策略建议" in html
    assert "JBT 数据研究员" in html


def test_morning_html_contains_sections(mock_hourly_reports):
    """测试早报包含完整四个板块"""
    html = build_morning_report_html(mock_hourly_reports, "2026-04-15")

    # 检查五个板块
    assert "一、市场总览" in html
    assert "二、信息来源与要闻" in html
    assert "三、重大策略建议" in html
    assert "四、变化要点" in html
    assert "五、采集统计" in html


def test_empty_morning_digest(temp_reports_dir, monkeypatch):
    """测试空早报（无报告）"""
    digest = DailyDigest()
    monkeypatch.setattr(digest, 'reports_dir', temp_reports_dir)

    date = "2026-04-15"
    morning_digest = digest.generate_morning_digest(date)

    assert morning_digest["success_count"] == 0
    assert morning_digest["digest_type"] == "早报"
    assert len(morning_digest["reports"]) == 0


def test_empty_evening_digest(temp_reports_dir, monkeypatch):
    """测试空晚报（无报告）"""
    digest = DailyDigest()
    monkeypatch.setattr(digest, 'reports_dir', temp_reports_dir)

    date = "2026-04-15"
    evening_digest = digest.generate_evening_digest(date)

    assert evening_digest["success_count"] == 0
    assert evening_digest["digest_type"] == "晚报"
    assert len(evening_digest["reports"]) == 0


def test_digest_extracts_news_sources(mock_hourly_reports):
    """测试日报提取信息来源"""
    digest = DailyDigest()
    news_sources = digest._extract_news_sources(mock_hourly_reports)

    assert isinstance(news_sources, list)
    assert len(news_sources) > 0
    # 第一个报告有 1 条新闻
    assert any("金十" in str(item) for item in news_sources)


def test_digest_extracts_strategy_suggestions(mock_hourly_reports):
    """测试日报提取策略建议"""
    digest = DailyDigest()
    suggestions = digest._extract_strategy_suggestions(mock_hourly_reports)

    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    # 策略建议应包含板块名称
    assert any("黑色系" in s or "贵金属" in s or "能源" in s for s in suggestions)


def test_legacy_digest_methods_exist(temp_reports_dir, monkeypatch):
    """测试旧调度器调用的兼容方法仍可用。"""
    digest = DailyDigest()
    monkeypatch.setattr(digest, 'reports_dir', temp_reports_dir)

    date = "2026-04-15"
    date_dir = temp_reports_dir / date
    date_dir.mkdir(exist_ok=True)

    sample_hours = {
        "0000": "夜间波动有限",
        "0800": "早盘情绪平稳",
        "1300": "午后板块轮动",
        "2100": "夜盘黑色偏强",
    }
    for filename, overview in sample_hours.items():
        with open(date_dir / f"{filename}.json", "w", encoding="utf-8") as f:
            json.dump({
                "report_id": f"rep-{filename}",
                "date": date,
                "futures_summary": {"symbols_covered": 1, "market_overview": overview, "symbols": {}},
                "stocks_summary": {"symbols_covered": 0},
                "crawler_stats": {"sources_crawled": 1, "articles_processed": 1, "news_items": []},
                "change_highlights": [],
                "elapsed_seconds": 10.0,
            }, f, ensure_ascii=False)

    assert digest.generate_night_digest(date)["digest_type"] == "夜间报"
    assert digest.generate_morning_report_digest(date)["digest_type"] == "上午报"
    assert digest.generate_afternoon_digest(date)["digest_type"] == "下午报"
    assert digest.generate_evening_session_digest(date)["digest_type"] == "夜盘报"
