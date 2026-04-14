"""测试 — 研究员独立通知体系"""

import pytest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.notify.feishu_sender import ResearcherFeishuSender
from researcher.notify.email_sender import ResearcherEmailSender
from researcher.notify.card_templates import (
    build_report_card,
    build_failure_card,
    build_daily_digest_card,
    build_report_html,
    build_daily_digest_html
)
from researcher.notify.daily_digest import DailyDigest


class TestResearcherFeishuSender:
    """测试飞书发送器"""

    @pytest.mark.asyncio
    async def test_send_card_success(self):
        """测试发送成功"""
        sender = ResearcherFeishuSender()
        sender.webhook_url = "https://example.com/webhook"

        card = {"msg_type": "interactive", "card": {}}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await sender.send_card(card)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_card_no_webhook(self):
        """测试无 webhook 配置"""
        sender = ResearcherFeishuSender()
        sender.webhook_url = ""

        card = {"msg_type": "interactive", "card": {}}
        result = await sender.send_card(card)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_card_failure(self):
        """测试发送失败"""
        sender = ResearcherFeishuSender()
        sender.webhook_url = "https://example.com/webhook"

        card = {"msg_type": "interactive", "card": {}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))

            result = await sender.send_card(card)
            assert result is False


class TestResearcherEmailSender:
    """测试邮件发送器"""

    def test_send_html_no_config(self):
        """测试无配置"""
        sender = ResearcherEmailSender()
        sender.smtp_host = ""

        result = sender.send_html("Test", "<html>Test</html>")
        assert result is False

    def test_send_html_success(self):
        """测试发送成功"""
        sender = ResearcherEmailSender()
        sender.smtp_host = "smtp.example.com"
        sender.smtp_port = 465
        sender.sender = "test@example.com"
        sender.password = "password"
        sender.recipients = ["recipient@example.com"]

        with patch("smtplib.SMTP_SSL") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = sender.send_html("Test", "<html>Test</html>")
            assert result is True
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()


class TestCardTemplates:
    """测试卡片模板"""

    def test_build_report_card(self):
        """测试报告卡片"""
        report = {
            "report_id": "RPT-20260415-盘前-001",
            "date": "2026-04-15",
            "segment": "盘前",
            "generated_at": "2026-04-15T08:45:00",
            "model": "qwen3:14b",
            "hour": "08",
            "minute": "00",
            "futures_summary": {"market_overview": "期货市场整体偏多", "symbols": {}},
            "stocks_summary": {"market_overview": "股票市场震荡"},
            "crawler_stats": {"sources_crawled": 5, "articles_processed": 20, "news_items": []},
            "change_highlights": ["螺纹钢从偏空转偏多"]
        }

        card = build_report_card(report)

        assert card["msg_type"] == "interactive"
        assert card["card"]["header"]["template"] == "blue"
        assert "08:00" in card["card"]["header"]["title"]["content"]
        assert "📈" in card["card"]["header"]["title"]["content"]

    def test_build_failure_card(self):
        """测试失败卡片"""
        card = build_failure_card("08", "网络超时")

        assert card["msg_type"] == "interactive"
        assert card["card"]["header"]["template"] == "orange"
        assert "失败" in card["card"]["header"]["title"]["content"]

    def test_build_daily_digest_card(self):
        """测试日报卡片"""
        digest = {
            "date": "2026-04-15",
            "success_count": 4,
            "total_count": 4,
            "total_elapsed": 120.5,
            "futures_total": 140,
            "stocks_total": 520,
            "articles_total": 80,
            "suggestions": ["市场平稳"]
        }

        card = build_daily_digest_card(digest)

        assert card["msg_type"] == "interactive"
        assert card["card"]["header"]["template"] == "blue"
        assert "总结" in card["card"]["header"]["title"]["content"]

    def test_build_report_html(self):
        """测试报告 HTML"""
        report = {
            "report_id": "RPT-20260415-盘前-001",
            "date": "2026-04-15",
            "segment": "盘前",
            "generated_at": "2026-04-15T08:45:00",
            "model": "qwen3:14b",
            "futures_summary": {"market_overview": "期货市场整体偏多"},
            "stocks_summary": {"market_overview": "股票市场震荡"},
            "crawler_stats": {"sources_crawled": 5, "articles_processed": 20},
            "change_highlights": ["螺纹钢从偏空转偏多"]
        }

        html = build_report_html(report)

        assert "<!DOCTYPE html>" in html
        assert "盘前" in html
        assert "期货市场" in html


class TestDailyDigest:
    """测试每日日报"""

    def test_generate_digest_empty(self, tmp_path):
        """测试空日报"""
        digest_gen = DailyDigest()
        digest_gen.reports_dir = tmp_path

        digest = digest_gen.generate_digest("2026-04-15")

        assert digest["success_count"] == 0
        assert digest["total_count"] == 4
        assert "无研究报告" in digest["suggestions"][0]

    def test_generate_digest_with_reports(self, tmp_path):
        """测试有报告的日报"""
        digest_gen = DailyDigest()
        digest_gen.reports_dir = tmp_path

        # 创建测试报告
        date_dir = tmp_path / "2026-04-15"
        date_dir.mkdir()

        report = {
            "report_id": "RPT-20260415-盘前-001",
            "date": "2026-04-15",
            "segment": "盘前",
            "elapsed_seconds": 30.5,
            "futures_summary": {"symbols_covered": 35},
            "stocks_summary": {"symbols_covered": 130},
            "crawler_stats": {"articles_processed": 20},
            "change_highlights": ["螺纹钢从偏空转偏多"]
        }

        import json
        with open(date_dir / "盘前.json", "w", encoding="utf-8") as f:
            json.dump(report, f)

        digest = digest_gen.generate_digest("2026-04-15")

        assert digest["success_count"] == 1
        assert digest["futures_total"] == 35
        assert digest["stocks_total"] == 130
        assert len(digest["suggestions"]) > 0

    def test_should_send_digest(self):
        """测试是否应该发送日报"""
        digest_gen = DailyDigest()

        # Mock 时间为 02:52
        from datetime import datetime
        with patch("researcher.notify.daily_digest.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 15, 2, 52)
            assert digest_gen.should_send_digest() is True

        # Mock 时间为 10:00
        with patch("researcher.notify.daily_digest.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 15, 10, 0)
            assert digest_gen.should_send_digest() is False
