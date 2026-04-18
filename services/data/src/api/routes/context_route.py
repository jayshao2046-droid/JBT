"""决策端上下文投喂路由 — GET /api/v1/context/daily + Mini 采集数据上下文端点"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

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
    from scheduler.preread_generator import PrereadGenerator

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


# ═══════════════════════════════════════════════════════════════
# Mini 采集数据上下文端点 — 供研究员从 Alienware 拉取
# 数据存储路径: {DATA_STORAGE_ROOT}/{symbol}/{data_type}/records.parquet
# ═══════════════════════════════════════════════════════════════

def _get_storage_root() -> str:
    return os.environ.get(
        "DATA_STORAGE_ROOT",
        str(Path(__file__).resolve().parents[4] / "runtime" / "data"),
    )


def _read_context_records(data_type: str, symbol: str, limit: int) -> list[dict[str, Any]]:
    """从 Parquet 存储读取上下文数据记录，解析 payload JSON 字段。"""
    try:
        from data.storage import HDF5Storage
        storage = HDF5Storage(base_dir=_get_storage_root())
        records = storage.read_records(
            data_type, symbol,
            sort_by="timestamp", ascending=False,
            limit=limit,
        )
        results = []
        for rec in records:
            payload = rec.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            entry: dict[str, Any] = {
                "indicator": rec.get("symbol_or_indicator", ""),
                "timestamp": rec.get("timestamp", ""),
            }
            if isinstance(payload, dict):
                entry.update(payload)
            results.append(entry)
        return results
    except Exception as exc:
        logger.warning("context read failed: data_type=%s symbol=%s err=%s", data_type, symbol, exc)
        return []


@router.get("/macro")
def get_macro_context(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """获取最近 N 天宏观数据（CPI/PPI/PMI/GDP 等，来自 Mini AkShare 采集）"""
    records = _read_context_records("macro", "macro_global", days * 20)
    return {"data_type": "macro", "records": records, "count": len(records)}


@router.get("/volatility")
def get_volatility_context(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """获取最近 N 天波动率指数（QVIX/CBOE VIX/VXN，来自 Mini 采集）"""
    records = _read_context_records("volatility", "volatility_index", days * 5)
    return {"data_type": "volatility", "records": records, "count": len(records)}


@router.get("/shipping")
def get_shipping_context(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """获取最近 N 天航运指数（BDI/BCI/BPI/BCTI，来自 Mini AkShare 采集）"""
    records = _read_context_records("shipping", "shipping", days * 5)
    return {"data_type": "shipping", "records": records, "count": len(records)}


@router.get("/sentiment")
def get_sentiment_context(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """获取最近 N 天市场情绪（融资融券/北向资金，来自 Mini AkShare 采集）"""
    records = _read_context_records("sentiment", "sentiment", days * 10)
    return {"data_type": "sentiment", "records": records, "count": len(records)}


@router.get("/rss")
def get_rss_context(hours: int = Query(24, ge=1, le=168)) -> dict[str, Any]:
    """获取最近 N 小时 RSS 新闻存档（来自 Mini RSS 采集）"""
    limit = (hours // 24 + 1) * 50
    records = _read_context_records("rss", "news_rss", limit)
    return {"data_type": "rss", "records": records, "count": len(records)}
