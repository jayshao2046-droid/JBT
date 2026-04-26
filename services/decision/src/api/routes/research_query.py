"""研报评级查询端点 — 策略引擎和门控主动拉取最新宏观分析结果

GET /api/v1/research/latest          — 所有类型最新评级
GET /api/v1/research/latest/{type}   — 指定类型最新评级
GET /api/v1/research/macro-summary   — 宏观分析摘要（策略沙箱专用）
GET /api/v1/research/history/{type}  — 指定类型最近 N 条评级
GET /api/v1/research/facts/latest    — researcher 三类事实总览
GET /api/v1/research/facts/latest/{group}   — researcher 单类事实最新快照
GET /api/v1/research/facts/history/{group}  — researcher 单类事实历史
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


@router.get("/facts/latest")
async def get_fact_overview(limit: Optional[int] = Query(5, ge=1, le=50)):
    """获取 researcher 三类事实总览。"""
    store = ResearchStore()
    return store.get_fact_overview(limit_per_group=limit)


@router.get("/facts/latest/{fact_group}")
async def get_fact_group_latest(fact_group: str, limit: Optional[int] = Query(5, ge=1, le=50)):
    """获取 researcher 单类事实最新快照。"""
    store = ResearchStore()
    return store.get_fact_group_snapshot(fact_group, limit=limit)


@router.get("/facts/history/{fact_group}")
async def get_fact_group_history(fact_group: str, limit: Optional[int] = Query(10, ge=1, le=50)):
    """获取 researcher 单类事实历史。"""
    store = ResearchStore()
    snapshot = store.get_fact_group_snapshot(fact_group, limit=limit)
    return {
        "available": snapshot.get("available", False),
        "fact_group": snapshot.get("fact_group", fact_group),
        "label": snapshot.get("label"),
        "primary_report_type": snapshot.get("primary_report_type"),
        "source_report_types": snapshot.get("source_report_types", []),
        "history": snapshot.get("history", []),
    }


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
