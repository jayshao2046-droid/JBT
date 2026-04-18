#!/usr/bin/env python3
"""测试单个策略的完整流程：V3生成逻辑 → Coder生成YAML → 回测验证"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / "services" / "decision" / ".env")

from services.decision.src.research.strategy_architect import StrategyArchitect
from services.decision.src.research.code_generator import CodeGenerator
from services.decision.src.research.yaml_signal_executor import YAMLSignalExecutor
from services.decision.src.research.symbol_profiler import SymbolProfiler, SymbolFeatures
from services.decision.src.llm.openai_client import OpenAICompatibleClient
import yaml


async def main():
    print("=" * 60)
    print("测试单策略流程：V3 → Coder → 回测")
    print("=" * 60)

    # 初始化在线客户端
    online_client = OpenAICompatibleClient(
        base_url=os.getenv("ONLINE_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        api_key=os.getenv("ONLINE_MODEL_API_KEY", "")
    )

    # 初始化组件
    architect = StrategyArchitect(online_client=online_client, model="qwen-plus")
    coder = CodeGenerator(online_client=online_client, model="qwen-coder-plus")
    executor = YAMLSignalExecutor()

    # 测试品种
    symbol = "rb"

    # Step 1: V3生成策略逻辑
    print("\n[1/3] V3生成策略逻辑...")
    features = SymbolFeatures(
        symbol=symbol,
        volatility_3m=0.025,
        volatility_1y=0.022,
        volatility_5y=0.020,
        volatility_weighted="High",
        trend_strength_3m=0.65,
        trend_strength_1y=0.58,
        trend_strength_weighted="Strong",
        autocorr_3m=0.15,
        autocorr_1y=0.12,
        skewness=0.3,
        kurtosis=3.5,
        liquidity="High"
    )
    strategy_design = await architect.design_strategy(features=features)

    if not strategy_design:
        print("❌ V3策略生成失败")
        return

    # 提取第一个策略（返回的是strategies数组）
    if 'strategies' in strategy_design and len(strategy_design['strategies']) > 0:
        strategy_design = strategy_design['strategies'][0]

    print(f"✅ 策略设计完成")
    print(f"   策略名称: {strategy_design.get('strategy_name', 'unknown')}")
    print(f"   逻辑描述: {strategy_design.get('logic_description', 'N/A')[:80]}...")
    print(f"   推荐因子: {strategy_design.get('recommended_factors', [])}")

    # Step 2: Coder生成YAML
    print("\n[2/3] Coder生成YAML...")
    yaml_path = await coder.generate_yaml_strategy(
        strategy_design=strategy_design,
        symbol=f"SHFE.{symbol}2505",
        timeframe=120
    )

    if not yaml_path:
        print("❌ YAML生成失败")
        return

    print(f"✅ YAML已生成: {yaml_path}")

    # 读取并显示YAML内容
    with open(yaml_path, 'r', encoding='utf-8') as f:
        strategy_yaml = yaml.safe_load(f)

    print("\n生成的YAML结构:")
    print(f"  - name: {strategy_yaml.get('name')}")
    print(f"  - factors: {[f['factor_name'] for f in strategy_yaml.get('factors', [])]}")
    print(f"  - long_condition: {strategy_yaml.get('signal', {}).get('long_condition', 'N/A')}")
    print(f"  - short_condition: {strategy_yaml.get('signal', {}).get('short_condition', 'N/A')}")

    # Step 3: 回测验证
    print("\n[3/3] 执行回测...")
    result = await executor.execute(
        strategy=strategy_yaml,
        start_date="2024-01-01",
        end_date="2024-12-31",
        params_override=None
    )

    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"状态: {result.status}")

    if result.status == "completed":
        print(f"交易次数: {result.trades_count}")
        print(f"Sharpe比率: {result.sharpe_ratio:.4f}")
        print(f"胜率: {result.win_rate:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"年化收益: {result.annualized_return:.2%}")

        # 判断是否达标
        is_qualified = (
            result.trades_count >= 10 and
            result.sharpe_ratio >= 0.5 and
            result.win_rate >= 0.4
        )

        if is_qualified:
            print("\n✅ 策略达到生产标准！")
        else:
            print("\n⚠️ 策略未达标，需要调优")
            print(f"   - 交易次数: {result.trades_count} (目标≥10)")
            print(f"   - Sharpe: {result.sharpe_ratio:.4f} (目标≥0.5)")
            print(f"   - 胜率: {result.win_rate:.2%} (目标≥40%)")
    else:
        print(f"❌ 回测失败: {result.error}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
