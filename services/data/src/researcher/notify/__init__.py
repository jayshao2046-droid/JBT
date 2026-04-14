"""研究员独立通知体系 — 完全独立于 data 端通知系统"""

from .feishu_sender import ResearcherFeishuSender
from .email_sender import ResearcherEmailSender
from .card_templates import (
    build_report_card,
    build_failure_card,
    build_daily_digest_card,
    build_urgent_card,
    build_morning_report_html,
    build_evening_report_html,
)
from .daily_digest import DailyDigest

__all__ = [
    "ResearcherFeishuSender",
    "ResearcherEmailSender",
    "build_report_card",
    "build_failure_card",
    "build_daily_digest_card",
    "build_urgent_card",
    "build_morning_report_html",
    "build_evening_report_html",
    "DailyDigest",
]
