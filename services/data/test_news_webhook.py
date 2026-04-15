#!/usr/bin/env python3
"""测试资讯群 webhook - 使用与交易群完全相同的卡片结构"""

import asyncio
import httpx
from datetime import datetime

NEWS_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"
TRADING_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/bfe0f163-1f1b-4cd0-8e54-7a440b9884a8"


async def send_card(webhook: str, name: str):
    """发送完全相同的卡片到不同 webhook"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📊 测试 - {name}"
                },
                "template": "grey"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**测试内容**: TASK-0120"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"JBT Test | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook, json=card, timeout=10.0)
            if resp.status_code == 200:
                result = resp.json()
                code = result.get('code')
                msg = result.get('msg')
                status = "✅" if code == 0 else "❌"
                print(f"{status} {name}: code={code}, msg={msg}")
                return code == 0
            else:
                print(f"❌ {name}: HTTP {resp.status_code}")
                return False
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False


async def main():
    print("="*60)
    print("使用相同卡片结构测试两个 webhook")
    print("="*60)
    print()

    await send_card(TRADING_WEBHOOK, "交易群")
    await asyncio.sleep(1)
    await send_card(NEWS_WEBHOOK, "资讯群")


if __name__ == "__main__":
    asyncio.run(main())
