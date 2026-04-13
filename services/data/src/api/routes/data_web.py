"""数据看板专用路由"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..data.progress_tracker import ProgressTracker
from ..data.validator import DataSourceValidator
from ..stats.health import DataSourceHealthCalculator
from ..stats.quality import DataQualityCalculator

router = APIRouter(prefix="/api/v1/data", tags=["data_web"])

# 全局实例
_progress_tracker = ProgressTracker()
_validator = DataSourceValidator()
_quality_calculator = DataQualityCalculator()
_health_calculator = DataSourceHealthCalculator()


@router.get("/collection/history")
def get_collection_history(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
) -> dict[str, Any]:
    """获取数据采集历史记录

    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        source: 数据源过滤

    Returns:
        采集历史记录列表
    """
    # 模拟历史记录（实际应该从数据库查询）
    history = [
        {
            "collection_id": "col-001",
            "source": "futures_minute",
            "start_time": "2026-04-13T09:00:00",
            "end_time": "2026-04-13T09:05:00",
            "status": "success",
            "records_count": 1500,
            "duration": 300,
        },
        {
            "collection_id": "col-002",
            "source": "stock_minute",
            "start_time": "2026-04-13T09:30:00",
            "end_time": "2026-04-13T09:35:00",
            "status": "success",
            "records_count": 3000,
            "duration": 280,
        },
        {
            "collection_id": "col-003",
            "source": "news_rss",
            "start_time": "2026-04-13T10:00:00",
            "end_time": "2026-04-13T10:02:00",
            "status": "failed",
            "records_count": 0,
            "duration": 120,
            "error": "网络超时",
        },
    ]

    # 应用过滤
    if source:
        history = [h for h in history if h["source"] == source]

    return {
        "total": len(history),
        "history": history,
    }


@router.post("/source/validate")
def validate_source(
    source_type: str = Query(...),
    config: dict[str, Any] = ...,
) -> dict[str, Any]:
    """验证数据源配置

    Args:
        source_type: 数据源类型
        config: 配置字典

    Returns:
        验证结果
    """
    # 验证配置完整性
    config_result = _validator.validate_config(source_type, config)
    if not config_result["ok"]:
        return {
            "ok": False,
            "validation": config_result,
            "connection": None,
            "permissions": None,
        }

    # 验证连接
    connection_result = _validator.validate_connection(source_type, config)

    # 验证权限
    permissions_result = _validator.validate_permissions(source_type, config)

    return {
        "ok": connection_result["ok"] and permissions_result["ok"],
        "validation": config_result,
        "connection": connection_result,
        "permissions": permissions_result,
    }


@router.get("/collection/progress/{collection_id}/stream")
async def stream_collection_progress(collection_id: str) -> StreamingResponse:
    """流式推送采集进度（SSE）

    Args:
        collection_id: 采集任务 ID

    Returns:
        SSE 流
    """
    async def event_generator():
        async for progress in _progress_tracker.stream_progress(collection_id):
            # SSE 格式
            yield f"data: {progress}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/collection/{collection_id}/quality")
def get_collection_quality(collection_id: str) -> dict[str, Any]:
    """获取采集任务的数据质量指标

    Args:
        collection_id: 采集任务 ID

    Returns:
        数据质量指标
    """
    # 模拟采集记录（实际应该从数据库查询）
    collections = [
        {
            "collection_id": collection_id,
            "expected_count": 1000,
            "actual_count": 980,
            "scheduled_time": 1713000000,
            "actual_time": 1713000120,
            "delay_threshold": 300,
            "validation_errors": 0,
            "schema_violations": 0,
            "status": "success",
            "start_time": 1713000000,
            "end_time": 1713000120,
        }
    ]

    metrics = _quality_calculator.calculate_all_metrics(collections)

    return {
        "collection_id": collection_id,
        "metrics": metrics,
    }


@router.get("/source/{source_id}/health")
def get_source_health(source_id: str) -> dict[str, Any]:
    """获取数据源健康指标

    Args:
        source_id: 数据源 ID

    Returns:
        数据源健康指标
    """
    # 模拟数据源记录（实际应该从数据库查询）
    source_records = [
        {
            "source_id": source_id,
            "status": "available",
            "response_time": 150,
            "last_update_time": 1713000000,
            "freshness_threshold": 24,
            "expected_symbols": 100,
            "actual_symbols": 98,
        },
        {
            "source_id": source_id,
            "status": "available",
            "response_time": 180,
            "last_update_time": 1713003600,
            "freshness_threshold": 24,
            "expected_symbols": 100,
            "actual_symbols": 99,
        },
    ]

    metrics = _health_calculator.calculate_all_metrics(source_records)

    return {
        "source_id": source_id,
        "metrics": metrics,
    }


@router.post("/collection/batch")
def create_batch_collection(
    sources: list[str] = ...,
    param_grid: Optional[dict[str, list[Any]]] = None,
) -> dict[str, Any]:
    """创建批量采集任务

    Args:
        sources: 数据源列表
        param_grid: 参数网格（可选）

    Returns:
        批量任务信息
    """
    if not sources:
        raise HTTPException(status_code=422, detail="sources 不能为空")

    # 生成批量任务
    tasks = []
    for source in sources:
        task = {
            "task_id": f"batch-{source}-{len(tasks)}",
            "source": source,
            "status": "pending",
            "params": param_grid or {},
        }
        tasks.append(task)

    return {
        "batch_id": "batch-001",
        "total_tasks": len(tasks),
        "tasks": tasks,
    }
