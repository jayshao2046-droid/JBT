"""
验证飞书通知是否真实发送成功
"""

import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def test_feishu_direct():
    """直接测试飞书 Webhook"""
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")

    if not webhook_url:
        print("❌ FEISHU_WEBHOOK_URL 未配置")
        return False

    print(f"飞书 Webhook: {webhook_url[:50]}...")

    # 构建测试消息
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": "orange",
                "title": {
                    "content": "🧪 TASK-0120 决策端通知测试",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": "这是一条测试通知，验证决策端通知体系是否正常工作。\n\n**测试时间**: 2026-04-15 22:38\n**测试模块**: L1/L2/L3 门控通知\n**状态**: ✅ 正常",
                        "tag": "lark_md"
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
                            "content": "JBT 决策服务 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    try:
        print("\n发送测试通知...")
        response = httpx.post(webhook_url, json=payload, timeout=10)

        print(f"HTTP 状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("\n✅ 飞书通知发送成功！")
                print("📱 请检查飞书交易群是否收到通知")
                return True
            else:
                print(f"\n❌ 飞书 API 返回错误: code={result.get('code')}, msg={result.get('msg')}")
                return False
        else:
            print(f"\n❌ HTTP 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ 发送失败: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("飞书通知直接测试")
    print("="*60)

    success = test_feishu_direct()

    if success:
        print("\n" + "="*60)
        print("✅ 测试通过！飞书通知功能正常")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ 测试失败！请检查配置")
        print("="*60)
