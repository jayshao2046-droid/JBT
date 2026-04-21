#!/usr/bin/env python3
"""JBT 核心服务守护巡检脚本。

设计目标：
1. 在 MacBook 上通过 launchd 周期执行。
2. 只通过 HTTP 健康端点巡检非 Air 核心服务，不跨端读取文件系统。
3. 复用本地现有 .env 中的飞书/SMTP 配置发送 P1 告警与恢复通知。
4. 使用状态文件去抖，默认连续失败 2 次后再告警，恢复后发送一次通知。
"""

from __future__ import annotations

import argparse
import json
import smtplib
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


OK_STATUSES = {"ok", "healthy", "success", "running"}


@dataclass(frozen=True)
class ServiceCheck:
    service_id: str
    service_name: str
    device: str
    port: int
    url: str
    mode: str = "json_status"
    expected_statuses: tuple[str, ...] = ("ok", "healthy")


SERVICE_CHECKS: list[ServiceCheck] = [
    ServiceCheck(
        service_id="data",
        service_name="数据服务",
        device="Mini",
        port=8105,
        url="http://192.168.31.76:8105/health",
        expected_statuses=("ok", "healthy"),
    ),
    ServiceCheck(
        service_id="sim-trading",
        service_name="模拟交易",
        device="Alienware",
        port=8101,
        url="http://192.168.31.223:8101/health",
        expected_statuses=("ok",),
    ),
    ServiceCheck(
        service_id="researcher",
        service_name="研究员",
        device="Alienware",
        port=8199,
        url="http://192.168.31.223:8199/health",
        expected_statuses=("ok",),
    ),
    ServiceCheck(
        service_id="decision",
        service_name="决策引擎",
        device="Studio",
        port=8104,
        url="http://192.168.31.142:8104/health",
        expected_statuses=("ok", "healthy"),
    ),
    ServiceCheck(
        service_id="dashboard",
        service_name="统一看板",
        device="Studio",
        port=8106,
        url="http://192.168.31.142:8106/health",
        expected_statuses=("healthy", "ok"),
    ),
    ServiceCheck(
        service_id="backtest",
        service_name="回测系统",
        device="Studio",
        port=8103,
        url="http://192.168.31.142:8103/api/health",
        expected_statuses=("ok", "healthy"),
    ),
]


CHANNEL_STYLE = {
    "P1": {"icon": "⚠️", "template": "orange", "hex": "#e67e22"},
    "NOTIFY": {"icon": "📣", "template": "turquoise", "hex": "#1abc9c"},
}


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JBT 核心服务守护巡检")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--state-path", default=str(Path.home() / "jbt-governance" / "state" / "jbt_service_guardian.json"))
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--failure-threshold", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def split_addrs(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_notification_config(repo_root: Path) -> dict[str, Any]:
    data_env = parse_env_file(repo_root / "services" / "data" / ".env")
    sim_env = parse_env_file(repo_root / "services" / "sim-trading" / ".env")
    decision_env = parse_env_file(repo_root / "services" / "decision" / ".env")

    webhook = (
        data_env.get("FEISHU_ALERT_WEBHOOK_URL")
        or sim_env.get("FEISHU_WEBHOOK_URL")
        or decision_env.get("FEISHU_WEBHOOK_URL")
        or ""
    )

    smtp_host = data_env.get("SMTP_HOST") or sim_env.get("ALERT_EMAIL_SMTP_HOST") or decision_env.get("EMAIL_SMTP_HOST") or ""
    smtp_port_raw = data_env.get("SMTP_PORT") or sim_env.get("ALERT_EMAIL_SMTP_PORT") or decision_env.get("EMAIL_SMTP_PORT") or "465"
    smtp_user = data_env.get("SMTP_USERNAME") or sim_env.get("ALERT_EMAIL_SMTP_USER") or decision_env.get("EMAIL_SMTP_USER") or ""
    smtp_password = data_env.get("SMTP_PASSWORD") or sim_env.get("ALERT_EMAIL_SMTP_PASSWORD") or decision_env.get("EMAIL_SMTP_PASSWORD") or ""
    smtp_sender = data_env.get("SMTP_FROM_ADDR") or sim_env.get("ALERT_EMAIL_FROM") or decision_env.get("EMAIL_FROM") or smtp_user
    smtp_to = split_addrs(data_env.get("SMTP_TO_ADDRS") or sim_env.get("ALERT_EMAIL_TO") or decision_env.get("EMAIL_TO"))
    smtp_use_ssl = parse_bool(data_env.get("SMTP_USE_SSL"), default=True)
    if "SMTP_USE_SSL" not in data_env:
        smtp_use_ssl = parse_bool(sim_env.get("ALERT_EMAIL_SMTP_USE_SSL"), default=(str(smtp_port_raw) == "465"))

    try:
        smtp_port = int(str(smtp_port_raw).strip())
    except ValueError:
        smtp_port = 465

    return {
        "feishu_webhook": webhook,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_password": smtp_password,
        "smtp_sender": smtp_sender,
        "smtp_to": smtp_to,
        "smtp_use_ssl": smtp_use_ssl,
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"services": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"services": {}}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def probe_service(check: ServiceCheck, timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    request = urllib.request.Request(check.url, headers={"User-Agent": "JBT-Service-Guardian/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            latency_ms = int((time.monotonic() - started) * 1000)
            if check.mode == "json_status":
                payload = json.loads(body)
                raw_status = str(payload.get("status", "")).strip().lower()
                ok = raw_status in {status.lower() for status in check.expected_statuses} or raw_status in OK_STATUSES
                detail = f"status={raw_status or 'missing'} http={response.status}"
            else:
                raw_status = str(response.status)
                ok = 200 <= response.status < 400
                detail = f"http={response.status}"
            return {
                "ok": ok,
                "latency_ms": latency_ms,
                "detail": detail,
                "raw_status": raw_status,
                "checked_at": now_ts(),
            }
    except urllib.error.HTTPError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "detail": f"http={exc.code}",
            "raw_status": "http_error",
            "checked_at": now_ts(),
        }
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "detail": str(exc),
            "raw_status": "exception",
            "checked_at": now_ts(),
        }


def build_feishu_payload(level: str, title: str, core_md: str, trace_md: str) -> dict[str, Any]:
    style = CHANNEL_STYLE[level]
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{style['icon']} [GUARDIAN-{level}] {title}",
                },
                "template": style["template"],
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": core_md}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": trace_md}},
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"JBT guardian | {now_ts()}"}
                    ],
                },
            ],
        },
    }


def build_email_html(level: str, title: str, core_rows: list[tuple[str, str]], trace_rows: list[tuple[str, str]]) -> str:
    style = CHANNEL_STYLE[level]

    def render_rows(rows: list[tuple[str, str]]) -> str:
        return "".join(
            f"<tr><td style='padding:6px 10px;color:#666;font-weight:600'>{key}</td><td style='padding:6px 10px;color:#222'>{value}</td></tr>"
            for key, value in rows
        )

    return f"""
<html>
  <body style='margin:0;padding:24px;background:#f5f6f8;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;'>
    <div style='max-width:720px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e7e9ee;'>
      <div style='background:{style['hex']};padding:18px 20px;color:#fff;font-size:18px;font-weight:700;'>
        {style['icon']} [GUARDIAN-{level}] {title}
        <div style='font-size:12px;font-weight:500;opacity:0.9;margin-top:4px;'>JBT guardian 通知</div>
      </div>
      <div style='padding:18px 20px;'>
        <p style='margin:0 0 8px 0;font-size:13px;font-weight:700;color:#444;'>核心信息</p>
        <table style='width:100%;border-collapse:collapse'>{render_rows(core_rows)}</table>
        <hr style='border:none;border-top:1px solid #eceff3;margin:18px 0;'>
        <p style='margin:0 0 8px 0;font-size:13px;font-weight:700;color:#444;'>追踪信息</p>
        <table style='width:100%;border-collapse:collapse'>{render_rows(trace_rows)}</table>
      </div>
      <div style='padding:14px 20px;background:#fafbfc;color:#6b7280;font-size:12px;'>JBT guardian | {now_ts()}</div>
    </div>
  </body>
</html>
""".strip()


def send_feishu(webhook_url: str, payload: dict[str, Any]) -> None:
    if not webhook_url:
        return
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        response.read()


def send_email(config: dict[str, Any], subject: str, html_body: str) -> None:
    recipients = config.get("smtp_to", [])
    if not config.get("smtp_host") or not config.get("smtp_user") or not config.get("smtp_password") or not recipients:
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = config.get("smtp_sender") or config.get("smtp_user")
    message["To"] = ", ".join(recipients)
    message.attach(MIMEText(html_body, "html", "utf-8"))

    if config.get("smtp_use_ssl", True):
        with smtplib.SMTP_SSL(config["smtp_host"], config["smtp_port"], context=ssl.create_default_context(), timeout=10) as server:
            server.login(config["smtp_user"], config["smtp_password"])
            server.sendmail(message["From"], recipients, message.as_string())
    else:
        with smtplib.SMTP(config["smtp_host"], config["smtp_port"], timeout=10) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(config["smtp_user"], config["smtp_password"])
            server.sendmail(message["From"], recipients, message.as_string())


def notify(level: str, title: str, core_rows: list[tuple[str, str]], trace_rows: list[tuple[str, str]], config: dict[str, Any], dry_run: bool) -> None:
    core_md = "\n".join(f"**{key}**: {value}" for key, value in core_rows)
    trace_md = "\n".join(f"**{key}**: {value}" for key, value in trace_rows)
    subject = f"{CHANNEL_STYLE[level]['icon']} [GUARDIAN-{level}] {title}"
    email_html = build_email_html(level, title, core_rows, trace_rows)
    feishu_payload = build_feishu_payload(level, title, core_md, trace_md)

    if dry_run:
        print(f"[dry-run] {subject}")
        return

    try:
        send_feishu(config.get("feishu_webhook", ""), feishu_payload)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 飞书发送失败: {exc}", file=sys.stderr)

    try:
        send_email(config, subject, email_html)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 邮件发送失败: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    state_path = Path(args.state_path).resolve()
    notification_config = load_notification_config(repo_root)
    state = load_state(state_path)
    state.setdefault("services", {})

    host_name = socket.gethostname()
    exit_code = 0

    for check in SERVICE_CHECKS:
        result = probe_service(check, timeout=args.timeout)
        service_state = state["services"].get(
            check.service_id,
            {
                "last_status": "unknown",
                "consecutive_failures": 0,
                "alert_sent": False,
                "last_detail": "",
                "last_checked_at": "",
            },
        )

        if result["ok"]:
            print(f"[ok] {check.service_id} latency={result['latency_ms']}ms detail={result['detail']}")
            if service_state.get("alert_sent"):
                core_rows = [
                    ("服务", check.service_name),
                    ("设备", check.device),
                    ("端口", str(check.port)),
                    ("结果", "已恢复"),
                ]
                trace_rows = [
                    ("地址", check.url),
                    ("延迟", f"{result['latency_ms']} ms"),
                    ("主机", host_name),
                    ("时间", result["checked_at"]),
                ]
                notify("NOTIFY", f"{check.service_name} 健康恢复", core_rows, trace_rows, notification_config, args.dry_run)

            service_state.update(
                {
                    "last_status": "ok",
                    "consecutive_failures": 0,
                    "alert_sent": False,
                    "last_detail": result["detail"],
                    "last_checked_at": result["checked_at"],
                }
            )
        else:
            exit_code = 1
            failures = int(service_state.get("consecutive_failures", 0)) + 1
            print(
                f"[fail] {check.service_id} failures={failures} latency={result['latency_ms']}ms detail={result['detail']}",
                file=sys.stderr,
            )
            if failures >= args.failure_threshold and not service_state.get("alert_sent"):
                core_rows = [
                    ("服务", check.service_name),
                    ("设备", check.device),
                    ("端口", str(check.port)),
                    ("结果", result["detail"]),
                    ("连续失败", str(failures)),
                ]
                trace_rows = [
                    ("地址", check.url),
                    ("状态", result["raw_status"]),
                    ("延迟", f"{result['latency_ms']} ms"),
                    ("主机", host_name),
                    ("时间", result["checked_at"]),
                ]
                notify("P1", f"{check.service_name} 健康检查失败", core_rows, trace_rows, notification_config, args.dry_run)
                service_state["alert_sent"] = True

            service_state.update(
                {
                    "last_status": "fail",
                    "consecutive_failures": failures,
                    "last_detail": result["detail"],
                    "last_checked_at": result["checked_at"],
                }
            )

        state["services"][check.service_id] = service_state

    save_state(state_path, state)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())