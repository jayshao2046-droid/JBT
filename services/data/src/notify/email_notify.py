"""JBT 数据端邮件通知 — 双通道邮件发送 + HTML 日报模板。

功能：
1. 告警邮件（P0/P1 实时发送）
2. 每日日报（09:30 + 16:30）含完整数据端健康评估
3. 渠道降级邮件（飞书失败时补发）

遵循 JBT 统一 HTML Card 格式。
"""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from notify.dispatcher import DataEvent

logger = logging.getLogger(__name__)

CN_TZ = timezone(timedelta(hours=8))

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


def _build_event_html(event: "DataEvent") -> str:
    """Build HTML card for a DataEvent."""
    ntype = event.notify_type.value
    color, icon = _COLOR_MAP.get(ntype, ("#1abc9c", "📣"))
    ts = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")

    body_table = "".join(
        f'<tr><td style="padding:4px 8px;font-weight:bold;white-space:nowrap">{k}</td>'
        f'<td style="padding:4px 8px">{v}</td></tr>'
        for k, v in event.body_rows
    ) if event.body_rows else f'<tr><td style="padding:8px">{event.body_md}</td></tr>'

    trace_html = ""
    if event.trace_rows:
        trace_table = "".join(
            f'<tr><td style="padding:4px 8px;font-weight:bold;white-space:nowrap">{k}</td>'
            f'<td style="padding:4px 8px">{v}</td></tr>'
            for k, v in event.trace_rows
        )
        trace_html = f"""
        <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
        <p style="font-size:13px;color:#666;margin:8px 0">追踪信息</p>
        <table style="width:100%;border-collapse:collapse;font-size:13px">{trace_table}</table>"""

    return f"""
    <div style="max-width:600px;margin:20px auto;font-family:sans-serif;border:1px solid #ddd;border-radius:8px;overflow:hidden">
      <div style="background:{color};padding:16px 20px;color:#fff">
        <div style="font-size:16px;font-weight:bold">{icon} [DATA-{ntype}] {event.title}</div>
        <div style="font-size:12px;opacity:0.85;margin-top:4px">{SERVICE_NAME} 通知</div>
      </div>
      <div style="padding:16px 20px">
        <p style="font-size:13px;color:#666;margin:0 0 8px">核心信息</p>
        <table style="width:100%;border-collapse:collapse;font-size:13px">{body_table}</table>
        {trace_html}
      </div>
      <div style="padding:8px 20px;background:#f9f9f9;font-size:11px;color:#999;text-align:center">
        {SERVICE_NAME} | {ts}
      </div>
    </div>"""


def build_daily_report_html(
    *,
    total_rounds: int,
    success_rate: float,
    failed_collectors: list[str],
    total_records: int,
    sources_freshness: list[dict[str, Any]],
    cpu_pct: float,
    mem_pct: float,
    disk_pct: float,
    process_status: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    news_collected: int,
    news_pushed: int,
    breaking_count: int,
    health_score: int,
) -> str:
    """Build the full daily report HTML Card."""
    ts = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    score_color = "#27ae60" if health_score >= 80 else ("#e67e22" if health_score >= 60 else "#c0392b")
    header_color = "#2980b9"

    # 采集统计
    failed_text = ", ".join(failed_collectors) if failed_collectors else "无"
    collect_section = f"""
    <p style="font-size:14px;font-weight:bold;color:#444;margin:16px 0 8px">📋 采集统计</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <tr><td style="padding:4px 8px;font-weight:bold">总采集轮次</td><td style="padding:4px 8px">{total_rounds} 轮</td></tr>
      <tr><td style="padding:4px 8px;font-weight:bold">成功率</td><td style="padding:4px 8px">{success_rate:.1f}%</td></tr>
      <tr><td style="padding:4px 8px;font-weight:bold">失败采集器</td><td style="padding:4px 8px">{failed_text}</td></tr>
      <tr><td style="padding:4px 8px;font-weight:bold">数据总条数</td><td style="padding:4px 8px">{total_records:,} 条</td></tr>
    </table>"""

    # 数据新鲜度
    freshness_rows = ""
    for s in sources_freshness:
        icon = "🟢" if s.get("ok") else "🔴"
        freshness_rows += f'<tr><td style="padding:3px 8px">{icon} {s["label"]}</td><td style="padding:3px 8px">{s.get("age_str", "")}</td></tr>'
    freshness_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
    <p style="font-size:14px;font-weight:bold;color:#444;margin:8px 0">📈 数据新鲜度</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">{freshness_rows}</table>"""

    # 设备健康
    def pct_color(p: float) -> str:
        return "#c0392b" if p >= 85 else ("#e67e22" if p >= 70 else "#27ae60")
    device_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
    <p style="font-size:14px;font-weight:bold;color:#444;margin:8px 0">🖥 设备健康</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <tr><td style="padding:4px 8px;font-weight:bold">CPU</td><td style="padding:4px 8px;color:{pct_color(cpu_pct)}">{cpu_pct:.0f}%</td>
          <td style="padding:4px 8px;font-weight:bold">内存</td><td style="padding:4px 8px;color:{pct_color(mem_pct)}">{mem_pct:.0f}%</td>
          <td style="padding:4px 8px;font-weight:bold">磁盘</td><td style="padding:4px 8px;color:{pct_color(disk_pct)}">{disk_pct:.0f}%</td></tr>
    </table>"""

    # 进程状态
    proc_rows = ""
    proc_ok = 0
    for p in process_status:
        icon = "🟢" if p["ok"] else "🔴"
        if p["ok"]:
            proc_ok += 1
        uptime = p.get("uptime", "")
        proc_rows += f'<tr><td style="padding:3px 8px">{icon} {p["label"]}</td><td style="padding:3px 8px">{uptime}</td></tr>'
    process_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
    <p style="font-size:14px;font-weight:bold;color:#444;margin:8px 0">⚙️ 进程状态 ({proc_ok}/{len(process_status)})</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">{proc_rows}</table>"""

    # 报错日志
    error_rows = ""
    for e in errors[:10]:
        error_rows += f'<tr><td style="padding:3px 8px;color:#666">[{e.get("time", "")}]</td><td style="padding:3px 8px">{e.get("msg", "")}</td></tr>'
    if not errors:
        error_rows = '<tr><td style="padding:3px 8px;color:#27ae60">无错误</td></tr>'
    error_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
    <p style="font-size:14px;font-weight:bold;color:#444;margin:8px 0">❌ 报错日志 (最近24h)</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">{error_rows}</table>"""

    # 新闻统计
    news_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
    <p style="font-size:14px;font-weight:bold;color:#444;margin:8px 0">📰 新闻统计</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <tr><td style="padding:4px 8px;font-weight:bold">采集</td><td style="padding:4px 8px">{news_collected:,} 条</td>
          <td style="padding:4px 8px;font-weight:bold">推送</td><td style="padding:4px 8px">{news_pushed:,} 条</td></tr>
      <tr><td style="padding:4px 8px;font-weight:bold">黑天鹅触发</td><td style="padding:4px 8px">{breaking_count} 次</td></tr>
    </table>"""

    # 健康评分
    score_section = f"""
    <hr style="border:none;border-top:1px solid #eee;margin:12px 0">
    <p style="font-size:18px;font-weight:bold;text-align:center;color:{score_color};margin:16px 0">
      📊 健康评分: {health_score}/100 {"✅" if health_score >= 80 else "⚠️"}
    </p>"""

    return f"""
    <div style="max-width:600px;margin:20px auto;font-family:sans-serif;border:1px solid #ddd;border-radius:8px;overflow:hidden">
      <div style="background:{header_color};padding:16px 20px;color:#fff">
        <div style="font-size:16px;font-weight:bold">📊 [DATA-INFO] JBT 数据端日报</div>
        <div style="font-size:12px;opacity:0.85;margin-top:4px">{SERVICE_NAME} 通知</div>
      </div>
      <div style="padding:16px 20px">
        {collect_section}
        {freshness_section}
        {device_section}
        {process_section}
        {error_section}
        {news_section}
        {score_section}
      </div>
      <div style="padding:8px 20px;background:#f9f9f9;font-size:11px;color:#999;text-align:center">
        {SERVICE_NAME} | {ts}
      </div>
    </div>"""


class EmailSender:
    """SMTP 邮件发送器。从环境变量读取配置。"""

    def __init__(self) -> None:
        self._host = os.environ.get("SMTP_HOST", "")
        self._port = int(os.environ.get("SMTP_PORT", "465"))
        self._username = os.environ.get("SMTP_USERNAME", "")
        self._password = os.environ.get("SMTP_PASSWORD", "")
        self._from_addr = os.environ.get("SMTP_FROM_ADDR", "")
        self._to_addrs = [
            a.strip() for a in os.environ.get("SMTP_TO_ADDRS", "").split(",") if a.strip()
        ]
        self._use_ssl = os.environ.get("SMTP_USE_SSL", "true").lower() == "true"

    def send(self, *, event: "DataEvent") -> bool:
        """发送告警/通知邮件。"""
        if not self._host or not self._to_addrs:
            logger.warning("email config incomplete, skipping")
            return False

        html = _build_event_html(event)
        ntype = event.notify_type.value
        _, icon = _COLOR_MAP.get(ntype, ("#1abc9c", "📣"))
        subject = f"{icon} [DATA-{ntype}] {event.title}"
        return self._send_html(subject=subject, html=html)

    def send_daily_report(self, *, html: str, report_type: str = "日报") -> bool:
        """发送每日日报。"""
        if not self._host or not self._to_addrs:
            logger.warning("email config incomplete, skipping daily report")
            return False

        subject = f"📊 [DATA-INFO] JBT 数据端{report_type}"
        return self._send_html(subject=subject, html=html)

    def send_raw(self, *, subject: str, html: str) -> bool:
        """发送任意 HTML 邮件（用于测试）。"""
        return self._send_html(subject=subject, html=html)

    def _send_html(self, *, subject: str, html: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from_addr
        msg["To"] = ", ".join(self._to_addrs)
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            if self._use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self._host, self._port, timeout=30, context=context) as server:
                    server.login(self._username, self._password)
                    server.sendmail(self._from_addr, self._to_addrs, msg.as_string())
            else:
                with smtplib.SMTP(self._host, self._port, timeout=30) as server:
                    server.starttls(context=ssl.create_default_context())
                    server.login(self._username, self._password)
                    server.sendmail(self._from_addr, self._to_addrs, msg.as_string())

            logger.info("email sent: %s → %s", subject, self._to_addrs)
            return True
        except Exception as exc:
            logger.error("email send failed: %s — %s", subject, exc)
            return False
