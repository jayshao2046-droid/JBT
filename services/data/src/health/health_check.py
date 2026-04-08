#!/usr/bin/env python3
"""BotQuant 设备健康检查 — 采集 CPU/内存/磁盘/GPU/进程/服务状态，输出 JSON 并触发 P0 告警。

用法:
    .venv/bin/python3 scripts/health_check.py              # 正常检查
    .venv/bin/python3 scripts/health_check.py --test-p0     # 模拟 P0（测试告警流程）
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# --------------- .env 加载 ---------------
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# --------------- 配置加载 ---------------
import yaml  # noqa: E402

MONITOR_CFG_PATH = ROOT / "configs" / "monitoring.yaml"


def load_config() -> dict:
    if MONITOR_CFG_PATH.exists():
        return yaml.safe_load(MONITOR_CFG_PATH.read_text()) or {}
    return {}


CFG = load_config()
TH = CFG.get("thresholds", {})

# --------------- 设备识别 ---------------
_hostname = (os.environ.get("BOTQUANT_DEVICE") or socket.gethostname()).lower()
IS_MINI = "mini" in _hostname or "jbotm" in _hostname
IS_STUDIO = "studio" in _hostname or "jbots" in _hostname
DEVICE = "mini" if IS_MINI else ("studio" if IS_STUDIO else _hostname)
LABEL = "Mini" if IS_MINI else ("Studio" if IS_STUDIO else _hostname)

# --------------- 时区 ---------------
CN_TZ = timezone(timedelta(hours=8))

# --------------- 数据目录 ---------------
DATA_ROOT = Path.home() / "J_BotQuant" / "BotQuan_Data"
ALARM_STATE_FILE = DATA_ROOT / "logs" / "collector_alarm_state.json"
COLLECTOR_STATUS_FILE = DATA_ROOT / "logs" / "collector_status_latest.json"

# --------------- 18 源新鲜度规则 ---------------
# max_age_h: 超过此时长未更新则触发告警
# trading_only: True = 仅交易时段检查; False = 全天检查
DATA_RULES: dict[str, dict] = {
    "futures_minute":  {"dir": DATA_ROOT / "futures_minute",       "max_age_h": 2,   "trading_only": True,  "weekend_skip": False, "label": "国内期货分钟"},
    "futures_eod":     {"dir": DATA_ROOT / "futures_minute",       "max_age_h": 26,  "trading_only": False, "weekend_skip": True,  "label": "国内期货EOD"},
    "overseas_minute": {"dir": DATA_ROOT / "overseas_kline" / "1m",    "max_age_h": 48,  "trading_only": False, "weekend_skip": True,  "label": "外盘期货分钟"},
    "overseas_daily":  {"dir": DATA_ROOT / "overseas_kline" / "1d",    "max_age_h": 50,  "trading_only": False, "weekend_skip": True,  "label": "外盘期货日线"},
    "stock_minute":    {"dir": DATA_ROOT / "stock_minute",             "max_age_h": 26,  "trading_only": False, "weekend_skip": True,  "label": "A股分钟"},
    "stock_realtime":  {"dir": DATA_ROOT / "stock_minute",          "max_age_h": 2,   "trading_only": True,  "weekend_skip": False, "label": "A股实时"},
    "watchlist":       {"dir": DATA_ROOT / "logs",                  "max_age_h": 26,  "trading_only": False, "weekend_skip": False, "label": "自选股"},
    "macro_global":    {"dir": DATA_ROOT / "macro_global",          "max_age_h": 720, "trading_only": False, "weekend_skip": False, "label": "宏观数据"},
    "news_rss":        {"dir": DATA_ROOT / "news_collected",        "max_age_h": 3,   "trading_only": False, "weekend_skip": False, "label": "新闻RSS"},
    "position_daily":  {"dir": DATA_ROOT / "position",              "max_age_h": 26,  "trading_only": False, "weekend_skip": True,  "label": "持仓日报"},
    "position_weekly": {"dir": DATA_ROOT / "position",              "max_age_h": 200, "trading_only": False, "weekend_skip": False, "label": "持仓周报"},
    "volatility_cboe": {"dir": DATA_ROOT / "volatility_index",      "max_age_h": 26,  "trading_only": False, "weekend_skip": True,  "label": "CBOE波动率"},
    "volatility_qvix": {"dir": DATA_ROOT / "volatility_index",      "max_age_h": 26,  "trading_only": False, "weekend_skip": True,  "label": "QVIX波动率"},
    "shipping":        {"dir": DATA_ROOT / "shipping",              "max_age_h": 26,  "trading_only": False, "weekend_skip": False, "label": "海运运费"},
    "tushare":         {"dir": DATA_ROOT / "tushare",               "max_age_h": 26,  "trading_only": False, "weekend_skip": True,  "label": "Tushare日线"},
    "weather":         {"dir": DATA_ROOT / "weather",               "max_age_h": 14,  "trading_only": False, "weekend_skip": False, "label": "天气"},
    "sentiment":       {"dir": DATA_ROOT / "sentiment",             "max_age_h": 26,  "trading_only": False, "weekend_skip": False, "label": "情绪指数"},
    "health_log":      {"dir": DATA_ROOT / "logs",                  "max_age_h": 1,   "trading_only": False, "weekend_skip": False, "label": "健康日志"},
}


def _is_weekend() -> bool:
    """今天是否为周末（周六/周日）。"""
    return datetime.now(CN_TZ).weekday() >= 5


def _is_intraday_futures() -> bool:
    """是否处于国内期货交易时段。
    上午 9:00-11:30, 下午 13:30-15:00, 夜盘 21:00-23:00
    """
    now = datetime.now(CN_TZ)
    if now.weekday() >= 5:
        return False
    t = now.hour * 60 + now.minute
    return (540 <= t <= 690) or (810 <= t <= 900) or (1260 <= t <= 1380)


def _is_intraday_stock() -> bool:
    """是否处于A股交易时段。
    上午 9:30-11:30, 下午 13:00-15:00
    """
    now = datetime.now(CN_TZ)
    if now.weekday() >= 5:
        return False
    t = now.hour * 60 + now.minute
    return (570 <= t <= 690) or (780 <= t <= 900)


def _is_intraday(name: str) -> bool:
    """根据数据源名称判断是否处于对应交易时段。"""
    if name in ("stock_realtime",):
        return _is_intraday_stock()
    return _is_intraday_futures()


# ===================== 采集函数 =====================
def get_cpu_info() -> dict:
    """CPU 核心数与利用率。"""
    cores = os.cpu_count() or 1
    # macOS: top 获取 idle，Linux: /proc/stat
    usage = 0.0
    try:
        if platform.system() == "Darwin":
            out = subprocess.check_output(
                ["top", "-l", "1", "-n", "0"], text=True, timeout=10
            )
            for line in out.splitlines():
                if "CPU usage" in line:
                    # e.g. "CPU usage: 5.55% user, 10.0% sys, 84.44% idle"
                    parts = line.split(",")
                    for p in parts:
                        if "idle" in p:
                            idle = float(p.strip().split("%")[0])
                            usage = round(100.0 - idle, 1)
                            break
                    break
        else:
            out = subprocess.check_output(
                ["grep", "cpu ", "/proc/stat"], text=True, timeout=5
            )
            vals = list(map(int, out.split()[1:]))
            idle = vals[3] if len(vals) > 3 else 0
            total = sum(vals)
            usage = round((1 - idle / max(total, 1)) * 100, 1)
    except Exception:
        usage = -1
    return {"cores": cores, "usage_percent": usage}


def get_memory_info() -> dict:
    """内存总量与使用量（MB）。使用 psutil 跨平台获取。"""
    try:
        import psutil
        m = psutil.virtual_memory()
        total_mb = m.total // (1024 * 1024)
        used_mb = (m.total - m.available) // (1024 * 1024)
        pct = round(used_mb / max(total_mb, 1) * 100, 1)
        return {"total_mb": total_mb, "used_mb": used_mb, "used_percent": pct}
    except Exception:
        return {"total_mb": 0, "used_mb": 0, "used_percent": 0.0}


def get_disk_info() -> list[dict]:
    """磁盘分区使用情况。"""
    disks = []
    try:
        out = subprocess.check_output(["df", "-h"], text=True, timeout=5)
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 6 and parts[-1] in ("/", "/System/Volumes/Data"):
                mount = parts[-1]
                total = parts[1]
                used = parts[2]
                avail = parts[3]
                pct_str = parts[4].rstrip("%")
                try:
                    pct = float(pct_str)
                except ValueError:
                    pct = 0
                disks.append({
                    "mount": mount,
                    "total": total,
                    "used": used,
                    "avail": avail,
                    "used_percent": pct,
                })
    except Exception:
        pass
    return disks


def get_gpu_info() -> list[dict]:
    """GPU 信息（macOS 用 powermetrics 概要或 ioreg; Linux 用 nvidia-smi）。"""
    gpus: list[dict] = []
    try:
        if platform.system() == "Darwin":
            # Apple Silicon: 使用 ioreg 获取 GPU 温度（需 sudo），
            # 简化版：标记为 Apple GPU，无精确利用率
            chip = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True, timeout=5
            ).strip()
            gpus.append({
                "name": chip,
                "util_percent": -1,  # macOS 无直接 CLI 获取 GPU 利用率
                "temp_c": -1,
            })
        else:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                text=True, timeout=10,
            )
            for line in out.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    gpus.append({
                        "name": parts[0],
                        "util_percent": float(parts[1]),
                        "temp_c": int(parts[2]),
                    })
    except Exception:
        pass
    return gpus


def get_high_mem_processes(top_n: int = 5) -> list[dict]:
    """占用内存最高的进程。"""
    procs = []
    try:
        out = subprocess.check_output(
            ["ps", "aux", "--sort=-rss"] if platform.system() != "Darwin" else ["ps", "aux"],
            text=True, timeout=10,
        )
        lines = out.strip().splitlines()[1:]  # skip header
        items = []
        for line in lines:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                try:
                    cpu_pct = float(parts[2])
                    mem_pct = float(parts[3])
                    rss_kb = int(parts[5])
                    cmd = parts[10][:120]
                    items.append((rss_kb, cpu_pct, mem_pct, cmd, int(parts[1])))
                except (ValueError, IndexError):
                    pass
        items.sort(key=lambda x: x[0], reverse=True)
        for rss_kb, cpu_pct, mem_pct, cmd, pid in items[:top_n]:
            procs.append({
                "pid": pid,
                "cmd": cmd,
                "mem_mb": rss_kb // 1024,
                "cpu_percent": cpu_pct,
            })
    except Exception:
        pass
    return procs


def get_service_status() -> dict:
    """VPN/mihomo/采集器服务状态。"""
    services: dict[str, Any] = {}

    # VPN / mihomo
    vpn_manager = ROOT / "scripts" / "vpn_proxy_manager.py"
    if IS_MINI or vpn_manager.exists():
        try:
            p = subprocess.run(
                [sys.executable, str(vpn_manager), "health"],
                capture_output=True, text=True, timeout=15,
            )
            services["vpn"] = "正常" if p.returncode == 0 else "异常"
        except Exception:
            services["vpn"] = "超时"
    else:
        services["vpn"] = "未部署"

    # mihomo API
    if IS_MINI:
        try:
            p = subprocess.run(
                ["curl", "-sS", "--max-time", "5", "http://127.0.0.1:9091/proxies"],
                capture_output=True, text=True, timeout=8,
            )
            if p.returncode == 0 and p.stdout:
                data = json.loads(p.stdout)
                auto = data.get("proxies", {}).get("BotQuant-Auto", {})
                services["mihomo"] = f"正常 ({auto.get('now', '未知节点')})"
            else:
                services["mihomo"] = "不可达"
        except Exception:
            services["mihomo"] = "不可达"
    else:
        services["mihomo"] = "未部署"

    # 采集器进程数
    collector_count = 0
    try:
        out = subprocess.check_output(["ps", "aux"], text=True, timeout=10)
        for line in out.splitlines():
            if "python" in line and ("collect" in line or "scheduler" in line):
                if "health_check" not in line and "aggregate" not in line:
                    collector_count += 1
    except Exception:
        pass
    services["collectors"] = collector_count

    return services


def get_parquet_status() -> dict:
    """Parquet 数据目录状态。"""
    parquet_dir = Path.home() / "J_BotQuant" / "BotQuan_Data" / "parquet"
    info: dict[str, Any] = {"exists": parquet_dir.exists()}
    if not parquet_dir.exists():
        return info

    # 最新写入
    latest = []
    for fp in parquet_dir.rglob("records.parquet"):
        try:
            t = fp.stat().st_mtime
            latest.append((t, str(fp.relative_to(parquet_dir))))
        except Exception:
            pass
    latest.sort(reverse=True)
    info["recent_files"] = [
        {"path": p, "mtime": datetime.fromtimestamp(t, tz=CN_TZ).strftime("%m-%d %H:%M")}
        for t, p in latest[:5]
    ]

    # 目录大小
    try:
        out = subprocess.check_output(["du", "-sh", str(parquet_dir)], text=True, timeout=10)
        info["size"] = out.split()[0]
    except Exception:
        info["size"] = "未知"

    return info


# ===================== 采集源新鲜度检查 =====================
def get_collector_freshness() -> list[dict[str, Any]]:
    """检查全部 18 个采集源的最新文件时间戳，返回各源状态列表。

    每项结构:
        name        — 规则键名 (如 "futures_minute")
        label       — 中文名
        ok          — bool: 是否在阈值内
        age_h       — float: 最新文件距今小时数; -1 = 目录不存在或无文件
        age_str     — 格式化字符串 (如 "1.2h" 或 "目录不存在")
        threshold_h — float: 告警阈值 (小时)
        trading_only— bool
        skipped     — bool: 非交易时段跳过检查
    """
    now_ts = datetime.now(CN_TZ).timestamp()
    results: list[dict[str, Any]] = []
    is_weekend = _is_weekend()

    for name, rule in DATA_RULES.items():
        d: Path = rule["dir"]
        threshold_h: float = rule["max_age_h"]
        label: str = rule["label"]
        trading_only: bool = rule["trading_only"]
        weekend_skip: bool = rule.get("weekend_skip", False)

        # 非交易时段跳过（分钟实时数据）
        if trading_only and not _is_intraday(name):
            results.append({
                "name": name, "label": label,
                "ok": True, "age_h": -1, "age_str": "非交易时段",
                "threshold_h": threshold_h, "trading_only": True, "skipped": True,
            })
            continue

        # 周末跳过（仅在交易日更新的数据源，周末不告警）
        if weekend_skip and is_weekend:
            results.append({
                "name": name, "label": label,
                "ok": True, "age_h": -1, "age_str": "周末休市",
                "threshold_h": threshold_h, "trading_only": trading_only, "skipped": True,
            })
            continue

        if not d.exists():
            results.append({
                "name": name, "label": label,
                "ok": False, "age_h": -1, "age_str": "目录不存在",
                "threshold_h": threshold_h, "trading_only": trading_only, "skipped": False,
            })
            continue

        # 查找目录下最新文件的 mtime
        latest_mtime: float = 0.0
        try:
            for fp in d.rglob("*"):
                if fp.is_file():
                    try:
                        t = fp.stat().st_mtime
                        if t > latest_mtime:
                            latest_mtime = t
                    except OSError:
                        pass
        except Exception:
            pass

        if latest_mtime == 0.0:
            results.append({
                "name": name, "label": label,
                "ok": False, "age_h": -1, "age_str": "无数据文件",
                "threshold_h": threshold_h, "trading_only": trading_only, "skipped": False,
            })
            continue

        age_h = (now_ts - latest_mtime) / 3600.0

        # 盘中期货分钟数据特别规则: 超 3min = P0
        effective_threshold = threshold_h
        if name == "futures_minute" and _is_intraday_futures():
            effective_threshold = 0.05  # 3 minutes

        is_ok = age_h <= effective_threshold
        if age_h < 1:
            age_str = f"{int(age_h*60)}min"
        elif age_h < 24:
            age_str = f"{age_h:.1f}h"
        else:
            age_str = f"{age_h/24:.1f}d"

        results.append({
            "name": name, "label": label,
            "ok": is_ok, "age_h": round(age_h, 3), "age_str": age_str,
            "threshold_h": effective_threshold, "trading_only": trading_only, "skipped": False,
        })

    return results


def load_alarm_state() -> dict[str, Any]:
    """加载持久化告警状态（连续失败次数、首次失败时间）。"""
    try:
        if ALARM_STATE_FILE.exists():
            return json.loads(ALARM_STATE_FILE.read_text())
    except Exception:
        pass
    return {}


def save_alarm_state(state: dict[str, Any]) -> None:
    """保存告警状态到文件。"""
    try:
        ALARM_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        ALARM_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[健康检查] 告警状态保存失败: {e}")


def build_collector_alarms(
    freshness: list[dict[str, Any]],
    alarm_state: dict[str, Any],
) -> tuple[list[dict], dict[str, Any], list[dict]]:
    """根据新鲜度检查结果和历史状态，计算需要发送的告警和恢复通知。

    Returns:
        (new_alarms, updated_state, recovered)
        new_alarms: 需要发送的告警列表（含 level P1/P0）
        updated_state: 更新后的状态字典
        recovered: 本次已恢复的源列表
    """
    now_iso = datetime.now(CN_TZ).isoformat()
    new_state: dict[str, Any] = {}
    alarms_to_send: list[dict] = []
    recovered: list[dict] = []

    failed_sources = [s for s in freshness if not s["ok"] and not s.get("skipped")]
    # 真正恢复 = ok=True 且 NOT skipped（周末跳过不算恢复）
    ok_names = {s["name"] for s in freshness if s["ok"] and not s.get("skipped")}

    # 检查恢复（只处理真实 ok，不含 skipped）
    for name, prev in alarm_state.items():
        if name in ok_names and prev.get("consecutive", 0) > 0:
            # 已恢复
            src = next((s for s in freshness if s["name"] == name), None)
            if src:
                recovered.append(src)
            # 不再写入 new_state（remove）

    # 计算新告警状态
    for src in failed_sources:
        name = src["name"]
        prev = alarm_state.get(name, {})
        consecutive = prev.get("consecutive", 0) + 1
        first_fail_ts = prev.get("first_fail_ts", now_iso)

        new_state[name] = {
            "consecutive": consecutive,
            "first_fail_ts": first_fail_ts,
            "last_fail_ts": now_iso,
            "label": src["label"],
        }

        # 确定告警级别
        # 盘中期货分钟 → 立即 P0
        if src["name"] == "futures_minute" and _is_intraday_futures():
            level = "P0"
            is_intraday = True
        elif consecutive == 1:
            level = "P1"
            is_intraday = False
        elif consecutive >= 2:
            level = "P0"
            is_intraday = False
        else:
            continue

        alarms_to_send.append({**src, "level": level, "consecutive": consecutive, "is_intraday": is_intraday})

    # 保留正在告警但本次跳过检查的源状态（skipped 不清除旧告警）
    for name, prev in alarm_state.items():
        if name not in new_state and name not in ok_names:
            new_state[name] = prev  # 跳过检查时保留旧状态（含 skipped 源）

    return alarms_to_send, new_state, recovered


# ===================== 告警判定 =====================
def evaluate_alarms(cpu: dict, mem: dict, disks: list, gpus: list, *, force_p0: bool = False) -> list[dict]:
    """根据阈值判定告警。"""
    alarms = []
    cpu_th = TH.get("cpu", {})
    mem_th = TH.get("memory", {})
    disk_th = TH.get("disk", {})
    gpu_th = TH.get("gpu", {})

    if force_p0:
        alarms.append({"metric": "测试", "level": "P0", "value": "模拟触发", "rule": "手动测试"})
        return alarms

    # CPU
    if cpu["usage_percent"] >= 0:
        if cpu["usage_percent"] >= cpu_th.get("critical_percent", 90):
            alarms.append({"metric": "CPU", "level": "P0", "value": f'{cpu["usage_percent"]}%', "rule": f'>={cpu_th.get("critical_percent", 90)}%'})
        elif cpu["usage_percent"] >= cpu_th.get("warn_percent", 75):
            alarms.append({"metric": "CPU", "level": "P1", "value": f'{cpu["usage_percent"]}%', "rule": f'>={cpu_th.get("warn_percent", 75)}%'})

    # 内存
    if mem["used_percent"] >= mem_th.get("critical_percent", 90):
        alarms.append({"metric": "内存", "level": "P0", "value": f'{mem["used_percent"]}%', "rule": f'>={mem_th.get("critical_percent", 90)}%'})
    elif mem["used_percent"] >= mem_th.get("warn_percent", 75):
        alarms.append({"metric": "内存", "level": "P1", "value": f'{mem["used_percent"]}%', "rule": f'>={mem_th.get("warn_percent", 75)}%'})

    # 磁盘
    for d in disks:
        if d["used_percent"] >= disk_th.get("critical_percent", 92):
            alarms.append({"metric": f'磁盘({d["mount"]})', "level": "P0", "value": f'{d["used_percent"]}%', "rule": f'>={disk_th.get("critical_percent", 92)}%'})
        elif d["used_percent"] >= disk_th.get("warn_percent", 80):
            alarms.append({"metric": f'磁盘({d["mount"]})', "level": "P1", "value": f'{d["used_percent"]}%', "rule": f'>={disk_th.get("warn_percent", 80)}%'})

    # GPU
    for g in gpus:
        if g["util_percent"] >= 0 and g["util_percent"] >= gpu_th.get("critical_util_percent", 90):
            alarms.append({"metric": f'GPU({g["name"][:20]})', "level": "P0", "value": f'{g["util_percent"]}%', "rule": "利用率严重"})
        if g["temp_c"] >= 0 and g["temp_c"] >= gpu_th.get("critical_temp_c", 85):
            alarms.append({"metric": f'GPU温度({g["name"][:20]})', "level": "P0", "value": f'{g["temp_c"]}°C', "rule": "温度严重"})

    return alarms


# ===================== 飞书 P0 立即告警 =====================
def send_p0_alert(report: dict) -> None:
    """发送 P0 级别立即告警到飞书（使用新通知系统）。"""
    webhook = os.environ.get("FEISHU_ALERT_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL") or ""
    if not webhook:
        print("[警告] 无飞书 webhook，跳过 P0 告警")
        return

    alarms = report.get("alarms", [])
    p0_list = [a for a in alarms if a["level"] == "P0"]
    if not p0_list:
        return

    try:
        from services.data.src.notify import card_templates as ct
        from services.data.src.notify.feishu import FeishuSender

        alarm_lines = "\n".join(f"  - {a['metric']}: {a['value']} ({a['rule']})" for a in p0_list)
        ops_base = os.environ.get("DATA_OPS_URL", "http://localhost:8105")
        ops_token = os.environ.get("DATA_OPS_SECRET", "")

        body_md = (
            f"**设备:** {report['device_label']}\n"
            f"**告警数:** {len(p0_list)}\n"
            f"**CPU:** {report['cpu']['usage_percent']}%\n"
            f"**内存:** {report['memory']['used_percent']}%\n\n"
            f"**告警详情:**\n{alarm_lines}"
        )
        card = ct.alert_p0_with_buttons(
            title=f"P0 紧急告警 — {report['device_label']}",
            body_md=body_md,
            ops_base_url=ops_base,
            ops_token=ops_token,
        )
        sender = FeishuSender()
        sender.send_card(webhook, card)
        print(f"[飞书] P0 告警已发送 (新通知系统)")
    except Exception as e:
        print(f"[飞书] P0 告警发送失败: {e}")
        # 回退: 尝试旧方式
        try:
            notifier = FeishuNotifier(webhook_url=webhook, keyword="BotQuant 报警", mock_mode=False)
            now_str = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M")
            alarm_lines = "\n".join(f"  - {a['metric']}: {a['value']} ({a['rule']})" for a in p0_list)
            card = {
                "header": {
                    "title": {"tag": "plain_text", "content": f"🚨 P0 紧急告警 — {report['device_label']}"},
                    "template": "red",
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"**设备:** {report['device_label']}\n**时间:** {now_str}\n**告警数:** {len(p0_list)}"}},
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"**告警详情:**\n{alarm_lines}"}},
                    {"tag": "hr"},
                ],
            }
            notifier.send_card(card)
        except Exception:
            pass


# ===================== 飞书修复确认消息 =====================
def send_remediation_confirm(report: dict, remediation_results: list) -> None:
    """修复完成后发送确认消息（使用新通知系统）。"""
    webhook = os.environ.get("FEISHU_ALERT_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL") or ""
    if not webhook:
        return

    try:
        from services.data.src.notify.feishu import FeishuSender
        sender = FeishuSender()

        all_ok = all(r.get("result") == "成功" for r in remediation_results)
        status_emoji = "✅" if all_ok else "⚠️"
        status_text = "全部恢复正常" if all_ok else "部分问题仍需人工处理"
        now_str = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M")

        action_lines = "\n".join(
            f"  - {r['action']}: **{r['result']}** {r.get('detail', '')}"
            for r in remediation_results
        )

        card = {
            "header": {
                "title": {"tag": "plain_text", "content": f"{status_emoji} 修复确认 — {report['device_label']}"},
                "template": "green" if all_ok else "orange",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**设备:** {report['device_label']}\n**时间:** {now_str}\n**状态:** {status_text}"}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**修复动作:**\n{action_lines}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": "如仍有异常，请在飞书群中 @管理员 处理。" if not all_ok else "系统已恢复正常运行。"}},
            ],
        }
        sender.send_card(webhook, card)
        print(f"[飞书] 修复确认已发送 (新通知系统)")
    except Exception as e:
        print(f"[飞书] 修复确认发送失败: {e}")


# ===================== 采集源告警推送 =====================
def send_collector_alert(
    alarms: list[dict[str, Any]],
    cpu: dict,
    mem: dict,
) -> None:
    """按告警级别发送采集源 P1/P0 卡片到飞书（使用新通知系统）。"""
    webhook = os.environ.get("FEISHU_ALERT_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL") or ""
    if not webhook:
        print("[警告] 无飞书 webhook，跳过采集源告警")
        return

    try:
        from services.data.src.notify import card_templates as ct
        from services.data.src.notify.feishu import FeishuSender
        sender = FeishuSender()

        for level in ("P0", "P1"):
            group = [a for a in alarms if a["level"] == level]
            if not group:
                continue
            sources_text = "\n".join(f"  - {a.get('label', a.get('name', ''))} ({a.get('age_str', '')})" for a in group)
            body_md = (
                f"**异常数:** {len(group)} 个\n"
                f"**CPU:** {cpu.get('usage_percent', 0)}%\n"
                f"**内存:** {mem.get('used_percent', 0)}%\n\n"
                f"**详情:**\n{sources_text}"
            )
            card = ct.alert_card(
                level=level,
                title=f"采集源{level}告警",
                body_md=body_md,
            )
            sender.send_card(webhook, card)
            print(f"[飞书] 采集源 {level} 告警已发送 (新通知系统)")
    except Exception as e:
        print(f"[飞书] 采集源告警发送失败: {e}")


def send_recovery_notice(
    recovered: list[dict[str, Any]],
    still_failed: list[dict[str, Any]],
) -> None:
    """发送采集源恢复通知（使用新通知系统）。"""
    webhook = os.environ.get("FEISHU_ALERT_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL") or ""
    if not webhook:
        return

    try:
        from services.data.src.notify import card_templates as ct
        from services.data.src.notify.feishu import FeishuSender
        sender = FeishuSender()

        recovered_names = [s.get("label", s.get("name", "")) for s in recovered]
        still_names = [s.get("label", s.get("name", "")) for s in still_failed]
        card = ct.collector_recovery_card(
            recovered=recovered_names,
            still_failed=still_names,
        )
        sender.send_card(webhook, card)
        print(f"[飞书] 采集恢复通知已发送 (新通知系统)")
    except Exception as e:
        print(f"[飞书] 采集恢复通知发送失败: {e}")


# ===================== 主流程 =====================
def run_health_check(force_p0: bool = False) -> dict:
    """执行健康检查并返回结构化报告。"""
    now_dt = datetime.now(CN_TZ)

    cpu = get_cpu_info()
    mem = get_memory_info()
    disks = get_disk_info()
    gpus = get_gpu_info()
    services = get_service_status()
    parquet = get_parquet_status() if IS_MINI else {"exists": False, "note": "数据在 Mini"}
    high_procs = get_high_mem_processes()
    alarms = evaluate_alarms(cpu, mem, disks, gpus, force_p0=force_p0)

    # 采集源新鲜度检查
    collector_freshness: list[dict[str, Any]] = []
    collector_alarms: list[dict[str, Any]] = []
    alarm_state_updated: dict[str, Any] = {}
    collector_recovered: list[dict[str, Any]] = []
    if IS_MINI:
        collector_freshness = get_collector_freshness()
        alarm_state = load_alarm_state()
        collector_alarms, alarm_state_updated, collector_recovered = build_collector_alarms(
            collector_freshness, alarm_state
        )

    report = {
        "device": DEVICE,
        "device_label": LABEL,
        "ts": now_dt.isoformat(),
        "ts_display": now_dt.strftime("%Y-%m-%d %H:%M"),
        "cpu": cpu,
        "memory": mem,
        "disk": disks,
        "gpu": gpus,
        "services": services,
        "parquet": parquet,
        "processes_high": high_procs,
        "alarms": alarms,
        "has_p0": any(a["level"] == "P0" for a in alarms),
        "has_p1": any(a["level"] == "P1" for a in alarms),
        "collector_freshness": collector_freshness,
        "collector_alarms": collector_alarms,
        "collector_recovered": collector_recovered,
        "_alarm_state_updated": alarm_state_updated,
        "remediate_attempts": [],
    }

    return report


def save_report(report: dict) -> Path:
    """保存 JSON 报告到 health_reports/ 目录。"""
    reports_dir = ROOT / "health_reports"
    reports_dir.mkdir(exist_ok=True)
    filepath = reports_dir / f"{report['device']}.json"
    filepath.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return filepath


def write_heartbeat() -> None:
    """写入心跳文件。"""
    suffix = ".mini_heartbeat" if IS_MINI else ".studio_heartbeat"
    hb = Path.home() / "J_BotQuant" / suffix
    hb.write_text(datetime.now(CN_TZ).isoformat())


def write_audit_log(report: dict) -> None:
    """追加审计日志。"""
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "health_audit.log"
    entry = {
        "ts": report["ts"],
        "device": report["device"],
        "cpu": report["cpu"]["usage_percent"],
        "mem": report["memory"]["used_percent"],
        "disk": [d["used_percent"] for d in report["disk"]],
        "alarms": len(report["alarms"]),
        "p0": report["has_p0"],
    }
    with log_file.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def print_summary(report: dict) -> None:
    """打印人可读摘要。"""
    lines = [
        f"{'='*50}",
        f"  {report['device_label']} 健康检查 — {report['ts_display']}",
        f"{'='*50}",
        f"  CPU:  {report['cpu']['usage_percent']}% ({report['cpu']['cores']} 核)",
        f"  内存: {report['memory']['used_mb']}MB / {report['memory']['total_mb']}MB ({report['memory']['used_percent']}%)",
    ]
    for d in report["disk"]:
        lines.append(f"  磁盘({d['mount']}): {d['used']}/{d['total']} ({d['used_percent']}%)")
    for g in report["gpu"]:
        util = f"{g['util_percent']}%" if g["util_percent"] >= 0 else "N/A"
        temp = f"{g['temp_c']}°C" if g["temp_c"] >= 0 else "N/A"
        lines.append(f"  GPU:  {g['name'][:40]} 利用率={util} 温度={temp}")
    lines.append(f"  服务: {report['services']}")
    if report["alarms"]:
        lines.append(f"  ⚠️ 告警: {len(report['alarms'])} 条")
        for a in report["alarms"]:
            lines.append(f"    [{a['level']}] {a['metric']}: {a['value']} ({a['rule']})")
    else:
        lines.append("  ✅ 无告警")
    lines.append(f"{'='*50}")
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="BotQuant 设备健康检查")
    parser.add_argument("--test-p0", action="store_true", help="模拟 P0 告警（测试用）")
    args = parser.parse_args()

    print(f"[健康检查] 设备={LABEL} 开始采集...")

    report = run_health_check(force_p0=args.test_p0)
    print_summary(report)

    # 保存 JSON
    fp = save_report(report)
    print(f"[健康检查] 报告已保存: {fp}")

    # 写心跳
    write_heartbeat()
    print("[健康检查] 心跳已更新")

    # 写审计日志
    write_audit_log(report)

    # ── 采集源告警处理 ──
    if IS_MINI:
        # 更新持久化告警状态
        alarm_state_updated = report.pop("_alarm_state_updated", {})
        save_alarm_state(alarm_state_updated)

        # 写 collector_status_latest.json（供看板读取）
        try:
            COLLECTOR_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            COLLECTOR_STATUS_FILE.write_text(json.dumps({
                "ts": report["ts"],
                "sources": report["collector_freshness"],
                "cpu": report["cpu"]["usage_percent"],
                "mem": report["memory"]["used_percent"],
                "disk": report["disk"][0]["used_percent"] if report["disk"] else 0,
            }, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[健康检查] 写 collector_status_latest.json 失败: {e}")

        # 发送采集源告警
        if report["collector_alarms"]:
            print(f"[健康检查] 检测到 {len(report['collector_alarms'])} 个采集源异常，发送告警...")
            send_collector_alert(report["collector_alarms"], report["cpu"], report["memory"])

        # 发送恢复通知
        if report["collector_recovered"]:
            still_failed = [s for s in report["collector_freshness"] if not s["ok"] and not s.get("skipped")]
            print(f"[健康检查] {len(report['collector_recovered'])} 个采集源已恢复，发送恢复通知...")
            send_recovery_notice(report["collector_recovered"], still_failed)
    else:
        report.pop("_alarm_state_updated", None)

    # P0 立即告警 + 自动修复
    if report["has_p0"]:
        print("[健康检查] 检测到 P0 告警，立即通知并启动自动修复...")
        send_p0_alert(report)

        # 调用自动修复
        try:
            remediate_script = ROOT / "scripts" / "health_remediate.py"
            if remediate_script.exists():
                p = subprocess.run(
                    [sys.executable, str(remediate_script), "--report", str(fp)],
                    capture_output=True, text=True, timeout=120,
                )
                print(p.stdout)
                if p.stderr:
                    print(p.stderr)

                # 重新读取报告（修复脚本会更新它）
                updated = json.loads(fp.read_text())
                if updated.get("remediate_attempts"):
                    send_remediation_confirm(updated, updated["remediate_attempts"])
        except Exception as e:
            print(f"[自动修复] 执行失败: {e}")

    print("[健康检查] 完成")
    sys.exit(0)


if __name__ == "__main__":
    main()
