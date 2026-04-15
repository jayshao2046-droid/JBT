"""
TASK-0120 决策端通知体系 - 飞书和邮件实际发送测试

测试通知是否能真实发送到飞书和邮箱。
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from notifier.gate_notifications import notify_l1_result, notify_l2_result, notify_l3_result, notify_strategy_tune
from notifier.daily_summary import get_daily_summary, send_daily_summary
from notifier.health_monitor import get_health_monitor

_TZ_CST = timezone(timedelta(hours=8))


def test_feishu_and_email():
    """测试飞书和邮件实际发送"""
    print("\n" + "="*60)
    print("TASK-0120 飞书和邮件实际发送测试")
    print("="*60)
    print(f"测试时间: {datetime.now(_TZ_CST).strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查环境变量
    print("\n[环境检查]")
    feishu_enabled = os.getenv("FEISHU_ENABLED", "false").lower() == "true"
    email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL", "")

    print(f"飞书启用: {feishu_enabled}")
    print(f"邮件启用: {email_enabled}")
    print(f"飞书 Webhook: {'已配置' if feishu_webhook else '未配置'}")

    if not feishu_enabled and not email_enabled:
        print("\n⚠️ 警告: 飞书和邮件均未启用，通知将不会实际发送")
        print("提示: 设置 FEISHU_ENABLED=true 或 EMAIL_ENABLED=true")

    # 测试 1: L1 拒绝通知（P1 级别）
    print("\n" + "="*60)
    print("测试 1: L1 拒绝通知（P1 级别）")
    print("="*60)

    notify_l1_result(
        signal_id="SIG-FEISHU-TEST-001",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IF2505",
        signal_direction=-1,
        passed=False,
        risk_flag="HIGH_VOLATILITY",
        confidence=0.35,
        reasoning="市场波动率过高，风险较大，建议拒绝",
        trace_id="TRACE-FEISHU-001",
    )
    print("✅ L1 拒绝通知已发送")
    print("📱 请检查飞书交易群是否收到通知")
    print("📧 请检查邮箱是否收到通知")

    # 测试 2: L2 通过通知（NOTIFY 级别）
    print("\n" + "="*60)
    print("测试 2: L2 通过通知（NOTIFY 级别）")
    print("="*60)

    notify_l2_result(
        signal_id="SIG-FEISHU-TEST-002",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IC2505",
        signal_direction=1,
        passed=True,
        risk_level="LOW",
        confidence=0.88,
        reasoning="多维度风险评估通过，持仓风险低，市场风险中等，流动性风险低",
        trace_id="TRACE-FEISHU-002",
    )
    print("✅ L2 通过通知已发送")
    print("📱 请检查飞书交易群是否收到通知")
    print("📧 请检查邮箱是否收到通知")

    # 测试 3: L3 超时通知（P2 级别）
    print("\n" + "="*60)
    print("测试 3: L3 超时通知（P2 级别）")
    print("="*60)

    notify_l3_result(
        signal_id="SIG-FEISHU-TEST-003",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IH2505",
        signal_direction=1,
        status="timeout",
        reason="等待超时，自动降级",
        trace_id="TRACE-FEISHU-003",
    )
    print("✅ L3 超时通知已发送")
    print("📱 请检查飞书交易群是否收到通知")
    print("📧 请检查邮箱是否收到通知")

    # 测试 4: 策略调优失败通知（P1 级别）
    print("\n" + "="*60)
    print("测试 4: 策略调优失败通知（P1 级别）")
    print("="*60)

    notify_strategy_tune(
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        success=False,
        metrics={},
        message="回测结果不理想，夏普比率下降 20%",
        rollback_point="v1.2.3",
        next_steps="检查市场环境变化，调整参数范围",
    )
    print("✅ 策略调优失败通知已发送")
    print("📱 请检查飞书交易群是否收到通知")
    print("📧 请检查邮箱是否收到通知")

    # 测试 5: 每日汇总邮件
    print("\n" + "="*60)
    print("测试 5: 每日汇总邮件")
    print("="*60)

    # 准备测试数据
    summary = get_daily_summary()

    # 添加测试数据
    for i in range(10):
        symbol = ["IF2505", "IC2505", "IH2505"][i % 3]
        summary.record_l1(symbol, i % 2 == 0, "HIGH_VOLATILITY" if i % 2 == 1 else "")
        summary.record_l2(symbol, i % 3 != 0, "HIGH" if i % 3 == 0 else "")
        summary.record_l3(symbol, ["confirmed", "rejected", "timeout"][i % 3], "测试原因")

    summary.add_risk_event("POSITION_LIMIT", "IF2505 持仓接近上限", "warning")
    summary.add_risk_event("MARKET_CRASH", "市场出现异常波动", "critical")

    send_daily_summary(summary)
    print("✅ 每日汇总邮件已发送")
    print("📧 请检查邮箱是否收到每日汇总邮件")

    # 测试 6: 健康快照通知（降级状态）
    print("\n" + "="*60)
    print("测试 6: 健康快照通知（降级状态）")
    print("="*60)

    monitor = get_health_monitor()
    snapshot = monitor.take_snapshot()
    monitor.send_snapshot_notification(snapshot)

    overall_status = snapshot["overall_status"]
    if overall_status == "healthy":
        print("ℹ️ 当前状态为健康，不会发送快照通知")
    else:
        print(f"✅ 健康快照通知已发送（状态: {overall_status}）")
        print("📱 请检查飞书交易群是否收到通知")
        print("📧 请检查邮箱是否收到通知")

    # 测试 7: 每日健康报告
    print("\n" + "="*60)
    print("测试 7: 每日健康报告")
    print("="*60)

    monitor.send_daily_report()
    print("✅ 每日健康报告已发送")
    print("📧 请检查邮箱是否收到每日健康报告")

    # 测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print("✅ 所有通知已发送")
    print("\n请检查以下内容:")
    print("1. 飞书交易群是否收到 5 条通知:")
    print("   - L1 拒绝通知（P1 橙色）")
    print("   - L2 通过通知（NOTIFY 青色）")
    print("   - L3 超时通知（P2 黄色）")
    print("   - 策略调优失败通知（P1 橙色）")
    if overall_status != "healthy":
        print(f"   - 健康快照通知（{overall_status}）")

    print("\n2. 邮箱是否收到 3 封邮件:")
    print("   - 每日门控汇总邮件")
    print("   - 每日健康报告邮件")
    print("   - 其他通知邮件（如果邮件通道启用）")

    print("\n" + "="*60)
    print("如果没有收到通知，请检查:")
    print("="*60)
    print("1. 环境变量配置:")
    print("   - FEISHU_ENABLED=true")
    print("   - EMAIL_ENABLED=true")
    print("   - FEISHU_WEBHOOK_URL=<飞书webhook地址>")
    print("   - EMAIL_SMTP_HOST=<SMTP服务器>")
    print("   - EMAIL_SMTP_PORT=<SMTP端口>")
    print("   - EMAIL_SMTP_USER=<发件人邮箱>")
    print("   - EMAIL_SMTP_PASSWORD=<邮箱密码>")
    print("   - EMAIL_FROM=<发件人邮箱>")
    print("   - EMAIL_TO=<收件人邮箱>")

    print("\n2. 网络连接:")
    print("   - 确保可以访问飞书 API")
    print("   - 确保可以访问 SMTP 服务器")

    print("\n3. 日志文件:")
    print("   - 查看 services/decision/logs/ 目录下的日志")
    print("   - 搜索 ERROR 或 WARNING 关键词")


if __name__ == "__main__":
    try:
        test_feishu_and_email()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
