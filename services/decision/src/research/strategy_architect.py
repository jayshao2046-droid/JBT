"""策略架构师 — TASK-U0-20260417-004

混合双驱模式第二层：LLM 策略设计师

基于品种特征 + 因子库元数据，调用 DeepSeek V3 生成创新策略逻辑。

核心理念:
- 拒绝"因子排列组合"的数学陷阱
- 利用 LLM 的创造力，跳出传统思维
- 基于品种特征的逻辑创新

工作流程:
1. 输入：品种标签（如 rb = 高波动+强趋势+高流动性）
2. 输入：因子库元数据（因子的适用场景描述）
3. 调用 DeepSeek V3 生成策略逻辑伪代码
4. 输出：策略逻辑 + 推荐因子列表

示例输出:
{
  "strategy_name": "rb_volatility_breakout_001",
  "logic_description": "基于波动率突破 + 持仓量异动的趋势跟踪策略",
  "recommended_factors": ["ATR", "ADX", "OBV"],
  "entry_logic": "当 ATR 突破20日高点 且 OBV 放量 且 ADX > 25 时开仓",
  "exit_logic": "ATR 回落至10日均线以下 或 ADX < 20 时平仓",
  "risk_management": "动态止损：ATR * 2.5",
  "innovation_points": ["引入持仓量异动作为确认信号", "动态止损根据波动率调整"]
}
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional

from services.decision.src.llm.openai_client import OpenAICompatibleClient
from .symbol_profiler import SymbolFeatures

logger = logging.getLogger(__name__)


class StrategyArchitect:
    """策略架构师

    基于品种特征生成创新策略逻辑。
    """

    # 因子库元数据
    FACTOR_LIBRARY = {
        "MACD": {
            "description": "趋势跟踪指标，适合强趋势品种",
            "适用场景": ["强趋势", "中高波动"],
            "不适用场景": ["震荡市", "低波动"],
        },
        "RSI": {
            "description": "超买超卖指标，适合震荡市和均值回归",
            "适用场景": ["弱趋势", "震荡市", "均值回归"],
            "不适用场景": ["强趋势"],
        },
        "ATR": {
            "description": "波动率指标，用于动态止损和仓位管理",
            "适用场景": ["所有品种", "风险管理"],
            "不适用场景": [],
        },
        "ADX": {
            "description": "趋势强度指标，用于过滤震荡市",
            "适用场景": ["趋势过滤", "强趋势确认"],
            "不适用场景": ["震荡市交易"],
        },
        "Bollinger": {
            "description": "布林带，适合均值回归和突破策略",
            "适用场景": ["震荡市", "均值回归", "突破确认"],
            "不适用场景": ["强趋势跟踪"],
        },
        "VolumeRatio": {
            "description": "成交量比率，用于确认趋势和突破",
            "适用场景": ["突破确认", "趋势确认", "高流动性品种"],
            "不适用场景": ["低流动性品种"],
        },
        "OBV": {
            "description": "能量潮指标，基于成交量的趋势指标",
            "适用场景": ["趋势确认", "背离信号", "高流动性品种"],
            "不适用场景": ["低流动性品种"],
        },
        "KDJ": {
            "description": "随机指标，适合震荡市和短线交易",
            "适用场景": ["震荡市", "短线交易", "超买超卖"],
            "不适用场景": ["强趋势跟踪"],
        },
        "CCI": {
            "description": "顺势指标，适合捕捉极端行情",
            "适用场景": ["极端行情", "突破交易", "高波动品种"],
            "不适用场景": ["低波动品种"],
        },
    }

    def __init__(
        self,
        online_client: OpenAICompatibleClient,
        model: str = "deepseek-chat",
    ):
        self.online_client = online_client
        self.model = model

        logger.info(f"🎨 策略架构师已启动（模型: {self.model}）")

    async def design_strategy(
        self,
        features: SymbolFeatures,
        existing_strategies: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """设计创新策略

        Args:
            features: 品种特征
            existing_strategies: 已有策略列表（避免重复）

        Returns:
            策略设计字典
        """
        logger.info(f"🎨 为 {features.symbol} 设计创新策略...")

        # 构建 Prompt
        prompt = self._build_design_prompt(features, existing_strategies)

        messages = [
            {
                "role": "system",
                "content": "你是 JBT 首席策略架构师，擅长基于品种特征设计创新交易策略。只输出纯 JSON。"
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.online_client.chat(self.model, messages, timeout=120.0)

            if "error" in response:
                logger.warning(f"策略设计失败: {response['error']}")
                return None

            content = response.get("content", "").strip()

            # 解析 JSON
            strategy_design = self._extract_json(content)

            if strategy_design:
                logger.info(f"✅ 策略设计完成: {strategy_design.get('strategy_name')}")
                return strategy_design
            else:
                logger.warning("策略设计返回格式错误")
                return None

        except Exception as e:
            logger.error(f"策略设计异常: {e}", exc_info=True)
            return None

    def _build_design_prompt(
        self,
        features: SymbolFeatures,
        existing_strategies: Optional[list[str]] = None,
    ) -> str:
        """构建策略设计 Prompt"""

        # 品种特征描述
        feature_desc = f"""品种: {features.symbol}

特征画像:
- 波动率: {features.volatility_weighted} (3个月: {features.volatility_3m:.4f}, 1年: {features.volatility_1y:.4f})
- 趋势强度: {features.trend_strength_weighted} (3个月: {features.trend_strength_3m:.4f}, 1年: {features.trend_strength_1y:.4f})
- 流动性: {features.liquidity}
- 自相关性: {features.autocorr_3m:.4f}
- 偏度: {features.skewness:.4f}
- 峰度: {features.kurtosis:.4f}
"""

        # 因子库描述
        factor_desc = "\n".join([
            f"- {name}: {meta['description']} | 适用: {', '.join(meta['适用场景'])}"
            for name, meta in self.FACTOR_LIBRARY.items()
        ])

        # 已有策略
        existing_desc = ""
        if existing_strategies:
            existing_desc = f"\n\n已有策略（避免重复）:\n" + "\n".join([f"- {s}" for s in existing_strategies])

        return f"""{feature_desc}

可用因子库:
{factor_desc}
{existing_desc}

【任务】
基于 {features.symbol} 的特征，设计 3 种从未被尝试过的创新策略逻辑。

【策略设计原则】
1. **初始策略应该适度宽松，避免0交易**
2. **目标：回测期间至少产生10笔交易**
3. **市场过滤条件应该比入场条件更宽松**（市场过滤是前置条件，不应该比开仓条件更严格）
4. **避免三重叠加**（市场过滤 + 入场条件 + 出场条件同时使用相同因子）

【参数建议】
- ATR阈值：0.002-0.005 * close（不要超过0.01，初始策略建议0.003左右）
- VolumeRatio：1.2-1.5（不要超过2.0，初始策略建议1.3左右）
- ADX：20-25（不要超过30，初始策略建议22左右）
- RSI：30-70区间（不要使用极端值如<20或>80）
- Bollinger偏移：使用middle±0.2*bandwidth（不要直接使用upper/lower突破）

【可用因子库】
只能使用以下因子，不要创造新因子：
- ATR: 平均真实波幅
- ADX: 平均趋向指标
- RSI: 相对强弱指标
- MACD: 指数平滑异同移动平均线
- SMA: 简单移动平均
- EMA: 指数移动平均
- Bollinger: 布林带
- VolumeRatio: 成交量比率
- CCI: 商品通道指标

【重要约束】
- **只能使用上述因子库中的因子**，不要创造新因子（如"偏度"、"Close"、"OBV"等）
- 入场/出场逻辑必须使用简单的阈值比较，不要使用"突破N日高点"、"回落至均线"等复杂表达
- 因子只能与固定数值或价格（close/open/high/low）比较
- close/open/high/low/volume 是内置变量，不需要在factors中定义
- 正确示例：
  * "ATR > 0.02 * close 且 ADX > 25 且 RSI < 70"
  * "RSI < 30 且 volume > 10000"
  * "VolumeRatio > 1.5 且 CCI > 100"
- 错误示例（不要使用）：
  * "ATR突破20日高点" ❌
  * "MACD金叉" ❌
  * "价格回落至均线" ❌
  * 使用不存在的因子如"偏度"、"Close"、"OBV" ❌

【要求】
1. 不要只是 MACD+RSI 的简单组合
2. 尝试引入"波动率 + 持仓量"等创新因子组合
3. 根据品种特征选择最适合的因子组合
4. 每个策略必须有明确的创新点
5. **入场/出场逻辑必须是简单的阈值比较**

【输出格式】
严格按照以下 JSON 格式输出（输出3个策略）：

```json
{{
  "strategies": [
    {{
      "strategy_name": "rb_volatility_momentum_001",
      "logic_description": "基于高波动率环境下的动量策略",
      "recommended_factors": ["ATR", "ADX", "OBV"],
      "entry_logic": "ATR > 0.02 * close 且 ADX > 25 且 OBV > 0",
      "exit_logic": "ATR < 0.01 * close 或 ADX < 20",
      "risk_management": "固定止损 1000 元",
      "innovation_points": [
        "使用ATR相对价格比例作为波动率过滤",
        "结合OBV确认趋势有效性"
      ],
      "适用品种特征": "高波动 + 强趋势 + 高流动性",
      "expected_advantage": "在高波动环境中捕捉强趋势"
    }},
    {{
      "strategy_name": "...",
      "logic_description": "...",
      ...
    }},
    {{
      "strategy_name": "...",
      "logic_description": "...",
      ...
    }}
  ]
}}
```

【严禁】
- 不要输出任何代码
- 不要使用 markdown 代码块标记
- 只输出纯 JSON
"""

    def _extract_json(self, content: str) -> Optional[dict]:
        """从 LLM 回复中提取 JSON"""
        # 去除 markdown 代码块标记
        content = content.replace("```json", "").replace("```", "").strip()

        # 尝试解析 JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON 片段
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

        return None

    def validate_strategy_design(self, design: dict) -> tuple[bool, str]:
        """验证策略设计是否合理

        Args:
            design: 策略设计字典

        Returns:
            (是否合理, 原因)
        """
        required_fields = [
            "strategy_name",
            "logic_description",
            "recommended_factors",
            "entry_logic",
            "exit_logic",
            "innovation_points",
        ]

        for field in required_fields:
            if field not in design:
                return False, f"缺少必填字段: {field}"

        # 检查因子是否在因子库中
        for factor in design.get("recommended_factors", []):
            if factor not in self.FACTOR_LIBRARY:
                return False, f"未知因子: {factor}"

        # 检查创新点
        if not design.get("innovation_points"):
            return False, "缺少创新点"

        return True, "策略设计合理"
