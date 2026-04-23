#!/usr/bin/env python3
"""测试修复后的研究员数据流"""
import requests
import time

ALIENWARE = "http://192.168.31.187:8199"

print("=" * 60)
print("测试修复后的研究员数据流")
print("=" * 60)

# 1. 健康检查（带重试）
print("\n[1/3] 健康检查...")
for i in range(5):
    try:
        time.sleep(2)
        resp = requests.get(f"{ALIENWARE}/health", timeout=5)
        print(f"  状态: {resp.status_code}")
        print(f"  响应: {resp.json()}")
        break
    except Exception as e:
        if i < 4:
            print(f"  尝试 {i+1}/5 失败，等待服务启动...")
        else:
            print(f"  ❌ 服务未启动: {e}")
            exit(1)

# 2. 触发研究员分析
print("\n[2/3] 触发研究员分析...")
resp = requests.post(f"{ALIENWARE}/run", timeout=60)
print(f"  状态: {resp.status_code}")
result = resp.json()
print(f"  响应: {result}")

# 3. 检查队列状态
print("\n[3/3] 检查队列状态...")
time.sleep(2)
resp = requests.get(f"{ALIENWARE}/queue/status", timeout=5)
print(f"  状态: {resp.status_code}")
queue = resp.json()
print(f"  待读报告: {queue.get('pending_count', 0)}")

print("\n" + "=" * 60)
if result.get("success"):
    print("✅ 测试完成")
else:
    print("❌ 测试失败")
print("=" * 60)
