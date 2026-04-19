"""研究员独立邮件发送器 — 使用 RESEARCHER_EMAIL_* 环境变量"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from ..config import ResearcherConfig


class ResearcherEmailSender:
    """研究员独立邮件发送器"""

    def __init__(self):
        self.smtp_host = os.getenv("RESEARCHER_EMAIL_SMTP_HOST", "")
        self.smtp_port = int(os.getenv("RESEARCHER_EMAIL_SMTP_PORT", "465"))
        self.sender = os.getenv("RESEARCHER_EMAIL_SENDER", "")
        self.password = os.getenv("RESEARCHER_EMAIL_PASSWORD", "")
        self.recipients = os.getenv("RESEARCHER_EMAIL_RECIPIENTS", "").split(",")
        self.recipients = [r.strip() for r in self.recipients if r.strip()]

        self.failure_log_path = Path("runtime/researcher/logs/email_failures.jsonl")
        self.failure_log_path.parent.mkdir(parents=True, exist_ok=True)

    def send_html(self, subject: str, html_content: str) -> bool:
        """
        发送 HTML 邮件

        Args:
            subject: 邮件主题（中文）
            html_content: HTML 内容

        Returns:
            True 表示发送成功，False 表示失败
        """
        if not all([self.smtp_host, self.sender, self.password, self.recipients]):
            self._log_failure("邮件配置不完整", subject)
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = ", ".join(self.recipients)

            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # SSL/TLS 加密
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=ResearcherConfig.SMTP_TIMEOUT) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())

            return True

        except Exception as e:
            self._log_failure(str(e), subject)
            return False

    def send_morning_report(self, date: str, html_content: str) -> bool:
        """
        发送早报邮件

        Args:
            date: 日期 YYYY-MM-DD
            html_content: HTML 内容

        Returns:
            True 表示发送成功
        """
        subject = f"[JBT 数据研究员] {date} 早报"
        return self.send_html(subject, html_content)

    def send_evening_report(self, date: str, html_content: str) -> bool:
        """
        发送晚报邮件

        Args:
            date: 日期 YYYY-MM-DD
            html_content: HTML 内容

        Returns:
            True 表示发送成功
        """
        subject = f"[JBT 数据研究员] {date} 晚报"
        return self.send_html(subject, html_content)

    # ── 4段日报 ──────────────────────────────────────────────────────────

    def send_night_report(self, date: str, html_content: str) -> bool:
        """08:00 发送：汇总 00:00~07:59 夜间动态"""
        subject = f"[JBT 数据研究员] {date} 夜间报 (00-08)"
        return self.send_html(subject, html_content)

    def send_morning_session_report(self, date: str, html_content: str) -> bool:
        """13:00 发送：汇总 08:00~12:59 上午行情"""
        subject = f"[JBT 数据研究员] {date} 上午报 (08-13)"
        return self.send_html(subject, html_content)

    def send_afternoon_report(self, date: str, html_content: str) -> bool:
        """20:00 发送：汇总 13:00~19:59 下午行情"""
        subject = f"[JBT 数据研究员] {date} 下午报 (13-20)"
        return self.send_html(subject, html_content)

    def send_evening_session_report(self, date: str, html_content: str) -> bool:
        """00:00 发送：汇总 20:00~23:59 夜盘"""
        subject = f"[JBT 数据研究员] {date} 夜盘报 (20-24)"
        return self.send_html(subject, html_content)

    def _log_failure(self, error: str, subject: str):
        """记录发送失败到本地日志"""
        failure_record = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "subject": subject
        }

        with open(self.failure_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(failure_record, ensure_ascii=False) + "\n")
