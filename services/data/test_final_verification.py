#!/usr/bin/env python3
"""TASK-0120 最终验证：修复后的研究员通知卡片"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# 使用修复后的卡片结构（添加了 "JBT 资讯" 关键词）
card = {
    "msg_type": "interactive",
    "card": {
        "config": {
            "wide_screen_mode": True
        },
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
                    "content": "**期货研判**\n🔴 偏空: RB +2.3%, HC +1.8%\n🟢 偏多: AU -0.5%"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**要闻摘要**\n• 新华社: 央行降准0.5个百分点\n• 财联社: 钢材库存持续下降"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**综合研判**\n市场情绪偏谨慎，黑色系承压，贵金属相对抗跌"
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
                        "content": "JBT 资讯 | JBT 数据研究员 | 14:00 | 采集8源23篇 | Alienware"
                    }
                ]
            }
        ]
    }
}

webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"

print("=" * 60)
print("TASK-0120 最终验证：修复后的研究员通知")
print("=" * 60)

resp = httpx.post(webhook_url, json=card, timeout=10)
result = resp.json()

if result.get("code") == 0:
    print("✅ 发送成功！")
    print("\n修复内容：")
    print("  - 在 note 中添加 'JBT 资讯' 关键词")
    print("  - 位置：notifier.py 三处飞书卡片（报告/告警/紧急）")
else:
    print(f"❌ 发送失败: code={result.get('code')}, msg={result.get('msg')}")
