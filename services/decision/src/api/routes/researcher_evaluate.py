"""研究员报告评级端点 - 接收 Alienware 研究员推送并触发 LLM 评级

使用 qwen3:14b 模型进行报告评级（2026-04-17 切换，原为 qwen3:14b）
"""

import logging
import asyncio
import os
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...llm.researcher_qwen3_scorer import ResearcherPhi4Scorer
from ...notifier.feishu import FeishuNotifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["researcher"])

_DEDUP_SECONDS = int(os.getenv("RESEARCHER_SCORE_DEDUP_SECONDS", "900"))
_report_dedup_cache: dict[str, float] = {}
_report_dedup_lock = asyncio.Lock()


async def _is_duplicate_report(report_type: str, report_id: str) -> bool:
    """同 report_type+report_id 在去重窗口内只处理一次。"""
    if not report_id:
        return False

    key = f"{report_type}:{report_id}"
    now = time.time()

    async with _report_dedup_lock:
        # 清理过期键
        expired = [k for k, ts in _report_dedup_cache.items() if now - ts > _DEDUP_SECONDS]
        for k in expired:
            _report_dedup_cache.pop(k, None)

        last_ts = _report_dedup_cache.get(key)
        if last_ts and now - last_ts <= _DEDUP_SECONDS:
            return True

        _report_dedup_cache[key] = now
        return False


class ReportBatchRequest(BaseModel):
    """报告批次请求"""
    batch_id: str
    date: str
    hour: int
    generated_at: str
    futures_report: Dict[str, Any] | None = None
    stocks_report: Dict[str, Any] | None = None
    news_report: Dict[str, Any] | None = None
    macro_report: Dict[str, Any] | None = None
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

        async def _evaluate_and_notify(report_kind: str, report_label: str, report_obj: Dict[str, Any]):
            report_id = report_obj.get("report_id")

            if await _is_duplicate_report(report_kind, report_id):
                logger.info("跳过重复评级: type=%s report_id=%s", report_kind, report_id)
                results.append({
                    "report_type": report_kind,
                    "report_id": report_id,
                    "status": "duplicate_skipped",
                })
                return

            score_result = await scorer.score_report_detail(report_obj)
            score = float(score_result.get("score", 50.0))
            reasoning = score_result.get("reasoning", "")
            observed_content = score_result.get("observed_content", "")

            results.append({
                "report_type": report_kind,
                "report_id": report_id,
                "score": score,
                "confidence": score_result.get("confidence", "low"),
                "reasoning": reasoning,
                "observed_content": observed_content,
            })

            await feishu.send_researcher_score(
                report_type=report_label,
                report_id=report_id,
                score=score,
                date=batch.date,
                hour=batch.hour,
                reasoning=reasoning,
                seen_content=observed_content,
            )

        # 评级期货报告
        if batch.futures_report:
            logger.info(f"评级期货报告: {batch.futures_report.get('report_id')}")
            await _evaluate_and_notify("futures", "期货", batch.futures_report)

        # 评级股票报告
        if batch.stocks_report:
            logger.info(f"评级股票报告: {batch.stocks_report.get('report_id')}")
            await _evaluate_and_notify("stocks", "股票", batch.stocks_report)

        # 评级新闻报告
        if batch.news_report:
            logger.info(f"评级新闻报告: {batch.news_report.get('report_id')}")
            await _evaluate_and_notify("news", "新闻", batch.news_report)

        # 评级宏观上下文报告（来自 Mini 全量采集数据的 LLM 综合分析）
        if batch.macro_report:
            logger.info(f"评级宏观报告: {batch.macro_report.get('report_id')}")
            await _evaluate_and_notify("macro", "宏观", batch.macro_report)

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
