"""LLM 计费 API — 为看板和手动查询提供接口。

GET  /api/v1/billing/hourly   — 当前小时统计
GET  /api/v1/billing/daily    — 今日累计统计
GET  /api/v1/billing/records  — 最近原始记录
POST /api/v1/billing/report   — 立即推送飞书报告
"""

import logging
from typing import Optional

from fastapi import APIRouter

from ...llm.billing import get_billing_tracker
from ...llm.billing_notifier import get_billing_notifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.get("/hourly")
async def billing_hourly():
    """获取当前小时计费汇总。"""
    return get_billing_tracker().get_hourly_summary()


@router.get("/daily")
async def billing_daily():
    """获取今日计费汇总（含预算进度）。"""
    return get_billing_tracker().get_daily_summary()


@router.get("/records")
async def billing_records(limit: int = 100):
    """获取最近 N 条原始计费记录。"""
    if limit > 1000:
        limit = 1000
    return get_billing_tracker().get_records_json(limit)


@router.post("/report")
async def billing_send_report():
    """立即推送当前计费报告到飞书。"""
    notifier = get_billing_notifier()
    if notifier is None:
        return {"sent": False, "error": "notifier not initialized"}
    success = await notifier.send_current_report()
    return {"sent": success}
