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

        # 邮件只发三个时段的收盘交易汇总，断联/交易通知只走飞书
        _EMAIL_ALLOWED_CODES = {"SESSION_CLOSE_SUMMARY"}
        if event.event_code not in _EMAIL_ALLOWED_CODES:
            logger.debug("EmailNotifier: skipping non-summary event %s", event.event_code)
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
        header_color = {"P0": "#c0392b", "P1": "#e67e22", "P2": "#f39c12"}.get(event.risk_level, "#1abc9c")
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"[JBT-SIM-{event.risk_level}] {event.event_code}: {event.message or event.reason}"
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
    <h2>{level_icon} [SIM-{event.risk_level}] {event.event_code}: {event.message or event.reason}</h2>
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


def send_risk_email(event: "RiskEvent") -> bool:
    """Convenience function: create a one-off EmailNotifier and send.

    If SMTP is not configured, safely degrades (logs warning, returns False).
    """
    notifier = EmailNotifier()
    return notifier.send(event)


def send_daily_report_email(report_data: dict) -> bool:
    """发送收盘日报邮件（蓝色资讯类卡片）。

    如果缺少 SMTP 配置，安全降级（log warning + return False）。
    """
    smtp_host = os.environ.get("ALERT_EMAIL_SMTP_HOST", "")
    smtp_port = int(os.environ.get("ALERT_EMAIL_SMTP_PORT", "587"))
    smtp_user = os.environ.get("ALERT_EMAIL_SMTP_USER", "")
    smtp_password = os.environ.get("ALERT_EMAIL_SMTP_PASSWORD", "")
    from_addr = os.environ.get("ALERT_EMAIL_FROM", "")
    to_addr = os.environ.get("ALERT_EMAIL_TO", "")

    missing = [
        name
        for name, val in [
            ("ALERT_EMAIL_SMTP_HOST", smtp_host),
            ("ALERT_EMAIL_SMTP_USER", smtp_user),
            ("ALERT_EMAIL_SMTP_PASSWORD", smtp_password),
            ("ALERT_EMAIL_FROM", from_addr),
            ("ALERT_EMAIL_TO", to_addr),
        ]
        if not val
    ]
    if missing:
        logger.warning("send_daily_report_email: missing SMTP env vars: %s — skipping", missing)
        return False

    from datetime import datetime

    report_date = report_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    total_pnl = report_data.get("total_pnl", 0)
    win_rate = report_data.get("win_rate", 0)
    trade_count = report_data.get("trade_count", 0)
    positions = report_data.get("positions", [])
    trades = report_data.get("trades", [])

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_color = "#2980b9"
    subject = f"📈 [SIM-DAILY] 模拟交易日报 {report_date}"

    # 持仓汇总行
    if positions:
        pos_rows = "".join(
            f"<tr><td>{p.get('symbol', '-')}</td><td>{p.get('direction', '-')}</td>"
            f"<td>{p.get('volume', '-')}</td><td>{p.get('pnl', '-')}</td></tr>"
            for p in positions
        )
    else:
        pos_rows = '<tr><td colspan="4" style="text-align:center;color:#999;">无持仓</td></tr>'

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
  td, th {{ padding: 7px 10px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }}
  td:first-child {{ color: #666; width: 110px; font-weight: 500; }}
  td:last-child {{ color: #222; word-break: break-all; }}
  .hr {{ border: none; border-top: 1px solid #eee; margin: 14px 0; }}
  .footer {{ font-size: 11px; color: #aaa; padding: 10px 20px 14px; border-top: 1px solid #f0f0f0; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2>📈 [SIM-DAILY] 模拟交易日报 {report_date}</h2>
    <div class="sub">JBT SimTrading 通知</div>
  </div>
  <div class="body">
    <p class="section-title">核心信息</p>
    <table>
      <tr><td>日期</td><td>{report_date}</td></tr>
      <tr><td>总盈亏</td><td>{total_pnl}</td></tr>
      <tr><td>胜率</td><td>{win_rate:.1f}%</td></tr>
      <tr><td>交易笔数</td><td>{trade_count}</td></tr>
    </table>
    <hr class="hr">
    <p class="section-title">持仓汇总</p>
    <table>
      <tr><th>品种</th><th>方向</th><th>数量</th><th>盈亏</th></tr>
      {pos_rows}
    </table>
  </div>
  <div class="footer">JBT SimTrading &nbsp;|&nbsp; {ts}</div>
</div>
</body></html>
"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, [to_addr], msg.as_string())
        logger.info("Daily report email sent for %s", report_date)
        return True
    except smtplib.SMTPException as exc:
        logger.error("send_daily_report_email SMTPException: %s", exc)
        return False
    except OSError as exc:
        logger.error("send_daily_report_email OSError: %s", exc)
        return False
    except Exception as exc:
        logger.error("send_daily_report_email unexpected error: %s", exc)
        return False
