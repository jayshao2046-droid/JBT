"""行情类型检测器 — TASK-0114

调用 phi4-reasoning 判断行情类型（5分类：趋势/震荡/高波动/压缩/事件驱动）。
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class Regime(str, Enum):
    """行情类型枚举（5分类）。

    trend:        明显单边趋势（技术跟随型策略适用）
    oscillation:  区间震荡（均值回归型策略适用）
    high_vol:     高波动非趋势（宽止损、减仓适用）
    compression:  低波幅收口，等待突破（不建仓）
    event_driven: 事件驱动/异常放量（停止正常交易，专属策略）
    """

    TREND = "trend"
    OSCILLATION = "oscillation"
    HIGH_VOL = "high_vol"
    COMPRESSION = "compression"
    EVENT_DRIVEN = "event_driven"

    @classmethod
    def values(cls) -> list:
        return [r.value for r in cls]


@dataclass
class RegimeResult:
    """行情检测结果。"""

    symbol: str
    regime: Regime
    confidence: float  # 0.0-1.0
    reasoning: str
    source: str  # "phi4" | "fallback"


class RegimeDetector:
    """调 phi4-reasoning 判断行情类型（趋势/震荡/高波动）。"""

    OLLAMA_URL = "http://192.168.31.142:11434"
    MODEL = "phi4-reasoning:14b"
    TIMEOUT = 15.0  # 超时降级为 trend
    FALLBACK_REGIME = Regime.TREND  # 保守降级策略

    def __init__(self, ollama_url: Optional[str] = None):
        """初始化行情检测器。

        Args:
            ollama_url: Ollama API 地址，默认使用类常量
        """
        self.ollama_url = ollama_url or self.OLLAMA_URL

    async def detect(
        self,
        symbol: str,
        bars_5d: List[Dict[str, Any]],
        bars_20d: List[Dict[str, Any]],
    ) -> RegimeResult:
        """检测行情类型。

        输入：5日日线 + 20日日线 K 线数据（OHLCV 格式）
        输出：RegimeResult
        超时或报错 → 自动降级为 trend + source="fallback"

        Args:
            symbol: 品种代码
            bars_5d: 5日日线数据
            bars_20d: 20日日线数据

        Returns:
            RegimeResult
        """
        try:
            prompt = self._build_prompt(symbol, bars_5d, bars_20d)

            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                response.raise_for_status()

                data = response.json()
                return self._parse_response(symbol, data)

        except httpx.TimeoutException:
            logger.warning(f"{symbol} 行情检测超时，降级为 {self.FALLBACK_REGIME}")
            return RegimeResult(
                symbol=symbol,
                regime=self.FALLBACK_REGIME,
                confidence=0.5,
                reasoning="timeout fallback",
                source="fallback",
            )
        except Exception as e:
            logger.warning(f"{symbol} 行情检测失败: {e}", exc_info=True)
            return RegimeResult(
                symbol=symbol,
                regime=self.FALLBACK_REGIME,
                confidence=0.5,
                reasoning=f"error fallback: {e}",
                source="fallback",
            )

    def _build_prompt(
        self,
        symbol: str,
        bars_5d: List[Dict[str, Any]],
        bars_20d: List[Dict[str, Any]],
    ) -> str:
        """构造结构化提示词，要求 phi4 输出 JSON。

        Args:
            symbol: 品种代码
            bars_5d: 5日日线数据
            bars_20d: 20日日线数据

        Returns:
            prompt 字符串
        """
        # 计算简单统计指标
        stats_5d = self._calc_stats(bars_5d)
        stats_20d = self._calc_stats(bars_20d)

        prompt = f"""你是期货市场分析专家。请分析 {symbol} 的行情类型，输出 JSON 格式。

品种：{symbol}

近5日统计：
- 收盘价范围：{stats_5d['close_min']:.2f} ~ {stats_5d['close_max']:.2f}
- 波动率：{stats_5d['volatility']:.4f}
- 趋势方向：{stats_5d['trend_direction']}
- 涨跌幅：{stats_5d['return_pct']:.2f}%

近20日统计：
- 收盘价范围：{stats_20d['close_min']:.2f} ~ {stats_20d['close_max']:.2f}
- 波动率：{stats_20d['volatility']:.4f}
- 趋势方向：{stats_20d['trend_direction']}
- 涨跌幅：{stats_20d['return_pct']:.2f}%

请判断当前行情类型（五选一）：
1. trend（趋势）：明显的单边上涨或下跌，ATR 处于正常区间
2. oscillation（震荡）：价格在区间内反复波动，无明显方向
3. high_vol（高波动）：波动率显著高于正常水平，价格剧烈波动
4. compression（压缩）：ATR 持续收窄至近期 20% 分位以下，布林带收口，等待突破
5. event_driven（事件驱动）：连续涨跌停或成交量异常放大 >3σ，政策/黑天鹅驱动

输出 JSON 格式（不要有其他文字）：
{{
  "regime": "trend" | "oscillation" | "high_vol" | "compression" | "event_driven",
  "confidence": 0.0-1.0之间的置信度,
  "reasoning": "判断理由"
}}

JSON:"""

        return prompt

    def _calc_stats(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算 K 线统计指标。

        Args:
            bars: K 线数据列表

        Returns:
            统计指标字典
        """
        if not bars:
            return {
                "close_min": 0.0,
                "close_max": 0.0,
                "volatility": 0.0,
                "trend_direction": "unknown",
                "return_pct": 0.0,
            }

        closes = [b["close"] for b in bars]
        close_min = min(closes)
        close_max = max(closes)

        # 计算收益率序列
        returns = []
        for i in range(1, len(closes)):
            if closes[i - 1] > 0:
                ret = (closes[i] - closes[i - 1]) / closes[i - 1]
                returns.append(ret)

        # 波动率（收益率标准差）
        if returns:
            import numpy as np

            volatility = float(np.std(returns))
        else:
            volatility = 0.0

        # 趋势方向（首尾价格对比）
        if len(closes) >= 2:
            total_return = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0.0
            return_pct = total_return * 100

            if total_return > 0.02:
                trend_direction = "up"
            elif total_return < -0.02:
                trend_direction = "down"
            else:
                trend_direction = "flat"
        else:
            trend_direction = "unknown"
            return_pct = 0.0

        return {
            "close_min": close_min,
            "close_max": close_max,
            "volatility": volatility,
            "trend_direction": trend_direction,
            "return_pct": return_pct,
        }

    def _parse_response(
        self, symbol: str, response_data: Dict[str, Any]
    ) -> RegimeResult:
        """解析 phi4 返回的 JSON。

        Args:
            symbol: 品种代码
            response_data: Ollama API 返回数据

        Returns:
            RegimeResult
        """
        response_text = response_data.get("response", "")

        try:
            # 尝试直接解析
            result = json.loads(response_text)

            # 验证必需字段
            if "regime" not in result or "confidence" not in result:
                raise ValueError("缺少必需字段")

            # 验证 regime 值
            regime_str = result["regime"]
            if regime_str not in Regime.values():
                raise ValueError(f"无效的 regime 值: {regime_str}")

            regime = Regime(regime_str)
            confidence = float(result["confidence"])
            confidence = max(0.0, min(1.0, confidence))  # 限制范围
            reasoning = result.get("reasoning", "")

            return RegimeResult(
                symbol=symbol,
                regime=regime,
                confidence=confidence,
                reasoning=reasoning,
                source="phi4",
            )

        except json.JSONDecodeError:
            # 尝试提取 JSON 片段
            try:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_text = response_text[start:end]
                    result = json.loads(json_text)

                    regime = Regime(result["regime"])
                    confidence = max(0.0, min(1.0, float(result["confidence"])))
                    reasoning = result.get("reasoning", "")

                    return RegimeResult(
                        symbol=symbol,
                        regime=regime,
                        confidence=confidence,
                        reasoning=reasoning,
                        source="phi4",
                    )
            except Exception:
                pass

            logger.warning(f"无法解析 phi4 返回: {response_text[:100]}")

        except Exception as e:
            logger.warning(f"解析 phi4 返回失败: {e}")

        # 解析失败，降级
        return RegimeResult(
            symbol=symbol,
            regime=self.FALLBACK_REGIME,
            confidence=0.5,
            reasoning="parse error fallback",
            source="fallback",
        )
