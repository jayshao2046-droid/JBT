#!/usr/bin/env python3
"""
TASK-0120 飞书通知实发测试脚本

测试目标：
1. 研究员报告 → 资讯群
2. 策略信号 → 交易群
3. 系统告警 → 报警群
"""

import asyncio
import httpx
from datetime import datetime

# 飞书 webhook 配置
FEISHU_WEBHOOKS = {
    "alert": "https://open.feishu.cn/open-apis/bot/v2/hook/622ca546-d6cc-48a2-bfdf-39e0c65303af",
    "trading": "https://open.feishu.cn/open-apis/bot/v2/hook/bfe0f163-1f1b-4cd0-8e54-7a440b9884a8",
    "news": "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da",
}


async def send_feishu_card(webhook_url: str, card: dict) -> bool:
    """发送飞书卡片"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=card, timeout=10.0)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0:
                    return True
                else:
                    print(f"   飞书返回错误: code={result.get('code')}, msg={result.get('msg')}")
                    return False
            else:
                print(f"   HTTP 错误: status={resp.status_code}, body={resp.text}")
                return False
    except Exception as e:
        print(f"   发送异常: {e}")
        return False


async def test_researcher_notification():
    """测试 1: 研究员报告通知 → 资讯群"""
    print("\n" + "="*60)
    print("测试 1: 研究员报告通知 → 资讯群")
    print("="*60)

    card = {
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
                        "content": "**期货研判**\n🟢 偏多: rb +1.2%\n⚪ 震荡: cu, ru\n\n*JBT 数据研究员 TASK-0120 测试*"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**要闻摘要**\n• 上期所: 螺纹钢库存下降\n• 文华财经: 铜价震荡整理"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**综合研判**\n市场整体偏强，螺纹钢受库存下降支撑"
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
                            "content": f"JBT 数据研究员 | 14:00 | 采集5源12篇 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    success = await send_feishu_card(FEISHU_WEBHOOKS["news"], card)
    if success:
        print("✅ 研究员报告发送成功")
        print(f"   目标: 资讯群 ({FEISHU_WEBHOOKS['news'][-20:]}...)")
    else:
        print("❌ 研究员报告发送失败")
    return success


async def test_strategy_notification():
    """测试 2: 策略信号通知 → 交易群"""
    print("\n" + "="*60)
    print("测试 2: 策略信号通知 → 交易群")
    print("="*60)

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 策略信号 - TASK-0120 测试"
                },
                "template": "grey"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**信号ID**: SIG-TEST-20260415-140001\n**策略**: 趋势跟踪\n**品种**: rb2505\n**操作**: 开多\n**价格**: 3850"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**置信度**: 0.85\n**理由**: 突破关键阻力位，成交量放大"
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"JBT Decision | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }

    success = await send_feishu_card(FEISHU_WEBHOOKS["trading"], card)
    if success:
        print("✅ 策略信号发送成功")
        print(f"   目标: 交易群 ({FEISHU_WEBHOOKS['trading'][-20:]}...)")
    else:
        print("❌ 策略信号发送失败")
    return success


async def test_alert_notification():
    """测试 3: 系统告警通知 → 报警群"""
    print("\n" + "="*60)
    print("测试 3: 系统告警通知 → 报警群")
    print("="*60)

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

    success = await send_feishu_card(FEISHU_WEBHOOKS["alert"], card)
    if success:
        print("✅ 系统告警发送成功")
        print(f"   目标: 报警群 ({FEISHU_WEBHOOKS['alert'][-20:]}...)")
    else:
        print("❌ 系统告警发送失败")
    return success


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("TASK-0120 飞书通知实发测试")
    print("="*60)
    print("\n配置信息:")
    print(f"  报警群: {FEISHU_WEBHOOKS['alert'][-20:]}...")
    print(f"  交易群: {FEISHU_WEBHOOKS['trading'][-20:]}...")
    print(f"  资讯群: {FEISHU_WEBHOOKS['news'][-20:]}...")

    results = []

    # 测试 1: 研究员报告
    results.append(("研究员报告 → 资讯群", await test_researcher_notification()))
    await asyncio.sleep(2)

    # 测试 2: 策略信号
    results.append(("策略信号 → 交易群", await test_strategy_notification()))
    await asyncio.sleep(2)

    # 测试 3: 系统告警
    results.append(("系统告警 → 报警群", await test_alert_notification()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status}  {name}")

    total = len(results)
    passed = sum(1 for _, s in results if s)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有飞书通知测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查飞书配置")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
