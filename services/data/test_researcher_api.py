#!/usr/bin/env python3
"""测试研究员飞书通知 API"""

import httpx

API_URL = "http://localhost:8001/api/researcher/test-notification"

print("=" * 60)
print("测试研究员飞书通知 API")
print("=" * 60)
print()

try:
    resp = httpx.post(API_URL, timeout=30.0)

    print(f"HTTP Status: {resp.status_code}")
    print()

    if resp.status_code == 200:
        result = resp.json()
        print("✅ API 调用成功")
        print(f"响应: {result}")
    else:
        print(f"❌ API 调用失败")
        print(f"响应: {resp.text}")

except httpx.ConnectError:
    print("❌ 连接失败：data-service 未启动")
    print("请先启动服务：cd services/data && python -m src.main")
except Exception as e:
    print(f"❌ 错误: {e}")
