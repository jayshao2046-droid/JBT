"""JBT 数据端邮件通知 — 全新实现（非迁移）。

遵循 JBT 统一 HTML Card 格式：
- 必须发送 HTML Card，禁止纯文本邮件
- 标题固定格式：{icon} [{STAGE}-{TYPE}] {标题}
- 底部 footer 必须包含服务名和时间戳

通知颜色映射：
  P0 → #c0392b  P1 → #e67e22  P2 → #f39c12
  TRADE → #7f8c8d  INFO → #2980b9  NEWS → #5dade2  NOTIFY → #1abc9c

此模块需 Jay.S 签单确认后才正式嵌入启动服务。
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

_COLOR_MAP: dict[str, tuple[str, str]] = {
    "P0": ("#c0392b", "🚨"),
    "P1": ("#e67e22", "⚠️"),
    "P2": ("#f39c12", "🔔"),
    "TRADE": ("#7f8c8d", "📊"),
    "INFO": ("#2980b9", "📈"),
    "NEWS": ("#5dade2", "📰"),
    "NOTIFY": ("#1abc9c", "📣"),
}

SERVICE_NAME = "JBT data-service"


def _build_html(
    *,
    title: str,
    notify_type: str,
    body_rows: list[tuple[str, str]],
    trace_rows: list[tuple[str, str]] | None = None,
) -> str:
    """Build an HTML email card."""
    color, icon = _COLOR_MAP.get(notify_type, ("#1abc9c", "📣"))
    stage = "DATA"

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body_table = "".join(
        f'<tr><td style="padding:4px 8px;font-weight:bold;white-space:nowrap">{k}</td>'
        f'<td style="padding:4px 8px">{v}</td></tr>'
        for k, v in body_rows
    )

    trace_html = ""
    if trace_rows:
        trace_table = "".join(
            f'<tr><td style="padding:4px 8px;font-weight:bold;white-space:nowrap">{k}</td>'
            f'<td style="padding:4px 8px">{v}</td></tr>'
            for k, v in trace_rows
        )
        trace_html = f"""
        <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
        <p style="font-size:13px;color:#666;margin:8px 0">追踪信息</p>
        <table style="width:100%;border-collapse:collapse;font-size:13px">{trace_table}</table>
        """

    return f"""
    <div style="max-width:600px;margin:20px auto;font-family:sans-serif;border:1px solid #ddd;border-radius:8px;overflow:hidden">
      <div style="background:{color};padding:16px 20px;color:#fff">
        <div style="font-size:16px;font-weight:bold">{icon} [{stage}-{notify_type}] {title}</div>
        <div style="font-size:12px;opacity:0.85;margin-top:4px">{SERVICE_NAME} 通知</div>
      </div>
      <div style="padding:16px 20px">
        <p style="font-size:13px;color:#666;margin:0 0 8px">核心信息</p>
        <table style="width:100%;border-collapse:collapse;font-size:13px">{body_table}</table>
        {trace_html}
      </div>
      <div style="padding:8px 20px;background:#f9f9f9;font-size:11px;color:#999;text-align:center">
        {SERVICE_NAME} | {timestamp}
      </div>
    </div>
    """


def send_email(
    *,
    smtp_host: str,
    smtp_port: int = 465,
    username: str,
    password: str,
    from_addr: str,
    to_addrs: list[str],
    title: str,
    notify_type: str = "NOTIFY",
    body_rows: list[tuple[str, str]],
    trace_rows: list[tuple[str, str]] | None = None,
    use_ssl: bool = True,
    use_tls: bool = False,
    timeout: float = 30.0,
) -> bool:
    """Send an HTML card email notification.

    Returns True if sent successfully, False otherwise.
    """
    if not smtp_host or not to_addrs:
        logger.warning("email config incomplete (host=%s, to=%s), skipping", smtp_host, to_addrs)
        return False

    color, icon = _COLOR_MAP.get(notify_type, ("#1abc9c", "📣"))
    subject = f"{icon} [DATA-{notify_type}] {title}"

    html = _build_html(
        title=title,
        notify_type=notify_type,
        body_rows=body_rows,
        trace_rows=trace_rows,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout, context=context) as server:
                server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())

        logger.info("email sent: %s → %s", subject, to_addrs)
        return True
    except Exception as exc:
        logger.error("email send failed: %s — %s", subject, exc)
        return False
