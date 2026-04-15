#!/usr/bin/env python3
"""简化版飞书测试 - 发送纯文本消息"""

import asyncio
import httpx

# 三个 webhook URL
WEBHOOKS = {
    "alert": "https://open.feishu.cn/open-apis/bot/v2/hook/622ca546-d6cc-48a2-bfdf-39e0c65303af",
    "trading": "https://open.feishu.cn/open-apis/bot/v2/hook/bfe0f163-1f1b-4cd0-8e54-7a440b9884a8",
    "news": "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da",
}


async def test_simple_text(name: str, webhook: str):
    """发送简单文本消息测试 webhook 连通性"""
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"TASK-0120 测试 - {name} - JBT 数据研究员"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook, json=payload, timeout=10.0)
            print(f"\n{name}:")
            print(f"  HTTP Status: {resp.status_code}")
            if resp.status_code == 200:
                result = resp.json()
                print(f"  Feishu Code: {result.get('code')}")
                print(f"  Feishu Msg: {result.get('msg')}")
                return result.get('code') == 0
            else:
                print(f"  Response: {resp.text[:200]}")
                return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


async def main():
    print("="*60)
    print("TASK-0120 飞书 Webhook 连通性测试（纯文本）")
    print("="*60)

    results = []
    for name, webhook in WEBHOOKS.items():
        success = await test_simple_text(name, webhook)
        results.append((name, success))
        await asyncio.sleep(1)

    print("\n" + "="*60)
    print("测试结果:")
    print("="*60)
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    passed = sum(1 for _, s in results if s)
    print(f"\n总计: {passed}/{len(results)} 通过")


if __name__ == "__main__":
    asyncio.run(main())
