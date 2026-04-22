#!/usr/bin/env python3
"""持续监控 35 个连续合约分钟回补进度。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


DEFAULT_HOST = "jaybot@192.168.31.76"
DEFAULT_TARGET_DIR = "/Users/jaybot/JBT/data/futures_minute/1m"
DEFAULT_LOG_DIR = "/Users/jaybot/JBT/data_backfill/logs"

CONTINUOUS_CONTRACTS = [
    "KQ.m@CZCE.CF", "KQ.m@CZCE.FG", "KQ.m@CZCE.MA", "KQ.m@CZCE.OI", "KQ.m@CZCE.PF",
    "KQ.m@CZCE.RM", "KQ.m@CZCE.SA", "KQ.m@CZCE.SR", "KQ.m@CZCE.TA", "KQ.m@CZCE.UR",
    "KQ.m@DCE.a", "KQ.m@DCE.c", "KQ.m@DCE.eb", "KQ.m@DCE.i", "KQ.m@DCE.j",
    "KQ.m@DCE.jd", "KQ.m@DCE.jm", "KQ.m@DCE.l", "KQ.m@DCE.lh", "KQ.m@DCE.m",
    "KQ.m@DCE.p", "KQ.m@DCE.pg", "KQ.m@DCE.pp", "KQ.m@DCE.v", "KQ.m@DCE.y",
    "KQ.m@SHFE.ag", "KQ.m@SHFE.al", "KQ.m@SHFE.au", "KQ.m@SHFE.cu", "KQ.m@SHFE.hc",
    "KQ.m@SHFE.rb", "KQ.m@SHFE.ru", "KQ.m@SHFE.sp", "KQ.m@SHFE.ss", "KQ.m@SHFE.zn",
]


def symbol_to_dirname(symbol: str) -> str:
    return symbol.replace(".", "_").replace("@", "_")


def build_probe_script(start_month: str, end_month: str, target_dir: str, log_dir: str) -> str:
    contracts_json = json.dumps(CONTINUOUS_CONTRACTS, ensure_ascii=True)
    return f"""
from pathlib import Path
import json
import re
import subprocess
from datetime import datetime

contracts = json.loads({contracts_json!r})
base = Path({target_dir!r})
log_dir = Path({log_dir!r})
start = {start_month!r}
end = {end_month!r}
pat = re.compile(r'^\\d{{6}}$')

def month_range(start_month, end_month):
    months = []
    year = int(start_month[:4])
    month = int(start_month[4:])
    end_year = int(end_month[:4])
    end_month_num = int(end_month[4:])
    while (year, month) <= (end_year, end_month_num):
        months.append(f"{{year}}{{month:02d}}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months

rows = []
for symbol in contracts:
    dirname = symbol.replace('.', '_').replace('@', '_')
    symbol_dir = base / dirname
    months = sorted([p.stem for p in symbol_dir.glob('*.parquet') if pat.match(p.stem)]) if symbol_dir.exists() else []
    if not months:
        rows.append({{
            'symbol': symbol,
            'dirname': dirname,
            'count': 0,
            'first': None,
            'last': None,
            'missing': len(month_range(start, end)),
            'inner_missing': len(month_range(start, end)),
            'tail_missing': 0,
        }})
        continue

    first = months[0]
    last = months[-1]
    anchor = max(first, start)
    expected = month_range(anchor, end)
    between = month_range(anchor, min(last, end)) if last >= anchor else []
    missing = [month for month in expected if month not in months]
    inner_missing = [month for month in between if month not in months]
    tail_missing = [month for month in expected if month > last]
    rows.append({{
        'symbol': symbol,
        'dirname': dirname,
        'count': len(months),
        'first': first,
        'last': last,
        'missing': len(missing),
        'inner_missing': len(inner_missing),
        'tail_missing': len(tail_missing),
    }})

proc = subprocess.run(
    "ps -axo pid=,command= | grep -E 'fill_continuous_contract_gaps.py --symbols|full_backfill_all.py --mode minute' | grep -v grep || true",
    shell=True,
    check=False,
    capture_output=True,
    text=True,
)
processes = [line for line in proc.stdout.splitlines() if line.strip()]

group_logs = []
for idx in range(1, 6):
    path = log_dir / f'fill_shfe_group{{idx}}.log'
    if path.exists():
        stat = path.stat()
        group_logs.append({{
            'name': path.name,
            'size': stat.st_size,
            'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        }})

full_logs = sorted(log_dir.glob('futures_minute_full_*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
latest_full_log = None
if full_logs:
    stat = full_logs[0].stat()
    latest_full_log = {{
        'name': full_logs[0].name,
        'size': stat.st_size,
        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
    }}

payload = {{
    'probe_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'rows': rows,
    'processes': processes,
    'group_logs': group_logs,
    'latest_full_log': latest_full_log,
}}
print(json.dumps(payload, ensure_ascii=False))
"""


def run_probe(host: str, script: str, timeout_seconds: int) -> dict:
    if host == "local":
        command = [sys.executable, "-"]
    else:
        command = ["ssh", host, "python3", "-"]

    completed = subprocess.run(
        command,
        input=script,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or f"probe failed with exit code {completed.returncode}"
        raise RuntimeError(stderr)
    return json.loads(completed.stdout)


def render_snapshot(snapshot: dict, previous: dict | None, host: str) -> str:
    rows = snapshot["rows"]
    incomplete = sorted((row for row in rows if row["missing"] > 0), key=lambda row: (-row["missing"], row["symbol"]))
    complete = len(rows) - len(incomplete)

    lines = [
        f"[{snapshot['probe_time']}] host={host}",
        f"完成 {complete}/{len(rows)} | 未完成 {len(incomplete)}/{len(rows)}",
    ]

    if snapshot.get("processes"):
        lines.append(f"活跃进程 {len(snapshot['processes'])} 条")
        lines.extend(f"  {line}" for line in snapshot["processes"])
    else:
        lines.append("活跃进程 0 条")

    if snapshot.get("latest_full_log"):
        full_log = snapshot["latest_full_log"]
        lines.append(f"全量 minute 日志: {full_log['name']} size={full_log['size']} mtime={full_log['mtime']}")

    if snapshot.get("group_logs"):
        lines.append("分组日志:")
        for item in snapshot["group_logs"]:
            lines.append(f"  {item['name']} size={item['size']} mtime={item['mtime']}")

    if incomplete:
        lines.append("未完成品种:")
        for row in incomplete:
            lines.append(
                "  {symbol} months={count} missing={missing} inner={inner_missing} tail={tail_missing} first={first} last={last}".format(**row)
            )
    else:
        lines.append("未完成品种: 0")

    if previous is not None:
        previous_rows = {row["symbol"]: row for row in previous["rows"]}
        deltas = []
        for row in rows:
            old = previous_rows.get(row["symbol"])
            if old is None:
                continue
            if row["count"] != old["count"] or row["missing"] != old["missing"]:
                deltas.append(
                    f"  {row['symbol']} months {old['count']} -> {row['count']}, missing {old['missing']} -> {row['missing']}"
                )
        if deltas:
            lines.append("本轮变化:")
            lines.extend(deltas)

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="每 5 分钟刷新连续合约回补进度")
    parser.add_argument("--host", default=DEFAULT_HOST, help="SSH 目标主机，使用 local 表示本机运行")
    parser.add_argument("--start-month", default="201801", help="统计起始月份 YYYYMM")
    parser.add_argument("--end-month", default="202604", help="统计结束月份 YYYYMM")
    parser.add_argument("--interval-seconds", type=int, default=300, help="刷新间隔秒数，默认 300")
    parser.add_argument("--command-timeout", type=int, default=60, help="单次探测超时秒数，默认 60")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help="连续合约月文件目录")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR, help="远端日志目录")
    parser.add_argument("--once", action="store_true", help="只执行一次探测")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    probe_script = build_probe_script(args.start_month, args.end_month, args.target_dir, args.log_dir)
    previous = None

    try:
        while True:
            snapshot = run_probe(args.host, probe_script, args.command_timeout)
            print(render_snapshot(snapshot, previous, args.host), flush=True)
            previous = snapshot
            if args.once:
                return 0
            print("-" * 80, flush=True)
            time.sleep(args.interval_seconds)
    except KeyboardInterrupt:
        print("监控已停止", flush=True)
        return 0
    except Exception as exc:
        print(f"监控失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())