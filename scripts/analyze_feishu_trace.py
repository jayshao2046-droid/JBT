#!/usr/bin/env python3
"""
分析飞书追踪日志，找出 TRADE_EXECUTED 的真实来源
用法：python scripts/analyze_feishu_trace.py
"""
import json
import sys
from collections import Counter
from datetime import datetime

def analyze_trace_log(log_file="/tmp/feishu_trace.jsonl"):
    """分析追踪日志"""
    if not __import__("os").path.exists(log_file):
        print(f"❌ 追踪日志不存在: {log_file}")
        print("请先运行 trace_feishu_sender.py 收集数据")
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
    print(f"飞书推送追踪分析报告")
    print(f"{'='*80}\n")
    print(f"总记录数: {len(records)}")
    print(f"时间范围: {records[0]['timestamp']} ~ {records[-1]['timestamp']}\n")

    # 按 event_code 分组统计
    event_counter = Counter(r["event_code"] for r in records)
    print(f"事件类型分布:")
    for event_code, count in event_counter.most_common():
        print(f"  {event_code}: {count} 次")

    # 重点分析 TRADE_EXECUTED
    trade_records = [r for r in records if r["event_code"] == "TRADE_EXECUTED"]
    if trade_records:
        print(f"\n{'='*80}")
        print(f"TRADE_EXECUTED 详细分析 (共 {len(trade_records)} 条)")
        print(f"{'='*80}\n")

        for i, rec in enumerate(trade_records, 1):
            print(f"\n[{i}] {rec['timestamp']}")
            print(f"  消息: {rec['message']}")
            print(f"  来源: {rec.get('source', 'N/A')}")
            print(f"  分类: {rec.get('category', 'N/A')}")
            print(f"\n  调用栈 (关键路径):")

            # 过滤出关键调用帧（排除标准库）
            key_frames = [
                f for f in rec["call_stack"]
                if "/services/sim-trading/" in f["file"]
                and "site-packages" not in f["file"]
            ]

            for frame in key_frames[-8:]:  # 最近 8 层
                file_short = frame["file"].split("/services/sim-trading/")[-1]
                print(f"    {file_short}:{frame['line']} in {frame['function']}()")
                if frame["code"]:
                    print(f"      → {frame['code']}")

            print(f"  {'-'*76}")

    # 分析是否有定时任务
    print(f"\n{'='*80}")
    print(f"定时任务检测")
    print(f"{'='*80}\n")

    scheduler_records = [
        r for r in records
        if any(
            "scheduler" in f["file"].lower() or
            "guardian" in f["file"].lower() or
            "timer" in f["function"].lower()
            for f in r["call_stack"]
        )
    ]

    if scheduler_records:
        print(f"⚠️  发现 {len(scheduler_records)} 条疑似定时任务触发的推送:")
        for rec in scheduler_records[:5]:  # 只显示前 5 条
            print(f"  - {rec['timestamp']} | {rec['event_code']} | {rec['message']}")
    else:
        print("✅ 未发现定时任务触发的推送")

    # 时间分布分析
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
        bar = "█" * (hour_counter[hour] // 2)
        print(f"  {hour:02d}:00 | {bar} {hour_counter[hour]}")

    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    analyze_trace_log()
