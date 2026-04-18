import httpx
from datetime import datetime, timedelta

# 测试 Mini data API
symbol = "KQ.m@SHFE.rb"
since = datetime.now() - timedelta(hours=24)
now = datetime.now()

url = "http://192.168.31.76:8105/api/v1/bars"
params = {
    "symbol": symbol,
    "start": since.isoformat(),
    "end": now.isoformat(),
    "limit": 10
}

print(f"请求 URL: {url}")
print(f"参数: {params}")
print()

resp = httpx.get(url, params=params, timeout=10)
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.text[:500]}")

if resp.status_code == 200:
    data = resp.json()
    bars = data.get("bars", [])
    print(f"\n返回 bars 数量: {len(bars)}")
    if bars:
        print(f"第一条数据: {bars[0]}")
