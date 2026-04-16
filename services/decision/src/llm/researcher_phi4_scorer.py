"""研究员报告 phi4 评级器 - 使用 phi4 模型对报告进行真实评级

职责：
1. 调用 phi4 模型评估报告质量
2. 评估报告对交易决策的价值
3. 返回评分和评级理由
"""
import logging
import json
from typing import Dict, Optional
from .client import OllamaClient

logger = logging.getLogger(__name__)


PHI4_SCORER_SYSTEM = """你是一个专业的量化交易研究员报告评级专家。

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
    """研究员报告 phi4 评级器"""

    def __init__(self, client: Optional[OllamaClient] = None, model: str = "phi4-reasoning:14b"):
        """初始化评级器

        Args:
            client: OllamaClient 实例
            model: phi4 模型名称
        """
        self.client = client or OllamaClient()
        self.model = model

    async def score_report(
        self,
        report: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """使用 phi4 评估报告

        Args:
            report: 报告字典
            context: 上下文信息（可包含 watched_symbols, current_positions 等）

        Returns:
            评级结果字典，包含 score, confidence, reasoning, key_insights, risk_alerts
        """
        try:
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

            # 格式化报告内容
            report_text = self._format_report(report)

            # 构建 prompt
            user_content = f"""请评估以下研究员报告：

【报告信息】
- 报告ID: {report.get('report_id')}
- 生成时间: {report.get('generated_at')}

【数据统计】
- 期货品种: {report.get('futures_summary', {}).get('symbols_covered', 0)} 个
- 股票数量: {report.get('stocks_summary', {}).get('symbols_covered', 0)} 个
- 新闻文章: {report.get('crawler_stats', {}).get('articles_processed', 0)} 篇

【市场概况】
期货: {report.get('futures_summary', {}).get('market_overview', '无')}
股票: {report.get('stocks_summary', {}).get('market_overview', '无')}

请给出评分、简短理由和改进建议。"""

            messages = [
                {"role": "system", "content": PHI4_SCORER_SYSTEM},
                {"role": "user", "content": user_content}
            ]

            # 调用 phi4
            result = await self.client.chat(self.model, messages)

            if "error" in result:
                logger.error(f"phi4 评级失败: {result['error']}")
                return self._fallback_score()

            # 解析 JSON 响应（支持中文字段）
            content = result.get("content", "")

            # 清理 phi4 的 <think> 标签
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            content = content.strip()

            try:
                score_result = json.loads(content)
                # 支持中文和英文字段名
                score = score_result.get("评分", score_result.get("score", 0.5))

                # 计算置信度
                confidence = self._calculate_confidence(score, report)

                return {
                    "score": score,
                    "confidence": confidence,
                    "reasoning": score_result.get("理由", score_result.get("reasoning", "")),
                    "improvements": score_result.get("改进建议", score_result.get("improvements", [])),
                    "model": result.get("model", self.model)
                }
            except json.JSONDecodeError:
                logger.warning(f"phi4 返回非 JSON 格式: {content}")
                # 尝试从文本中提取评分
                score = self._extract_score_from_text(content)
                confidence = self._calculate_confidence(score, report)

                return {
                    "score": score,
                    "confidence": confidence,
                    "reasoning": content,
                    "improvements": [],
                    "model": result.get("model", self.model)
                }

        except Exception as e:
            logger.error(f"phi4 评级异常: {e}")
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

    def _calculate_confidence(self, score: float, report: Dict) -> str:
        """计算置信度

        Args:
            score: phi4 评分 (0-100)
            report: 报告数据

        Returns:
            置信度等级: "high" / "medium" / "low"
        """
        # 基于数据完整性计算置信度
        futures_covered = report.get("futures_summary", {}).get("symbols_covered", 0)
        stocks_covered = report.get("stocks_summary", {}).get("symbols_covered", 0)
        news_count = len(report.get("crawler_stats", {}).get("news_items", []))

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
        """降级评分（当 phi4 不可用时）"""
        return {
            "score": 50,
            "confidence": "low",
            "reasoning": "phi4 评级服务不可用，使用默认评分",
            "key_insights": [],
            "risk_alerts": [],
            "model": "fallback"
        }
