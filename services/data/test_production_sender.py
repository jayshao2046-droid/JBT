#!/usr/bin/env python3
"""使用生产环境的 ResearcherFeishuSender 发送测试"""

import asyncio
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from researcher.notify.feishu_sender import ResearcherFeishuSender


async def test_with_production_sender():
    """使用生产环境的发送器"""

    # 设置环境变量
    os.environ["RESEARCHER_FEISHU_WEBHOOK_URL"] = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"

    sender = ResearcherFeishuSender()

    # 测试 1: 使用 lark_md
    card_md = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📈 [JBT 数据研究员-14:00] 2026-04-15"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**期货研判**\n🟢 偏多: rb +1.2%"
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
                            "content": "JBT 数据研究员 | 14:00 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    # 测试 2: 使用 plain_text
    card_plain = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📈 [JBT 数据研究员-14:00] 2026-04-15"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content": "期货研判\n偏多: rb +1.2%"
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
                            "content": "JBT 数据研究员 | 14:00 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    print("="*60)
    print("使用 ResearcherFeishuSender 测试")
    print("="*60)
    print()

    print("测试 1: lark_md 格式")
    result1 = await sender.send_card(card_md)
    print(f"  结果: {'✅ 成功' if result1 else '❌ 失败'}")
    print()

    await asyncio.sleep(2)

    print("测试 2: plain_text 格式")
    result2 = await sender.send_card(card_plain)
    print(f"  结果: {'✅ 成功' if result2 else '❌ 失败'}")
    print()

    if result1 and result2:
        print("🎉 两种格式都成功！")
    elif result2 and not result1:
        print("⚠️  只有 plain_text 成功，lark_md 失败")
        print("   建议：将生产代码改为使用 plain_text")
    else:
        print("❌ 两种格式都失败")


if __name__ == "__main__":
    asyncio.run(test_with_production_sender())
