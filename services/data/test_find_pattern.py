#!/usr/bin/env python3
"""对比成功和失败的消息，找出规律"""

import requests
import json

# 资讯群 webhook
NEWS_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"

def send_card(card_data, description):
    """发送卡片并返回结果"""
    response = requests.post(NEWS_WEBHOOK, json=card_data, timeout=10)
    result = response.json()
    status = "✅" if result.get("code") == 0 else "❌"
    print(f"{status} {description}")
    print(f"   code={result.get('code')}, msg={result.get('msg')}")
    return result.get("code") == 0


print("="*60)
print("对比测试：找出成功的规律")
print("="*60)
print()

# 成功的 SLA 样式（简化版）
sla_simple = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "测试标题"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "测试内容"}}
        ]
    }
}

# 测试 1: 最简 SLA
send_card(sla_simple, "最简 SLA 结构")

# 测试 2: 添加 note
sla_with_note = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "测试标题"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "测试内容"}},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "备注"}]}
        ]
    }
}

send_card(sla_with_note, "SLA + note")

# 测试 3: 添加 hr
sla_with_hr = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "测试标题"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "测试内容"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "备注"}]}
        ]
    }
}

send_card(sla_with_hr, "SLA + hr + note")

# 测试 4: 使用研究员的标题
researcher_title = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "📈 [JBT 数据研究员-14:00] 2026-04-15"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "测试内容"}}
        ]
    }
}

send_card(researcher_title, "研究员标题格式")

# 测试 5: 使用研究员的完整内容
researcher_full = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "📈 [JBT 数据研究员-14:00] 2026-04-15"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "期货研判\n偏多: rb +1.2%"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "JBT 数据研究员 | 14:00 | Alienware"}]}
        ]
    }
}

send_card(researcher_full, "研究员完整结构")

# 测试 6: 改用 grey 模板
researcher_grey = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "📈 [JBT 数据研究员-14:00] 2026-04-15"},
            "template": "grey"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "期货研判\n偏多: rb +1.2%"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "JBT 数据研究员 | 14:00 | Alienware"}]}
        ]
    }
}

send_card(researcher_grey, "研究员结构 + grey 模板")

# 测试 7: 改用 orange 模板
researcher_orange = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "📈 [JBT 数据研究员-14:00] 2026-04-15"},
            "template": "orange"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": "期货研判\n偏多: rb +1.2%"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "JBT 数据研究员 | 14:00 | Alienware"}]}
        ]
    }
}

send_card(researcher_orange, "研究员结构 + orange 模板")
