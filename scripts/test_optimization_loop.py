#!/usr/bin/env python3
"""
简化版策略优化闭环 - 验证流程

V3生成逻辑 → Coder生成YAML → 本地回测 → 评估
"""
import asyncio
import json
import logging
import os
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services/decision/src"))

from research.yaml_signal_executor import YAMLSignalExecutor
from llm.openai_client import OpenAICompatibleClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "services/decision/.env")

# 生产标准
PRODUCTION_STANDARDS = {
    "sharpe_ratio": 1.5,
    "trades_count": 20,
    "win_rate": 0.5,
    "max_drawdown": 0.03,
    "annualized_return": 0.15,
}


async def generate_strategy_with_v3_and_coder(symbol: str, strategy_type: str) -> str:
    """使用V3+Coder生成策略YAML"""
    logger.info(f"🎯 生成策略: {symbol} - {strategy_type}")

    # 使用qwen-plus替代deepseek-chat（阿里云API）
    client = OpenAICompatibleClient()

    # V3生成策略逻辑（使用qwen-plus）
    v3_prompt = f"""你是量化策略设计专家。为品种 {symbol} 设计一个{strategy_type}策略。

要求：
1. 策略类型: {strategy_type}
2. 品种: {symbol}
3. 时间周期: 120分钟
4. 输出策略的核心逻辑、入场条件、出场条件、风控参数

请简洁输出，不要废话。"""

    v3_response = await client.chat("qwen-plus", [
        {"role": "user", "content": v3_prompt}
    ])

    strategy_logic = v3_response.get("content", "")
    logger.info(f"V3策略逻辑:\n{strategy_logic[:200]}...")

    # Coder生成YAML
    coder_prompt = f"""将以下策略逻辑转换为JBT标准YAML格式。

策略逻辑：
{strategy_logic}

品种：{symbol}
时间周期：120分钟

**关键要求**：
1. 必须包含 symbol 字段，值为 {symbol}
2. 所有数值必须是具体数字，不要使用模板语法如 {{{{ }}}}
3. position_fraction 必须是 0.05-0.2 之间的数值（如 0.1）
4. stop_loss_yuan 必须是具体数值（如 1000）
5. 标准格式示例：
```yaml
strategy:
  symbol: {symbol}
  timeframe: 120
  parameters:
    position_fraction: 0.1
    stop_loss_yuan: 1000
  signals:
    entry:
      long: "..."
      short: "..."
    exit:
      long: "..."
      short: "..."
```

只输出YAML内容，不要其他解释。"""

    coder_response = await client.chat("qwen-coder-plus", [
        {"role": "user", "content": coder_prompt}
    ])

    yaml_content = coder_response.get("content", "").strip()

    # 提取YAML（去除markdown代码块）
    if "```yaml" in yaml_content:
        yaml_content = yaml_content.split("```yaml")[1].split("```")[0].strip()
    elif "```" in yaml_content:
        yaml_content = yaml_content.split("```")[1].split("```")[0].strip()

    return yaml_content


async def backtest_and_evaluate(yaml_content: str, symbol: str) -> dict:
    """回测并评估策略"""
    logger.info(f"📊 回测策略: {symbol}")

    # 解析YAML
    strategy = yaml.safe_load(yaml_content)

    # 确保symbol字段正确（可能在strategy子字段中）
    if 'strategy' in strategy:
        if 'symbol' not in strategy['strategy']:
            strategy['strategy']['symbol'] = symbol
        # 如果有instrument字段，改为symbol
        if 'instrument' in strategy['strategy']:
            strategy['strategy']['symbol'] = strategy['strategy'].pop('instrument')
    else:
        if 'symbol' not in strategy:
            strategy['symbol'] = symbol
        if 'instrument' in strategy:
            strategy['symbol'] = strategy.pop('instrument')

    logger.info(f"策略配置: {json.dumps(strategy, indent=2, ensure_ascii=False)[:300]}...")

    # 执行回测
    executor = YAMLSignalExecutor(
        data_service_url="http://192.168.31.156:8105",
        initial_capital=500_000.0
    )

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    result = await executor.execute(
        strategy=strategy,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        params_override=None
    )

    if result.status not in ["success", "completed"]:
        logger.error(f"回测失败: {result.error}")
        return {"status": "failed", "error": result.error}

    # 评估
    logger.info(f"回测结果: Sharpe={result.sharpe_ratio:.2f}, "
               f"交易={result.trades_count}, 胜率={result.win_rate:.2%}")

    passed_checks = 0
    total_checks = 5

    if result.sharpe_ratio >= PRODUCTION_STANDARDS["sharpe_ratio"]:
        passed_checks += 1
    if result.trades_count >= PRODUCTION_STANDARDS["trades_count"]:
        passed_checks += 1
    if result.win_rate >= PRODUCTION_STANDARDS["win_rate"]:
        passed_checks += 1
    if result.max_drawdown <= PRODUCTION_STANDARDS["max_drawdown"]:
        passed_checks += 1
    if result.annualized_return >= PRODUCTION_STANDARDS["annualized_return"]:
        passed_checks += 1

    is_qualified = passed_checks >= 4  # 至少4项达标

    return {
        "status": "success",
        "qualified": is_qualified,
        "passed_checks": f"{passed_checks}/{total_checks}",
        "sharpe_ratio": result.sharpe_ratio,
        "trades_count": result.trades_count,
        "win_rate": result.win_rate,
        "max_drawdown": result.max_drawdown,
        "annualized_return": result.annualized_return,
    }


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🚀 简化版策略优化闭环测试")
    logger.info("="*60)

    # 测试一个策略
    symbol = "SHFE.ru2505"
    strategy_type = "volatility_breakout"

    try:
        # 1. 生成策略
        yaml_content = await generate_strategy_with_v3_and_coder(symbol, strategy_type)

        # 保存YAML
        output_dir = Path("/Users/jayshao/JBT/runtime/test_strategies")
        output_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = output_dir / f"{symbol.replace('.', '_')}_{strategy_type}_test.yaml"
        yaml_path.write_text(yaml_content)
        logger.info(f"✅ 策略已保存: {yaml_path}")

        # 2. 回测评估
        result = await backtest_and_evaluate(yaml_content, symbol)

        # 3. 输出结果
        logger.info("\n" + "="*60)
        if result["status"] == "success":
            if result["qualified"]:
                logger.info("✅ 策略合格！达到生产标准")
            else:
                logger.info(f"⚠️ 策略不合格 ({result['passed_checks']} 通过)")

            logger.info(f"  Sharpe: {result['sharpe_ratio']:.2f}")
            logger.info(f"  交易次数: {result['trades_count']}")
            logger.info(f"  胜率: {result['win_rate']:.2%}")
            logger.info(f"  最大回撤: {result['max_drawdown']:.2%}")
            logger.info(f"  年化收益: {result['annualized_return']:.2%}")
        else:
            logger.error(f"❌ 失败: {result.get('error', '未知错误')}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ 异常: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
