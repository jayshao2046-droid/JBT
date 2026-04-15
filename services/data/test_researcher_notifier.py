#!/usr/bin/env python3
"""直接测试 ResearcherNotifier 飞书通知"""

import asyncio
import sys
import os
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from researcher.notifier import ResearcherNotifier
from researcher.models import ResearchReport

# 设置环境变量
os.environ["FEISHU_WEBHOOK_URL"] = "https://open.feishu.cn/open-apis/bot/v2/hook/c51f4956-2a5c-4cad-86c2-17684da5e4da"


async def test_report_notification():
    """测试研究员报告通知"""
    print("=" * 60)
    print("测试研究员报告通知")
    print("=" * 60)
    print()

    # 构造测试报告
    report = ResearchReport(
        report_id="test-20260415-1400",
        segment="14:00",
        date="2026-04-15",
        generated_at=datetime.now(),
        futures_summary={
            "market_overview": "市场情绪偏谨慎，黑色系承压，贵金属相对抗跌",
            "symbols": {
                "RB": {"trend": "偏空", "change_pct": 2.3},
                "HC": {"trend": "偏空", "change_pct": 1.8},
                "AU": {"trend": "偏多", "change_pct": -0.5}
            }
        },
        crawler_stats={
            "sources_crawled": 8,
            "articles_processed": 23,
            "news_items": [
                {"source": "新华社", "title": "央行降准0.5个百分点"},
                {"source": "财联社", "title": "钢材库存持续下降"}
            ]
        },
        llm_summary={},
        decision_signals=[]
    )

    notifier = ResearcherNotifier()

    print("发送测试报告...")
    success = await notifier.notify_report_done(report)

    if success:
        print("✅ 报告通知发送成功")
    else:
        print("❌ 报告通知发送失败")

    return success


async def test_alert_notification():
    """测试告警通知"""
    print()
    print("=" * 60)
    print("测试告警通知")
    print("=" * 60)
    print()

    notifier = ResearcherNotifier()

    print("发送测试告警...")
    await notifier.notify_report_fail("14", "测试错误：数据源连接超时")
    print("✅ 告警通知已发送")


async def test_urgent_notification():
    """测试紧急通知"""
    print()
    print("=" * 60)
    print("测试紧急通知")
    print("=" * 60)
    print()

    notifier = ResearcherNotifier()

    print("发送测试紧急通知...")
    await notifier.notify_urgent(
        headline="央行突然宣布降准0.5个百分点",
        source="新华社",
        url="https://example.com/news/123"
    )
    print("✅ 紧急通知已发送")


async def main():
    # 测试三种通知类型
    await test_report_notification()
    await asyncio.sleep(2)

    await test_alert_notification()
    await asyncio.sleep(2)

    await test_urgent_notification()

    print()
    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
