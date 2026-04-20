#!/usr/bin/env python3
"""简化测试：直接发送修复后的研究员通知卡片"""

import httpx
from datetime import datetime

WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"


def test_report_card():
    """测试研究员报告卡片"""
    now = datetime.now()
    hour = now.strftime('%H')
    minute = now.strftime('%M')
    date = now.strftime('%Y-%m-%d')

    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📈 [JBT 数据研究员-{hour}:00] {date}"
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
                            "content": f"JBT 资讯 | JBT 数据研究员 | {hour}:{minute} | 采集8源23篇 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    resp = httpx.post(WEBHOOK_URL, json=card, timeout=10)
    result = resp.json()
    return result.get("code") == 0, result


def test_alert_card():
    """测试告警卡片"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "⚠️ [JBT 数据研究员-报警] 执行失败"
                },
                "template": "orange"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**时段**: 14:00\n**错误**: 测试错误：数据源连接超时\n**时间**: {timestamp}"
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
                            "content": f"JBT 资讯 | JBT 数据研究员 | {timestamp} | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    resp = httpx.post(WEBHOOK_URL, json=card, timeout=10)
    result = resp.json()
    return result.get("code") == 0, result


def test_urgent_card():
    """测试紧急通知卡片"""
    detected_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚨 [JBT 数据研究员-紧急] 央行突然宣布降准0.5个百分点..."
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**标题**: 央行突然宣布降准0.5个百分点\n**来源**: 新华社\n**链接**: https://example.com/news/123\n**发现时间**: {detected_at}"
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
                            "content": "JBT 资讯 | JBT 数据研究员 | 突发紧急 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    resp = httpx.post(WEBHOOK_URL, json=card, timeout=10)
    result = resp.json()
    return result.get("code") == 0, result


if __name__ == "__main__":
    print("=" * 60)
    print("测试研究员飞书通知（三种卡片类型）")
    print("=" * 60)
    print()

    # 测试 1: 研究员报告
    print("1️⃣ 测试研究员报告卡片...")
    success, result = test_report_card()
    if success:
        print("   ✅ 报告卡片发送成功")
    else:
        print(f"   ❌ 报告卡片发送失败: {result}")
    print()

    # 测试 2: 告警
    print("2️⃣ 测试告警卡片...")
    success, result = test_alert_card()
    if success:
        print("   ✅ 告警卡片发送成功")
    else:
        print(f"   ❌ 告警卡片发送失败: {result}")
    print()

    # 测试 3: 紧急通知
    print("3️⃣ 测试紧急通知卡片...")
    success, result = test_urgent_card()
    if success:
        print("   ✅ 紧急通知卡片发送成功")
    else:
        print(f"   ❌ 紧急通知卡片发送失败: {result}")
    print()

    print("=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
