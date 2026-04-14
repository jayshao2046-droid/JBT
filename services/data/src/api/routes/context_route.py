"""决策端上下文投喂路由 — GET /api/v1/context/daily"""

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/context", tags=["context"])

CN_TZ = timezone(timedelta(hours=8))


@router.get("/daily")
def get_daily_context(date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今日")) -> dict[str, Any]:
    """获取指定日期的四角色预读摘要。

    Args:
        date: 日期字符串 YYYY-MM-DD，默认今日

    Returns:
        {
            "researcher_context": {...},
            "l1_briefing": {...},
            "l2_audit_context": {...},
            "analyst_dataset": {...},
            "ready_flag": bool,
            "generated_at": str,
            "errors": [...]
        }

    Raises:
        HTTPException: 404 摘要文件不存在
        HTTPException: 500 摘要加载失败
    """
    from src.scheduler.preread_generator import PrereadGenerator

    date_str = date or datetime.now(CN_TZ).strftime("%Y-%m-%d")
    storage_root = os.environ.get(
        "DATA_STORAGE_ROOT",
        str(Path(__file__).resolve().parents[4] / "runtime" / "data"),
    )

    generator = PrereadGenerator(storage_root=storage_root)
    snapshot = generator.load_snapshot(date_str=date_str)

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=f"预读摘要不存在: date={date_str}",
        )

    return snapshot
