"""研究员报告评级端点 - 接收 Alienware 研究员推送并触发 LLM 评级

使用 qwen3:14b 模型进行报告评级（2026-04-17 切换，原为 qwen3:14b）
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...llm.researcher_qwen3_scorer import ResearcherPhi4Scorer
from ...notifier.feishu import FeishuNotifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["researcher"])


class ReportBatchRequest(BaseModel):
    """报告批次请求"""
    batch_id: str
    date: str
    hour: int
    generated_at: str
    futures_report: Dict[str, Any] | None = None
    stocks_report: Dict[str, Any] | None = None
    news_report: Dict[str, Any] | None = None
    rss_report: Dict[str, Any] | None = None
    sentiment_report: Dict[str, Any] | None = None
    total_reports: int = 0
    elapsed_seconds: float = 0.0


@router.post("/evaluate")
async def evaluate_researcher_reports(batch: ReportBatchRequest):
    """
    接收研究员报告批次并触发 qwen3 评级

    Args:
        batch: 报告批次

    Returns:
        评级结果
    """
    try:
        logger.info(f"收到研究员报告批次: {batch.batch_id}, 共 {batch.total_reports} 份报告")

        # 初始化评级器（使用 qwen3:14b）
        scorer = ResearcherPhi4Scorer()
        feishu = FeishuNotifier()

        results = []

        # 评级期货报告
        if batch.futures_report:
            logger.info(f"评级期货报告: {batch.futures_report.get('report_id')}")
            score = await scorer.score_report(batch.futures_report)
            results.append({
                "report_type": "futures",
                "report_id": batch.futures_report.get("report_id"),
                "score": score,
                "confidence": batch.futures_report.get("confidence", 0.0)
            })

            # 发送飞书通知
            await feishu.send_researcher_score(
                report_type="期货",
                report_id=batch.futures_report.get("report_id"),
                score=score,
                date=batch.date,
                hour=batch.hour
            )

        # 评级股票报告
        if batch.stocks_report:
            logger.info(f"评级股票报告: {batch.stocks_report.get('report_id')}")
            score = await scorer.score_report(batch.stocks_report)
            results.append({
                "report_type": "stocks",
                "report_id": batch.stocks_report.get("report_id"),
                "score": score,
                "confidence": batch.stocks_report.get("confidence", 0.0)
            })

            # 发送飞书通知
            await feishu.send_researcher_score(
                report_type="股票",
                report_id=batch.stocks_report.get("report_id"),
                score=score,
                date=batch.date,
                hour=batch.hour
            )

        # 评级新闻报告
        if batch.news_report:
            logger.info(f"评级新闻报告: {batch.news_report.get('report_id')}")
            score = await scorer.score_report(batch.news_report)
            results.append({
                "report_type": "news",
                "report_id": batch.news_report.get("report_id"),
                "score": score,
                "confidence": batch.news_report.get("confidence", 0.0)
            })

            # 发送飞书通知
            await feishu.send_researcher_score(
                report_type="新闻",
                report_id=batch.news_report.get("report_id"),
                score=score,
                date=batch.date,
                hour=batch.hour
            )

        logger.info(f"完成 qwen3 评级: {batch.batch_id}, 评级 {len(results)} 份报告")

        return {
            "success": True,
            "batch_id": batch.batch_id,
            "evaluated_count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"评级失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"评级失败: {str(e)}")
