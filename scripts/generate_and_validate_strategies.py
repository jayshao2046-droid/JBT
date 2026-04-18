#!/usr/bin/env python3
"""
生成策略 → 回测验证 → 评价 → 不合格则重新调优
确保生成的策略达到生产标准
"""
import asyncio
import json
import logging
import os
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services/decision/src"))

from research.symbol_profiler import SymbolProfiler
from research.strategy_architect import StrategyArchitect
from research.code_generator import CodeGenerator
from research.yaml_signal_executor import YAMLSignalExecutor
from llm.openai_client import OpenAICompatibleClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 生产级标准
PRODUCTION_STANDARDS = {
    "sharpe_ratio": 1.5,
    "trades_count": 20,
    "win_rate": 0.5,
    "max_drawdown": 0.03,
    "annualized_return": 0.15,
}

# 最大重试次数
MAX_RETRIES = 3


async def generate_strategy(
    profiler: SymbolProfiler,
    architect: StrategyArchitect,
    generator: CodeGenerator,
    symbol: str,
    strategy_type: str,
) -> tuple[Path, dict]:
    """生成单个策略

    Returns:
        (yaml_path, strategy_design)
    """
    logger.info(f"🔧 生成策略: {symbol} - {strategy_type}")

    # 1. 品种画像
    profile = await profiler.profile_symbol(symbol)

    # 2. 策略设计
    strategy_design = await architect.design_strategy(
        symbol=symbol,
        profile=profile,
        strategy_type=strategy_type
    )

    if not strategy_design:
        raise ValueError(f"策略设计失败: {symbol} - {strategy_type}")

    # 3. 生成YAML
    yaml_path = await generator.generate_yaml_strategy(
        strategy_design=strategy_design,
        symbol=symbol,
        timeframe=120
    )

    if not yaml_path:
        raise ValueError(f"YAML生成失败: {symbol} - {strategy_type}")

    return yaml_path, strategy_design


async def validate_strategy(
    executor: YAMLSignalExecutor,
    yaml_path: Path,
    start_date: str,
    end_date: str,
) -> tuple[bool, dict, str]:
    """验证策略是否达到生产标准

    Returns:
        (is_valid, result_dict, reason)
    """
    logger.info(f"🔍 验证策略: {yaml_path.name}")

    # 读取策略
    with open(yaml_path, 'r', encoding='utf-8') as f:
        strategy = yaml.safe_load(f)

    # 执行回测
    result = await executor.execute(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        params_override=None
    )

    if result.status != "success":
        return False, {}, f"回测失败: {result.error}"

    # 检查是否达标
    checks = []

    if result.sharpe_ratio < PRODUCTION_STANDARDS["sharpe_ratio"]:
        checks.append(f"Sharpe {result.sharpe_ratio:.2f} < {PRODUCTION_STANDARDS['sharpe_ratio']}")

    if result.trades_count < PRODUCTION_STANDARDS["trades_count"]:
        checks.append(f"交易次数 {result.trades_count} < {PRODUCTION_STANDARDS['trades_count']}")

    if result.win_rate < PRODUCTION_STANDARDS["win_rate"]:
        checks.append(f"胜率 {result.win_rate:.2%} < {PRODUCTION_STANDARDS['win_rate']:.0%}")

    if result.max_drawdown > PRODUCTION_STANDARDS["max_drawdown"]:
        checks.append(f"最大回撤 {result.max_drawdown:.2%} > {PRODUCTION_STANDARDS['max_drawdown']:.0%}")

    if result.annualized_return < PRODUCTION_STANDARDS["annualized_return"]:
        checks.append(f"年化收益 {result.annualized_return:.2%} < {PRODUCTION_STANDARDS['annualized_return']:.0%}")

    if checks:
        return False, result.to_dict(), "; ".join(checks)

    return True, result.to_dict(), "达到生产标准"


async def generate_with_retry(
    profiler: SymbolProfiler,
    architect: StrategyArchitect,
    generator: CodeGenerator,
    executor: YAMLSignalExecutor,
    symbol: str,
    strategy_type: str,
    start_date: str,
    end_date: str,
) -> dict:
    """生成并验证策略，失败则重试

    Returns:
        结果字典
    """
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"📊 尝试 {attempt}/{MAX_RETRIES}: {symbol} - {strategy_type}")

        try:
            # 生成策略
            yaml_path, strategy_design = await generate_strategy(
                profiler, architect, generator, symbol, strategy_type
            )

            # 验证策略
            is_valid, result_dict, reason = await validate_strategy(
                executor, yaml_path, start_date, end_date
            )

            if is_valid:
                logger.info(f"✅ 策略合格: {yaml_path.name}")
                return {
                    "status": "success",
                    "symbol": symbol,
                    "strategy_type": strategy_type,
                    "yaml_path": str(yaml_path),
                    "attempt": attempt,
                    "result": result_dict,
                    "reason": reason,
                }
            else:
                logger.warning(f"⚠️ 策略不合格 (尝试 {attempt}/{MAX_RETRIES}): {reason}")

                if attempt == MAX_RETRIES:
                    return {
                        "status": "failed",
                        "symbol": symbol,
                        "strategy_type": strategy_type,
                        "yaml_path": str(yaml_path),
                        "attempt": attempt,
                        "result": result_dict,
                        "reason": f"达到最大重试次数: {reason}",
                    }

        except Exception as e:
            logger.error(f"❌ 生成异常 (尝试 {attempt}/{MAX_RETRIES}): {e}", exc_info=True)

            if attempt == MAX_RETRIES:
                return {
                    "status": "error",
                    "symbol": symbol,
                    "strategy_type": strategy_type,
                    "attempt": attempt,
                    "error": str(e),
                }

    return {
        "status": "failed",
        "symbol": symbol,
        "strategy_type": strategy_type,
        "reason": "未知错误",
    }


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🚀 生成并验证策略（生产标准）")
    logger.info("="*60)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / "services/decision/.env"
        load_dotenv(env_path)
        logger.info(f"✅ 已加载环境变量: {env_path}")
    except ImportError:
        logger.warning("⚠️ 未安装 python-dotenv")

    # 品种和策略类型
    tasks = [
        ("SHFE.ru2505", "volatility_breakout"),
        ("SHFE.ru2505", "trend_momentum"),
        ("SHFE.ru2505", "mean_reversion"),
        ("SHFE.rb2505", "volatility_breakout"),
        ("SHFE.rb2505", "trend_momentum"),
        ("SHFE.rb2505", "mean_reversion"),
        ("DCE.p2505", "volatility_breakout"),
        ("DCE.p2505", "trend_momentum"),
        ("DCE.p2505", "mean_reversion"),
    ]

    # 初始化组件
    online_client = OpenAICompatibleClient()
    profiler = SymbolProfiler(
        online_client=online_client,
        data_service_url="http://192.168.31.76:8105"
    )
    architect = StrategyArchitect(online_client=online_client)
    generator = CodeGenerator(online_client=online_client)
    executor = YAMLSignalExecutor(
        data_service_url="http://192.168.31.76:8105",
        initial_capital=500_000.0
    )

    # 回测参数
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # 结果汇总
    results = []

    # 逐个生成并验证
    for i, (symbol, strategy_type) in enumerate(tasks, 1):
        logger.info("")
        logger.info("="*60)
        logger.info(f"📊 [{i}/{len(tasks)}] {symbol} - {strategy_type}")
        logger.info("="*60)

        result = await generate_with_retry(
            profiler, architect, generator, executor,
            symbol, strategy_type,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        results.append(result)

    # 保存报告
    report_path = Path(__file__).parent.parent / "runtime/strategy_generation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "production_standards": PRODUCTION_STANDARDS,
            "max_retries": MAX_RETRIES,
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] != "success"),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info("="*60)
    logger.info(f"🎉 策略生成完成")
    logger.info(f"   总计: {len(results)} 个")
    logger.info(f"   成功: {sum(1 for r in results if r['status'] == 'success')} 个")
    logger.info(f"   失败: {sum(1 for r in results if r['status'] != 'success')} 个")
    logger.info(f"   报告: {report_path}")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
