#!/usr/bin/env python3
"""策略架构师测试脚本 — TASK-U0-20260417-004

测试第二层 LLM 策略设计师，验证创新策略生成能力。

测试品种:
- rb (螺纹钢): 高波动 + 强趋势 + 高流动性
- p (棕榈油): 中波动 + 弱趋势 + 中流动性
- au (黄金): 低波动 + 强趋势 + 高流动性
- cu (铜): 中波动 + 强趋势 + 高流动性
- i (铁矿石): 高波动 + 强趋势 + 高流动性

输出:
- 每个品种生成3个创新策略
- 保存到 runtime/strategy_designs/
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.strategy_architect import StrategyArchitect
from services.decision.src.research.symbol_profiler import SymbolProfiler
from services.decision.src.llm.openai_client import OpenAICompatibleClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🎨 测试策略架构师（第二层 LLM 策略设计师）")
    logger.info("="*60)

    # 环境变量配置
    os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
    os.environ["DEEPSEEK_BASE_URL"] = "https://api.deepseek.com/v1"

    # 测试品种
    test_symbols = ["DCE.rb0", "DCE.p0", "SHFE.au0", "SHFE.cu0", "DCE.i0"]

    # 初始化组件
    online_client = OpenAICompatibleClient()
    symbol_profiler = SymbolProfiler(data_service_url="http://192.168.31.156:8105")
    strategy_architect = StrategyArchitect(online_client=online_client, model="deepseek-chat")

    # 输出目录
    output_dir = Path("./runtime/strategy_designs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 测试每个品种
    for symbol in test_symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 测试品种: {symbol}")
        logger.info(f"{'='*60}")

        # 1. 计算品种特征
        logger.info("📊 计算品种特征...")
        features = await symbol_profiler.calculate_features(symbol)

        if not features:
            logger.warning(f"品种 {symbol} 特征计算失败，跳过")
            continue

        logger.info(f"✅ 特征: 波动率={features.volatility_weighted}, 趋势={features.trend_strength_weighted}, 流动性={features.liquidity}")

        # 2. 设计创新策略
        logger.info("🎨 设计创新策略...")
        strategy_design = await strategy_architect.design_strategy(features)

        if not strategy_design:
            logger.warning(f"品种 {symbol} 策略设计失败，跳过")
            continue

        # 3. 验证策略设计
        strategies = strategy_design.get("strategies", [])
        logger.info(f"✅ 生成 {len(strategies)} 个策略")

        for i, strategy in enumerate(strategies, 1):
            is_valid, reason = strategy_architect.validate_strategy_design(strategy)
            if is_valid:
                logger.info(f"  {i}. {strategy['strategy_name']} ✅")
                logger.info(f"     逻辑: {strategy['logic_description']}")
                logger.info(f"     因子: {', '.join(strategy['recommended_factors'])}")
                logger.info(f"     创新点: {', '.join(strategy['innovation_points'])}")
            else:
                logger.warning(f"  {i}. {strategy.get('strategy_name', 'unknown')} ❌ {reason}")

        # 4. 保存设计
        output_file = output_dir / f"{symbol.replace('.', '_')}_designs.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "symbol": symbol,
                "features": {
                    "volatility_weighted": features.volatility_weighted,
                    "trend_strength_weighted": features.trend_strength_weighted,
                    "liquidity": features.liquidity,
                },
                "strategies": strategies,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 已保存设计: {output_file}")

    logger.info("\n" + "="*60)
    logger.info("🎉 测试完成")
    logger.info(f"设计文件保存在: {output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
