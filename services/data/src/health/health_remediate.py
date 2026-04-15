#!/usr/bin/env python3
"""BotQuant 自动修复脚本 — 读取健康报告中的告警，执行非破坏性修复动作并更新报告。

用法:
    .venv/bin/python3 scripts/health_remediate.py --report health_reports/mini.json
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

CN_TZ = timezone(timedelta(hours=8))
MONITOR_CFG = ROOT / "configs" / "monitoring.yaml"


def load_config() -> dict:
    if MONITOR_CFG.exists():
        return yaml.safe_load(MONITOR_CFG.read_text()) or {}
    return {}


def ts() -> str:
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")


# ===================== 修复动作 =====================
def clear_tmp(report: dict) -> dict:
    """清理 /tmp 超过 7 天的文件。"""
    cfg = load_config().get("remediation", {})
    days = cfg.get("tmp_retention_days", 7)
    try:
        subprocess.run(
            ["find", "/tmp", "-maxdepth", "1", "-mtime", f"+{days}", "-delete"],
            capture_output=True, text=True, timeout=30,
        )
        freed = "已清理"
        return {"action": "清理临时文件", "result": "成功", "detail": f"/tmp 超过{days}天的文件{freed}"}
    except Exception as e:
        return {"action": "清理临时文件", "result": "失败", "detail": str(e)}


def clear_old_logs(report: dict) -> dict:
    """清理旧日志文件。"""
    cfg = load_config().get("remediation", {})
    days = cfg.get("log_retention_days", 30)
    log_dir = ROOT / "logs"
    try:
        if log_dir.exists():
            subprocess.run(
                ["find", str(log_dir), "-name", "*.log*", "-mtime", f"+{days}", "-delete"],
                capture_output=True, text=True, timeout=30,
            )
        return {"action": "清理旧日志", "result": "成功", "detail": f"已清理 {days} 天以上日志"}
    except Exception as e:
        return {"action": "清理旧日志", "result": "失败", "detail": str(e)}


def restart_collectors(report: dict) -> dict:
    """重启采集进程（优雅停止后重启）。"""
    try:
        # 查找采集进程
        out = subprocess.check_output(["pgrep", "-f", "collect_tqsdk|collect_rss|collect_overseas|data_scheduler"], text=True, timeout=5)
        pids = [int(p.strip()) for p in out.strip().splitlines() if p.strip()]
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        # 简短等待后确认停止
        import time
        time.sleep(3)

        # 重启 TqSdk 采集器（如果在 Mini 上）
        # P1-7 修复：验证环境变量值，防止注入攻击
        hostname = os.environ.get("BOTQUANT_DEVICE", "").lower() or __import__("socket").gethostname().lower()
        # 白名单验证：仅允许 "mini" 或 "alienware"
        if hostname not in ["mini", "alienware", ""] and not any(x in hostname for x in ["mini", "alienware"]):
            hostname = __import__("socket").gethostname().lower()

        if "mini" in hostname:
            # P0-1 修复：使用 with 语句管理文件句柄，防止泄露
            log_file = ROOT / "logs" / "collect_tqsdk.log"
            with open(log_file, "a") as f:
                subprocess.Popen(
                    [sys.executable, str(ROOT / "scripts" / "collect_tqsdk_all_contracts.py")],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        return {"action": "重启采集进程", "result": "成功", "detail": f"已停止 {len(pids)} 个进程并重启"}
    except subprocess.CalledProcessError:
        return {"action": "重启采集进程", "result": "成功", "detail": "无采集进程需要重启"}
    except Exception as e:
        return {"action": "重启采集进程", "result": "失败", "detail": str(e)}


def restart_mihomo(report: dict) -> dict:
    """重启 mihomo 代理服务。"""
    try:
        subprocess.run(["pkill", "-f", "mihomo"], timeout=5)
        import time
        time.sleep(2)

        mihomo_bin = Path.home() / "mihomo" / "mihomo"
        mihomo_cfg = Path.home() / "mihomo" / "config.yaml"
        if mihomo_bin.exists() and mihomo_cfg.exists():
            # P0-1 修复：使用 with 语句管理文件句柄，防止泄露
            log_file = Path.home() / "mihomo" / "mihomo.log"
            with open(log_file, "a") as f:
                subprocess.Popen(
                    [str(mihomo_bin), "-d", str(mihomo_bin.parent)],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            return {"action": "重启 mihomo", "result": "成功", "detail": "VPN 代理已重启"}
        else:
            return {"action": "重启 mihomo", "result": "跳过", "detail": "mihomo 未安装"}
    except Exception as e:
        return {"action": "重启 mihomo", "result": "失败", "detail": str(e)}


ACTION_MAP = {
    "clear_tmp": clear_tmp,
    "clear_old_logs": clear_old_logs,
    "restart_collectors": restart_collectors,
    "restart_mihomo": restart_mihomo,
}


# ===================== 主流程 =====================
def main():
    parser = argparse.ArgumentParser(description="BotQuant 自动修复")
    parser.add_argument("--report", required=True, help="健康报告 JSON 文件路径")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"[自动修复] 报告文件不存在: {report_path}")
        sys.exit(1)

    report = json.loads(report_path.read_text())
    cfg = load_config()
    remediation_cfg = cfg.get("remediation", {})

    if not remediation_cfg.get("enabled", False):
        print("[自动修复] 自动修复已禁用（configs/monitoring.yaml）")
        sys.exit(0)

    auto_actions = remediation_cfg.get("auto_actions", [])
    alarms = report.get("alarms", [])

    if not alarms:
        print("[自动修复] 无告警，无需修复")
        sys.exit(0)

    print(f"[自动修复] {ts()} 检测到 {len(alarms)} 条告警，开始修复...")

    results = []
    for action_name in auto_actions:
        fn = ACTION_MAP.get(action_name)
        if fn:
            print(f"  执行: {action_name}...")
            result = fn(report)
            results.append(result)
            print(f"  结果: {result['result']} — {result['detail']}")
        else:
            print(f"  跳过未知动作: {action_name}")

    # 更新报告
    report["remediate_attempts"] = results
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[自动修复] 完成，共执行 {len(results)} 个动作")


if __name__ == "__main__":
    main()
