"""Online Confirmer for DashScope L3 confirmation.

TASK-0112 Batch B: DashScope OpenAI-compatible API 封装，L3 在线确认。
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class OnlineConfirmer:
    """DashScope L3 在线确认器（OpenAI-compatible API）。"""

    def __init__(self):
        """初始化在线确认器。"""
        self.base_url = os.getenv(
            "ONLINE_MODEL_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.api_key = os.getenv("ONLINE_MODEL_API_KEY", "")
        self.default_model = os.getenv("ONLINE_MODEL_DEFAULT", "qwen-plus")
        self.backup_model = os.getenv("ONLINE_MODEL_BACKUP", "deepseek-chat")
        self.dispute_model = os.getenv("ONLINE_MODEL_DISPUTE", "deepseek-reasoner")
        self.timeout = 30.0

    def should_trigger_l3(
        self,
        signal_strength: float,
        l1_confidence: float,
        l2_confidence: float,
        risk_assessment: str,
    ) -> bool:
        """判断是否需要触发 L3 在线确认。

        触发条件（任一满足）：
        1. signal_strength > 0.8（高强度信号）
        2. L1 和 L2 confidence 差异 > 0.3（评分不一致）
        3. risk_assessment 为 "high"（L2 标记高风险）

        Args:
            signal_strength: 信号强度
            l1_confidence: L1 置信度
            l2_confidence: L2 置信度
            risk_assessment: L2 风险评估

        Returns:
            True if L3 should be triggered
        """
        # 条件 1: 高强度信号
        if signal_strength > 0.8:
            logger.info(f"L3 触发条件满足: signal_strength={signal_strength:.2f} > 0.8")
            return True

        # 条件 2: L1/L2 评分不一致
        confidence_diff = abs(l1_confidence - l2_confidence)
        if confidence_diff > 0.3:
            logger.info(
                f"L3 触发条件满足: L1/L2 confidence 差异={confidence_diff:.2f} > 0.3"
            )
            return True

        # 条件 3: L2 标记高风险
        if risk_assessment == "high":
            logger.info(f"L3 触发条件满足: risk_assessment=high")
            return True

        return False

    async def confirm(
        self,
        decision_context: Dict[str, Any],
        use_dispute_model: bool = False,
    ) -> Dict[str, Any]:
        """调用 DashScope L3 在线模型进行确认。

        Args:
            decision_context: 决策上下文（包含策略、信号、L1/L2 结果等）
            use_dispute_model: 是否使用争议模型（DeepSeek-R1）

        Returns:
            Dict containing:
                - confirmed: bool, 是否确认
                - reasoning: str, 推理过程
                - model_used: str, 使用的模型
                - degraded: bool, 是否降级为 L2 结论
                - error: str (optional), 错误信息
        """
        if not self.api_key:
            logger.warning("ONLINE_MODEL_API_KEY 未配置，降级为 L2 结论")
            return self._degrade_to_l2(decision_context, "API key not configured")

        # 选择模型
        model = self.dispute_model if use_dispute_model else self.default_model

        # 构造 prompt
        system_prompt = """你是 L3 在线确认审查员，负责最终确认决策。
任务：综合 L1/L2 本地审查结果，做出最终确认决策。
输出格式：严格 JSON，包含 confirmed(bool), reasoning(str)。"""

        user_prompt = self._build_user_prompt(decision_context)

        # 调用 DashScope API
        try:
            result = await self._call_dashscope(model, system_prompt, user_prompt)
            return result
        except Exception as exc:
            logger.error(f"L3 默认模型 {model} 调用失败: {exc}")

            # 尝试备援模型
            if not use_dispute_model and self.backup_model != model:
                logger.info(f"尝试备援模型: {self.backup_model}")
                try:
                    result = await self._call_dashscope(
                        self.backup_model, system_prompt, user_prompt
                    )
                    return result
                except Exception as backup_exc:
                    logger.error(f"L3 备援模型 {self.backup_model} 调用失败: {backup_exc}")

            # 全部失败，降级为 L2
            return self._degrade_to_l2(decision_context, str(exc))

    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        """构造 L3 用户 prompt。"""
        strategy_id = context.get("strategy_id", "unknown")
        symbol = context.get("symbol", "unknown")
        signal = context.get("signal", 0)
        signal_strength = context.get("signal_strength", 0.0)
        l1_result = context.get("l1_result", {})
        l2_result = context.get("l2_result", {})

        signal_desc = "做多" if signal == 1 else "做空" if signal == -1 else "观望"

        prompt = f"""策略: {strategy_id}
标的: {symbol}
信号: {signal_desc} (强度 {signal_strength:.2f})

L1 快审结果:
  通过: {l1_result.get('pass', False)}
  风险标记: {l1_result.get('risk_flag', 'unknown')}
  置信度: {l1_result.get('confidence', 0.0):.2f}
  推理: {l1_result.get('reasoning', 'N/A')}

L2 深审结果:
  批准: {l2_result.get('approve', False)}
  置信度: {l2_result.get('confidence', 0.0):.2f}
  风险评估: {l2_result.get('risk_assessment', 'unknown')}
  推理: {l2_result.get('reasoning', 'N/A')}

请综合 L1/L2 结果，做出最终确认决策，输出 JSON。"""

        return prompt

    async def _call_dashscope(
        self, model: str, system_prompt: str, user_prompt: str
    ) -> Dict[str, Any]:
        """调用 DashScope OpenAI-compatible API。"""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # 检测网关伪 200 错误 (中转站返回 HTTP 200 + status "439" 等)
            gw_status = data.get("status")
            if gw_status and str(gw_status) != "200":
                error_msg = data.get("msg", f"upstream error {gw_status}")
                raise RuntimeError(f"Gateway [{gw_status}]: {error_msg[:200]}")

            # 记录计费
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            from .billing import get_billing_tracker
            get_billing_tracker().record(
                model=model,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                component="online_confirmer",
            )

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 解析 JSON 响应
            import json

            try:
                parsed = json.loads(content)
                return {
                    "confirmed": parsed.get("confirmed", False),
                    "reasoning": parsed.get("reasoning", ""),
                    "model_used": model,
                    "degraded": False,
                }
            except json.JSONDecodeError:
                logger.warning(f"L3 响应 JSON 解析失败: {content}")
                return {
                    "confirmed": False,
                    "reasoning": f"JSON 解析失败，原始响应: {content[:200]}",
                    "model_used": model,
                    "degraded": False,
                    "error": "json_parse_error",
                }

    def _degrade_to_l2(
        self, decision_context: Dict[str, Any], error_msg: str
    ) -> Dict[str, Any]:
        """降级为 L2 结论。"""
        l2_result = decision_context.get("l2_result", {})
        return {
            "confirmed": l2_result.get("approve", False),
            "reasoning": f"L3 在线模型不可用，降级采用 L2 结论。错误: {error_msg}",
            "model_used": "L2_degraded",
            "degraded": True,
        }
