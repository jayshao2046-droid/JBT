#!/usr/bin/env python3
"""复制成功消息的结构测试资讯群"""

import asyncio
import httpx
from datetime import datetime

NEWS_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"


async def test_alert_style():
    """测试告警样式（已知在报警群成功）"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚨 [P1] 数据采集延迟 - TASK-0120 测试"
                },
                "template": "orange"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**告警ID**: ALERT-TEST-20260415-140002\n**来源**: data-collector\n**详情**: Tushare 日线数据采集超时 (>30s)，可能影响策略决策"
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
            print(f"告警样式: code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"告警样式: Error - {e}")
        return False


async def test_sla_style():
    """测试 SLA 报告样式（已知在报警群成功）"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "JBT SLA 日报 — 🟢 全部正常"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content": "采集 SLA 日报\n活跃告警: 0\n状态: 全部正常"
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
                            "content": f"JBT 资讯 | JBT data-service | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
            print(f"SLA样式: code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"SLA样式: Error - {e}")
        return False


async def test_minimal():
    """最简消息"""
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "Test"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content": "TASK-0120"
                    }
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(NEWS_WEBHOOK, json=card, timeout=10.0)
            result = resp.json()
            print(f"最简消息: code={result.get('code')}, msg={result.get('msg')}")
            return result.get('code') == 0
    except Exception as e:
        print(f"最简消息: Error - {e}")
        return False


async def main():
    print("="*60)
    print("使用成功消息的结构测试资讯群")
    print("="*60)
    print()

    await test_minimal()
    await asyncio.sleep(1)

    await test_alert_style()
    await asyncio.sleep(1)

    await test_sla_style()


if __name__ == "__main__":
    asyncio.run(main())
