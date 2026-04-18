import httpx
from datetime import datetime, timedelta

# 测试多个时间范围
symbol = "KQ.m@SHFE.rb"
now = datetime.now()

test_cases = [
    ("过去1小时", timedelta(hours=1)),
    ("过去6小时", timedelta(hours=6)),
    ("过去24小时", timedelta(hours=24)),
    ("过去7天", timedelta(days=7)),
]

url = "http://192.168.31.76:8105/api/v1/bars"

for label, delta in test_cases:
    since = now - delta
    params = {
        "symbol": symbol,
        "start": since.isoformat(),
        "end": now.isoformat(),
        "limit": 1000
    }

    resp = httpx.get(url, params=params, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        count = data.get("count", 0)
        print(f"{label}: {count} 条数据")
    else:
        print(f"{label}: 请求失败 ({resp.status_code})")
