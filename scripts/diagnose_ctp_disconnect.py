#!/usr/bin/env python3
"""
CTP 断联深度诊断脚本
用法：在 Alienware 上运行，持续监控 CTP 连接状态并记录断联详情
"""
import sys
import os
import time
import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path

# 添加 sim-trading 到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../services/sim-trading"))

SIMNOW_MD_HOST = "180.168.146.187"
SIMNOW_MD_PORT = 10131
SIMNOW_TD_HOST = "180.168.146.187"
SIMNOW_TD_PORT = 10130

LOG_FILE = "/tmp/ctp_disconnect_diagnosis.jsonl"

def check_network_connectivity(host, port, timeout=5):
    """检查网络连通性"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def get_network_stats():
    """获取网络统计信息"""
    try:
        # TCP 连接数
        result = subprocess.run(
            ["netstat", "-an", "|", "grep", SIMNOW_MD_HOST],
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        tcp_connections = result.stdout.strip().split("\n") if result.stdout else []

        # Ping 延迟
        ping_result = subprocess.run(
            ["ping", "-c", "3", "-W", "2", SIMNOW_MD_HOST],
            capture_output=True,
            text=True,
            timeout=10
        )
        ping_output = ping_result.stdout

        # 提取平均延迟
        avg_latency = None
        if "avg" in ping_output:
            try:
                # macOS: round-trip min/avg/max/stddev = 1.234/2.345/3.456/0.123 ms
                parts = ping_output.split("=")[-1].strip().split("/")
                avg_latency = float(parts[1])
            except:
                pass

        return {
            "tcp_connections": len([c for c in tcp_connections if c.strip()]),
            "ping_avg_ms": avg_latency,
            "ping_success": ping_result.returncode == 0,
        }
    except Exception as e:
        return {"error": str(e)}

def get_system_resources():
    """获取系统资源使用情况"""
    try:
        # CPU 和内存
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # 查找 sim-trading 进程
        sim_lines = [line for line in result.stdout.split("\n") if "sim-trading" in line or "main.py" in line]

        cpu_usage = 0.0
        mem_usage = 0.0
        if sim_lines:
            for line in sim_lines:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        cpu_usage += float(parts[2])
                        mem_usage += float(parts[3])
                    except:
                        pass

        return {
            "cpu_percent": cpu_usage,
            "mem_percent": mem_usage,
        }
    except Exception as e:
        return {"error": str(e)}

def diagnose_disconnect(gateway_status, prev_status):
    """诊断断联原因"""
    reasons = []

    # 检查网络连通性
    md_reachable = check_network_connectivity(SIMNOW_MD_HOST, SIMNOW_MD_PORT)
    td_reachable = check_network_connectivity(SIMNOW_MD_HOST, SIMNOW_TD_PORT)

    if not md_reachable:
        reasons.append("行情前置网络不可达")
    if not td_reachable:
        reasons.append("交易前置网络不可达")

    # 检查是否是状态变化
    if prev_status:
        if prev_status.get("md_connected") and not gateway_status.get("md_connected"):
            reasons.append("行情通道从连接变为断开")
        if prev_status.get("td_connected") and not gateway_status.get("td_connected"):
            reasons.append("交易通道从连接变为断开")

    # 检查断联原因代码
    md_reason = gateway_status.get("last_md_disconnect_reason")
    td_reason = gateway_status.get("last_td_disconnect_reason")

    if md_reason is not None:
        reasons.append(f"行情断联原因码: {md_reason} ({_explain_disconnect_reason(md_reason)})")
    if td_reason is not None:
        reasons.append(f"交易断联原因码: {td_reason} ({_explain_disconnect_reason(td_reason)})")

    return reasons

def _explain_disconnect_reason(reason_code):
    """解释 CTP 断联原因码"""
    reasons = {
        0x1001: "网络读失败",
        0x1002: "网络写失败",
        0x2001: "接收心跳超时",
        0x2002: "发送心跳失败",
        0x2003: "收到错误报文",
    }
    return reasons.get(reason_code, f"未知原因 0x{reason_code:04x}")

def monitor_ctp_connection():
    """持续监控 CTP 连接"""
    print(f"[MONITOR] CTP 断联诊断启动")
    print(f"[MONITOR] 日志文件: {LOG_FILE}")
    print(f"[MONITOR] 监控目标: {SIMNOW_MD_HOST}:{SIMNOW_MD_PORT} (MD) / {SIMNOW_TD_HOST}:{SIMNOW_TD_PORT} (TD)")
    print(f"{'='*80}\n")

    # 导入 gateway
    try:
        from src.api.router import _get_gateway
    except ImportError:
        print("❌ 无法导入 gateway，请确保在 sim-trading 环境中运行")
        return

    prev_status = None
    disconnect_count = 0

    while True:
        try:
            timestamp = datetime.now().isoformat()

            # 获取 gateway 状态
            gw = _get_gateway()
            if gw is None:
                print(f"[{timestamp}] ⚠️  Gateway 未初始化")
                time.sleep(10)
                continue

            status = gw.status
            md_connected = status.get("md_connected", False)
            td_connected = status.get("td_connected", False)

            # 检测断联
            is_disconnected = not md_connected or not td_connected

            if is_disconnected:
                disconnect_count += 1

                # 收集诊断信息
                network_stats = get_network_stats()
                system_resources = get_system_resources()
                reasons = diagnose_disconnect(status, prev_status)

                # 构造诊断记录
                diagnosis = {
                    "timestamp": timestamp,
                    "disconnect_count": disconnect_count,
                    "status": {
                        "md_connected": md_connected,
                        "td_connected": td_connected,
                        "md_status": status.get("md"),
                        "td_status": status.get("td"),
                    },
                    "disconnect_reasons": reasons,
                    "network": {
                        "md_reachable": check_network_connectivity(SIMNOW_MD_HOST, SIMNOW_MD_PORT),
                        "td_reachable": check_network_connectivity(SIMNOW_MD_HOST, SIMNOW_TD_PORT),
                        **network_stats,
                    },
                    "system": system_resources,
                    "last_md_disconnect_time": status.get("last_md_disconnect_time"),
                    "last_td_disconnect_time": status.get("last_td_disconnect_time"),
                }

                # 写入日志
                with open(LOG_FILE, "a") as f:
                    f.write(json.dumps(diagnosis, ensure_ascii=False) + "\n")

                # 打印到控制台
                print(f"\n{'='*80}")
                print(f"[DISCONNECT #{disconnect_count}] {timestamp}")
                print(f"{'='*80}")
                print(f"状态: MD={md_connected} ({status.get('md')}) | TD={td_connected} ({status.get('td')})")
                print(f"\n诊断原因:")
                for reason in reasons:
                    print(f"  - {reason}")
                print(f"\n网络状态:")
                print(f"  MD 可达: {diagnosis['network']['md_reachable']}")
                print(f"  TD 可达: {diagnosis['network']['td_reachable']}")
                if diagnosis['network'].get('ping_avg_ms'):
                    print(f"  Ping 延迟: {diagnosis['network']['ping_avg_ms']:.2f} ms")
                print(f"  TCP 连接数: {diagnosis['network'].get('tcp_connections', 'N/A')}")
                print(f"\n系统资源:")
                print(f"  CPU: {diagnosis['system'].get('cpu_percent', 'N/A')}%")
                print(f"  内存: {diagnosis['system'].get('mem_percent', 'N/A')}%")
                print(f"{'='*80}\n")
            else:
                # 连接正常，每 30 秒打印一次心跳
                if disconnect_count > 0 or int(time.time()) % 30 == 0:
                    print(f"[{timestamp}] ✅ CTP 连接正常 (MD={md_connected}, TD={td_connected})")

            prev_status = status
            time.sleep(5)  # 每 5 秒检查一次

        except KeyboardInterrupt:
            print("\n[MONITOR] 用户中断，退出监控")
            break
        except Exception as e:
            print(f"[ERROR] 监控异常: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_ctp_connection()
