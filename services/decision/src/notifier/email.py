"""
DecisionEmailNotifier — TASK-0021 F batch
SMTP HTML 邮件通知，遵循 JBT 统一 Card 邮件结构。
"""
import html
import logging
import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dispatcher import DecisionEvent

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))

_LEVEL_HEX = {
    "P0": "#c0392b",
    "P1": "#e67e22",
    "P2": "#f39c12",
    "SIGNAL": "#7f8c8d",
    "RESEARCH": "#2980b9",
    "NOTIFY": "#1abc9c",
}

_LEVEL_ICON = {
    "P0": "🚨",
    "P1": "⚠️",
    "P2": "🔔",
    "SIGNAL": "📊",
    "RESEARCH": "📈",
    "NOTIFY": "📣",
}

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin:0; padding:20px; background:#f5f5f5; }}
  .card {{ max-width:600px; margin:0 auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.1); }}
  .header {{ padding:20px 24px; color:#fff; }}
  .header h1 {{ margin:0; font-size:18px; font-weight:600; }}
  .header .sub {{ margin:4px 0 0; font-size:13px; opacity:.85; }}
  .body {{ padding:20px 24px; }}
  .section-title {{ font-size:13px; font-weight:600; color:#666; text-transform:uppercase; letter-spacing:.5px; margin:16px 0 8px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  td {{ padding:6px 8px; border-bottom:1px solid #f0f0f0; }}
  td:first-child {{ color:#666; width:30%; }}
  td:last-child {{ color:#222; font-weight:500; }}
  hr {{ border:none; border-top:1px solid #eee; margin:16px 0; }}
  .footer {{ padding:12px 24px; background:#fafafa; font-size:12px; color:#999; border-top:1px solid #eee; }}
</style>
</head>
<body>
<div class="card">
  <div class="header" style="background:{color}">
    <h1>{icon} [DECISION-{level}] {title}</h1>
    <div class="sub">JBT Decision 通知</div>
  </div>
  <div class="body">
    <p class="section-title">核心信息</p>
    <table>
      <tr><td>事件代码</td><td>{event_code}</td></tr>
      <tr><td>摘要</td><td>{body_plain}</td></tr>
    </table>
    <hr/>
    <p class="section-title">追踪信息</p>
    <table>
      {track_rows}
    </table>
  </div>
  <div class="footer">JBT Decision | {ts}</div>
</div>
</body>
</html>
"""


class DecisionEmailNotifier:
    """邮件 SMTP 通道。通过 NOTIFY_EMAIL_ENABLED 整体开关。"""

    def __init__(self) -> None:
        raw = os.environ.get("NOTIFY_EMAIL_ENABLED", "false").strip().lower()
        self._enabled = raw == "true"
        self._smtp_host: str = os.environ.get("ALERT_EMAIL_SMTP_HOST", "")
        self._smtp_port: int = int(os.environ.get("ALERT_EMAIL_SMTP_PORT", "587"))
        self._smtp_user: str = os.environ.get("ALERT_EMAIL_SMTP_USER", "")
        self._smtp_password: str = os.environ.get("ALERT_EMAIL_SMTP_PASSWORD", "")
        self._from_addr: str = os.environ.get("ALERT_EMAIL_FROM", "")
        self._to_addr: str = os.environ.get("ALERT_EMAIL_TO", "")

    def send(self, event: "DecisionEvent") -> bool:
        if not self._enabled:
            logger.debug("EmailNotifier disabled, skipping %s", event.event_code)
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

        level_str = event.notify_level.value if hasattr(event.notify_level, "value") else str(event.notify_level)
        color = _LEVEL_HEX.get(level_str, "#2980b9")
        icon = _LEVEL_ICON.get(level_str, "📋")
        ts = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")

        track_items = [
            ("策略", event.strategy_id),
            ("模型", event.model_id),
            ("信号", event.signal_id),
            ("会话", event.session_id),
            ("追踪", event.trace_id),
        ]
        track_rows = "\n".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>"
            for k, v in track_items if v
        ) or "<tr><td colspan=2>-</td></tr>"

        body_plain = event.body.replace("\n", " ")[:200]

        # 安全修复：P1-2 - HTML 转义防止注入
        html_content = _HTML_TEMPLATE.format(
            color=color, icon=icon, level=level_str,
            title=html.escape(event.title),
            event_code=html.escape(event.event_code),
            body_plain=html.escape(body_plain),
            track_rows=track_rows, ts=ts,
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[DECISION-{level_str}] {event.title}"
        msg["From"] = self._from_addr
        msg["To"] = self._to_addr
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._from_addr, [self._to_addr], msg.as_string())
            logger.info("Email sent for event %s", event.event_code)
            return True
        except smtplib.SMTPException as exc:
            logger.error("EmailNotifier SMTP error event=%s: %s", event.event_code, exc)
            return False
        except Exception as exc:
            logger.error("EmailNotifier unexpected error event=%s: %s", event.event_code, exc)
            return False
