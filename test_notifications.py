#!/usr/bin/env python3
"""TASK-0120: 飞书+邮件实发验证脚本"""

import asyncio
import os
import sys
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/data/src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/decision/src'))

async def test_data_researcher_notifications():
    """测试数据研究员通知（飞书+邮件）"""
    print("\n" + "="*60)
    print("测试 1: 数据研究员通知系统")
    print("="*60)

    from researcher.notifier import ResearcherNotifier
    from researcher.notify.email_sender import ResearcherEmailSender
    from researcher.notify.feishu_sender import ResearcherFeishuSender
    from researcher.models import ResearchReport, SymbolResearch

    # 创建测试报告
    test_report = ResearchReport(
        report_id="TEST-20260415-12-00-001",
        date="2026-04-15",
        segment="12:00",
        generated_at=datetime.now(),
        model="qwen3:14b",
        futures_summary={
            "symbols_covered": 3,
            "market_overview": "测试：市场整体震荡，黑色系偏强",
            "symbols": {
                "rb": {"trend": "偏多", "confidence": 0.72, "key_factors": ["需求回暖"], "change_pct": 1.2},
                "cu": {"trend": "震荡", "confidence": 0.55, "key_factors": ["库存高位"], "change_pct": 0.3},
                "au": {"trend": "偏空", "confidence": 0.68, "key_factors": ["美元走强"], "change_pct": -0.8},
            }
        },
        stocks_summary={
            "symbols_covered": 0,
            "market_overview": "测试：股票市场暂无数据",
            "top_movers": []
        },
        crawler_stats={
            "sources_crawled": 5,
            "articles_processed": 12,
            "failed_sources": [],
            "news_items": [
                {"source": "金十数据", "title": "测试新闻1", "time": "12:00"},
                {"source": "东方财富", "title": "测试新闻2", "time": "12:05"},
            ]
        },
        previous_report_id=None,
        change_highlights=["rb 从震荡转偏多"]
    )

    # 测试飞书通知
    print("\n📱 测试飞书通知...")
    notifier = ResearcherNotifier()
    if notifier.feishu_webhook:
        try:
            await notifier.notify_report_done(test_report)
            print("✅ 飞书通知发送成功")
            print(f"   Webhook: {notifier.feishu_webhook[:50]}...")
        except Exception as e:
            print(f"❌ 飞书通知发送失败: {e}")
    else:
        print("⚠️  飞书 Webhook 未配置 (FEISHU_WEBHOOK_URL)")

    # 测试邮件通知
    print("\n📧 测试邮件通知...")
    email_sender = ResearcherEmailSender()
    if all([email_sender.smtp_host, email_sender.sender, email_sender.password, email_sender.recipients]):
        try:
            html_content = f"""
            <html>
            <body>
                <h2>JBT 数据研究员测试报告</h2>
                <p><strong>报告ID:</strong> {test_report.report_id}</p>
                <p><strong>时间:</strong> {test_report.date} {test_report.segment}</p>
                <p><strong>市场研判:</strong> {test_report.futures_summary['market_overview']}</p>
                <p><strong>采集统计:</strong> {test_report.crawler_stats['sources_crawled']}源 / {test_report.crawler_stats['articles_processed']}篇</p>
            </body>
            </html>
            """
            success = email_sender.send_html(
                subject=f"[JBT 测试] 数据研究员报告 {test_report.date}",
                html_content=html_content
            )
            if success:
                print("✅ 邮件发送成功")
                print(f"   收件人: {', '.join(email_sender.recipients)}")
            else:
                print("❌ 邮件发送失败")
        except Exception as e:
            print(f"❌ 邮件发送异常: {e}")
    else:
        print("⚠️  邮件配置不完整 (RESEARCHER_EMAIL_*)")

    return True


async def test_decision_notifications():
    """测试决策端通知（飞书+邮件）"""
    print("\n" + "="*60)
    print("测试 2: 决策端通知系统")
    print("="*60)

    from notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

    # 创建测试事件
    test_event = DecisionEvent(
        event_type="SIGNAL",
        notify_level=NotifyLevel.SIGNAL,
        event_code="TEST-SIGNAL-001",
        title="测试信号通知",
        body="这是一个测试信号通知，用于验证飞书和邮件通道是否正常工作。",
        strategy_id="TEST_STRATEGY",
        model_id="phi4-reasoning:14b",
        signal_id="SIG-TEST-001",
        trace_id="TRACE-TEST-001"
    )

    # 获取调度器
    dispatcher = get_dispatcher()

    print("\n📱 测试决策端飞书通知...")
    feishu_enabled = os.getenv("NOTIFY_FEISHU_ENABLED", "false").lower() == "true"
    if feishu_enabled:
        print(f"   飞书通道: 已启用")
    else:
        print(f"   飞书通道: 未启用 (NOTIFY_FEISHU_ENABLED=false)")

    print("\n📧 测试决策端邮件通知...")
    email_enabled = os.getenv("NOTIFY_EMAIL_ENABLED", "false").lower() == "true"
    if email_enabled:
        print(f"   邮件通道: 已启用")
    else:
        print(f"   邮件通道: 未启用 (NOTIFY_EMAIL_ENABLED=false)")

    # 发送测试通知
    print("\n🚀 发送测试通知...")
    try:
        dispatch_state = dispatcher.dispatch(test_event)
        print(f"✅ 通知调度完成")
        print(f"   调度状态: {dispatch_state.value}")

        # 获取运行时快照
        snapshot = dispatcher.runtime_snapshot(recent_limit=1)
        print(f"\n📊 通知统计:")
        for channel in snapshot['channels']:
            print(f"   {channel['channel']}: {channel['status']} (成功率: {channel['success_rate']}%)")
            if channel['last_error']:
                print(f"      最后错误: {channel['last_error']}")

    except Exception as e:
        print(f"❌ 通知调度失败: {e}")
        import traceback
        traceback.print_exc()

    return True


async def test_researcher_phi4_rating():
    """测试研究员 phi4 评级"""
    print("\n" + "="*60)
    print("测试 3: 研究员 phi4 评级系统")
    print("="*60)

    from researcher.report_reviewer import ReportReviewer
    from researcher.models import ResearchReport
    from researcher.daily_stats import DailyStatsTracker

    # 创建测试报告
    test_report = ResearchReport(
        report_id="TEST-20260415-14-00-001",
        date="2026-04-15",
        segment="14:00",
        generated_at=datetime.now(),
        model="qwen3:14b",
        futures_summary={
            "symbols_covered": 5,
            "market_overview": "测试：黑色系整体偏强，有色震荡，贵金属偏弱",
            "symbols": {
                "rb": {"trend": "偏多", "confidence": 0.75, "key_factors": ["需求回暖", "库存下降"]},
                "hc": {"trend": "偏多", "confidence": 0.70, "key_factors": ["跟随螺纹"]},
                "cu": {"trend": "震荡", "confidence": 0.55, "key_factors": ["库存高位"]},
                "al": {"trend": "震荡", "confidence": 0.52, "key_factors": ["供需平衡"]},
                "au": {"trend": "偏空", "confidence": 0.68, "key_factors": ["美元走强", "避险需求下降"]},
            }
        },
        stocks_summary={"symbols_covered": 0, "market_overview": "", "top_movers": []},
        crawler_stats={
            "sources_crawled": 8,
            "articles_processed": 25,
            "failed_sources": [],
            "news_items": []
        },
        previous_report_id=None,
        change_highlights=[]
    )

    # 创建评审器
    stats_tracker = DailyStatsTracker("runtime/researcher/logs")
    reviewer = ReportReviewer(
        feishu_webhook=os.getenv("FEISHU_WEBHOOK_URL", ""),
        stats_tracker=stats_tracker
    )

    print("\n🤖 执行 phi4 评级...")
    try:
        result = await reviewer.review_and_notify(test_report)
        print(f"✅ 评级完成")
        print(f"   置信度: {result['confidence']:.2f}")
        print(f"   评级: {result['level']}")
        print(f"   理由: {result['reason']}")
        print(f"   Fallback: {'是' if result['fallback'] else '否（phi4 语义评级）'}")

        # 检查 KPI 记录
        print(f"\n📝 检查 KPI 记录...")
        date = test_report.date
        stats_file = stats_tracker.stats_dir / f"daily_stats_{date}.json"
        if stats_file.exists():
            import json
            with open(stats_file, 'r') as f:
                stats = json.load(f)

            # 查找该报告的评级记录
            for report in stats.get('reports', []):
                if report.get('report_id') == test_report.report_id:
                    print(f"✅ KPI 记录已写入")
                    print(f"   report_id: {report.get('report_id')}")
                    print(f"   confidence: {report.get('decision_confidence')}")
                    print(f"   reviewed_at: {report.get('decision_reviewed_at')}")
                    break
            else:
                print(f"⚠️  未找到该报告的 KPI 记录")
        else:
            print(f"⚠️  统计文件不存在: {stats_file}")

    except Exception as e:
        print(f"❌ 评级失败: {e}")
        import traceback
        traceback.print_exc()

    return True


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("TASK-0120: 飞书+邮件实发验证")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查环境变量
    print("\n🔧 环境变量检查:")
    env_vars = {
        "FEISHU_WEBHOOK_URL": os.getenv("FEISHU_WEBHOOK_URL", ""),
        "RESEARCHER_EMAIL_SMTP_HOST": os.getenv("RESEARCHER_EMAIL_SMTP_HOST", ""),
        "RESEARCHER_EMAIL_SENDER": os.getenv("RESEARCHER_EMAIL_SENDER", ""),
        "RESEARCHER_EMAIL_RECIPIENTS": os.getenv("RESEARCHER_EMAIL_RECIPIENTS", ""),
        "NOTIFY_FEISHU_ENABLED": os.getenv("NOTIFY_FEISHU_ENABLED", "false"),
        "NOTIFY_EMAIL_ENABLED": os.getenv("NOTIFY_EMAIL_ENABLED", "false"),
        "PHI4_API_URL": os.getenv("PHI4_API_URL", "http://192.168.31.142:11434/api/generate"),
    }

    for key, value in env_vars.items():
        if value:
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ⚠️  {key}: 未配置")

    # 执行测试
    try:
        await test_data_researcher_notifications()
        await test_decision_notifications()
        await test_researcher_phi4_rating()

        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
