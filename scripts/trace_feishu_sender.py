#!/usr/bin/env python3
"""
飞书推送反向追踪脚本
用法：在 Alienware 上运行，hook FeishuNotifier.send() 方法，记录完整调用栈
"""
import sys
import os
import traceback
import json
from datetime import datetime

# 添加 sim-trading 到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../services/sim-trading"))

# Monkey patch FeishuNotifier.send
from src.notifier.feishu import FeishuNotifier

_original_send = FeishuNotifier.send

def _traced_send(self, event):
    """Hook 版本：记录完整调用栈到文件"""
    # 获取调用栈
    stack = traceback.extract_stack()[:-1]  # 排除当前帧

    # 构造追踪记录
    trace_record = {
        "timestamp": datetime.now().isoformat(),
        "event_code": event.event_code,
        "risk_level": event.risk_level,
        "message": event.message or event.reason,
        "account_id": event.account_id,
        "task_id": event.task_id,
        "source": event.source,
        "category": event.category,
        "call_stack": [
            {
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line,
            }
            for frame in stack
        ],
    }

    # 写入追踪日志
    log_file = "/tmp/feishu_trace.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(trace_record, ensure_ascii=False) + "\n")

    # 同时打印到控制台
    print(f"\n{'='*80}")
    print(f"[TRACE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Event: {event.event_code} | Level: {event.risk_level}")
    print(f"Message: {event.message or event.reason}")
    print(f"Source: {event.source} | Category: {event.category}")
    print(f"\nCall Stack (最近 5 层):")
    for frame in stack[-5:]:
        print(f"  {frame.filename}:{frame.lineno} in {frame.name}()")
        if frame.line:
            print(f"    → {frame.line.strip()}")
    print(f"{'='*80}\n")

    # 调用原始方法
    return _original_send(self, event)

# 替换方法
FeishuNotifier.send = _traced_send

print(f"[TRACER] FeishuNotifier.send() hooked")
print(f"[TRACER] Trace log: /tmp/feishu_trace.jsonl")
print(f"[TRACER] Starting sim-trading with tracing enabled...\n")

# 启动 sim-trading
from src.main import app
import uvicorn

port = int(os.getenv("SERVICE_PORT", "8101"))
uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
