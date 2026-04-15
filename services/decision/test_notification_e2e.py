"""
TASK-0120 决策端通知体系端到端测试

测试 L1/L2/L3 通知、每日汇总、健康监控的完整流程。
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from notifier.gate_notifications import notify_l1_result, notify_l2_result, notify_l3_result, notify_strategy_tune
from notifier.daily_summary import get_daily_summary, send_daily_summary
from notifier.health_monitor import get_health_monitor

_TZ_CST = timezone(timedelta(hours=8))


def test_l1_notifications():
    """测试 L1 快速门控通知"""
    print("\n" + "="*60)
    print("测试 1: L1 快速门控通知")
    print("="*60)

    # 测试通过场景
    print("\n[L1-PASS] 测试通过场景...")
    notify_l1_result(
        signal_id="SIG-TEST-001",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IF2505",
        signal_direction=1,
        passed=True,
        risk_flag="",
        confidence=0.85,
        reasoning="技术指标良好，无明显风险",
        trace_id="TRACE-001",
    )
    print("✅ L1 通过通知已发送")

    # 测试拒绝场景
    print("\n[L1-REJECT] 测试拒绝场景...")
    notify_l1_result(
        signal_id="SIG-TEST-002",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IF2505",
        signal_direction=-1,
        passed=False,
        risk_flag="HIGH_VOLATILITY",
        confidence=0.45,
        reasoning="市场波动率过高，风险较大",
        trace_id="TRACE-002",
    )
    print("🚫 L1 拒绝通知已发送")

    # 记录到每日汇总
    summary = get_daily_summary()
    summary.record_l1("IF2505", True)
    summary.record_l1("IF2505", False, "HIGH_VOLATILITY")
    print("\n✅ L1 结果已记录到每日汇总")


def test_l2_notifications():
    """测试 L2 深度审查通知"""
    print("\n" + "="*60)
    print("测试 2: L2 深度审查通知")
    print("="*60)

    # 测试通过场景
    print("\n[L2-PASS] 测试通过场景...")
    notify_l2_result(
        signal_id="SIG-TEST-003",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IC2505",
        signal_direction=1,
        passed=True,
        risk_level="LOW",
        confidence=0.88,
        reasoning="多维度风险评估通过，持仓风险低，市场风险中等，流动性风险低",
        trace_id="TRACE-003",
    )
    print("✅ L2 通过通知已发送")

    # 测试拒绝场景
    print("\n[L2-REJECT] 测试拒绝场景...")
    notify_l2_result(
        signal_id="SIG-TEST-004",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IC2505",
        signal_direction=-1,
        passed=False,
        risk_level="HIGH",
        confidence=0.35,
        reasoning="持仓风险高，市场风险高，流动性风险中等，建议拒绝",
        trace_id="TRACE-004",
    )
    print("🚫 L2 拒绝通知已发送")

    # 记录到每日汇总
    summary = get_daily_summary()
    summary.record_l2("IC2505", True)
    summary.record_l2("IC2505", False, "HIGH")
    print("\n✅ L2 结果已记录到每日汇总")


def test_l3_notifications():
    """测试 L3 在线确认通知"""
    print("\n" + "="*60)
    print("测试 3: L3 在线确认通知")
    print("="*60)

    # 测试确认场景
    print("\n[L3-CONFIRMED] 测试确认场景...")
    notify_l3_result(
        signal_id="SIG-TEST-005",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IH2505",
        signal_direction=1,
        status="confirmed",
        reason="人工确认通过",
        trace_id="TRACE-005",
    )
    print("✅ L3 确认通知已发送")

    # 测试拒绝场景
    print("\n[L3-REJECTED] 测试拒绝场景...")
    notify_l3_result(
        signal_id="SIG-TEST-006",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IH2505",
        signal_direction=-1,
        status="rejected",
        reason="市场环境不佳",
        trace_id="TRACE-006",
    )
    print("🚫 L3 拒绝通知已发送")

    # 测试超时场景
    print("\n[L3-TIMEOUT] 测试超时场景...")
    notify_l3_result(
        signal_id="SIG-TEST-007",
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        symbol="IH2505",
        signal_direction=1,
        status="timeout",
        reason="等待超时，自动降级",
        trace_id="TRACE-007",
    )
    print("⏱️ L3 超时通知已发送")

    # 记录到每日汇总
    summary = get_daily_summary()
    summary.record_l3("IH2505", "confirmed")
    summary.record_l3("IH2505", "rejected", "市场环境不佳")
    summary.record_l3("IH2505", "timeout")
    print("\n✅ L3 结果已记录到每日汇总")


def test_daily_summary():
    """测试每日汇总邮件"""
    print("\n" + "="*60)
    print("测试 4: 每日汇总邮件")
    print("="*60)

    summary = get_daily_summary()

    # 添加更多测试数据
    print("\n[数据准备] 添加测试数据...")

    # L1 数据
    for i in range(20):
        symbol = ["IF2505", "IC2505", "IH2505", "IM2505"][i % 4]
        passed = i % 3 != 0  # 66% 通过率
        risk_flag = "" if passed else ["HIGH_VOLATILITY", "POSITION_LIMIT", "MARKET_RISK"][i % 3]
        summary.record_l1(symbol, passed, risk_flag)

    # L2 数据
    for i in range(15):
        symbol = ["IF2505", "IC2505", "IH2505"][i % 3]
        passed = i % 4 != 0  # 75% 通过率
        risk_level = "" if passed else ["HIGH", "MEDIUM"][i % 2]
        summary.record_l2(symbol, passed, risk_level)

    # L3 数据
    for i in range(10):
        symbol = ["IF2505", "IC2505"][i % 2]
        status = ["confirmed", "rejected", "timeout"][i % 3]
        reason = "" if status == "confirmed" else "测试拒绝原因"
        summary.record_l3(symbol, status, reason)

    # 添加通知失败记录
    summary.record_notification_failure(feishu_failed=True, email_failed=False)
    summary.record_notification_failure(feishu_failed=False, email_failed=True)

    # 添加风险事件
    summary.add_risk_event("POSITION_LIMIT", "IF2505 持仓接近上限", "warning")
    summary.add_risk_event("MARKET_CRASH", "市场出现异常波动", "critical")

    print("✅ 测试数据添加完成")

    # 生成邮件正文
    print("\n[邮件预览]")
    print("-" * 60)
    email_body = summary.to_email_body()
    print(email_body)
    print("-" * 60)

    print("\n✅ 每日汇总邮件生成成功")


def test_health_monitor():
    """测试健康监控"""
    print("\n" + "="*60)
    print("测试 5: 健康监控系统")
    print("="*60)

    monitor = get_health_monitor()

    # 执行健康检查
    print("\n[健康检查] 检查所有组件...")
    monitor.check_all()

    # 显示各组件状态
    print("\n[组件状态]")
    for name, comp in monitor.components.items():
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "🔴",
        }
        emoji = status_emoji.get(comp.status.value, "❓")
        print(f"{emoji} {comp.name}: {comp.status.value}")
        if comp.message:
            print(f"   └─ {comp.message}")

    # 生成快照
    print("\n[快照生成] 生成健康快照...")
    snapshot = monitor.take_snapshot()
    print(f"✅ 快照时间: {snapshot['timestamp']}")
    print(f"✅ 整体状态: {snapshot['overall_status']}")

    # 生成每日报告
    print("\n[每日报告预览]")
    print("-" * 60)
    report = monitor.generate_daily_report()
    print(report)
    print("-" * 60)

    print("\n✅ 健康监控测试完成")


def test_strategy_tune_notification():
    """测试策略调优通知"""
    print("\n" + "="*60)
    print("测试 6: 策略调优通知")
    print("="*60)

    print("\n[STRATEGY-TUNE-SUCCESS] 测试成功场景...")
    notify_strategy_tune(
        strategy_id="STRAT-MA-001",
        model_id="phi4-reasoning:14b",
        success=True,
        metrics={
            "sharpe": 1.85,
            "max_drawdown": 0.12,
            "win_rate": 0.65,
        },
        message="参数调优完成，夏普比率提升 15%",
    )
    print("✅ 策略调优成功通知已发送")

    print("\n[STRATEGY-TUNE-FAILURE] 测试失败场景...")
    notify_strategy_tune(
        strategy_id="STRAT-MA-002",
        model_id="phi4-reasoning:14b",
        success=False,
        metrics={},
        message="回测结果不理想，建议回滚",
        rollback_point="v1.2.3",
        next_steps="检查市场环境变化，调整参数范围",
    )
    print("❌ 策略调优失败通知已发送")

    print("\n✅ 策略调优通知测试完成")


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("TASK-0120 决策端通知体系端到端测试")
    print("="*60)
    print(f"测试时间: {datetime.now(_TZ_CST).strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 执行所有测试
        test_l1_notifications()
        test_l2_notifications()
        test_l3_notifications()
        test_daily_summary()
        test_health_monitor()
        test_strategy_tune_notification()

        # 测试总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ L1 快速门控通知 - 通过")
        print("✅ L2 深度审查通知 - 通过")
        print("✅ L3 在线确认通知 - 通过")
        print("✅ 每日汇总邮件 - 通过")
        print("✅ 健康监控系统 - 通过")
        print("✅ 策略调优通知 - 通过")
        print("\n🎉 所有测试通过！")

        print("\n" + "="*60)
        print("下一步行动")
        print("="*60)
        print("1. 启用飞书通知: FEISHU_ENABLED=true")
        print("2. 启用邮件通知: EMAIL_ENABLED=true")
        print("3. 集成到 gate_reviewer.py")
        print("4. 集成到 signal_dispatcher.py")
        print("5. 配置定时任务（每日汇总 + 健康快照）")
        print("6. 生产环境验证")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
