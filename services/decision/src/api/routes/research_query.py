"""研报评级查询端点 — 策略引擎和门控主动拉取最新宏观分析结果

GET /api/v1/research/latest          — 所有类型最新评级
GET /api/v1/research/latest/{type}   — 指定类型最新评级
GET /api/v1/research/macro-summary   — 宏观分析摘要（策略沙箱专用）
GET /api/v1/research/history/{type}  — 指定类型最近 N 条评级
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from ...research.research_store import ResearchStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["research-query"])


@router.get("/latest")
async def get_all_latest():
    """获取所有类型最新评级结果"""
    store = ResearchStore()
    return store.get_all_latest()


@router.get("/latest/{report_type}")
async def get_latest_by_type(report_type: str):
    """获取指定类型最新评级结果"""
    store = ResearchStore()
    result = store.get_latest(report_type)
    if result is None:
        return {"available": False, "report_type": report_type}
    return result


@router.get("/macro-summary")
async def get_macro_summary():
    """获取最新宏观分析摘要（策略沙箱和门控专用）"""
    store = ResearchStore()
    return store.get_macro_summary()


@router.get("/history/{report_type}")
async def get_history(report_type: str, limit: Optional[int] = Query(10, ge=1, le=50)):
    """获取指定类型最近 N 条评级结果"""
    store = ResearchStore()
    return store.get_history(report_type, limit=limit)
