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


@router.get("/cftc")
def get_cftc_context(days: int = Query(14, ge=1, le=60)) -> dict[str, Any]:
    """CFTC 持仓周报（来自 Mini 采集）"""
    records = _read_context_records("cftc", "cftc", days * 5)
    return {"data_type": "cftc", "records": records, "count": len(records)}


@router.get("/forex")
def get_forex_context(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """外汇数据（USD/CNY、USDX 等，来自 Mini 采集）"""
    records = _read_context_records("forex", "forex", days * 5)
    return {"data_type": "forex", "records": records, "count": len(records)}


@router.get("/news_api")
def get_news_api_context(days: int = Query(3, ge=1, le=14)) -> dict[str, Any]:
    """新闻 API 采集数据（来自 Mini）"""
    records = _read_context_records("news_api", "news_api", days * 20)
    return {"data_type": "news_api", "records": records, "count": len(records)}


@router.get("/weather")
def get_weather_context(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """主产区天气数据（来自 Mini 采集）"""
    records = _read_context_records("weather", "weather", days * 5)
    return {"data_type": "weather", "records": records, "count": len(records)}


@router.get("/options")
def get_options_context(days: int = Query(5, ge=1, le=30)) -> dict[str, Any]:
    """期权数据（PCR / 隐含波动率等，来自 Mini 采集）"""
    records = _read_context_records("options", "options", days * 10)
    return {"data_type": "options", "records": records, "count": len(records)}


@router.get("/position")
def get_position_context(days: int = Query(5, ge=1, le=30)) -> dict[str, Any]:
    """期货持仓日报（来自 Mini 采集）"""
    records = _read_context_records("position", "position_daily", days * 10)
    return {"data_type": "position", "records": records, "count": len(records)}


# ─── 期货分钟K专项端点（三级路径，多月分文件，按品种聚合）────────────────────

def _read_futures_minute_summary(hours: int) -> list[dict[str, Any]]:
    """读取所有期货品种近 N 小时分钟K聚合摘要。

    路径结构：{root}/futures_minute/1m/{symbol}/{yyyymm}.parquet
    每个品种取最新月份文件，过滤到近 hours 小时，计算涨跌幅/高低点/成交量。
    """
    try:
        import pandas as pd
    except ImportError:
        logger.warning("pandas not available, cannot read futures_minute")
        return []

    root = _get_storage_root()
    base = Path(root) / "futures_minute" / "1m"
    if not base.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=hours)
    results: list[dict[str, Any]] = []

    for sym_dir in sorted(base.iterdir()):
        if not sym_dir.is_dir():
            continue
        symbol = sym_dir.name  # e.g. KQ_m_SHFE_rb
        parquets = sorted(sym_dir.glob("*.parquet"))
        if not parquets:
            continue
        # 从最新月份往前找，直到找到近期数据
        for parquet_file in reversed(parquets):
            try:
                df = pd.read_parquet(parquet_file)
                if df.empty:
                    continue
                # 统一去时区（tqsdk 存储可能带 UTC）
                if hasattr(df["datetime"].dtype, "tz") and df["datetime"].dtype.tz is not None:
                    df["datetime"] = df["datetime"].dt.tz_localize(None)
                df_recent = df[df["datetime"] >= cutoff]
                if df_recent.empty:
                    continue
                open_price = float(df_recent.iloc[0]["open"])
                latest_close = float(df_recent.iloc[-1]["close"])
                high = float(df_recent["high"].max())
                low = float(df_recent["low"].min())
                volume = float(df_recent["volume"].sum())
                change_pct = (
                    round((latest_close - open_price) / open_price * 100, 2)
                    if open_price else 0.0
                )
                results.append({
                    "symbol": symbol,
                    "latest_close": latest_close,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "volume": volume,
                    "change_pct": change_pct,
                    "latest_time": str(df_recent.iloc[-1]["datetime"])[:16],
                    "bars_count": len(df_recent),
                })
                break  # 找到有效数据后停止向前找
            except Exception as exc:
                logger.warning("futures_minute read error: %s %s", symbol, exc)
                continue

    return results


@router.get("/futures_minute")
def get_futures_minute_context(hours: int = Query(2, ge=1, le=8)) -> dict[str, Any]:
    """获取所有期货品种近 N 小时分钟K行情摘要（按品种聚合，供宏观分析使用）"""
    summaries = _read_futures_minute_summary(hours)
    return {"data_type": "futures_minute", "hours": hours, "summaries": summaries, "count": len(summaries)}


# ─── 期货 35 品种情绪端点（on-demand，依赖 researcher_store 最新研报）────────────

@router.get("/futures_sentiment")
def get_futures_sentiment_context(
    symbol: Optional[str] = Query(None, description="品种短码（如 rb），不区分大小写；不传则返回全 35 品种"),
) -> dict[str, Any]:
    """获取期货 35 品种情绪聚合（基于 researcher 最新研报，on-demand 读取）。

    Returns:
        {
            "data_type": "futures_sentiment",
            "data": [{symbol, trend, confidence, sentiment_score, key_factors}, ...],
            "stale": bool,
            "last_updated": str | null,
            "reason": str | null,
            "symbol_count": int
        }

    当研报不可用时 data=[]，stale=True；绝不合成默认中性值。
    """
    from data.futures_sentiment import get_futures_sentiment

    result = get_futures_sentiment(symbol=symbol)
    return {"data_type": "futures_sentiment", **result}
