#!/usr/bin/env python3
"""测试资讯群关键词"""

import asyncio
import httpx

NEWS_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"

# 尝试不同的关键词
KEYWORDS = [
    "JBT",
    "数据研究员",
    "JBT 数据研究员",
    "研究员",
    "报告",
    "期货",
    "市场",
    "资讯",
    "TASK-0120",
]


async def test_keyword(keyword: str):
    """测试单个关键词"""
    payload = {
        "msg_type": "text",
        "content": {
            "text": keyword
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(NEWS_WEBHOOK, json=payload, timeout=10.0)
            if resp.status_code == 200:
                result = resp.json()
                code = result.get('code')
                msg = result.get('msg')
                status = "✅" if code == 0 else "❌"
                print(f"{status} '{keyword}' -> code={code}, msg={msg}")
                return code == 0
            else:
                print(f"❌ '{keyword}' -> HTTP {resp.status_code}")
                return False
    except Exception as e:
        print(f"❌ '{keyword}' -> Error: {e}")
        return False


async def main():
    print("="*60)
    print("资讯群关键词测试")
    print("="*60)
    print()

    for keyword in KEYWORDS:
        await test_keyword(keyword)
        await asyncio.sleep(0.5)

    print()
    print("="*60)
    print("如果所有关键词都失败，说明 webhook 配置了我们不知道的关键词")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
