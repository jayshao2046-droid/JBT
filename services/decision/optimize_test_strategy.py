#!/usr/bin/env python3
"""策略调优脚本 - 方案 A 验证

目标：将 test_strategy_d.yaml 从 D 级（32分）提升到 A 级（80+分）

调优策略：
1. 收紧风控参数（提升风控评分）
2. 优化回测参数（提升回测评分）
"""
import asyncio
import yaml
from pathlib import Path
from src.research.strategy_evaluator import StrategyEvaluator


async def main():
    print("=" * 60)
    print("策略调优验证 - test_strategy_d.yaml")
    print("=" * 60)
    print()

    # 读取原始策略
    base_dir = Path(__file__).parent
    strategy_file = base_dir / 'test_strategies' / 'test_strategy_d.yaml'
    with open(strategy_file, 'r', encoding='utf-8') as f:
        strategy = yaml.safe_load(f)

    print("📋 原始策略配置：")
    print(f"  - 最大仓位: {strategy['risk_control']['max_position_per_symbol']}")
    print(f"  - 日亏损限制: {strategy['risk_control']['daily_loss_limit_yuan']} 元")
    print(f"  - 单品种熔断: {strategy['risk_control']['per_symbol_fuse_yuan']} 元")
    print(f"  - 最大回撤: {strategy['risk_control']['max_drawdown_pct'] * 100}%")
    print()

    # 评估原始策略
    print("🔍 评估原始策略...")
    evaluator = StrategyEvaluator()
    original_report = await evaluator.evaluate_strategy(
        str(strategy_file), '2024-01-01', '2024-12-31'
    )
    print(f"  ✓ 原始评分: {original_report['final_score']:.1f} ({original_report['grade']} 级)")
    print()

    # 调优方案：收紧风控参数
    print("🔧 应用调优方案...")
    optimized_strategy = strategy.copy()
    optimized_strategy['risk_control'] = {
        'max_position_per_symbol': 0.08,     # 从 0.20 收紧到 0.08
        'daily_loss_limit_yuan': 2500,       # 从 10000 收紧到 2500 (0.5%)
        'per_symbol_fuse_yuan': 5000,        # 从 15000 收紧到 5000 (1.0%)
        'max_drawdown_pct': 0.015,           # 从 0.05 收紧到 0.015 (1.5%)
    }

    print("  调优后配置：")
    print(f"  - 最大仓位: {optimized_strategy['risk_control']['max_position_per_symbol']}")
    print(f"  - 日亏损限制: {optimized_strategy['risk_control']['daily_loss_limit_yuan']} 元")
    print(f"  - 单品种熔断: {optimized_strategy['risk_control']['per_symbol_fuse_yuan']} 元")
    print(f"  - 最大回撤: {optimized_strategy['risk_control']['max_drawdown_pct'] * 100}%")
    print()

    # 保存调优后的策略
    optimized_file = base_dir / 'test_strategies' / 'test_strategy_d_optimized.yaml'
    with open(optimized_file, 'w', encoding='utf-8') as f:
        yaml.dump(optimized_strategy, f, allow_unicode=True, default_flow_style=False)

    # 评估调优后的策略
    print("🔍 评估调优后策略...")
    optimized_report = await evaluator.evaluate_strategy(
        str(optimized_file), '2024-01-01', '2024-12-31'
    )
    print(f"  ✓ 调优后评分: {optimized_report['final_score']:.1f} ({optimized_report['grade']} 级)")
    print()

    # 对比结果
    print("=" * 60)
    print("📊 调优效果对比")
    print("=" * 60)
    print()
    print(f"{'指标':<20} {'原始':<15} {'调优后':<15} {'变化':<15}")
    print("-" * 60)
    print(f"{'总分':<20} {original_report['final_score']:<15.1f} {optimized_report['final_score']:<15.1f} {optimized_report['final_score'] - original_report['final_score']:+.1f}")
    print(f"{'等级':<20} {original_report['grade']:<15} {optimized_report['grade']:<15} {'✓' if optimized_report['grade'] < original_report['grade'] else '✗'}")

    if 'stages' in original_report and 'stages' in optimized_report:
        orig_stages = original_report['stages']
        opt_stages = optimized_report['stages']

        print(f"{'基础合规':<20} {orig_stages.get('basic_compliance', {}).get('score', 0):<15.1f} {opt_stages.get('basic_compliance', {}).get('score', 0):<15.1f} {opt_stages.get('basic_compliance', {}).get('score', 0) - orig_stages.get('basic_compliance', {}).get('score', 0):+.1f}")
        print(f"{'回测表现':<20} {orig_stages.get('backtest', {}).get('score', 0):<15.1f} {opt_stages.get('backtest', {}).get('score', 0):<15.1f} {opt_stages.get('backtest', {}).get('score', 0) - orig_stages.get('backtest', {}).get('score', 0):+.1f}")
        print(f"{'PBO 验证':<20} {orig_stages.get('pbo', {}).get('score', 0):<15.1f} {opt_stages.get('pbo', {}).get('score', 0):<15.1f} {opt_stages.get('pbo', {}).get('score', 0) - orig_stages.get('pbo', {}).get('score', 0):+.1f}")
        print(f"{'因子验证':<20} {orig_stages.get('factor', {}).get('score', 0):<15.1f} {opt_stages.get('factor', {}).get('score', 0):<15.1f} {opt_stages.get('factor', {}).get('score', 0) - orig_stages.get('factor', {}).get('score', 0):+.1f}")
        print(f"{'风控评分':<20} {orig_stages.get('risk', {}).get('score', 0):<15.1f} {opt_stages.get('risk', {}).get('score', 0):<15.1f} {opt_stages.get('risk', {}).get('score', 0) - orig_stages.get('risk', {}).get('score', 0):+.1f}")

    print()
    print("=" * 60)

    if optimized_report['grade'] in ['S', 'A']:
        print("✅ 调优成功！策略已达到 A 级或以上")
    elif optimized_report['final_score'] > original_report['final_score']:
        print(f"⚠️  调优有效但未达到 A 级，提升了 {optimized_report['final_score'] - original_report['final_score']:.1f} 分")
    else:
        print("❌ 调优无效，需要调整方案")

    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
