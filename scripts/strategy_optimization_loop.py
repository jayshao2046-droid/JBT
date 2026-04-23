#!/usr/bin/env python3
"""
策略优化闭环系统

完整流程：
1. V3生成策略逻辑 → 2. Coder生成YAML → 3. 回测定基线 →
4. Qwen14b诊断 → 5. V3调优 → 6. Coder重新生成 → 7. 回测验证

循环直到达到生产标准
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "decision" / "src"))

from research.symbol_profiler import SymbolProfiler
from research.strategy_architect import StrategyArchitect
from research.code_generator import CodeGenerator
from research.strategy_template import (
    PRODUCTION_STANDARDS,
    MAIN_CONTRACT_MAPPING,
    STRATEGY_TYPE_TEMPLATES,
)
from llm.openai_client import OpenAICompatibleClient

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / "services" / "decision" / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/strategy_optimization_loop.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class StrategyOptimizationLoop:
    """策略优化闭环系统"""

    def __init__(self):
        # 初始化客户端
        self.v3_client = OpenAICompatibleClient(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            model="deepseek-v3",
        )
        self.coder_client = OpenAICompatibleClient(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            model="qwen-coder-plus-latest",
        )
        self.qwen14b_client = OpenAICompatibleClient(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            model="qwen-plus",
        )

        # 初始化组件
        self.profiler = SymbolProfiler(data_service_url="http://192.168.31.74:8105")
        self.architect = StrategyArchitect(client=self.v3_client)
        self.code_gen = CodeGenerator(client=self.coder_client)

        # 输出目录
        self.output_dir = Path("/Users/jayshao/JBT/runtime/optimized_strategies")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_initial_strategy(
        self, symbol: str, strategy_type: str, iteration: int = 1
    ) -> Optional[Dict]:
        """生成初始策略（V3 + Coder）"""
        logger.info(f"🎯 [{symbol}] 生成策略 (迭代 {iteration})")

        # 1. 获取品种特征
        features = await self.profiler.calculate_features(symbol)
        if not features:
            logger.error(f"无法获取品种 {symbol} 的特征")
            return None

        # 2. V3生成策略逻辑
        template = STRATEGY_TYPE_TEMPLATES.get(strategy_type, {})
        strategy_design = await self.architect.design_strategy(
            symbol=symbol,
            features=features,
            strategy_type=strategy_type,
            template_hint=template,
        )

        if not strategy_design:
            logger.error(f"V3生成策略逻辑失败")
            return None

        # 3. Coder生成YAML
        yaml_content = await self.code_gen.generate_yaml(
            symbol=symbol,
            strategy_design=strategy_design,
            features=features,
        )

        if not yaml_content:
            logger.error(f"Coder生成YAML失败")
            return None

        # 保存策略文件
        strategy_name = f"{symbol.replace('.', '_')}_{strategy_type}_v{iteration}"
        yaml_path = self.output_dir / f"{strategy_name}.yaml"
        yaml_path.write_text(yaml_content)

        logger.info(f"✅ 策略已保存: {yaml_path}")

        return {
            "name": strategy_name,
            "yaml_path": str(yaml_path),
            "design": strategy_design,
            "iteration": iteration,
        }

    async def backtest_strategy(self, yaml_path: str) -> Optional[Dict]:
        """回测策略（定基线）"""
        logger.info(f"📊 回测策略: {yaml_path}")

        # 调用回测脚本
        cmd = f"python3 /Users/jayshao/JBT/scripts/backtest_local_nine_strategies.py {yaml_path}"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"回测失败: {stderr.decode()}")
            return None

        # 解析回测结果
        try:
            result = json.loads(stdout.decode())
            logger.info(f"回测结果: Sharpe={result.get('sharpe_ratio', 0):.2f}, "
                       f"交易次数={result.get('trades_count', 0)}, "
                       f"胜率={result.get('win_rate', 0):.2%}")
            return result
        except Exception as e:
            logger.error(f"解析回测结果失败: {e}")
            return None

    async def diagnose_with_qwen14b(
        self, strategy_design: str, backtest_result: Dict
    ) -> str:
        """Qwen14b诊断策略问题"""
        logger.info(f"🔍 Qwen14b诊断策略问题")

        prompt = f"""
你是一位资深量化策略分析师。请分析以下策略的回测结果，找出问题并提出改进建议。

策略设计：
{strategy_design}

回测结果：
- Sharpe Ratio: {backtest_result.get('sharpe_ratio', 0):.2f}
- 交易次数: {backtest_result.get('trades_count', 0)}
- 胜率: {backtest_result.get('win_rate', 0):.2%}
- 最大回撤: {backtest_result.get('max_drawdown', 0):.2%}
- 年化收益: {backtest_result.get('annualized_return', 0):.2%}

生产标准：
- Sharpe Ratio ≥ {PRODUCTION_STANDARDS['sharpe_ratio']}
- 交易次数 ≥ {PRODUCTION_STANDARDS['trades_count']}
- 胜率 ≥ {PRODUCTION_STANDARDS['win_rate']:.0%}
- 最大回撤 ≤ {PRODUCTION_STANDARDS['max_drawdown']:.0%}
- 年化收益 ≥ {PRODUCTION_STANDARDS['annualized_return']:.0%}

请回答：
1. 哪些指标不达标？
2. 可能的原因是什么？
3. 具体的改进建议（参数调整、逻辑优化等）

请用简洁的语言回答，重点突出可操作的改进方向。
"""

        response = await self.qwen14b_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        diagnosis = response.get("content", "")
        logger.info(f"诊断结果:\n{diagnosis}")
        return diagnosis

    async def optimize_with_v3(
        self, original_design: str, diagnosis: str, features: Dict
    ) -> str:
        """V3根据诊断结果调优策略"""
        logger.info(f"🔧 V3调优策略")

        prompt = f"""
你是一位资深量化策略设计师。请根据诊断结果优化策略设计。

原始策略设计：
{original_design}

诊断结果：
{diagnosis}

品种特征：
{json.dumps(features, indent=2, ensure_ascii=False)}

请输出优化后的策略设计，重点改进诊断中指出的问题。
保持策略的核心逻辑，但调整参数、优化入场/出场条件、改进风控规则。

输出格式：
1. 策略名称
2. 核心逻辑（简述）
3. 入场条件（具体）
4. 出场条件（具体）
5. 风控参数（具体数值）
6. 改进说明（相比原策略的变化）
"""

        response = await self.v3_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        optimized_design = response.get("content", "")
        logger.info(f"优化后的策略设计:\n{optimized_design}")
        return optimized_design

    async def evaluate_strategy(self, backtest_result: Dict) -> bool:
        """评估策略是否达到生产标准"""
        if not backtest_result:
            return False

        checks = [
            backtest_result.get("sharpe_ratio", 0) >= PRODUCTION_STANDARDS["sharpe_ratio"],
            backtest_result.get("trades_count", 0) >= PRODUCTION_STANDARDS["trades_count"],
            backtest_result.get("win_rate", 0) >= PRODUCTION_STANDARDS["win_rate"],
            backtest_result.get("max_drawdown", 0) <= PRODUCTION_STANDARDS["max_drawdown"],
            backtest_result.get("annualized_return", 0) >= PRODUCTION_STANDARDS["annualized_return"],
        ]

        passed = sum(checks)
        total = len(checks)
        logger.info(f"生产标准检查: {passed}/{total} 通过")

        return passed >= 4  # 至少4项达标

    async def optimize_single_strategy(
        self, symbol: str, strategy_type: str, max_iterations: int = 5
    ) -> Optional[Dict]:
        """优化单个策略（完整闭环）"""
        logger.info(f"\n{'='*60}")
        logger.info(f"开始优化策略: {symbol} - {strategy_type}")
        logger.info(f"{'='*60}\n")

        # 获取品种特征（用于后续调优）
        features = await self.profiler.calculate_features(symbol)
        if not features:
            logger.error(f"无法获取品种特征")
            return None

        current_design = None
        best_result = None
        best_yaml_path = None

        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n--- 迭代 {iteration}/{max_iterations} ---")

            # 1. 生成策略（首次或根据调优结果重新生成）
            if iteration == 1:
                strategy_info = await self.generate_initial_strategy(
                    symbol, strategy_type, iteration
                )
            else:
                # 使用V3调优后的设计重新生成
                yaml_content = await self.code_gen.generate_yaml(
                    symbol=symbol,
                    strategy_design=current_design,
                    features=features,
                )
                strategy_name = f"{symbol.replace('.', '_')}_{strategy_type}_v{iteration}"
                yaml_path = self.output_dir / f"{strategy_name}.yaml"
                yaml_path.write_text(yaml_content)

                strategy_info = {
                    "name": strategy_name,
                    "yaml_path": str(yaml_path),
                    "design": current_design,
                    "iteration": iteration,
                }

            if not strategy_info:
                logger.error(f"策略生成失败")
                continue

            current_design = strategy_info["design"]

            # 2. 回测
            backtest_result = await self.backtest_strategy(strategy_info["yaml_path"])
            if not backtest_result:
                logger.warning(f"回测失败，跳过本次迭代")
                continue

            # 3. 评估
            if self.evaluate_strategy(backtest_result):
                logger.info(f"✅ 策略达到生产标准！")
                return {
                    "strategy_info": strategy_info,
                    "backtest_result": backtest_result,
                    "iterations": iteration,
                }

            # 记录最佳结果
            if not best_result or backtest_result.get("sharpe_ratio", 0) > best_result.get("sharpe_ratio", 0):
                best_result = backtest_result
                best_yaml_path = strategy_info["yaml_path"]

            # 4. 诊断
            diagnosis = await self.diagnose_with_qwen14b(current_design, backtest_result)

            # 5. V3调优
            current_design = await self.optimize_with_v3(
                current_design, diagnosis, features.__dict__
            )

        # 达到最大迭代次数
        logger.warning(f"⚠️ 达到最大迭代次数 ({max_iterations})，未达到生产标准")
        logger.info(f"最佳结果: Sharpe={best_result.get('sharpe_ratio', 0):.2f}")

        return {
            "strategy_info": {"yaml_path": best_yaml_path},
            "backtest_result": best_result,
            "iterations": max_iterations,
            "status": "max_iterations_reached",
        }

    async def optimize_batch(
        self, symbols: List[str], strategy_types: List[str], max_iterations: int = 5
    ) -> Dict:
        """批量优化策略"""
        results = {}

        for symbol in symbols:
            for strategy_type in strategy_types:
                key = f"{symbol}_{strategy_type}"
                result = await self.optimize_single_strategy(
                    symbol, strategy_type, max_iterations
                )
                results[key] = result

        # 保存汇总报告
        report_path = self.output_dir / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        logger.info(f"\n汇总报告已保存: {report_path}")

        return results


async def main():
    """主函数"""
    # 三个品种
    symbols = ["SHFE.ru2505", "SHFE.rb2505", "DCE.p2505"]

    # 三种策略类型
    strategy_types = ["volatility_breakout", "trend_momentum", "mean_reversion"]

    # 初始化优化器
    optimizer = StrategyOptimizationLoop()

    # 批量优化（每个品种3个策略，共9个）
    results = await optimizer.optimize_batch(
        symbols=symbols,
        strategy_types=strategy_types,
        max_iterations=5,  # 每个策略最多5次迭代
    )

    # 统计结果
    total = len(results)
    passed = sum(1 for r in results.values() if r and r.get("status") != "max_iterations_reached")

    logger.info(f"\n{'='*60}")
    logger.info(f"优化完成: {passed}/{total} 个策略达到生产标准")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
