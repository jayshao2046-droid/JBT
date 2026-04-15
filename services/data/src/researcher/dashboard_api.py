"""Dashboard API - 提供前台控制接口

职责：
1. 提供研究员状态查询
2. 提供数据源开关控制
3. 提供报告查询
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/researcher/dashboard", tags=["dashboard"])


@router.get("/status")
async def get_status():
    """获取研究员运行状态"""
    return {
        "status": "running",
        "processes": {
            "kline_monitor": "running",
            "news_crawler": "running",
            "fundamental_crawler": "running",
            "llm_analyzer": "running",
            "report_generator": "running"
        },
        "uptime": "24h"
    }


@router.get("/sources")
async def get_sources():
    """获取数据源列表"""
    return {
        "news_sources": [
            {"name": "新浪财经", "enabled": True, "status": "ok"},
            {"name": "东方财富", "enabled": True, "status": "ok"}
        ],
        "fundamental_sources": [
            {"name": "我的钢铁网", "enabled": True, "status": "ok"}
        ]
    }


@router.post("/sources/{source_name}/toggle")
async def toggle_source(source_name: str, enabled: bool):
    """开关数据源"""
    logger.info(f"Toggle source {source_name}: {enabled}")
    return {"source": source_name, "enabled": enabled}


@router.get("/reports")
async def get_reports(limit: int = 10):
    """获取最近的报告列表"""
    return {
        "reports": [],
        "total": 0
    }
