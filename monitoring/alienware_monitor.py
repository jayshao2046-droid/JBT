#!/usr/bin/env python3
"""Alienware 进程资源监控 — 写入每日 JSON，7天自动清理

采样周期：每 5 分钟
输出目录：runtime/monitor/
文件格式：process_monitor_YYYY-MM-DD.json

JSON 结构（追加写入，每次采样 append 到 samples 数组）：
{
  "date": "2026-04-15",
  "machine": "Alienware",
  "samples": [
    {
      "ts": "2026-04-15T14:30:00",
      "system": {
        "cpu_percent": 45.2,
        "memory_percent": 68.5,
        "memory_used_gb": 21.9,
        "memory_total_gb": 32.0
      },
      "gpu": {
        "name": "NVIDIA RTX ...",
        "memory_total_mb": 24576,
        "memory_used_mb": 8192,
        "memory_free_mb": 16384,
        "utilization_percent": 78,
        "temperature_c": 72
      },
      "processes": {
        "researcher": {"pid": 23520, "cpu_percent": 12.5, "memory_mb": 512, "status": "running"},
        "sim_trading": {"pid": 12345, "cpu_percent": 2.1, "memory_mb": 256, "status": "running"}
      }
    }
  ]
}
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

# ── 配置 ──────────────────────────────────────────────────────────────────────

SAMPLE_INTERVAL_S = 300        # 每 5 分钟采样一次
RETENTION_DAYS    = 7          # 保留 7 天
BASE_DIR          = Path(__file__).resolve().parent
OUTPUT_DIR        = BASE_DIR / "runtime" / "monitor"

# 关注进程关键词（匹配命令行参数，Windows 下进程名为 python.exe）
WATCHED_PROCS = {
    "researcher": ["run_researcher", "researcher"],
    "sim_trading": ["run_sim_trading", "sim_trading", "sim-trading"],
}

# ── GPU 采样 ──────────────────────────────────────────────────────────────────

def _query_gpu() -> dict:
    """调用 nvidia-smi 获取 GPU 状态，返回空 dict 表示无 GPU / 调用失败。"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,"
                "utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {}
        line = result.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        return {
            "name":              parts[0],
            "memory_total_mb":   int(parts[1]),
            "memory_used_mb":    int(parts[2]),
            "memory_free_mb":    int(parts[3]),
            "utilization_percent": int(parts[4]),
            "temperature_c":     int(parts[5]),
        }
    except Exception:
        return {}


# ── 进程采样 ──────────────────────────────────────────────────────────────────

def _query_processes() -> dict:
    """查找关注进程的 CPU/内存状态。"""
    result = {key: {"pid": None, "status": "not_found", "cpu_percent": 0.0, "memory_mb": 0.0}
              for key in WATCHED_PROCS}

    for proc in psutil.process_iter(["pid", "name", "cmdline", "status"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or []).lower()
            for key, keywords in WATCHED_PROCS.items():
                if result[key]["pid"] is not None:
                    continue  # 已找到，跳过
                if any(kw in cmdline for kw in keywords):
                    cpu = proc.cpu_percent(interval=0.1)
                    mem = proc.memory_info().rss / (1024 * 1024)
                    result[key] = {
                        "pid":         proc.info["pid"],
                        "status":      proc.info["status"] or "running",
                        "cpu_percent": round(cpu, 2),
                        "memory_mb":   round(mem, 1),
                    }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return result


# ── 系统采样 ──────────────────────────────────────────────────────────────────

def _query_system() -> dict:
    mem = psutil.virtual_memory()
    return {
        "cpu_percent":    round(psutil.cpu_percent(interval=1), 2),
        "memory_percent": round(mem.percent, 2),
        "memory_used_gb": round(mem.used / (1024 ** 3), 2),
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
    }


# ── 写入 ──────────────────────────────────────────────────────────────────────

def _write_sample(sample: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = OUTPUT_DIR / f"process_monitor_{date_str}.json"

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {"date": date_str, "machine": "Alienware", "samples": []}
    else:
        data = {"date": date_str, "machine": "Alienware", "samples": []}

    data["samples"].append(sample)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 7 天清理 ──────────────────────────────────────────────────────────────────

def _cleanup_old_files() -> None:
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    for p in OUTPUT_DIR.glob("process_monitor_*.json"):
        try:
            date_part = p.stem.replace("process_monitor_", "")
            file_date = datetime.strptime(date_part, "%Y-%m-%d")
            if file_date < cutoff:
                p.unlink()
        except (ValueError, OSError):
            continue


# ── 主循环 ────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[monitor] 启动 Alienware 进程监控，采样间隔={SAMPLE_INTERVAL_S}s，保留={RETENTION_DAYS}天")
    print(f"[monitor] 输出目录: {OUTPUT_DIR}")

    iteration = 0
    while True:
        try:
            now = datetime.now()
            sample = {
                "ts":        now.isoformat(timespec="seconds"),
                "system":    _query_system(),
                "gpu":       _query_gpu(),
                "processes": _query_processes(),
            }
            _write_sample(sample)

            iteration += 1
            # 每小时清理一次旧文件（12次采样 × 5分钟 = 60分钟）
            if iteration % 12 == 0:
                _cleanup_old_files()

            print(
                f"[monitor] {now.strftime('%H:%M:%S')} "
                f"CPU={sample['system']['cpu_percent']}% "
                f"MEM={sample['system']['memory_percent']}% "
                f"GPU用量={sample['gpu'].get('utilization_percent', 'N/A')}%"
            )

        except Exception as e:
            print(f"[monitor] 采样错误: {e}", file=sys.stderr)

        time.sleep(SAMPLE_INTERVAL_S)


if __name__ == "__main__":
    # --once 模式：采样一次后退出（由 Windows 任务计划程序每 5 分钟周期触发）
    # 无参数模式：进程常驻，内部 sleep 循环
    if "--once" in sys.argv:
        try:
            now = datetime.now()
            sample = {
                "ts":        now.isoformat(timespec="seconds"),
                "system":    _query_system(),
                "gpu":       _query_gpu(),
                "processes": _query_processes(),
            }
            _write_sample(sample)
            _cleanup_old_files()
        except Exception as e:
            print(f"[monitor] 采样失败: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        main()
