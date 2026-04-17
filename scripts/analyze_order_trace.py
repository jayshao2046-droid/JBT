#!/usr/bin/env python3
"""
分析订单追踪日志，找出下单来源
用法：python scripts/analyze_order_trace.py
"""
import json
import sys
from collections import Counter
from datetime import datetime

def analyze_order_trace(log_file="/tmp/order_trace.jsonl"):
    """分析订单追踪日志"""
    import os
    if not os.path.exists(log_file):
        print(f"❌ 追踪日志不存在: {log_file}")
        print("请先运行 trace_order_source.py 收集数据")
        return

    records = []
    with open(log_file) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        print("❌ 追踪日志为空")
        return

    print(f"\n{'='*80}")
    print(f"订单来源追踪分析报告")
    print(f"{'='*80}\n")
    print(f"总订单数: {len(records)}")
    print(f"时间范围: {records[0]['timestamp']} ~ {records[-1]['timestamp']}\n")

    # 统计品种
    instrument_counter = Counter(r["order"]["instrument_id"] for r in records)
    print(f"品种分布:")
    for instrument, count in instrument_counter.most_common():
        print(f"  {instrument}: {count} 笔")

    # 统计方向
    direction_counter = Counter(r["order"]["direction_str"] for r in records)
    print(f"\n方向分布:")
    for direction, count in direction_counter.items():
        print(f"  {direction}: {count} 笔")

    # 统计开平
    offset_counter = Counter(r["order"]["offset_str"] for r in records)
    print(f"\n开平分布:")
    for offset, count in offset_counter.items():
        print(f"  {offset}: {count} 笔")

    # 分析调用来源
    print(f"\n{'='*80}")
    print(f"调用来源分析")
    print(f"{'='*80}\n")

    # 统计调用栈中的关键函数
    caller_functions = []
    for rec in records:
        stack = rec["call_stack"]
        # 找到第一个非 gateway 的调用者
        for frame in reversed(stack):
            if "/gateway/" not in frame["file"] and "/services/sim-trading/" in frame["file"]:
                caller_functions.append(f"{frame['function']}() in {frame['file'].split('/')[-1]}")
                break

    caller_counter = Counter(caller_functions)
    print(f"调用函数统计:")
    for caller, count in caller_counter.most_common():
        print(f"  [{count:3d}次] {caller}")

    # 检测是否有 API 调用
    api_calls = [
        r for r in records
        if any("/api/" in f["file"] or "router" in f["file"] for f in r["call_stack"])
    ]
    print(f"\n通过 API 下单: {len(api_calls)} 笔 ({len(api_calls)/len(records)*100:.1f}%)")

    # 检测是否有策略调用
    strategy_calls = [
        r for r in records
        if any("strategy" in f["file"].lower() or "strategy" in f["function"].lower() for f in r["call_stack"])
    ]
    print(f"通过策略下单: {len(strategy_calls)} 笔 ({len(strategy_calls)/len(records)*100:.1f}%)")

    # 检测是否有定时任务
    scheduler_calls = [
        r for r in records
        if any("scheduler" in f["file"].lower() or "timer" in f["function"].lower() for f in r["call_stack"])
    ]
    print(f"通过定时任务下单: {len(scheduler_calls)} 笔 ({len(scheduler_calls)/len(records)*100:.1f}%)")

    # 时间分布
    print(f"\n{'='*80}")
    print(f"时间分布分析")
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
        bar = "█" * (hour_counter[hour] // 2 or 1)
        print(f"  {hour:02d}:00 | {bar} {hour_counter[hour]}")

    # 详细记录（最近 5 笔）
    print(f"\n{'='*80}")
    print(f"最近 5 笔订单详情")
    print(f"{'='*80}\n")

    for i, rec in enumerate(records[-5:], 1):
        order = rec["order"]
        print(f"[{i}] {rec['timestamp']}")
        print(f"  订单: {order['direction_str']}{order['offset_str']} {order['instrument_id']} "
              f"{order['volume']}手@{order['price']:.2f}")

        # 调用者上下文
        ctx = rec.get("caller_context", {})
        locals_dict = ctx.get("locals", {})
        globals_dict = ctx.get("globals", {})

        if locals_dict or globals_dict:
            print(f"  调用者上下文:")
            if globals_dict:
                print(f"    全局变量: {globals_dict}")
            if locals_dict:
                print(f"    局部变量: {list(locals_dict.keys())[:5]}")

        # 调用栈（关键路径）
        print(f"  调用栈 (关键路径):")
        key_frames = [
            f for f in rec["call_stack"]
            if "/services/sim-trading/" in f["file"]
            and "site-packages" not in f["file"]
        ]

        for frame in key_frames[-5:]:  # 最近 5 层
            file_short = frame["file"].split("/services/sim-trading/")[-1]
            print(f"    {file_short}:{frame['line']} in {frame['function']}()")
            if frame["code"]:
                print(f"      → {frame['code']}")

        print()

    print(f"{'='*80}\n")

if __name__ == "__main__":
    analyze_order_trace()
