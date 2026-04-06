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

        level_icon = {"P0": "🚨", "P1": "⚠️", "P2": "🔔"}.get(event.risk_level, "📋")
        header_color = {"P0": "#c0392b", "P1": "#e67e22", "P2": "#27ae60"}.get(event.risk_level, "#2980b9")
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"[JBT-SimTrading-{event.risk_level}] {event.event_code}"
        html_body = f"""
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
  .card {{ background: #fff; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.12); max-width: 560px; margin: 0 auto; overflow: hidden; }}
  .header {{ background: {header_color}; color: #fff; padding: 16px 20px; }}
  .header h2 {{ margin: 0; font-size: 16px; font-weight: 600; }}
  .header .sub {{ margin: 4px 0 0; font-size: 12px; opacity: .85; }}
  .body {{ padding: 16px 20px; }}
  .section-title {{ font-size: 12px; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: .5px; margin: 0 0 8px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ padding: 7px 10px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }}
  td:first-child {{ color: #666; width: 110px; font-weight: 500; }}
  td:last-child {{ color: #222; word-break: break-all; }}
  .reason-row td:last-child {{ color: {header_color}; font-weight: 600; }}
  .hr {{ border: none; border-top: 1px solid #eee; margin: 14px 0; }}
  .footer {{ font-size: 11px; color: #aaa; padding: 10px 20px 14px; border-top: 1px solid #f0f0f0; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2>{level_icon} [{event.stage_preset.upper()}-{event.risk_level}] {event.event_code}</h2>
    <div class="sub">JBT SimTrading 风险通知</div>
  </div>
  <div class="body">
    <p class="section-title">核心信息</p>
    <table>
      <tr class="reason-row"><td>原因</td><td>{event.reason}</td></tr>
      <tr><td>账户</td><td>{event.account_id or '-'}</td></tr>
      <tr><td>事件代码</td><td>{event.event_code}</td></tr>
      <tr><td>品种</td><td>{event.symbol or '-'}</td></tr>
    </table>
    <hr class="hr">
    <p class="section-title">追踪信息</p>
    <table>
      <tr><td>任务</td><td>{event.task_id}</td></tr>
      <tr><td>环境</td><td>{event.stage_preset}</td></tr>
      <tr><td>风险等级</td><td>{event.risk_level}</td></tr>
      <tr><td>策略</td><td>{event.strategy_id or '-'}</td></tr>
      <tr><td>信号 ID</td><td>{event.signal_id or '-'}</td></tr>
      <tr><td>追踪 ID</td><td>{event.trace_id or '-'}</td></tr>
    </table>
  </div>
  <div class="footer">JBT SimTrading &nbsp;|&nbsp; {ts}</div>
</div>
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
