"""
EmailNotifier — TASK-0014 P1
通过 SMTP 发送 HTML 邮件通知，从环境变量读取配置，无真实凭证。
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dispatcher import RiskEvent

logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件 SMTP 通道。通过 NOTIFY_EMAIL_ENABLED 可整体禁用。"""

    def __init__(self) -> None:
        raw = os.environ.get("NOTIFY_EMAIL_ENABLED", "false").strip().lower()
        self._enabled = raw == "true"
        self._smtp_host: str = os.environ.get("ALERT_EMAIL_SMTP_HOST", "")
        self._smtp_port: int = int(os.environ.get("ALERT_EMAIL_SMTP_PORT", "587"))
        self._smtp_user: str = os.environ.get("ALERT_EMAIL_SMTP_USER", "")
        self._smtp_password: str = os.environ.get("ALERT_EMAIL_SMTP_PASSWORD", "")
        self._from_addr: str = os.environ.get("ALERT_EMAIL_FROM", "")
        self._to_addr: str = os.environ.get("ALERT_EMAIL_TO", "")

    def send(self, event: "RiskEvent") -> bool:
        """
        发送 HTML 邮件通知。
        - disabled → 直接返回 True（跳过即通过）
        - 成功发送 → True
        - 失败 → logging.error + 返回 False
        """
        if not self._enabled:
            logger.debug("EmailNotifier disabled, skipping event %s", event.event_code)
            return True

        missing = [
            name
            for name, val in [
                ("ALERT_EMAIL_SMTP_HOST", self._smtp_host),
                ("ALERT_EMAIL_SMTP_USER", self._smtp_user),
                ("ALERT_EMAIL_SMTP_PASSWORD", self._smtp_password),
                ("ALERT_EMAIL_FROM", self._from_addr),
                ("ALERT_EMAIL_TO", self._to_addr),
            ]
            if not val
        ]
        if missing:
            logger.error("EmailNotifier missing env vars: %s", missing)
            return False

        subject = f"[SimTrading-{event.risk_level}] {event.event_code}: {event.symbol}"
        html_body = f"""
<html><body>
<h2>[{event.stage_preset.upper()}] {event.risk_level} — {event.event_code}</h2>
<table border="1" cellpadding="4" cellspacing="0">
  <tr><th>Field</th><th>Value</th></tr>
  <tr><td>task_id</td><td>{event.task_id}</td></tr>
  <tr><td>stage_preset</td><td>{event.stage_preset}</td></tr>
  <tr><td>risk_level</td><td>{event.risk_level}</td></tr>
  <tr><td>account_id</td><td>{event.account_id}</td></tr>
  <tr><td>strategy_id</td><td>{event.strategy_id}</td></tr>
  <tr><td>symbol</td><td>{event.symbol}</td></tr>
  <tr><td>signal_id</td><td>{event.signal_id}</td></tr>
  <tr><td>trace_id</td><td>{event.trace_id}</td></tr>
  <tr><td>event_code</td><td>{event.event_code}</td></tr>
  <tr><td>reason</td><td>{event.reason}</td></tr>
</table>
</body></html>
"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from_addr
        msg["To"] = self._to_addr
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if self._smtp_port == 465:
                with smtplib.SMTP_SSL(self._smtp_host, self._smtp_port, timeout=15) as server:
                    server.login(self._smtp_user, self._smtp_password)
                    server.sendmail(self._from_addr, [self._to_addr], msg.as_string())
            else:
                with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self._smtp_user, self._smtp_password)
                    server.sendmail(self._from_addr, [self._to_addr], msg.as_string())
            return True
        except smtplib.SMTPException as exc:
            logger.error("EmailNotifier SMTPException for event %s: %s", event.event_code, exc)
            return False
        except OSError as exc:
            logger.error("EmailNotifier OSError for event %s: %s", event.event_code, exc)
            return False
        except Exception as exc:
            logger.error("EmailNotifier unexpected error for event %s: %s", event.event_code, exc)
            return False
