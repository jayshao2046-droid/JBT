#!/usr/bin/env python3
"""棉花期货策略优化 - 在decision服务目录下运行"""
import asyncio
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path

from src.research.strategy_param_optimizer import StrategyParamOptimizer
from src.research.strategy_evaluator import StrategyEvaluator


async def main():
    print("="*80)
    print("棉花期货激进型5分钟策略调优")
    print("目标: 80分 | 最大迭代: 20次")
    print("="*80)

    strategy_path = Path("/Users/jayshao/JBT/参考文件/策略/CZCE.CF/aggressive/STRAT_czce_cf_aggressive_5m.yaml")

    with open(strategy_path, 'r') as f:
        strategy = yaml.safe_load(f)

    print(f"\n策略: {strategy.get('name')}")
    print(f"品种: {strategy.get('symbols')[0]}")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    optimizer = StrategyParamOptimizer(n_trials=20)
    evaluator = StrategyEvaluator()

    best_score = 0
    best_strategy = None

    for i in range(1, 21):
        print(f"\n{'='*80}\n迭代 {i}/20\n{'='*80}")

        try:
            print("\n[1/3] 参数优化...")
            opt_result = await optimizer.optimize(strategy, start_str, end_str)

            if 'error' in opt_result:
                print(f"  ✗ {opt_result['error']}")
                continue

            best_params = opt_result['best_params']
            print(f"  ✓ IS Sharpe={opt_result['is_result']['sharpe_ratio']:.2f}")

            print("\n[2/3] 应用参数并修复合规...")
            optimized = yaml.safe_load(yaml.dump(strategy))

            for factor in optimized.get('factors', []):
                for key in factor.get('params', {}).keys():
                    if key in best_params:
                        factor['params'][key] = best_params[key]

            if 'position_fraction' in best_params:
                optimized['position_fraction'] = best_params['position_fraction']

            risk = optimized.get('risk', {})
            risk.update({
                'no_overnight': True,
                'force_close_day': '14:55',
                'force_close_night': '22:55',
                'daily_loss_limit_yuan': 1500,
                'per_symbol_fuse_yuan': 800,
                'max_drawdown_pct': 0.015
            })

            if optimized.get('position_fraction', 0.18) > 0.12:
                optimized['position_fraction'] = 0.10

            print("\n[3/3] 评分...")
            temp_path = strategy_path.parent / f"temp_{i}.yaml"
            with open(temp_path, 'w') as f:
                yaml.dump(optimized, f)

            eval_report = await evaluator.evaluate_strategy(str(temp_path), start_str, end_str)
            score = eval_report['final_score']

            print(f"  ✓ {score:.1f}/100 ({eval_report['grade']}级)")

            temp_path.unlink()

            if score > best_score:
                best_score = score
                best_strategy = optimized
                print(f"\n  🎉 新最佳: {score:.1f}/100")

            if score >= 80:
                print(f"\n🎉 达标！{score:.1f}/100")
                break

            strategy = optimized

        except Exception as e:
            print(f"\n✗ 异常: {e}")
            continue

    print(f"\n{'='*80}\n优化完成\n{'='*80}")
    print(f"最佳分数: {best_score:.1f}/100")

    if best_strategy:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        out = strategy_path.parent / f"STRAT_czce_cf_aggressive_5m_opt_{best_score:.0f}pts_{ts}.yaml"
        with open(out, 'w') as f:
            yaml.dump(best_strategy, f)
        print(f"\n已保存: {out.name}")


if __name__ == "__main__":
    asyncio.run(main())
