#!/usr/bin/env python3
"""
TASK-0120 飞书通知测试 - 丰富 Mock 数据版本
发送所有优化后的通知，使用真实场景的 mock 数据
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from notifier.gate_notifications import GateNotifier
from notifier.health_monitor import HealthMonitor, ComponentHealth, HealthStatus
from notifier.daily_summary import DailyGateSummary

def test_l1_notifications():
    """测试 L1 快速门控通知 - 多种场景"""
    print("\n" + "=" * 60)
    print("测试 1: L1 快速门控通知（多种场景）")
    print("=" * 60)

    notifier = GateNotifier()

    # 场景 1: 高置信度通过
    print("\n[L1-PASS-1] 高置信度通过...")
    notifier.notify_l1_result(
        signal_id="SIG_20260415_225800_001",
        symbol="IF2505",
        direction="做多",
        passed=True,
        risk_flags=["LOW"],
        confidence=0.92,
        message="市场趋势强劲，技术指标多头排列，成交量放大确认突破有效"
    )

    # 场景 2: 中等置信度通过
    print("\n[L1-PASS-2] 中等置信度通过...")
    notifier.notify_l1_result(
        signal_id="SIG_20260415_225800_002",
        symbol="IC2505",
        direction="做空",
        passed=True,
        risk_flags=["MEDIUM"],
        confidence=0.78,
        message="短期超买信号，但需关注支撑位"
    )

    # 场景 3: 高波动拒绝
    print("\n[L1-REJECT-1] 高波动拒绝...")
    notifier.notify_l1_result(
        signal_id="SIG_20260415_225800_003",
        symbol="IH2505",
        direction="做多",
        passed=False,
        risk_flags=["HIGH_VOLATILITY", "POSITION_LIMIT"],
        confidence=0.65,
        message="当前波动率超过阈值 2.5 倍，且持仓已达上限 80%，建议观望"
    )

    # 场景 4: 流动性不足拒绝
    print("\n[L1-REJECT-2] 流动性不足拒绝...")
    notifier.notify_l1_result(
        signal_id="SIG_20260415_225800_004",
        symbol="IM2505",
        direction="做空",
        passed=False,
        risk_flags=["LOW_LIQUIDITY"],
        confidence=0.55,
        message="盘口深度不足，买一卖一价差过大，可能导致滑点超过 0.5%"
    )

def test_l2_notifications():
    """测试 L2 深度审查通知 - 多种场景"""
    print("\n" + "=" * 60)
    print("测试 2: L2 深度审查通知（多种场景）")
    print("=" * 60)

    notifier = GateNotifier()

    # 场景 1: 完美通过
    print("\n[L2-PASS-1] 完美通过...")
    notifier.notify_l2_result(
        signal_id="SIG_20260415_225800_001",
        symbol="IF2505",
        direction="做多",
        passed=True,
        risk_level="LOW",
        model_score=0.89,
        message="基本面支撑强劲：PMI 数据超预期，外资持续流入，技术面突破关键阻力位 4850"
    )

    # 场景 2: 有风险但通过
    print("\n[L2-PASS-2] 有风险但通过...")
    notifier.notify_l2_result(
        signal_id="SIG_20260415_225800_002",
        symbol="IC2505",
        direction="做空",
        passed=True,
        risk_level="MEDIUM",
        model_score=0.72,
        message="短期技术面偏空，但需警惕政策面变化，建议设置止损位 6850"
    )

    # 场景 3: 高风险拒绝
    print("\n[L2-REJECT-1] 高风险拒绝...")
    notifier.notify_l2_result(
        signal_id="SIG_20260415_225800_003",
        symbol="IH2505",
        direction="做多",
        passed=False,
        risk_level="HIGH",
        model_score=0.58,
        message="风险评估：当前市场情绪指数 VIX 达到 28，历史回测显示此环境下胜率仅 42%，建议等待市场企稳"
    )

    # 场景 4: 模型分歧拒绝
    print("\n[L2-REJECT-2] 模型分歧拒绝...")
    notifier.notify_l2_result(
        signal_id="SIG_20260415_225800_005",
        symbol="TS2506",
        direction="做空",
        passed=False,
        risk_level="MEDIUM",
        model_score=0.48,
        message="多模型分歧：趋势模型看空 0.65，均值回归模型看多 0.58，机器学习模型中性 0.51，建议观望"
    )

def test_l3_notifications():
    """测试 L3 在线确认通知 - 多种场景"""
    print("\n" + "=" * 60)
    print("测试 3: L3 在线确认通知（多种场景）")
    print("=" * 60)

    notifier = GateNotifier()

    # 场景 1: 快速确认
    print("\n[L3-CONFIRMED-1] 快速确认...")
    notifier.notify_l3_result(
        signal_id="SIG_20260415_225800_001",
        symbol="IF2505",
        direction="做多",
        confirmed=True,
        reviewer="张三",
        wait_time=45,
        message="确认执行：当前价位 4865 接近目标入场点 4860，盘口流动性充足，立即开仓"
    )

    # 场景 2: 延迟确认
    print("\n[L3-CONFIRMED-2] 延迟确认...")
    notifier.notify_l3_result(
        signal_id="SIG_20260415_225800_002",
        symbol="IC2505",
        direction="做空",
        confirmed=True,
        reviewer="李四",
        wait_time=180,
        message="延迟确认：等待价格回调至 6820 后执行，当前 6835 略高于理想入场点"
    )

    # 场景 3: 市场变化拒绝
    print("\n[L3-REJECTED-1] 市场变化拒绝...")
    notifier.notify_l3_result(
        signal_id="SIG_20260415_225800_003",
        symbol="IH2505",
        direction="做多",
        confirmed=False,
        reviewer="王五",
        wait_time=120,
        reason="市场突发利空：央行意外加息 25BP，盘面快速下跌，信号失效"
    )

    # 场景 4: 超时自动拒绝
    print("\n[L3-TIMEOUT-1] 超时自动拒绝...")
    notifier.notify_l3_result(
        signal_id="SIG_20260415_225800_004",
        symbol="IM2505",
        direction="做空",
        confirmed=False,
        reviewer="系统",
        wait_time=300,
        reason="超时未确认：信号发出后 5 分钟内未收到人工确认，价格已偏离入场点 1.2%，自动取消"
    )

def test_strategy_tune_notifications():
    """测试策略调优通知 - 多种场景"""
    print("\n" + "=" * 60)
    print("测试 4: 策略调优通知（多种场景）")
    print("=" * 60)

    notifier = GateNotifier()

    # 场景 1: 显著改进
    print("\n[TUNE-SUCCESS-1] 显著改进...")
    notifier.notify_strategy_tune(
        strategy_id="STRAT_momentum_15m_v2.3",
        success=True,
        metrics={
            "sharpe": 2.15,
            "max_drawdown": 0.085,
            "win_rate": 0.68,
            "annual_return": 0.42
        },
        message="参数优化成功：止损从 2% 调整至 1.5%，止盈从 3% 调整至 4%，回测期 2025-01-01 至 2026-04-15，样本量 1247 笔交易"
    )

    # 场景 2: 小幅改进
    print("\n[TUNE-SUCCESS-2] 小幅改进...")
    notifier.notify_strategy_tune(
        strategy_id="STRAT_mean_reversion_30m_v1.8",
        success=True,
        metrics={
            "sharpe": 1.52,
            "max_drawdown": 0.125,
            "win_rate": 0.58
        },
        message="微调成功：入场阈值从 2σ 调整至 2.2σ，胜率提升 3%，但最大回撤略有增加"
    )

    # 场景 3: 过拟合失败
    print("\n[TUNE-FAILURE-1] 过拟合失败...")
    notifier.notify_strategy_tune(
        strategy_id="STRAT_breakout_5m_v3.1",
        success=False,
        metrics={
            "sharpe": 0.85,
            "max_drawdown": 0.285,
            "win_rate": 0.45
        },
        rollback_point="v3.0 (2026-04-10)",
        next_steps="样本外测试失败，疑似过拟合，建议回滚至 v3.0 并重新设计特征工程",
        message="调优失败：新参数在训练集表现优异（Sharpe 2.8），但样本外测试大幅回撤 28.5%，确认过拟合"
    )

    # 场景 4: 市场环境不匹配
    print("\n[TUNE-FAILURE-2] 市场环境不匹配...")
    notifier.notify_strategy_tune(
        strategy_id="STRAT_trend_following_1h_v2.0",
        success=False,
        metrics={
            "sharpe": 0.62,
            "max_drawdown": 0.195,
            "win_rate": 0.41
        },
        rollback_point="v1.9 (2026-03-25)",
        next_steps="当前震荡市不适合趋势策略，建议暂停调优，等待趋势行情",
        message="环境不匹配：策略在趋势行情中表现优异，但近期市场进入震荡区间，连续止损 8 次"
    )

def test_health_monitor():
    """测试健康监控通知 - 多种场景"""
    print("\n" + "=" * 60)
    print("测试 5: 健康监控通知（多种场景）")
    print("=" * 60)

    monitor = HealthMonitor()

    # 场景 1: 全部健康
    print("\n[HEALTH-1] 全部健康...")
    monitor.components = {
        "data_source": ComponentHealth(
            name="数据源",
            status=HealthStatus.HEALTHY,
            message="TuShare 连接正常，延迟 < 100ms，数据完整性 100%"
        ),
        "model_service": ComponentHealth(
            name="模型服务",
            status=HealthStatus.HEALTHY,
            message="3 个模型全部在线，平均推理时间 45ms"
        ),
        "strategy_engine": ComponentHealth(
            name="策略引擎",
            status=HealthStatus.HEALTHY,
            message="12 个策略运行中，CPU 使用率 35%，内存 2.1GB"
        ),
        "notification": ComponentHealth(
            name="通知系统",
            status=HealthStatus.HEALTHY,
            message="飞书和邮件通道正常，24h 成功率 99.8%"
        ),
        "gate_reviewer": ComponentHealth(
            name="门控审查器",
            status=HealthStatus.HEALTHY,
            message="L1/L2/L3 全部正常，平均响应时间 < 200ms"
        )
    }
    monitor.send_health_snapshot()

    # 场景 2: 部分降级
    print("\n[HEALTH-2] 部分降级...")
    monitor.components = {
        "data_source": ComponentHealth(
            name="数据源",
            status=HealthStatus.DEGRADED,
            message="TuShare 延迟升高至 850ms，但数据仍可用"
        ),
        "model_service": ComponentHealth(
            name="模型服务",
            status=HealthStatus.HEALTHY,
            message="3 个模型全部在线"
        ),
        "strategy_engine": ComponentHealth(
            name="策略引擎",
            status=HealthStatus.HEALTHY,
            message="12 个策略运行中"
        ),
        "notification": ComponentHealth(
            name="通知系统",
            status=HealthStatus.DEGRADED,
            message="邮件通道异常，SMTP 连接超时，已切换至飞书单通道"
        ),
        "gate_reviewer": ComponentHealth(
            name="门控审查器",
            status=HealthStatus.HEALTHY,
            message="L1/L2/L3 全部正常"
        )
    }
    monitor.send_health_snapshot()

    # 场景 3: 严重故障
    print("\n[HEALTH-3] 严重故障...")
    monitor.components = {
        "data_source": ComponentHealth(
            name="数据源",
            status=HealthStatus.CRITICAL,
            message="TuShare API 返回 503，已连续失败 15 分钟，切换至备用数据源"
        ),
        "model_service": ComponentHealth(
            name="模型服务",
            status=HealthStatus.CRITICAL,
            message="模型服务崩溃，OOM killed，正在重启（第 3 次尝试）"
        ),
        "strategy_engine": ComponentHealth(
            name="策略引擎",
            status=HealthStatus.DEGRADED,
            message="因模型服务故障，策略引擎降级为规则模式"
        ),
        "notification": ComponentHealth(
            name="通知系统",
            status=HealthStatus.HEALTHY,
            message="通知系统正常"
        ),
        "gate_reviewer": ComponentHealth(
            name="门控审查器",
            status=HealthStatus.DEGRADED,
            message="L2 深审因模型服务故障暂时跳过，仅执行 L1 和 L3"
        )
    }
    monitor.send_health_snapshot()

def test_daily_summary():
    """测试每日汇总邮件 - 丰富数据"""
    print("\n" + "=" * 60)
    print("测试 6: 每日汇总邮件（丰富数据）")
    print("=" * 60)

    summary = DailyGateSummary()

    # 添加大量测试数据
    print("\n[数据准备] 添加丰富的测试数据...")

    # L1 数据：50 条信号
    for i in range(50):
        symbol = ["IF2505", "IC2505", "IH2505", "IM2505", "TS2506", "TF2506", "T2506"][i % 7]
        passed = i % 3 != 0  # 66% 通过率
        risk_flags = ["LOW", "MEDIUM", "HIGH_VOLATILITY", "POSITION_LIMIT"][i % 4]

        summary.record_l1_result(
            signal_id=f"SIG_20260415_{i:04d}",
            symbol=symbol,
            passed=passed,
            risk_flags=[risk_flags],
            confidence=0.5 + (i % 40) / 100
        )

    # L2 数据：35 条信号
    for i in range(35):
        symbol = ["IF2505", "IC2505", "IH2505", "IM2505", "TS2506"][i % 5]
        passed = i % 4 != 0  # 75% 通过率
        risk_level = ["LOW", "MEDIUM", "HIGH"][i % 3]

        summary.record_l2_result(
            signal_id=f"SIG_20260415_{i:04d}",
            symbol=symbol,
            passed=passed,
            risk_level=risk_level,
            model_score=0.5 + (i % 45) / 100
        )

    # L3 数据：25 条信号
    for i in range(25):
        symbol = ["IF2505", "IC2505", "IH2505", "IM2505"][i % 4]
        if i % 5 == 0:
            # 超时
            summary.record_l3_result(
                signal_id=f"SIG_20260415_{i:04d}",
                symbol=symbol,
                confirmed=False,
                reviewer="系统",
                wait_time=300,
                reason="超时未确认"
            )
        elif i % 3 == 0:
            # 拒绝
            summary.record_l3_result(
                signal_id=f"SIG_20260415_{i:04d}",
                symbol=symbol,
                confirmed=False,
                reviewer=["张三", "李四", "王五"][i % 3],
                wait_time=120,
                reason=["市场环境不佳", "价格偏离过大", "流动性不足"][i % 3]
            )
        else:
            # 确认
            summary.record_l3_result(
                signal_id=f"SIG_20260415_{i:04d}",
                symbol=symbol,
                confirmed=True,
                reviewer=["张三", "李四", "王五"][i % 3],
                wait_time=60 + i * 5,
                message="确认执行"
            )

    # 通知失败记录
    summary.record_notification_failure("feishu", "SIG_20260415_0010", "网络超时")
    summary.record_notification_failure("feishu", "SIG_20260415_0025", "Webhook 返回 500")
    summary.record_notification_failure("email", "SIG_20260415_0032", "SMTP 连接失败")

    # 风险事件
    summary.add_risk_event("MARKET_CRASH", "市场出现异常波动，VIX 指数飙升至 35", "critical")
    summary.add_risk_event("POSITION_LIMIT", "IF2505 持仓接近上限 90%", "warning")
    summary.add_risk_event("MODEL_DEGRADED", "模型服务响应时间超过 1 秒", "warning")

    print("✅ 测试数据添加完成")
    print(f"   L1: {len(summary.l1_results)} 条")
    print(f"   L2: {len(summary.l2_results)} 条")
    print(f"   L3: {len(summary.l3_results)} 条")

    # 生成并发送邮件
    print("\n[邮件生成] 生成每日汇总邮件...")
    summary.send_daily_summary()
    print("✅ 每日汇总邮件已发送")

def main():
    """主测试流程"""
    print("=" * 60)
    print("TASK-0120 飞书通知测试 - 丰富 Mock 数据版本")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查环境变量
    print("\n[环境检查]")
    print(f"飞书启用: {os.getenv('FEISHU_ENABLED', 'false')}")
    print(f"邮件启用: {os.getenv('EMAIL_ENABLED', 'false')}")
    print(f"飞书 Webhook: {'已配置' if os.getenv('FEISHU_WEBHOOK_URL') else '未配置'}")

    # 执行所有测试
    test_l1_notifications()
    test_l2_notifications()
    test_l3_notifications()
    test_strategy_tune_notifications()
    test_health_monitor()
    test_daily_summary()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("✅ 所有通知已发送")
    print("\n请检查飞书交易群，应该收到以下通知:")
    print("  1. L1 快速门控通知 x 4（2 通过 + 2 拒绝）")
    print("  2. L2 深度审查通知 x 4（2 通过 + 2 拒绝）")
    print("  3. L3 在线确认通知 x 4（2 确认 + 1 拒绝 + 1 超时）")
    print("  4. 策略调优通知 x 4（2 成功 + 2 失败）")
    print("  5. 健康快照通知 x 3（全健康 + 部分降级 + 严重故障）")
    print("  6. 每日汇总邮件 x 1（包含 50 条 L1 + 35 条 L2 + 25 条 L3）")
    print("\n总计: 约 20 条飞书通知")

if __name__ == "__main__":
    main()
