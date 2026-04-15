#!/usr/bin/env python3
"""验证关键词假设：BotQuant 资讯"""

import asyncio
import httpx
from datetime import datetime

NEWS_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"


async def test_with_keyword():
    """包含 'BotQuant 资讯' 关键词"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "测试消息"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "这是测试内容"
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
                            "content": f"BotQuant 资讯 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(NEWS_WEBHOOK, json=card, timeout=10.0)
            result = resp.json()
            print(f"✅ 包含 'BotQuant 资讯': code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"❌ 包含 'BotQuant 资讯': Error - {e}")
        return False


async def test_without_keyword():
    """不包含关键词"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "测试消息"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "这是测试内容"
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
                            "content": f"JBT Data Service | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(NEWS_WEBHOOK, json=card, timeout=10.0)
            result = resp.json()
            print(f"❌ 不包含关键词: code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"❌ 不包含关键词: Error - {e}")
        return False


async def test_keyword_in_title():
    """关键词在标题中"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "BotQuant 资讯 - 测试消息"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "这是测试内容"
                    }
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(NEWS_WEBHOOK, json=card, timeout=10.0)
            result = resp.json()
            print(f"✅ 关键词在标题: code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"❌ 关键词在标题: Error - {e}")
        return False


async def test_keyword_in_content():
    """关键词在正文中"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "测试消息"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "BotQuant 资讯 - 这是测试内容"
                    }
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(NEWS_WEBHOOK, json=card, timeout=10.0)
            result = resp.json()
            print(f"✅ 关键词在正文: code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"❌ 关键词在正文: Error - {e}")
        return False


async def main():
    print("="*60)
    print("验证关键词假设：BotQuant 资讯")
    print("="*60)
    print()

    await test_without_keyword()
    await asyncio.sleep(1)

    await test_with_keyword()
    await asyncio.sleep(1)

    await test_keyword_in_title()
    await asyncio.sleep(1)

    await test_keyword_in_content()


if __name__ == "__main__":
    asyncio.run(main())
