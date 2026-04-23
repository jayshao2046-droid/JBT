"""研究员报告评级器 - 使用 LLM 模型对报告进行真实评级

职责：
1. 调用 LLM 模型（默认 qwen3:14b）评估报告质量
2. 评估报告对交易决策的价值
3. 返回评分和评级理由
4. 标记报告为已读

注：原使用 phi4-reasoning:14b，现切换到 qwen3:14b（用户测试反馈 qwen3 更合适）
"""
import logging
import json
import httpx
from typing import Dict, Optional, Any
from .client import OllamaClient, HybridClient
from .openai_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


RESEARCHER_SCORER_SYSTEM = """你是一个专业的量化交易研究员报告评级专家。

你的任务是评估研究员报告对交易决策的价值，并给出 0-100 分的评分。

评分标准：
1. 数据完整性（50%）- 是否包含期货、股票、新闻数据
2. 信息质量（30%）- 数据是否真实、分析是否有深度
3. 时效性（20%）- 报告是否及时、信息是否新鲜

请以 JSON 格式返回评级结果：
{
  "score": 85,
  "reasoning": "简短评价（1-2句话）",
  "improvements": ["改进建议1", "改进建议2"]
}

评分参考：
- 80-100分: 优秀，数据完整且有价值
- 60-80分: 良好，数据基本完整
- 40-60分: 一般，数据不完整
- 20-40分: 较差，缺少关键数据
- 0-20分: 很差，几乎无数据

注意：全部使用中文回复，不要出现英文。
"""


class ResearcherPhi4Scorer:
    """研究员报告评级器"""

    def __init__(
        self,
        client=None,
        model: str = "qwen3:14b-q4_K_M",
        researcher_api_url: str = "http://192.168.31.187:8199"
    ):
        """初始化评级器

        Args:
            client: OllamaClient 或 OpenAICompatibleClient 实例
            model: 评级模型名称
            researcher_api_url: Alienware 研究员服务 API 地址
        """
        import os
        # 评分走 HybridClient：Ollama 优先，超时降级在线
        llm_provider = os.getenv("PIPELINE_LLM_PROVIDER", "hybrid").lower()
        if client is not None:
            self.client = client
        elif llm_provider == "online":
            self.client = OpenAICompatibleClient(component="phi4_scorer")
        elif llm_provider == "ollama":
            self.client = OllamaClient(component="phi4_scorer")
        else:
            self.client = HybridClient(component="phi4_scorer")
        self.model = os.getenv("ONLINE_AUDITOR_MODEL", "gpt-5.4") if llm_provider == "online" else model
        self.researcher_api_url = researcher_api_url

    async def score_report_detail(
        self,
        report: Dict,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """返回完整评分详情（含看到内容和评分理由）。"""
        try:
            logger.info(f"[SCORER] 开始评级报告: {report.get('report_id')}")

            result = await self._score_report_full(report, context)
            score = float(result.get("score", 50.0))

            report_id = report.get("report_id")
            if report_id:
                await self._mark_report_read(
                    report_id,
                    score=score,
                    reasoning=result.get("reasoning", ""),
                    model=result.get("model", self.model),
                )

            logger.info(
                f"[SCORER] 评级完成: {report_id}, "
                f"score={score:.2f}, model={result.get('model')}"
            )
            return result
        except Exception as e:
            logger.error(f"[SCORER] 评级异常: {e}", exc_info=True)
            return self._fallback_score()

    async def score_report(
        self,
        report: Dict,
        context: Optional[Dict] = None
    ) -> float:
        """使用 LLM 评估报告

        Args:
            report: 报告字典
            context: 上下文信息（可包含 watched_symbols, current_positions 等）

        Returns:
            评分（0-100）
        """
        result = await self.score_report_detail(report, context)
        return float(result.get("score", 50.0))

    def _normalize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """统一 data/decision 两侧结构，供评分器使用。"""
        report_type = str(report.get("report_type") or "unknown").lower()
        data = report.get("data") or {}

        futures_symbols = 0
        stocks_symbols = 0
        news_items = []
        urgent_items = []

        futures_summary = report.get("futures_summary") or {}
        stocks_summary = report.get("stocks_summary") or {}
        crawler_stats = report.get("crawler_stats") or {}

        if futures_summary:
            futures_symbols = int(futures_summary.get("symbols_covered") or 0)
        elif report_type == "futures":
            futures_symbols = int(data.get("total_symbols") or len(data.get("reports") or []))

        if stocks_summary:
            stocks_symbols = int(stocks_summary.get("symbols_covered") or 0)
        elif report_type == "stocks":
            stocks_symbols = int(data.get("total_symbols") or len(data.get("reports") or []))

        if crawler_stats.get("news_items"):
            news_items = crawler_stats.get("news_items") or []
        elif report_type == "news":
            news_items = data.get("items") or []

        if report_type == "news":
            urgent_items = data.get("urgent_items") or [x for x in news_items if x.get("is_urgent")]

        sample_titles = []
        for item in news_items[:3]:
            title = str(item.get("title") or "").strip()
            if title:
                sample_titles.append(title)

        observed_parts = [
            f"类型={report_type}",
            f"期货品种={futures_symbols}",
            f"股票数量={stocks_symbols}",
            f"新闻条数={len(news_items)}",
            f"紧急新闻={len(urgent_items)}",
        ]
        if sample_titles:
            observed_parts.append("样本标题=" + " | ".join(sample_titles))

        return {
            "report_type": report_type,
            "futures_symbols": futures_symbols,
            "stocks_symbols": stocks_symbols,
            "news_items": news_items,
            "urgent_items": urgent_items,
            "sample_titles": sample_titles,
            "observed_content": "；".join(observed_parts),
        }

    async def _score_report_full(
        self,
        report: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """使用 LLM 评估报告（完整结果）

        Args:
            report: 报告字典
            context: 上下文信息（可包含 watched_symbols, current_positions 等）

        Returns:
            评级结果字典，包含 score, confidence, reasoning, improvements
        """
        try:
            normalized = self._normalize_report(report)
            report_type = normalized["report_type"]

            # 提取上下文信息
            watched_symbols = context.get("watched_symbols", set()) if context else set()
            current_positions = context.get("current_positions", set()) if context else set()

            # 构建评级上下文
            context_parts = []

            # 添加持仓和关注信息
            if current_positions:
                context_parts.append(f"当前持仓: {', '.join(current_positions)}")
            if watched_symbols:
                context_parts.append(f"关注品种: {', '.join(watched_symbols)}")

            context_text = "\n".join(context_parts) if context_parts else "无特定持仓和关注品种"

            if report_type == "news":
                scoring_rule = "新闻报告评分：信息覆盖(40%) + 关键信息密度(40%) + 时效性(20%)。新闻单类报告不因缺少期货/股票而扣分。"
            elif report_type == "futures":
                scoring_rule = "期货报告评分：品种覆盖(40%) + 趋势/结构分析质量(40%) + 时效性(20%)。期货单类报告不因缺少股票/新闻而扣分。"
            elif report_type == "stocks":
                scoring_rule = "股票报告评分：覆盖度(40%) + 行业/轮动分析质量(40%) + 时效性(20%)。股票单类报告不因缺少期货/新闻而扣分。"
            elif report_type == "macro":
                scoring_rule = "宏观报告评分：数据覆盖广度(30%) + 趋势判断逻辑(40%) + 风险提示质量(30%)。需包含宏观趋势/波动率/CFTC持仓/外汇信号至少2项。"
            else:
                scoring_rule = "综合报告评分：完整性(40%) + 信息质量(40%) + 时效性(20%)。"

            # 构建 prompt
            user_content = f"""请评估以下研究员报告：

【报告信息】
- 报告ID: {report.get('report_id')}
- 报告类型: {report_type}
- 生成时间: {report.get('generated_at')}

【评分口径】
{scoring_rule}

【可见内容摘要】
{normalized['observed_content']}

请给出评分、简短理由和改进建议。"""

            messages = [
                {"role": "system", "content": RESEARCHER_SCORER_SYSTEM},
                {"role": "user", "content": user_content}
            ]

            # 调用 LLM 模型
            result = await self.client.chat(self.model, messages)

            if "error" in result:
                logger.error(f"LLM 评级失败: {result['error']}")
                return self._fallback_score()

            # 解析 JSON 响应（支持中文字段）
            content = result.get("content", "")

            # 清理可能的 <think> 标签（phi4 特有，qwen3 通常不会有）
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            content = content.strip()

            try:
                score_result = json.loads(content)
                # 支持中文和英文字段名
                raw_score = score_result.get("评分", score_result.get("score", 50.0))
                try:
                    score = float(raw_score)
                except Exception:
                    score = 50.0
                # 兼容 0-1 归一化评分
                if 0.0 <= score <= 1.0:
                    score = score * 100.0
                score = max(0.0, min(100.0, score))

                # 计算置信度
                confidence = self._calculate_confidence(score, normalized)

                return {
                    "score": score,
                    "confidence": confidence,
                    "reasoning": score_result.get("理由", score_result.get("reasoning", "")),
                    "improvements": score_result.get("改进建议", score_result.get("improvements", [])),
                    "observed_content": normalized["observed_content"],
                    "model": result.get("model", self.model)
                }
            except json.JSONDecodeError:
                logger.warning(f"LLM 返回非 JSON 格式: {content}")
                # 尝试从文本中提取评分
                score = self._extract_score_from_text(content)
                confidence = self._calculate_confidence(score, normalized)

                return {
                    "score": score,
                    "confidence": confidence,
                    "reasoning": content,
                    "improvements": [],
                    "observed_content": normalized["observed_content"],
                    "model": result.get("model", self.model)
                }

        except Exception as e:
            logger.error(f"LLM 评级异常: {e}")
            return self._fallback_score()

    def _format_report(self, report: Dict) -> str:
        """格式化报告内容"""
        lines = []

        # 基本信息
        report_id = report.get("report_id", "")
        generated_at = report.get("generated_at", "")
        lines.append(f"报告ID: {report_id}")
        lines.append(f"生成时间: {generated_at}")
        lines.append("")

        # 期货市场
        futures_summary = report.get("futures_summary", {})
        if futures_summary.get("symbols_covered", 0) > 0:
            lines.append("期货市场:")
            lines.append(f"  覆盖品种: {futures_summary.get('symbols_covered', 0)}")
            lines.append(f"  市场概况: {futures_summary.get('market_overview', '')}")
            lines.append("")

        # 股票市场
        stocks_summary = report.get("stocks_summary", {})
        if stocks_summary.get("symbols_covered", 0) > 0:
            lines.append("股票市场:")
            lines.append(f"  覆盖股票: {stocks_summary.get('symbols_covered', 0)}")
            lines.append(f"  市场概况: {stocks_summary.get('market_overview', '')}")

            sector_rotation = stocks_summary.get("sector_rotation", {})
            if sector_rotation:
                lines.append("  板块轮动:")
                for category, sectors in sector_rotation.items():
                    if sectors:
                        lines.append(f"    {category}: {', '.join(sectors)}")
            lines.append("")

        # 爬虫新闻
        crawler_stats = report.get("crawler_stats", {})
        news_items = crawler_stats.get("news_items", [])
        if news_items:
            lines.append("重要新闻:")
            for i, item in enumerate(news_items[:5], 1):
                title = item.get("title", "")
                source = item.get("source", "")
                lines.append(f"  {i}. [{source}] {title}")
            lines.append("")

        return "\n".join(lines)

    def _extract_score_from_text(self, text: str) -> float:
        """从文本中提取评分"""
        import re
        # 尝试匹配 0-100 的整数评分
        match = re.search(r'\b(\d{1,3})\b', text)
        if match:
            try:
                score = int(match.group())
                if 0 <= score <= 100:
                    return float(score)
            except ValueError:
                pass
        return 50.0

    def _calculate_confidence(self, score: float, normalized: Dict[str, Any]) -> str:
        """计算置信度

        Args:
            score: phi4 评分 (0-100)
            report: 报告数据

        Returns:
            置信度等级: "high" / "medium" / "low"
        """
        # 基于数据完整性计算置信度
        futures_covered = int(normalized.get("futures_symbols", 0))
        stocks_covered = int(normalized.get("stocks_symbols", 0))
        news_count = len(normalized.get("news_items", []))

        # 数据完整性评分
        data_completeness = 0
        if futures_covered > 0:
            data_completeness += 0.3
        if stocks_covered > 0:
            data_completeness += 0.3
        if news_count > 0:
            data_completeness += 0.4

        # 综合评估置信度
        if score >= 70 and data_completeness >= 0.6:
            return "high"
        elif score >= 50 and data_completeness >= 0.3:
            return "medium"
        else:
            return "low"

    def _fallback_score(self) -> Dict:
        """降级评分（当 LLM 不可用时）"""
        return {
            "score": 50,
            "confidence": "low",
            "reasoning": "LLM 评级服务不可用，使用默认评分",
            "improvements": [],
            "observed_content": "评分服务降级，未获取到完整可见内容摘要",
            "model": "fallback"
        }

    async def _mark_report_read(
        self,
        report_id: str,
        score: float,
        reasoning: str,
        model: str
    ) -> bool:
        """
        标记报告为已读

        Args:
            report_id: 报告ID
            score: 评分
            reasoning: 评级理由
            model: 使用的模型

        Returns:
            True 表示标记成功
        """
        try:
            url = f"{self.researcher_api_url}/reports/{report_id}/mark_read"
            payload = {
                "score": score,
                "reasoning": reasoning,
                "model": model
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                logger.info(f"[SCORER] 标记已读成功: {report_id}")
                return True

        except httpx.HTTPError as e:
            logger.warning(f"[SCORER] 标记已读失败: {report_id}, {e}")
            return False
        except Exception as e:
            logger.error(f"[SCORER] 标记已读异常: {report_id}, {e}", exc_info=True)
            return False
