#!/usr/bin/env python3
"""
订单来源追踪脚本 - 完整版
Hook CTP 下单方法，记录每笔订单的完整调用栈和上下文
"""
import sys
import os
import traceback
import json
import inspect
from datetime import datetime

# 添加 sim-trading 到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../services/sim-trading"))

# Monkey patch SimNowGateway.insert_order
from src.gateway.simnow import SimNowGateway

_original_insert_order = SimNowGateway.insert_order

def _traced_insert_order(self, instrument_id, direction, offset, price, volume):
    """Hook 版本：记录完整调用栈和上下文"""
    # 获取调用栈
    stack = traceback.extract_stack()[:-1]  # 排除当前帧

    # 获取调用者的局部变量（尝试找到策略信息）
    caller_frame = inspect.currentframe().f_back
    caller_locals = {}
    caller_globals = {}

    try:
        if caller_frame:
            # 获取调用者的局部变量
            caller_locals = {
                k: str(v)[:200]  # 限制长度
                for k, v in caller_frame.f_locals.items()
                if not k.startswith("_") and k not in ["self", "cls"]
            }
            # 获取调用者的全局变量（只取关键的）
            caller_globals = {
                k: str(v)[:200]
                for k, v in caller_frame.f_globals.items()
                if k in ["strategy_id", "signal_id", "task_id", "account_id"]
            }
    except Exception as e:
        caller_locals = {"error": str(e)}

    # 方向和开平转换
    direction_str = "买" if direction == "0" else "卖"
    offset_str = {"0": "开仓", "1": "平仓", "3": "平今", "4": "平昨"}.get(offset, offset)

    # 构造追踪记录
    trace_record = {
        "timestamp": datetime.now().isoformat(),
        "order": {
            "instrument_id": instrument_id,
            "direction": direction,
            "direction_str": direction_str,
            "offset": offset,
            "offset_str": offset_str,
            "price": price,
            "volume": volume,
        },
        "caller_context": {
            "locals": caller_locals,
            "globals": caller_globals,
        },
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
    log_file = "/tmp/order_trace.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(trace_record, ensure_ascii=False) + "\n")

    # 打印到控制台
    print(f"\n{'='*80}")
    print(f"[ORDER TRACE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"订单: {direction_str}{offset_str} {instrument_id} {volume}手@{price:.2f}")
    print(f"\n调用者上下文:")
    if caller_locals:
        print(f"  局部变量:")
        for k, v in list(caller_locals.items())[:5]:  # 只显示前 5 个
            print(f"    {k} = {v}")
    if caller_globals:
        print(f"  全局变量:")
        for k, v in caller_globals.items():
            print(f"    {k} = {v}")

    print(f"\n调用栈 (最近 8 层):")
    for frame in stack[-8:]:
        file_short = frame.filename.split("/services/sim-trading/")[-1] if "/services/sim-trading/" in frame.filename else frame.filename
        print(f"  {file_short}:{frame.lineno} in {frame.name}()")
        if frame.line:
            print(f"    → {frame.line.strip()}")
    print(f"{'='*80}\n")

    # 调用原始方法
    return _original_insert_order(self, instrument_id, direction, offset, price, volume)

# 替换方法
SimNowGateway.insert_order = _traced_insert_order

print(f"[TRACER] SimNowGateway.insert_order() hooked")
print(f"[TRACER] Order trace log: /tmp/order_trace.jsonl")
print(f"[TRACER] Starting sim-trading with order tracing enabled...\n")

# 启动 sim-trading
from src.main import app
import uvicorn

port = int(os.getenv("SERVICE_PORT", "8101"))
uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
