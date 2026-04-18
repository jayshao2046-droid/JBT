#!/usr/bin/env python3
"""三品种策略生成脚本 — 橡胶/螺纹钢/棕榈油

为三个品种各生成 3 个创新策略，共 9 个策略。
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.symbol_profiler import SymbolProfiler
from services.decision.src.research.strategy_architect import StrategyArchitect
from services.decision.src.research.code_generator import CodeGenerator
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
    logger.info("🚀 三品种策略生成：橡胶/螺纹钢/棕榈油")
    logger.info("="*60)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / "services/decision/.env"
        load_dotenv(env_path)
        logger.info(f"✅ 已加载环境变量: {env_path}")
    except ImportError:
        logger.warning("python-dotenv 未安装，使用系统环境变量")

    # 测试品种（修正品种代码）
    test_symbols = {
        "SHFE.ru0": "橡胶",
        "SHFE.rb0": "螺纹钢",  # 修正：螺纹钢在上期所
        "DCE.p0": "棕榈油"
    }

    # 初始化组件（使用阿里云模型）
    online_client = OpenAICompatibleClient()
    symbol_profiler = SymbolProfiler(data_service_url="http://192.168.31.76:8105")
    strategy_architect = StrategyArchitect(online_client=online_client, model="qwen-plus")  # 改用 qwen-plus
    code_generator = CodeGenerator(online_client=online_client, model="qwen-coder-plus")

    # 输出目录
    output_dir = Path("./runtime/three_symbols_strategies")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_strategies = []

    # 处理每个品种
    for symbol, name in test_symbols.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 处理品种: {name} ({symbol})")
        logger.info(f"{'='*60}")

        # 第一层：计算品种特征
        logger.info("📊 第一层：计算品种特征...")
        features = await symbol_profiler.calculate_features(symbol)

        if not features:
            logger.error(f"品种 {symbol} 特征计算失败，跳过")
            continue

        logger.info(f"✅ 特征: 波动率={features.volatility_weighted}, 趋势={features.trend_strength_weighted}, 流动性={features.liquidity}")

        # 第二层：设计创新策略
        logger.info("🎨 第二层：设计创新策略...")
        strategy_design = await strategy_architect.design_strategy(features)

        if not strategy_design:
            logger.error(f"品种 {symbol} 策略设计失败，跳过")
            continue

        strategies = strategy_design.get("strategies", [])
        logger.info(f"✅ 生成 {len(strategies)} 个策略")

        # 第三层：生成 YAML 策略文件
        logger.info("🔧 第三层：生成 YAML 策略文件...")

        for i, strategy in enumerate(strategies[:3], 1):  # 只取前3个
            logger.info(f"\n  策略 {i}: {strategy['strategy_name']}")
            logger.info(f"  逻辑: {strategy['logic_description']}")
            logger.info(f"  因子: {', '.join(strategy['recommended_factors'])}")

            # 生成 YAML
            yaml_file = await code_generator.generate_yaml_strategy(
                strategy_design=strategy,
                symbol=symbol,
                timeframe=120
            )

            if yaml_file:
                logger.info(f"  ✅ YAML 已生成: {yaml_file}")

                all_strategies.append({
                    "symbol": symbol,
                    "symbol_name": name,
                    "strategy_name": strategy['strategy_name'],
                    "yaml_file": str(yaml_file),
                    "logic_description": strategy['logic_description'],
                    "recommended_factors": strategy['recommended_factors'],
                    "innovation_points": strategy.get('innovation_points', [])
                })
            else:
                logger.warning(f"  ❌ YAML 生成失败")

    # 保存汇总报告
    summary_file = output_dir / "strategies_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_strategies": len(all_strategies),
            "symbols": list(test_symbols.values()),
            "strategies": all_strategies
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*60}")
    logger.info(f"🎉 策略生成完成")
    logger.info(f"{'='*60}")
    logger.info(f"总计生成: {len(all_strategies)} 个策略")
    logger.info(f"汇总报告: {summary_file}")
    logger.info(f"策略文件: strategies/")
    logger.info(f"{'='*60}")

    # 输出策略清单
    logger.info("\n📋 策略清单:")
    for i, s in enumerate(all_strategies, 1):
        logger.info(f"{i}. {s['symbol_name']} - {s['strategy_name']}")
        logger.info(f"   文件: {s['yaml_file']}")


if __name__ == "__main__":
    asyncio.run(main())
