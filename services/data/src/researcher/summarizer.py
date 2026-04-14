"""LLM 归纳 — qwen3 Ollama 调用封装"""

import httpx
from typing import Dict, Any, Optional, List
import json

from .config import ResearcherConfig
from .models import SymbolResearch


class Summarizer:
    """LLM 归纳器"""

    def __init__(self):
        self.ollama_url = ResearcherConfig.OLLAMA_URL
        self.model = ResearcherConfig.OLLAMA_MODEL
        self.temperature = ResearcherConfig.OLLAMA_TEMPERATURE
        self.num_ctx = ResearcherConfig.OLLAMA_NUM_CTX
        self.timeout = ResearcherConfig.OLLAMA_TIMEOUT

    def summarize_symbol(
        self,
        symbol: str,
        incremental_data: List[Dict[str, Any]],
        previous_summary: Optional[Dict[str, Any]] = None,
        news_items: Optional[List[str]] = None
    ) -> SymbolResearch:
        """
        归纳单个品种

        Args:
            symbol: 品种代码
            incremental_data: 增量数据
            previous_summary: 上期摘要（用于变化对比）
            news_items: 相关新闻

        Returns:
            SymbolResearch
        """
        prompt = self._build_prompt(symbol, incremental_data, previous_summary, news_items)

        try:
            response = self._call_ollama(prompt)
            return self._parse_response(symbol, response)
        except Exception as e:
            # 降级：返回"无法归纳"
            return SymbolResearch(
                symbol=symbol,
                trend="观望",
                confidence=0.0,
                key_factors=[f"归纳失败: {str(e)}"],
                overnight_context=None,
                news_highlights=news_items or [],
                position_change=None
            )

    def _build_prompt(
        self,
        symbol: str,
        incremental_data: List[Dict[str, Any]],
        previous_summary: Optional[Dict[str, Any]],
        news_items: Optional[List[str]]
    ) -> str:
        """构建 prompt"""
        prompt_parts = [
            f"# 品种研究任务：{symbol}\n",
            "## 当期增量数据\n",
        ]

        # 增量数据摘要
        if incremental_data:
            latest = incremental_data[-1]
            prompt_parts.append(f"- 最新价格: {latest.get('close', 'N/A')}\n")
            prompt_parts.append(f"- 成交量: {latest.get('volume', 'N/A')}\n")
            prompt_parts.append(f"- 数据条数: {len(incremental_data)}\n")
        else:
            prompt_parts.append("- 无新增数据\n")

        # 上期摘要（变化对比）
        if previous_summary and symbol in previous_summary.get("symbols", {}):
            prev = previous_summary["symbols"][symbol]
            prompt_parts.append("\n## 上期摘要\n")
            prompt_parts.append(f"- 趋势: {prev.get('trend', 'N/A')}\n")
            prompt_parts.append(f"- 信心度: {prev.get('confidence', 'N/A')}\n")
            prompt_parts.append(f"- 关键因素: {', '.join(prev.get('key_factors', []))}\n")

        # 相关新闻
        if news_items:
            prompt_parts.append("\n## 相关新闻\n")
            for item in news_items[:5]:  # 最多 5 条
                prompt_parts.append(f"- {item}\n")

        # 输出要求
        prompt_parts.append("\n## 输出要求\n")
        prompt_parts.append("## 输出格式要求\n")
        prompt_parts.append("先用 <think>...</think> 写完整推理过程（必须），再输出 JSON。\n")
        prompt_parts.append("推理链必须包含：数据趋势判断 → 关键驱动因素 → 风险点 → 结论信心校准。\n")
        prompt_parts.append("推理完成后，另起一行输出严格 JSON（不加 markdown 代码块）：\n")
        prompt_parts.append('{"trend": "偏多/偏空/震荡/观望", "confidence": 0.0~1.0, "key_factors": ["因素1", "因素2"], "overnight_context": "隔夜背景", "risk_note": "主要风险"}\n')

        return "".join(prompt_parts)

    def _call_ollama(self, prompt: str) -> str:
        """调用 Alienware Ollama"""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx
            }
        }

        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()

        result = resp.json()
        return result.get("response", "")

    def _parse_response(self, symbol: str, response: str) -> SymbolResearch:
        """解析 LLM 响应，保留 <think> 推理链，从 think 块之后提取 JSON"""
        try:
            # 提取 <think> 推理链（如有）
            think_content = None
            think_start = response.find("<think>")
            think_end = response.find("</think>")
            if think_start >= 0 and think_end > think_start:
                think_content = response[think_start + 7:think_end].strip()
                # JSON 只从 </think> 之后查找
                search_from = response[think_end + 8:]
            else:
                search_from = response

            # 从 think 后区域提取 JSON
            start = search_from.rfind("{")  # 取最后一个{，避免 think 内部 JSON 干扰
            end = search_from.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = search_from[start:end]
                data = json.loads(json_str)

                return SymbolResearch(
                    symbol=symbol,
                    trend=data.get("trend", "观望"),
                    confidence=float(data.get("confidence", 0.5)),
                    key_factors=data.get("key_factors", []),
                    overnight_context=data.get("overnight_context"),
                    risk_note=data.get("risk_note"),
                    news_highlights=[],
                    position_change=data.get("position_change"),
                    think_chain=think_content
                )
            else:
                raise ValueError("No JSON found in response")
        except Exception:
            # 解析失败，返回默认值
            return SymbolResearch(
                symbol=symbol,
                trend="观望",
                confidence=0.5,
                key_factors=["LLM 响应解析失败"],
                overnight_context=None,
                news_highlights=[],
                position_change=None
            )

    def summarize_market_overview(
        self,
        symbol_researches: List[SymbolResearch],
        asset_type: str
    ) -> str:
        """
        生成市场综述

        Args:
            symbol_researches: 品种研究列表
            asset_type: 资产类型（期货/股票）

        Returns:
            市场综述文本
        """
        if not symbol_researches:
            return f"{asset_type}市场无新增数据"

        # 统计趋势分布
        trend_counts = {}
        for sr in symbol_researches:
            trend_counts[sr.trend] = trend_counts.get(sr.trend, 0) + 1

        # 构建综述
        overview_parts = [
            f"{asset_type}市场共覆盖 {len(symbol_researches)} 个品种。",
            f"趋势分布：{', '.join([f'{k} {v}个' for k, v in trend_counts.items()])}。"
        ]

        # 高信心品种
        high_conf = [sr for sr in symbol_researches if sr.confidence >= 0.7]
        if high_conf:
            overview_parts.append(f"高信心品种（≥0.7）：{', '.join([sr.symbol for sr in high_conf])}。")

        return " ".join(overview_parts)
