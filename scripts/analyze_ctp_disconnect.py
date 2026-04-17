#!/usr/bin/env python3
"""
分析 CTP 断联诊断日志，找出根本原因
用法：python scripts/analyze_ctp_disconnect.py
"""
import json
import sys
from collections import Counter
from datetime import datetime

def analyze_disconnect_log(log_file="/tmp/ctp_disconnect_diagnosis.jsonl"):
    """分析断联日志"""
    import os
    if not os.path.exists(log_file):
        print(f"❌ 诊断日志不存在: {log_file}")
        print("请先运行 diagnose_ctp_disconnect.py 收集数据")
        return

    records = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        print("❌ 诊断日志为空")
        return

    print(f"\n{'='*80}")
    print(f"CTP 断联诊断分析报告")
    print(f"{'='*80}\n")
    print(f"总断联次数: {len(records)}")
    print(f"时间范围: {records[0]['timestamp']} ~ {records[-1]['timestamp']}\n")

    # 统计断联原因
    print(f"{'='*80}")
    print(f"断联原因统计")
    print(f"{'='*80}\n")

    all_reasons = []
    for rec in records:
        all_reasons.extend(rec.get("disconnect_reasons", []))

    reason_counter = Counter(all_reasons)
    for reason, count in reason_counter.most_common():
        print(f"  [{count:3d}次] {reason}")

    # 网络可达性分析
    print(f"\n{'='*80}")
    print(f"网络可达性分析")
    print(f"{'='*80}\n")

    md_unreachable = sum(1 for r in records if not r.get("network", {}).get("md_reachable", True))
    td_unreachable = sum(1 for r in records if not r.get("network", {}).get("td_reachable", True))

    print(f"行情前置不可达: {md_unreachable}/{len(records)} ({md_unreachable/len(records)*100:.1f}%)")
    print(f"交易前置不可达: {td_unreachable}/{len(records)} ({td_unreachable/len(records)*100:.1f}%)")

    # Ping 延迟分析
    ping_latencies = [
        r["network"]["ping_avg_ms"]
        for r in records
        if r.get("network", {}).get("ping_avg_ms") is not None
    ]

    if ping_latencies:
        avg_latency = sum(ping_latencies) / len(ping_latencies)
        max_latency = max(ping_latencies)
        min_latency = min(ping_latencies)
        print(f"\nPing 延迟统计:")
        print(f"  平均: {avg_latency:.2f} ms")
        print(f"  最小: {min_latency:.2f} ms")
        print(f"  最大: {max_latency:.2f} ms")

    # 时间分布分析
    print(f"\n{'='*80}")
    print(f"断联时间分布")
    print(f"{'='*80}\n")

    hour_counter = Counter()
    for rec in records:
        try:
            dt = datetime.fromisoformat(rec["timestamp"])
            hour_counter[dt.hour] += 1
        except:
            pass

    print("按小时统计:")
    for hour in sorted(hour_counter.keys()):
        bar = "█" * hour_counter[hour]
        print(f"  {hour:02d}:00 | {bar} {hour_counter[hour]}")

    # 断联模式分析
    print(f"\n{'='*80}")
    print(f"断联模式分析")
    print(f"{'='*80}\n")

    md_only = sum(1 for r in records if not r["status"]["md_connected"] and r["status"]["td_connected"])
    td_only = sum(1 for r in records if r["status"]["md_connected"] and not r["status"]["td_connected"])
    both = sum(1 for r in records if not r["status"]["md_connected"] and not r["status"]["td_connected"])

    print(f"仅行情断开: {md_only} 次 ({md_only/len(records)*100:.1f}%)")
    print(f"仅交易断开: {td_only} 次 ({td_only/len(records)*100:.1f}%)")
    print(f"双通道断开: {both} 次 ({both/len(records)*100:.1f}%)")

    # 根因推断
    print(f"\n{'='*80}")
    print(f"根因推断")
    print(f"{'='*80}\n")

    if md_unreachable > len(records) * 0.5 or td_unreachable > len(records) * 0.5:
        print("🔴 网络层问题：超过 50% 的断联时前置服务器不可达")
        print("   建议：检查 Alienware 到 SimNow 的网络路由、防火墙、DNS")
    elif ping_latencies and max(ping_latencies) > 100:
        print("🟡 网络延迟问题：Ping 延迟超过 100ms")
        print("   建议：检查网络质量、带宽占用、路由跳数")
    elif both > len(records) * 0.8:
        print("🔴 双通道同时断开：可能是本地网络或 SimNow 服务器问题")
        print("   建议：检查本地网卡状态、SimNow 服务器维护公告")
    elif "接收心跳超时" in str(all_reasons):
        print("🟡 心跳超时：CTP 连接空闲超时")
        print("   建议：检查 SimNow 是否有空闲连接限制、增加心跳频率")
    else:
        print("🟢 未发现明显网络问题，可能是 SimNow 服务器主动断开")
        print("   建议：查看 SimNow 官方公告、检查账户是否有连接时长限制")

    # 详细记录（最近 5 次）
    print(f"\n{'='*80}")
    print(f"最近 5 次断联详情")
    print(f"{'='*80}\n")

    for i, rec in enumerate(records[-5:], 1):
        print(f"[{i}] {rec['timestamp']}")
        print(f"  状态: MD={rec['status']['md_connected']} ({rec['status']['md_status']}) | "
              f"TD={rec['status']['td_connected']} ({rec['status']['td_status']})")
        print(f"  原因:")
        for reason in rec.get("disconnect_reasons", []):
            print(f"    - {reason}")
        print(f"  网络: MD可达={rec['network']['md_reachable']}, TD可达={rec['network']['td_reachable']}")
        if rec['network'].get('ping_avg_ms'):
            print(f"  延迟: {rec['network']['ping_avg_ms']:.2f} ms")
        print()

    print(f"{'='*80}\n")

if __name__ == "__main__":
    analyze_disconnect_log()
