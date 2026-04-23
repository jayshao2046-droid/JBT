#!/usr/bin/env python3
"""完整流水线测试脚本 — TASK-U0-20260417-004

测试混合双驱模式三层流水线：
第一层：SymbolProfiler → 品种特征
第二层：StrategyArchitect → 策略逻辑
第三层：CodeGenerator → YAML 策略文件

测试品种: DCE.rb0 (螺纹钢)
"""
import asyncio
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
    logger.info("🚀 测试混合双驱模式三层流水线")
    logger.info("="*60)

    # 环境变量配置
    os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
    os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY", "")

    # 测试品种
    test_symbol = "DCE.rb0"
    logger.info(f"\n测试品种: {test_symbol}")

    # 初始化组件
    online_client = OpenAICompatibleClient()
    symbol_profiler = SymbolProfiler(data_service_url="http://192.168.31.74:8105")
    strategy_architect = StrategyArchitect(online_client=online_client, model="deepseek-chat")
    code_generator = CodeGenerator(online_client=online_client, model="qwen-coder-plus")

    # 第一层：计算品种特征
    logger.info("\n" + "="*60)
    logger.info("📊 第一层：计算品种特征")
    logger.info("="*60)

    features = await symbol_profiler.calculate_features(test_symbol)

    if not features:
        logger.error("品种特征计算失败")
        return

    logger.info(f"✅ 特征: 波动率={features.volatility_weighted}, 趋势={features.trend_strength_weighted}, 流动性={features.liquidity}")

    # 第二层：设计创新策略
    logger.info("\n" + "="*60)
    logger.info("🎨 第二层：设计创新策略")
    logger.info("="*60)

    strategy_design = await strategy_architect.design_strategy(features)

    if not strategy_design:
        logger.error("策略设计失败")
        return

    strategies = strategy_design.get("strategies", [])
    logger.info(f"✅ 生成 {len(strategies)} 个策略")

    # 选择第一个策略进行代码生成
    if not strategies:
        logger.error("没有生成任何策略")
        return

    selected_strategy = strategies[0]
    logger.info(f"\n选择策略: {selected_strategy['strategy_name']}")
    logger.info(f"逻辑: {selected_strategy['logic_description']}")
    logger.info(f"因子: {', '.join(selected_strategy['recommended_factors'])}")

    # 第三层：生成 YAML 策略文件
    logger.info("\n" + "="*60)
    logger.info("🔧 第三层：生成 YAML 策略文件")
    logger.info("="*60)

    yaml_file = await code_generator.generate_yaml_strategy(
        strategy_design=selected_strategy,
        symbol=test_symbol,
        timeframe=120
    )

    if not yaml_file:
        logger.error("YAML 生成失败")
        return

    logger.info(f"✅ YAML 文件已生成: {yaml_file}")

    # 读取并显示生成的 YAML
    with open(yaml_file, "r", encoding="utf-8") as f:
        yaml_content = f.read()

    logger.info("\n生成的 YAML 内容:")
    logger.info("-"*60)
    logger.info(yaml_content)
    logger.info("-"*60)

    logger.info("\n" + "="*60)
    logger.info("🎉 三层流水线测试完成")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
