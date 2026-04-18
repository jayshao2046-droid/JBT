"""Gate Reviewer for qwen3:14b L1/L2 signal review.

TASK-0112 Batch A: qwen3:14b L1 快审 + L2 深审封装。
"""

import json
import logging
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional

from .client import OllamaClient, HybridClient
from .openai_client import OpenAICompatibleClient
from ..notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

logger = logging.getLogger(__name__)

# 研报消费审计日志
_GATE_AUDIT_LOG: list[dict] = []


class GateReviewer:
    """qwen3:14b L1/L2 门控审查器。"""

    MODEL = "qwen3:14b-q4_K_M"
    # 安全修复：P2-3 - 从环境变量读取超时配置
    L1_TIMEOUT = float(os.environ.get("GATE_L1_TIMEOUT", "30.0"))  # L1 快审超时
    L2_TIMEOUT = float(os.environ.get("GATE_L2_TIMEOUT", "60.0"))  # L2 深审超时

    def __init__(self, client=None):
        """初始化门控审查器。

        Args:
            client: OllamaClient 或 OpenAICompatibleClient 实例，默认按 LLM_PROVIDER 选择
        """
        # L1/L2 高频审查走 HybridClient：Ollama 优先，超时自动降级在线
        llm_provider = os.getenv("GATE_LLM_PROVIDER", "hybrid").lower()
        if client is not None:
            self.client = client
        elif llm_provider == "online":
            self.client = OpenAICompatibleClient(component="gate_reviewer")
        elif llm_provider == "ollama":
            self.client = OllamaClient(component="gate_reviewer")
        else:
            self.client = HybridClient(component="gate_reviewer")

        if llm_provider == "online":
            self.model = os.getenv("ONLINE_AUDITOR_MODEL", "gpt-5.4")
        else:
            self.model = self.MODEL

    @staticmethod
    def _sanitize_context(context: str) -> str:
        """清理 context 防止 prompt 注入（安全修复：P0-3）。

        Args:
            context: 原始上下文字符串

        Returns:
            清理后的上下文字符串
        """
        if not context:
            return ""

        # 移除可能的 prompt 注入关键词
        dangerous_patterns = [
            r'(?i)ignore\s+(all\s+)?(previous\s+)?(instructions?|prompts?|rules?)',
            r'(?i)system\s+(prompt|message|instruction)',
            r'(?i)forget\s+(everything|all|previous)',
            r'(?i)you\s+are\s+now',
            r'(?i)new\s+(instruction|prompt|role)',
            r'(?i)disregard\s+(previous|above)',
            r'(?i)override\s+(instruction|prompt)',
        ]

        cleaned = context
        for pattern in dangerous_patterns:
            cleaned = re.sub(pattern, '[FILTERED]', cleaned)

        # 限制长度防止过长输入
        return cleaned[:2000]

    async def l1_quick_review(
        self,
        strategy_id: str,
        symbol: str,
        signal: int,
        signal_strength: float,
        factors: List[Dict[str, Any]],
        context: str,
        missing_sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """L1 快审：5日日线K线 + 简洁判断信号方向是否与近期趋势严重矛盾。

        Args:
            strategy_id: 策略 ID
            symbol: 交易标的
            signal: 信号方向 (1=多, -1=空, 0=观望)
            signal_strength: 信号强度 [0, 1]
            factors: 因子列表
            context: L1 上下文（5日日线K线）
            missing_sources: 缺失的数据源列表

        Returns:
            Dict containing:
                - pass: bool, 是否通过
                - risk_flag: str, 风险标记
                - confidence: float, 置信度
                - reasoning: str, 推理过程
                - degraded: bool, 是否降级模式
        """
        # 数据缺失报警
        if missing_sources:
            await self._send_data_missing_alert(
                "L1_QUICK_REVIEW",
                strategy_id,
                symbol,
                missing_sources,
            )

        # 构造 L1 prompt
        factor_summary = ", ".join([f"{f['name']}={f['value']:.3f}" for f in factors[:5]])
        signal_desc = "做多" if signal == 1 else "做空" if signal == -1 else "观望"

        # 清理 context 防止 prompt 注入（安全修复：P0-3）
        context = self._sanitize_context(context)

        system_prompt = """你是 qwen3 门控审查员，负责 L1 快速审查。
任务：判断信号方向是否与近期趋势严重矛盾。
输出格式：严格 JSON，包含 pass(bool), risk_flag(str), confidence(float), reasoning(str)。"""

        user_prompt = f"""策略: {strategy_id}
标的: {symbol}
信号: {signal_desc} (强度 {signal_strength:.2f})
因子摘要: {factor_summary}

{context}

请判断该信号是否与近期趋势严重矛盾，输出 JSON。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = await self.client.chat(self.model, messages, timeout=self.L1_TIMEOUT)

        if "error" in result:
            logger.error(f"L1 快审失败: {result['error']}")
            return {
                "pass": False,
                "risk_flag": "llm_error",
                "confidence": 0.0,
                "reasoning": f"L1 LLM 调用失败: {result['error']}",
                "degraded": bool(missing_sources),
            }

        # 解析 JSON 响应
        try:
            content = result.get("content", "")
            parsed = json.loads(content)
            return {
                "pass": parsed.get("pass", False),
                "risk_flag": parsed.get("risk_flag", "unknown"),
                "confidence": max(0.0, min(1.0, parsed.get("confidence", 0.0))),
                "reasoning": parsed.get("reasoning", ""),
                "degraded": bool(missing_sources),
            }
        except json.JSONDecodeError:
            # 安全修复：P1-6 - 不记录完整内容，仅记录长度
            logger.warning(f"L1 快审 JSON 解析失败，内容长度: {len(content)}")
            return {
                "pass": False,
                "risk_flag": "json_parse_error",
                "confidence": 0.0,
                "reasoning": f"JSON 解析失败，原始响应: {content[:200]}",
                "degraded": bool(missing_sources),
            }

    async def l2_deep_review(
        self,
        strategy_id: str,
        symbol: str,
        signal: int,
        signal_strength: float,
        factors: List[Dict[str, Any]],
        market_context: Dict[str, Any],
        l1_result: Dict[str, Any],
        context: str,
        missing_sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """L2 深审：20日日线 + 60根分钟线 + 研报摘要 + 综合评估。

        Args:
            strategy_id: 策略 ID
            symbol: 交易标的
            signal: 信号方向
            signal_strength: 信号强度
            factors: 因子列表
            market_context: 市场上下文
            l1_result: L1 审查结果
            context: L2 上下文（20日日线 + 60根分钟线 + 研报）
            missing_sources: 缺失的数据源列表

        Returns:
            Dict containing:
                - approve: bool, 是否批准
                - reasoning: str, 推理过程
                - confidence: float, 置信度
                - risk_assessment: str, 风险评估
                - degraded: bool, 是否降级模式
        """
        # 数据缺失报警
        if missing_sources:
            await self._send_data_missing_alert(
                "L2_DEEP_REVIEW",
                strategy_id,
                symbol,
                missing_sources,
            )

        # 构造 L2 prompt
        factor_detail = "\n".join([f"  {f['name']}: {f['value']:.4f}" for f in factors[:10]])
        signal_desc = "做多" if signal == 1 else "做空" if signal == -1 else "观望"

        # 注入最新宏观判断
        macro_block = ""
        try:
            from ..research.research_store import ResearchStore
            macro = ResearchStore().get_macro_summary()
            if macro.get("available"):
                macro_block = (
                    f"\n宏观研判:\n"
                    f"  趋势: {macro.get('macro_trend', 'N/A')}\n"
                    f"  风险等级: {macro.get('risk_level', 'N/A')}\n"
                    f"  关键驱动: {', '.join(macro.get('key_drivers', []))}\n"
                )
                # 审计日志
                import time as _time
                _GATE_AUDIT_LOG.append({
                    "consumer": "gate_reviewer.l2_deep_review",
                    "strategy_id": strategy_id,
                    "symbol": symbol,
                    "report_type": "macro",
                    "action": "inject_to_l2_prompt",
                    "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "risk_level": macro.get("risk_level"),
                })
                logger.info("L2 深审已注入宏观风险等级: %s", macro.get("risk_level"))
        except Exception as e:
            logger.warning(f"L2 注入宏观判断失败（非致命）: {e}")

        system_prompt = """你是 qwen3 门控审查员，负责 L2 深度审查。
任务：综合评估策略可执行性、风险水平、市场环境匹配度。
输出格式：严格 JSON，包含 approve(bool), reasoning(str), confidence(float), risk_assessment(str)。"""

        user_prompt = f"""策略: {strategy_id}
标的: {symbol}
信号: {signal_desc} (强度 {signal_strength:.2f})

因子详情:
{factor_detail}

市场上下文:
  市场时段: {market_context.get('market_session', 'unknown')}
  波动率状态: {market_context.get('volatility_regime', 'unknown')}
  流动性状态: {market_context.get('liquidity_regime', 'unknown')}
  头条风险: {market_context.get('headline_risk_level', 'unknown')}

L1 快审结果:
  通过: {l1_result.get('pass')}
  风险标记: {l1_result.get('risk_flag')}
  置信度: {l1_result.get('confidence'):.2f}
{macro_block}
{context}

请综合评估该策略是否可执行，输出 JSON。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = await self.client.chat(self.model, messages, timeout=self.L2_TIMEOUT)

        if "error" in result:
            logger.error(f"L2 深审失败: {result['error']}")
            return {
                "approve": False,
                "reasoning": f"L2 LLM 调用失败: {result['error']}",
                "confidence": 0.0,
                "risk_assessment": "llm_error",
                "degraded": bool(missing_sources),
            }

        # 解析 JSON 响应
        try:
            content = result.get("content", "")
            parsed = json.loads(content)
            return {
                "approve": parsed.get("approve", False),
                "reasoning": parsed.get("reasoning", ""),
                "confidence": max(0.0, min(1.0, parsed.get("confidence", 0.0))),
                "risk_assessment": parsed.get("risk_assessment", "unknown"),
                "degraded": bool(missing_sources),
            }
        except json.JSONDecodeError:
            # 安全修复：P1-6 - 不记录完整内容，仅记录长度
            logger.warning(f"L2 深审 JSON 解析失败，内容长度: {len(content)}")
            return {
                "approve": False,
                "reasoning": "JSON 解析失败",
                "confidence": 0.0,
                "risk_assessment": "json_parse_error",
                "degraded": bool(missing_sources),
            }

    async def _send_data_missing_alert(
        self,
        review_layer: str,
        strategy_id: str,
        symbol: str,
        missing_sources: List[str],
    ) -> None:
        """发送数据缺失 P1 报警到飞书。

        Args:
            review_layer: 审查层级 (L1_QUICK_REVIEW / L2_DEEP_REVIEW)
            strategy_id: 策略 ID
            symbol: 交易标的
            missing_sources: 缺失的数据源列表
        """
        event = DecisionEvent(
            event_type="SYSTEM",
            event_code="DATA_MISSING_DEGRADED",
            title=f"{review_layer} 数据缺失降级",
            body=f"策略 {strategy_id} 标的 {symbol} 门控审查时检测到数据缺失，已降级继续。\n缺失数据源: {', '.join(missing_sources)}",
            notify_level=NotifyLevel.P1,
            strategy_id=strategy_id,
        )
        dispatcher = get_dispatcher()
        await dispatcher.dispatch(event)
        logger.warning(
            f"{review_layer} 数据缺失报警已发送: strategy={strategy_id} symbol={symbol} missing={missing_sources}"
        )
