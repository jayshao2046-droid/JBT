#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程守护脚本 - 确保 sim-trading 相关进程永久在线
每 60 秒检查一次，如果进程挂了自动重启
"""
import os
import sys
import time
import subprocess
import socket
import psutil
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 进程配置
PROCESSES = [
    {
        "name": "sim-trading",
        "command": [".venv/Scripts/python.exe", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8101"],
        "working_dir": "services/sim-trading",
        "log": "C:/temp/sim-trading.log" if sys.platform == "win32" else "/tmp/sim-trading.log",
        "check_port": 8101,
        "check_keyword": "src.main:app",
    },
    {
        "name": "ctp-diagnosis",
        "script": "scripts/diagnose_ctp_disconnect.py",
        "log": "C:/temp/ctp_diagnosis.log" if sys.platform == "win32" else "/tmp/ctp_diagnosis.log",
        "check_keyword": "diagnose_ctp_disconnect.py",
    },
]

CHECK_INTERVAL = 60  # 检查间隔（秒）


def is_port_listening(port):
    """检查本机端口是否已监听。"""
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=1):
            return True
    except OSError:
        return False

def is_process_running(keyword):
    """检查进程是否运行"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any(keyword in arg for arg in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def start_process(script_path=None, log_path=None, working_dir=None, command=None):
    """启动进程"""
    try:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        cwd = working_dir
        if cwd and not os.path.isabs(cwd):
            cwd = os.path.abspath(cwd)

        if sys.platform == "win32":
            if command is not None:
                launch_cmd = command
            else:
                launch_cmd = ["pythonw.exe", script_path]

            # Windows: sim-trading 使用 .venv + uvicorn，其余脚本维持后台 pythonw
            proc = subprocess.Popen(
                launch_cmd,
                stdout=open(log_path, "w"),
                stderr=subprocess.STDOUT,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            launch_cmd = command if command is not None else ["python3", script_path]
            proc = subprocess.Popen(
                launch_cmd,
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
    print("Sim-Trading 进程守护")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"检查间隔: {CHECK_INTERVAL} 秒")
    print(f"守护进程: {len(PROCESSES)} 个")
    print()

    # 切换到 JBT 目录
    jbt_dir = os.path.expanduser("~/JBT")
    if not os.path.exists(jbt_dir):
        print(f"[ERROR] JBT 目录不存在: {jbt_dir}")
        sys.exit(1)
    os.chdir(jbt_dir)

    restart_count = {p["name"]: 0 for p in PROCESSES}

    while True:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{timestamp}] 检查进程状态...")

            for proc_config in PROCESSES:
                name = proc_config["name"]
                keyword = proc_config.get("check_keyword", "")
                script = proc_config.get("script")
                command = proc_config.get("command")
                log = proc_config["log"]
                working_dir = proc_config.get("working_dir")
                check_port = proc_config.get("check_port")

                if check_port is not None:
                    running = is_port_listening(check_port)
                else:
                    running = is_process_running(keyword)

                if running:
                    print(f"  [OK] {name} 运行中")
                else:
                    print(f"  [WARN] {name} 未运行，正在重启...")
                    pid = start_process(script, log, working_dir=working_dir, command=command)
                    if pid:
                        restart_count[name] += 1
                        print(f"  [OK] {name} 已重启 (PID: {pid}, 累计重启: {restart_count[name]} 次)")
                    else:
                        print(f"  [ERROR] {name} 重启失败")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n[INFO] 用户中断，退出守护")
            break
        except Exception as e:
            print(f"\n[ERROR] 守护异常: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
