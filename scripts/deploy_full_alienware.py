#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alienware 完整部署脚本（Python 版本，兼容 Windows）
部署心跳报告 + 集成订单追踪 + CTP 断联诊断
"""
import os
import sys
import time
import subprocess
import signal
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def kill_process_by_name(name):
    """杀死指定名称的进程"""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", f"WINDOWTITLE eq *{name}*"],
                          capture_output=True, timeout=5)
        else:
            subprocess.run(["pkill", "-f", name], capture_output=True, timeout=5)
        return True
    except Exception as e:
        print(f"  警告: {e}")
        return False

def start_background_process(script_path=None, log_path=None, working_dir=None, command=None):
    """启动后台进程"""
    try:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        cwd = working_dir

        if command is None:
            if sys.platform == "win32":
                command = ["pythonw.exe", script_path]
            else:
                command = ["python3", script_path]

        if sys.platform == "win32":
            proc = subprocess.Popen(
                command,
                stdout=open(log_path, "w"),
                stderr=subprocess.STDOUT,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            proc = subprocess.Popen(
                command,
                stdout=open(log_path, "w"),
                stderr=subprocess.STDOUT,
                cwd=cwd,
                preexec_fn=os.setpgrp
            )
        return proc.pid
    except Exception as e:
        print(f"  [ERROR] 启动失败: {e}")
        return None

def main():
    print("=" * 60)
    print("Sim-Trading 完整部署")
    print("=" * 60)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"系统平台: {sys.platform}")
    print()

    # 切换到 JBT 目录
    jbt_dir = os.path.expanduser("~/JBT")
    if not os.path.exists(jbt_dir):
        print(f"❌ JBT 目录不存在: {jbt_dir}")
        sys.exit(1)
    os.chdir(jbt_dir)
    print(f"工作目录: {os.getcwd()}")
    print()

    # 1. 停止所有相关进程
    print("[1/5] 停止现有进程...")
    kill_process_by_name("sim-trading")
    kill_process_by_name("main.py")
    kill_process_by_name("trace_order_source.py")
    kill_process_by_name("diagnose_ctp_disconnect.py")
    time.sleep(3)
    print("  [OK] 进程已停止")

    # 2. 验证文件
    print()
    print("[2/5] 验证文件...")
    required_files = [
        "services/sim-trading/src/health/heartbeat.py",
        "scripts/diagnose_ctp_disconnect.py",
    ]
    for file in required_files:
        if not os.path.exists(file):
            print(f"  [ERROR] {file} 不存在")
            sys.exit(1)
    print("  [OK] 所有文件就绪")

    # 3. 清理旧日志
    print()
    print("[3/5] 清理旧日志...")

    # 创建日志目录
    if sys.platform == "win32":
        log_dir = "C:/temp"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"  创建日志目录: {log_dir}")

    log_files = [
        "/tmp/sim-trading.log" if sys.platform != "win32" else "C:/temp/sim-trading.log",
        "/tmp/order_trace.jsonl" if sys.platform != "win32" else "C:/temp/order_trace.jsonl",
        "/tmp/ctp_disconnect_diagnosis.jsonl" if sys.platform != "win32" else "C:/temp/ctp_disconnect_diagnosis.jsonl",
    ]
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                os.remove(log_file)
        except:
            pass
    print("  [OK] 日志已清理")

    # 4. 启动 sim-trading
    print()
    print("[4/5] 启动 sim-trading（带心跳报告，00:00-08:00 静默）...")
    sim_log = log_files[0]
    sim_working_dir = os.path.join(jbt_dir, "services/sim-trading")
    sim_command = [
        os.path.join(sim_working_dir, ".venv", "Scripts", "python.exe"),
        "-m", "uvicorn", "src.main:app",
        "--host", "0.0.0.0", "--port", "8101",
    ]
    sim_pid = start_background_process(log_path=sim_log, working_dir=sim_working_dir, command=sim_command)
    if sim_pid:
        print(f"  进程 PID: {sim_pid}")
    else:
        print("  [ERROR] 启动失败")

    # 5. 启动 CTP 断联诊断
    print()
    print("[5/5] 启动 CTP 断联诊断...")
    ctp_log = log_files[0].replace("sim-trading.log", "ctp_diagnosis.log")
    ctp_pid = start_background_process("scripts/diagnose_ctp_disconnect.py", ctp_log, working_dir=jbt_dir)
    if ctp_pid:
        print(f"  进程 PID: {ctp_pid}")
        print(f"  诊断日志: {log_files[2]}")
    else:
        print("  [ERROR] 启动失败")

    print()
    order_trace_log = log_files[1]
    print(f"  [INFO] 订单追踪已集成到 sim-trading 主服务，输出: {order_trace_log}")

    # 等待启动
    print()
    print("等待启动（15秒）...")
    time.sleep(15)

    # 显示启动日志
    print()
    print("=" * 60)
    print("Sim-Trading 启动日志（最近 20 行）")
    print("=" * 60)
    try:
        with open(sim_log, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())
    except Exception as e:
        print(f"  无法读取日志: {e}")

    # 计算下一个心跳时间
    print()
    print("=" * 60)
    print("部署完成！")
    print("=" * 60)
    print()
    print("📊 心跳健康报告:")
    current_hour = datetime.now().hour
    if 0 <= current_hour < 8:
        print("  下一次: 今天 08:00（当前静默时段）")
    elif current_hour >= 22:
        print("  下一次: 明天 08:00")
    else:
        next_hour = ((current_hour // 2) * 2 + 2)
        print(f"  下一次: 今天 {next_hour:02d}:00")
    print("  静默时段: 00:00-08:00")
    print()
    print("🔍 订单追踪:")
    print("  状态: 已集成到 sim-trading 主服务")
    print(f"  日志: {order_trace_log}")
    print(f"  分析: python scripts/analyze_order_trace.py")
    print()
    print("🔧 CTP 断联诊断:")
    print(f"  状态: 运行中（PID {ctp_pid}）" if ctp_pid else "  状态: 启动失败")
    print(f"  日志: {ctp_log}")
    print(f"  分析: python scripts/analyze_ctp_disconnect.py")
    print()

if __name__ == "__main__":
    main()
