"""三级渐进式熔断优化器 — TASK-U0-20260417-004

DeepSeek V3 常规推理 + DeepSeek R1 深度推理 + Qwen Coder 代码实现
三级渐进式升级，单策略最多 10 轮 V3 + 1 轮 R1。

角色分工:
- DeepSeek V3: 主治医生 - 常规推理、策略逻辑重构
- DeepSeek R1: 专家会诊 - 深度推理、复杂问题归因（最后手段）
- Qwen Coder: 药剂师 - 代码实现、参数微调、语法修正
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from ..llm.openai_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """优化结果"""
    success: bool
    final_score: float
    iterations: int
    v3_calls: int
    r1_calls: int
    total_cost: float
    stop_reason: str
    best_strategy: dict
    iteration_history: list[dict] = field(default_factory=list)


class ThreeTierOptimizer:
    """三级渐进式熔断优化器

    工作流程:
    1. 阶段1: V3 快速迭代（最多10轮）
       - 触发 R1 条件: 连续3次得分为0 或 连续5次改进<5%
    2. 阶段2: R1 救场（1次机会）
       - 有明显改进(>5%) → 回到阶段1继续用V3
       - 无明显改进 → 暂停，标记为"需要人工介入"
    3. 终止条件:
       - 达到及格线（Sharpe≥0.5, 交易次数≥10, 胜率≥40%）
       - 10轮V3 + 1轮R1 后仍未及格
       - R1 调用后无改进
    """

    # 及格线标准
    PASSING_STANDARDS = {
        "sharpe": 0.5,
        "trades": 10,
        "win_rate": 0.4,
    }

    # 成本估算（美元/次）
    COST_PER_CALL = {
        "deepseek-chat": 0.01,      # V3
        "deepseek-reasoner": 0.10,  # R1
        "qwen-coder-plus": 0.001,   # Coder
    }

    def __init__(
        self,
        online_client: OpenAICompatibleClient,
        context_compressor: Any,
        max_v3_iterations: int = 10,
        r1_trigger_zero_count: int = 3,
        r1_trigger_small_improvement_count: int = 5,
        minimum_improvement_rate: float = 0.05,
    ):
        self.online_client = online_client
        self.compressor = context_compressor

        # 配置参数
        self.max_v3_iterations = max_v3_iterations
        self.r1_trigger_zero_count = r1_trigger_zero_count
        self.r1_trigger_small_improvement_count = r1_trigger_small_improvement_count
        self.minimum_improvement_rate = minimum_improvement_rate

        # 模型配置
        self.v3_model = os.getenv("DEEPSEEK_V3_MODEL", "deepseek-chat")
        self.r1_model = os.getenv("DEEPSEEK_R1_MODEL", "deepseek-reasoner")
        self.coder_model = os.getenv("QWEN_CODER_MODEL", "qwen-coder-plus")

        # 统计信息
        self.v3_calls = 0
        self.r1_calls = 0
        self.total_cost = 0.0

    async def optimize(
        self,
        strategy: dict,
        executor: Any,
        start_date: str,
        end_date: str,
    ) -> OptimizationResult:
        """执行三级优化流程

        Args:
            strategy: 策略配置
            executor: YAMLSignalExecutor 实例
            start_date: 回测起始日期
            end_date: 回测结束日期

        Returns:
            OptimizationResult
        """
        logger.info("🚀 启动三级渐进式熔断优化器")

        iteration_history = []
        best_result = None
        best_score = -999.0
        consecutive_zero_count = 0
        consecutive_small_improvement = 0
        current_strategy = strategy.copy()

        # 阶段1: V3 快速迭代
        for iteration in range(1, self.max_v3_iterations + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 迭代 {iteration}/{self.max_v3_iterations} - 使用 DeepSeek V3")
            logger.info(f"{'='*60}")

            # 执行回测
            result = await executor.execute(current_strategy, start_date, end_date, None)

            if result.status == "failed":
                logger.warning(f"迭代 {iteration} 回测失败: {result.error}")
                iteration_history.append({
                    "iteration": iteration,
                    "model": "V3",
                    "status": "failed",
                    "error": result.error,
                })
                continue

            # 计算得分
            score = self._calculate_score(result)

            # 记录迭代结果
            iteration_record = {
                "iteration": iteration,
                "model": "V3",
                "trades": result.trades_count,
                "sharpe": result.sharpe_ratio,
                "win_rate": result.win_rate,
                "max_dd": result.max_drawdown,
                "score": score,
            }
            iteration_history.append(iteration_record)

            logger.info(f"📊 迭代 {iteration} 结果:")
            logger.info(f"  - 交易次数: {result.trades_count}")
            logger.info(f"  - Sharpe: {result.sharpe_ratio:.4f}")
            logger.info(f"  - 胜率: {result.win_rate:.2%}")
            logger.info(f"  - 综合得分: {score:.4f}")

            # 更新最佳结果
            if score > best_score:
                improvement_rate = (score - best_score) / abs(best_score) if best_score != 0 else 1.0
                best_score = score
                best_result = result

                # 检查改进幅度
                if score == 0:
                    consecutive_zero_count += 1
                    consecutive_small_improvement = 0
                elif improvement_rate < self.minimum_improvement_rate:
                    consecutive_small_improvement += 1
                    consecutive_zero_count = 0
                else:
                    consecutive_zero_count = 0
                    consecutive_small_improvement = 0

                logger.info(f"✅ 新最佳得分: {score:.4f} (改进率: {improvement_rate:.2%})")
            else:
                consecutive_small_improvement += 1
                logger.info(f"⚠️ 无改进（连续 {consecutive_small_improvement} 轮）")

            # 检查是否达到及格线
            if self._check_passing(result):
                logger.info(f"🎉 达到及格线！迭代 {iteration} 轮完成")
                return OptimizationResult(
                    success=True,
                    final_score=best_score,
                    iterations=iteration,
                    v3_calls=self.v3_calls,
                    r1_calls=self.r1_calls,
                    total_cost=self.total_cost,
                    stop_reason="达到及格线",
                    best_strategy=current_strategy,
                    iteration_history=iteration_history,
                )

            # 检查是否需要升级到 R1
            should_use_r1 = (
                (consecutive_zero_count >= self.r1_trigger_zero_count and self.r1_calls == 0) or
                (consecutive_small_improvement >= self.r1_trigger_small_improvement_count and self.r1_calls == 0)
            )

            if should_use_r1:
                logger.warning(f"⚠️ 触发 R1 升级条件（连续{consecutive_zero_count}次得分0 或 连续{consecutive_small_improvement}次改进<5%）")

                # 阶段2: R1 救场
                r1_strategy = await self._call_r1_rescue(
                    current_strategy, result, iteration_history
                )

                if r1_strategy:
                    logger.info("✅ R1 返回新策略，回到 V3 继续优化")
                    current_strategy = r1_strategy
                    consecutive_zero_count = 0
                    consecutive_small_improvement = 0
                    continue
                else:
                    logger.error("❌ R1 救场失败，停止优化")
                    return OptimizationResult(
                        success=False,
                        final_score=best_score,
                        iterations=iteration,
                        v3_calls=self.v3_calls,
                        r1_calls=self.r1_calls,
                        total_cost=self.total_cost,
                        stop_reason="R1 救场失败",
                        best_strategy=current_strategy,
                        iteration_history=iteration_history,
                    )

            # 调用 V3 诊断并调整策略
            if iteration < self.max_v3_iterations:
                logger.info(f"🔍 调用 DeepSeek V3 诊断...")
                context = await self.compressor.compress_context(iteration_history)
                feedback = await self._call_v3_diagnosis(
                    current_strategy, result, context
                )

                if feedback:
                    logger.info(f"📋 V3 反馈:\n{json.dumps(feedback, indent=2, ensure_ascii=False)}")
                    # 调用 Qwen Coder 应用调整
                    current_strategy = await self._call_coder_apply(
                        current_strategy, feedback
                    )
                    iteration_history[-1]["v3_feedback"] = feedback
                else:
                    logger.warning("⚠️ V3 未返回有效反馈")

        # V3 达到上限
        logger.warning(f"🛑 V3 达到 {self.max_v3_iterations} 轮上限，停止优化")
        return OptimizationResult(
            success=False,
            final_score=best_score,
            iterations=self.max_v3_iterations,
            v3_calls=self.v3_calls,
            r1_calls=self.r1_calls,
            total_cost=self.total_cost,
            stop_reason=f"V3 达到 {self.max_v3_iterations} 轮上限",
            best_strategy=current_strategy if best_result else strategy,
            iteration_history=iteration_history,
        )

    async def _call_v3_diagnosis(
        self, strategy: dict, result: Any, context: dict
    ) -> Optional[dict]:
        """调用 DeepSeek V3 诊断问题"""
        prompt = self._build_v3_prompt(strategy, result, context)

        messages = [
            {
                "role": "system",
                "content": "你是 JBT 首席策略师，负责诊断和设计调优方案。只输出纯 JSON。"
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.online_client.chat(self.v3_model, messages, timeout=60.0)
            self.v3_calls += 1
            self.total_cost += self.COST_PER_CALL[self.v3_model]

            if "error" in response:
                logger.warning(f"V3 调用失败: {response['error']}")
                return None

            content = response.get("content", "").strip()

            # 解析 JSON
            try:
                feedback = json.loads(content)
                return feedback
            except json.JSONDecodeError:
                # 尝试提取 JSON 片段
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
                return None

        except Exception as e:
            logger.error(f"V3 调用异常: {e}", exc_info=True)
            return None

    async def _call_r1_rescue(
        self, strategy: dict, result: Any, history: list[dict]
    ) -> Optional[dict]:
        """调用 DeepSeek R1 深度推理救场"""
        logger.info("🚨 调用 DeepSeek R1 专家会诊...")

        prompt = self._build_r1_prompt(strategy, result, history)

        messages = [
            {
                "role": "system",
                "content": "你是 JBT 专家会诊医生，负责深度推理。先输出思维链，再输出 JSON。"
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.online_client.chat(self.r1_model, messages, timeout=120.0)
            self.r1_calls += 1
            self.total_cost += self.COST_PER_CALL[self.r1_model]

            if "error" in response:
                logger.warning(f"R1 调用失败: {response['error']}")
                return None

            content = response.get("content", "").strip()

            # 提取思维链
            thought_match = re.search(r'<thought_process>(.*?)</thought_process>', content, re.DOTALL)
            if thought_match:
                thought_process = thought_match.group(1).strip()
                logger.info(f"🧠 R1 思维链:\n{thought_process}")

            # 解析 JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    feedback = json.loads(json_match.group(0))
                    # 调用 Qwen Coder 应用调整
                    return await self._call_coder_apply(strategy, feedback)
                except json.JSONDecodeError:
                    pass

            return None

        except Exception as e:
            logger.error(f"R1 调用异常: {e}", exc_info=True)
            return None

    async def _call_coder_apply(
        self, strategy: dict, feedback: dict
    ) -> dict:
        """调用 Qwen Coder 应用调整建议"""
        changes = feedback.get("parameter_suggestions", {})

        if not changes:
            logger.warning("未提供参数调整建议")
            return strategy

        logger.info(f"🔧 应用参数调整: {json.dumps(changes, ensure_ascii=False)}")

        # 简化版：直接应用参数调整（实际应该调用 Coder 生成代码）
        new_strategy = strategy.copy()

        # 更新因子参数
        for factor in new_strategy.get("factors", []):
            factor_name = factor.get("factor_name", "").lower()
            params = factor.get("params", {})

            for key, value_info in changes.items():
                if isinstance(value_info, dict) and "to" in value_info:
                    new_value = value_info["to"]
                else:
                    new_value = value_info

                key_lower = key.lower()

                # 直接匹配
                if key in params:
                    params[key] = float(new_value)
                    logger.info(f"  - {factor_name}.{key}: {params[key]}")
                # 模糊匹配
                elif any(k.lower() == key_lower for k in params.keys()):
                    for k in params.keys():
                        if k.lower() == key_lower:
                            params[k] = float(new_value)
                            logger.info(f"  - {factor_name}.{k}: {params[k]}")
                            break

        self.total_cost += self.COST_PER_CALL[self.coder_model]

        return new_strategy

    def _build_v3_prompt(self, strategy: dict, result: Any, context: dict) -> str:
        """构建 DeepSeek V3 诊断 Prompt"""
        factors = strategy.get("factors", [])
        signal = strategy.get("signal", {})

        return f"""你是 JBT 首席策略师，负责诊断和设计调优方案。

【当前策略配置】
- 因子: {[f.get('factor_name') for f in factors]}
- 因子参数: {json.dumps({f.get('factor_name'): f.get('params', {}) for f in factors}, ensure_ascii=False)}
- 多头条件: {signal.get('long_condition', '')}
- 空头条件: {signal.get('short_condition', '')}

【回测结果】
- 交易次数: {result.trades_count} (目标: ≥{self.PASSING_STANDARDS['trades']})
- Sharpe: {result.sharpe_ratio:.4f} (目标: ≥{self.PASSING_STANDARDS['sharpe']})
- 胜率: {result.win_rate:.2%} (目标: ≥{self.PASSING_STANDARDS['win_rate']:.0%})
- 最大回撤: {result.max_drawdown:.2%}

【历史上下文】
{json.dumps(context, ensure_ascii=False, indent=2)}

【任务】
1. 分析根本原因（用 Chain-of-Thought 推理）
2. 给出具体的参数调整建议（具体数值）

【输出格式】
严格按照以下 JSON 格式输出：
{{
  "root_cause_analysis": "...",
  "parameter_suggestions": {{
    "atr_threshold": {{"from": 0.006, "to": 0.002, "reason": "..."}},
    "adx_threshold": {{"from": 25, "to": 15, "reason": "..."}}
  }},
  "expected_improvement": "..."
}}

【严禁】
- 不要输出任何代码
- 不要使用 markdown 代码块
- 只输出纯 JSON
"""

    def _build_r1_prompt(self, strategy: dict, result: Any, history: list[dict]) -> str:
        """构建 DeepSeek R1 深度推理 Prompt"""
        factors = strategy.get("factors", [])
        signal = strategy.get("signal", {})

        # 提取最近3轮失败记录
        recent_failures = [h for h in history[-5:] if h.get("score", 0) <= 0]

        return f"""你是 JBT 专家会诊医生，负责深度推理。

【当前策略配置】
- 因子: {[f.get('factor_name') for f in factors]}
- 因子参数: {json.dumps({f.get('factor_name'): f.get('params', {}) for f in factors}, ensure_ascii=False)}
- 多头条件: {signal.get('long_condition', '')}
- 空头条件: {signal.get('short_condition', '')}

【回测结果】
- 交易次数: {result.trades_count}
- Sharpe: {result.sharpe_ratio:.4f}
- 胜率: {result.win_rate:.2%}

【最近失败记录】
{json.dumps(recent_failures, ensure_ascii=False, indent=2)}

【任务】
1. 先在 <thought_process> 标签内输出你的推理过程（Chain-of-Thought）
2. 然后输出纯 JSON 格式的调优方案

【输出格式】
<thought_process>
第一步：分析根本原因...
第二步：评估可能的解决方案...
第三步：选择最优方案...
</thought_process>

{{
  "root_cause_analysis": "...",
  "parameter_suggestions": {{
    "atr_threshold": {{"from": 0.006, "to": 0.002, "reason": "..."}},
    "adx_threshold": {{"from": 25, "to": 15, "reason": "..."}}
  }},
  "expected_improvement": "..."
}}
"""

    @staticmethod
    def _calculate_score(result: Any) -> float:
        """计算综合得分"""
        # 归一化各指标
        sharpe_score = min(result.sharpe_ratio / ThreeTierOptimizer.PASSING_STANDARDS["sharpe"], 1.0)
        trades_score = min(result.trades_count / ThreeTierOptimizer.PASSING_STANDARDS["trades"], 1.0)
        win_rate_score = min(result.win_rate / ThreeTierOptimizer.PASSING_STANDARDS["win_rate"], 1.0)

        # 加权平均
        score = (
            sharpe_score * 0.4 +
            trades_score * 0.3 +
            win_rate_score * 0.3
        )
        return max(score, 0.0)

    @staticmethod
    def _check_passing(result: Any) -> bool:
        """检查是否达到及格线"""
        return all([
            result.sharpe_ratio >= ThreeTierOptimizer.PASSING_STANDARDS["sharpe"],
            result.trades_count >= ThreeTierOptimizer.PASSING_STANDARDS["trades"],
            result.win_rate >= ThreeTierOptimizer.PASSING_STANDARDS["win_rate"],
        ])
