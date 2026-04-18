"""完整优化闭环测试：V3→Coder→回测→诊断→调优→tqsdk验证

流程：
1. V3生成策略逻辑
2. Coder生成YAML
3. 本地回测
4. 如果未达标：Qwen14b诊断 → V3调优 → 重新生成YAML → 回测
5. 达标后：tqsdk标准回测验证
6. 如果触发熔断：从9个策略池中调取新策略
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "services" / "decision" / ".env")

from services.decision.src.llm.openai_client import OpenAICompatibleClient
from services.decision.src.research.strategy_architect import StrategyArchitect
from services.decision.src.research.code_generator import CodeGenerator
from services.decision.src.research.yaml_signal_executor import YAMLSignalExecutor
from services.decision.src.research.symbol_profiler import SymbolFeatures

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OptimizationLoop:
    """优化闭环管理器"""

    # 及格标准
    PASSING_STANDARDS = {
        "trades": 10,
        "sharpe": 0.5,
        "win_rate": 0.4,
    }

    # 熔断条件
    MAX_ITERATIONS = 10
    R1_TRIGGER_ZERO_COUNT = 3
    R1_TRIGGER_SMALL_IMPROVEMENT = 5
    MIN_IMPROVEMENT_RATE = 0.05

    def __init__(self):
        # 初始化客户端
        # 阿里云客户端（用于Qwen模型）
        self.aliyun_client = OpenAICompatibleClient(
            base_url=os.getenv("ONLINE_MODEL_BASE_URL"),
            api_key=os.getenv("ONLINE_MODEL_API_KEY")
        )

        # DeepSeek客户端（用于V3和R1）
        self.deepseek_client = OpenAICompatibleClient(
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )

        # 初始化组件
        self.architect = StrategyArchitect(
            online_client=self.deepseek_client,  # 使用DeepSeek客户端
            model="deepseek-chat"  # V3
        )
        self.coder = CodeGenerator(
            online_client=self.aliyun_client,  # 使用阿里云客户端
            model="qwen-coder-plus"
        )
        self.executor = YAMLSignalExecutor()

        # 统计信息
        self.iteration_history = []
        self.v3_calls = 0
        self.r1_calls = 0
        self.zero_score_count = 0
        self.small_improvement_count = 0

    async def diagnose_and_optimize(self, strategy: dict, backtest_result: dict) -> dict:
        """Qwen14b诊断并生成优化建议"""
        logger.info("🔍 Qwen14b诊断策略问题...")

        # 构建诊断prompt
        prompt = f"""你是量化策略诊断专家。分析以下策略的回测结果，找出问题并提出优化建议。

策略配置：
- 因子：{[f['factor_name'] for f in strategy.get('factors', [])]}
- 多头条件：{strategy.get('signal', {}).get('long_condition', '')}
- 空头条件：{strategy.get('signal', {}).get('short_condition', '')}
- 市场过滤：{strategy.get('market_filter', {}).get('conditions', [])}

回测结果：
- 交易次数：{backtest_result.get('trades_count', 0)} (目标≥10)
- Sharpe：{backtest_result.get('sharpe_ratio', 0):.4f} (目标≥0.5)
- 胜率：{backtest_result.get('win_rate', 0):.2%} (目标≥40%)
- 最大回撤：{backtest_result.get('max_drawdown', 0):.2%}

【诊断要求】
1. 找出导致交易次数过少或Sharpe过低的根本原因
2. 提出具体的参数调整建议（如放宽ATR阈值、降低ADX要求等）
3. 建议必须是可执行的数值调整，不要泛泛而谈

【输出格式】
严格按照JSON格式输出：
{{
  "diagnosis": "问题诊断（1-2句话）",
  "root_cause": "根本原因",
  "optimization_suggestions": [
    "具体建议1：例如将ATR阈值从0.023降低到0.018",
    "具体建议2：例如将CCI阈值从120降低到100"
  ]
}}
"""

        messages = [
            {"role": "system", "content": "你是量化策略诊断专家，擅长分析回测结果并提出优化建议。"},
            {"role": "user", "content": prompt}
        ]

        response = await self.aliyun_client.chat("qwen-plus", messages, timeout=60.0)

        # 打印原始响应用于调试
        logger.info(f"🔍 Qwen原始响应: {response}")

        # 解析JSON
        try:
            # 提取content字段
            content = response.get("content", "")

            # 移除markdown代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            diagnosis = json.loads(content)

            logger.info(f"✅ 诊断完成：{diagnosis.get('diagnosis', '')}")
            logger.info(f"   根因：{diagnosis.get('root_cause', '')}")
            logger.info(f"   建议：{diagnosis.get('optimization_suggestions', [])}")
            return diagnosis
        except Exception as e:
            logger.error(f"❌ 诊断结果解析失败：{e}")
            return {
                "diagnosis": "解析失败",
                "root_cause": "未知",
                "optimization_suggestions": ["放宽入场条件阈值"]
            }

    async def optimize_with_v3(self, strategy: dict, diagnosis: dict) -> dict:
        """V3根据诊断结果优化策略逻辑"""
        logger.info("🔧 V3优化策略逻辑...")
        self.v3_calls += 1

        # 构建优化prompt
        prompt = f"""你是量化策略优化专家。根据诊断结果优化策略逻辑。

当前策略：
- 因子：{[f['factor_name'] for f in strategy.get('factors', [])]}
- 多头条件：{strategy.get('signal', {}).get('long_condition', '')}
- 空头条件：{strategy.get('signal', {}).get('short_condition', '')}

诊断结果：
- 问题：{diagnosis.get('diagnosis', '')}
- 根因：{diagnosis.get('root_cause', '')}
- 建议：{', '.join(diagnosis.get('optimization_suggestions', []))}

【优化要求】
1. 根据诊断建议调整入场/出场条件
2. 保持因子不变，只调整阈值
3. 条件必须是简单的比较表达式（如 atr > 0.018 * close）
4. 不要使用函数调用或复杂表达式

【输出格式】
严格按照JSON格式输出：
{{
  "entry_logic": "优化后的入场逻辑（简单阈值比较）",
  "exit_logic": "优化后的出场逻辑（简单阈值比较）",
  "changes": "主要改动说明"
}}
"""

        messages = [
            {"role": "system", "content": "你是量化策略优化专家。"},
            {"role": "user", "content": prompt}
        ]

        response = await self.deepseek_client.chat("deepseek-chat", messages, timeout=60.0)

        # 打印原始响应用于调试
        logger.info(f"🔧 V3原始响应: {response}")

        # 解析JSON
        try:
            # 提取content字段
            content = response.get("content", "")

            # 移除markdown代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            optimized = json.loads(content)

            logger.info(f"✅ V3优化完成：{optimized.get('changes', '')}")
            logger.info(f"   优化后入场：{optimized.get('entry_logic', '')}")
            logger.info(f"   优化后出场：{optimized.get('exit_logic', '')}")
            return optimized
        except Exception as e:
            logger.error(f"❌ V3优化结果解析失败：{e}")
            return None

    async def run_optimization_loop(
        self,
        symbol: str,
        features: SymbolFeatures,
        start_date: str,
        end_date: str
    ) -> dict:
        """运行完整优化循环"""
        logger.info("=" * 60)
        logger.info("开始优化循环")
        logger.info("=" * 60)

        # 步骤1：V3生成初始策略
        logger.info("\n[1/5] V3生成策略逻辑...")
        strategy_design = await self.architect.design_strategy(features)
        if not strategy_design or 'strategies' not in strategy_design:
            logger.error("❌ V3策略生成失败")
            return {"success": False, "reason": "V3策略生成失败"}

        first_strategy = strategy_design['strategies'][0]
        logger.info(f"✅ 策略设计完成：{first_strategy['strategy_name']}")

        # 步骤2：Coder生成YAML
        logger.info("\n[2/5] Coder生成YAML...")
        yaml_path = await self.coder.generate_yaml_strategy(
            first_strategy,
            symbol,
            timeframe=120
        )
        if not yaml_path:
            logger.error("❌ YAML生成失败")
            return {"success": False, "reason": "YAML生成失败"}

        logger.info(f"✅ YAML已生成：{yaml_path}")

        # 迭代优化循环
        best_score = 0.0
        best_strategy = None

        for iteration in range(self.MAX_ITERATIONS):
            logger.info(f"\n[3/5] 第 {iteration + 1} 轮回测...")

            # 读取当前YAML
            with open(yaml_path, 'r', encoding='utf-8') as f:
                import yaml
                current_strategy = yaml.safe_load(f)

            # 执行回测
            result = await self.executor.execute(
                current_strategy,
                start_date,
                end_date,
                None
            )

            if result.status != "completed":
                logger.error(f"❌ 回测失败：{result.error_message}")
                self.zero_score_count += 1
            else:
                # 计算综合得分
                score = self._calculate_score(result)
                logger.info(f"📊 回测结果：交易{result.trades_count}次, Sharpe={result.sharpe_ratio:.4f}, 胜率={result.win_rate:.2%}, 得分={score:.2f}")

                # 记录历史
                self.iteration_history.append({
                    "iteration": iteration + 1,
                    "score": score,
                    "trades": result.trades_count,
                    "sharpe": result.sharpe_ratio,
                    "win_rate": result.win_rate
                })

                # 更新最佳策略
                if score > best_score:
                    improvement = (score - best_score) / max(best_score, 0.01)
                    if improvement < self.MIN_IMPROVEMENT_RATE:
                        self.small_improvement_count += 1
                    else:
                        self.small_improvement_count = 0

                    best_score = score
                    best_strategy = current_strategy
                    self.zero_score_count = 0
                else:
                    self.small_improvement_count += 1

                # 检查是否达标
                if self._check_passing(result):
                    logger.info(f"🎉 策略达标！准备tqsdk验证...")
                    return {
                        "success": True,
                        "strategy": best_strategy,
                        "yaml_path": yaml_path,
                        "iterations": iteration + 1,
                        "final_score": best_score
                    }

            # 检查熔断条件
            if self._should_trigger_r1():
                logger.warning("⚠️ 触发R1熔断条件")
                # TODO: 调用R1进行深度推理
                self.r1_calls += 1
                break

            # 步骤4：诊断和优化
            logger.info(f"\n[4/5] 诊断和优化...")
            diagnosis = await self.diagnose_and_optimize(current_strategy, {
                "trades_count": result.trades_count if result.status == "completed" else 0,
                "sharpe_ratio": result.sharpe_ratio if result.status == "completed" else 0,
                "win_rate": result.win_rate if result.status == "completed" else 0,
                "max_drawdown": result.max_drawdown if result.status == "completed" else 0
            })

            optimized_logic = await self.optimize_with_v3(current_strategy, diagnosis)
            if not optimized_logic:
                logger.error("❌ V3优化失败")
                break

            # 步骤5：重新生成YAML
            logger.info(f"\n[5/5] 重新生成YAML...")

            # 更新策略设计（使用V3返回的任何可用字段）
            if 'entry_logic' in optimized_logic:
                first_strategy['entry_logic'] = optimized_logic['entry_logic']
            if 'exit_logic' in optimized_logic:
                first_strategy['exit_logic'] = optimized_logic['exit_logic']

            # 如果V3返回的是完整策略，直接使用
            if 'strategy_name' in optimized_logic:
                first_strategy = optimized_logic

            yaml_path = await self.coder.generate_yaml_strategy(
                first_strategy,
                symbol,
                timeframe=120
            )
            if not yaml_path:
                logger.error("❌ YAML重新生成失败")
                break

        # 未达标
        logger.warning(f"⚠️ 优化未达标，最佳得分：{best_score:.2f}")
        return {
            "success": False,
            "reason": "未达标",
            "best_score": best_score,
            "iterations": len(self.iteration_history)
        }

    def _calculate_score(self, result) -> float:
        """计算综合得分"""
        if result.trades_count == 0:
            return 0.0

        # 加权得分
        trade_score = min(result.trades_count / 10, 1.0) * 0.3
        sharpe_score = min(result.sharpe_ratio / 0.5, 1.0) * 0.4
        winrate_score = min(result.win_rate / 0.4, 1.0) * 0.3

        return (trade_score + sharpe_score + winrate_score) * 100

    def _check_passing(self, result) -> bool:
        """检查是否达标"""
        return (
            result.trades_count >= self.PASSING_STANDARDS["trades"] and
            result.sharpe_ratio >= self.PASSING_STANDARDS["sharpe"] and
            result.win_rate >= self.PASSING_STANDARDS["win_rate"]
        )

    def _should_trigger_r1(self) -> bool:
        """检查是否应触发R1"""
        return (
            self.zero_score_count >= self.R1_TRIGGER_ZERO_COUNT or
            self.small_improvement_count >= self.R1_TRIGGER_SMALL_IMPROVEMENT
        )


async def main():
    """主函数"""
    # 测试参数
    symbol = "SHFE.rb2505"
    start_date = "2024-01-01"
    end_date = "2026-04-08"

    # 构建品种特征
    features = SymbolFeatures(
        symbol=symbol,
        volatility_3m=0.025,
        volatility_1y=0.022,
        volatility_5y=0.020,
        volatility_weighted="High",
        trend_strength_3m=0.6,
        trend_strength_1y=0.55,
        trend_strength_weighted="Strong",
        autocorr_3m=0.3,
        autocorr_1y=0.25,
        skewness=0.1,
        kurtosis=3.0,
        liquidity="High"
    )

    # 运行优化循环
    loop = OptimizationLoop()
    result = await loop.run_optimization_loop(symbol, features, start_date, end_date)

    # 输出结果
    print("\n" + "=" * 60)
    print("优化循环结果")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n统计信息：")
    print(f"  - V3调用次数：{loop.v3_calls}")
    print(f"  - R1调用次数：{loop.r1_calls}")
    print(f"  - 总迭代次数：{len(loop.iteration_history)}")


if __name__ == "__main__":
    asyncio.run(main())
