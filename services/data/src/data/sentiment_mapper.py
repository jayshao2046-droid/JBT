"""P1-010: 情绪数据映射器 — 将 P3 payload 转换为 P5 因子可消费的扁平 DataFrame.

Migrated from legacy codebase.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import polars as pl

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 关键词词表
# ---------------------------------------------------------------------------
_POSITIVE_KW: set[str] = {"涨", "利好", "突破", "上涨", "增长", "反弹", "创新高", "利多", "买入", "强势"}
_NEGATIVE_KW: set[str] = {"跌", "利空", "下跌", "暴跌", "下滑", "亏损", "创新低", "卖出", "弱势"}


def _extract_payload(raw: Any) -> dict:
    """Safely extract payload dict from a record."""
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def _keyword_score(text: str) -> float:
    """基于关键词的情绪评分, base=0.5, clamp [0,1]."""
    score = 0.5
    for kw in _POSITIVE_KW:
        if kw in text:
            score += 0.1
    for kw in _NEGATIVE_KW:
        if kw in text:
            score -= 0.1
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def map_news_to_score(records: list[dict[str, Any]]) -> pl.DataFrame:
    """将 news_api 原始记录转换为带 news_score 列的 DataFrame.

    评分逻辑（基于关键词）：
    - 正面关键词 (+0.1 each): 涨, 利好, 突破, 上涨, 增长, 反弹, 创新高, 利多, 买入, 强势
    - 负面关键词 (-0.1 each): 跌, 利空, 下跌, 暴跌, 下滑, 亏损, 创新低, 卖出, 弱势
    - 基础分 0.5, clamp 到 [0, 1]

    Returns:
        pl.DataFrame with columns [timestamp, news_score]
    """
    if not records:
        return pl.DataFrame(schema={"timestamp": pl.Utf8, "news_score": pl.Float64})

    rows: list[dict[str, Any]] = []
    for rec in records:
        ts = rec.get("timestamp")
        if ts is None:
            continue
        payload = _extract_payload(rec.get("payload", {}))
        # 尝试从多个字段提取文本
        text = " ".join(
            str(payload.get(k, ""))
            for k in ("title", "title_original", "title_translated", "summary", "content", "description")
        )
        rows.append({"timestamp": str(ts), "news_score": _keyword_score(text)})

    if not rows:
        return pl.DataFrame(schema={"timestamp": pl.Utf8, "news_score": pl.Float64})

    return pl.DataFrame(rows).with_columns(
        pl.col("timestamp").cast(pl.Utf8),
        pl.col("news_score").cast(pl.Float64),
    )


def map_sentiment_to_score(records: list[dict[str, Any]]) -> pl.DataFrame:
    """将 sentiment 原始记录转换为带 social_score 列的 DataFrame.

    映射逻辑：
    - margin_sh/margin_sz: 融资买入额 > 0 → 偏多, 归一化到 0.3~0.7
    - north_flow: net_buy > 0 → 偏多, 归一化到 0.3~0.7
    - vix: close 反比关系, VIX高→恐慌→低分
    - market_activity: value 直接归一化
    - mock data: bullish 字段直接用

    Returns:
        pl.DataFrame with columns [timestamp, social_score]
    """
    if not records:
        return pl.DataFrame(schema={"timestamp": pl.Utf8, "social_score": pl.Float64})

    rows: list[dict[str, Any]] = []
    for rec in records:
        ts = rec.get("timestamp")
        if ts is None:
            continue
        payload = _extract_payload(rec.get("payload", {}))
        indicator = rec.get("symbol_or_indicator", "") or payload.get("indicator", "")
        score = _sentiment_indicator_to_score(indicator, payload)
        if score is not None:
            rows.append({"timestamp": str(ts), "social_score": score})

    if not rows:
        return pl.DataFrame(schema={"timestamp": pl.Utf8, "social_score": pl.Float64})

    return pl.DataFrame(rows).with_columns(
        pl.col("timestamp").cast(pl.Utf8),
        pl.col("social_score").cast(pl.Float64),
    )


def _sentiment_indicator_to_score(indicator: str, payload: dict) -> float | None:
    """Map a single sentiment indicator + payload to a score in [0, 1]."""
    ind = indicator.lower()

    # margin_sh / margin_sz — 融资买入额
    if ind in ("margin_sh", "margin_sz"):
        buy_amount = _to_float(payload.get("rzjme") or payload.get("buy_amount") or payload.get("value", 0))
        # 正值偏多, 负值偏空, 映射到 0.3~0.7
        return _clamp(0.5 + buy_amount / (abs(buy_amount) + 1e-9) * 0.2, 0.3, 0.7)

    # north_flow — 北向资金
    if ind in ("north_flow", "northbound"):
        net_buy = _to_float(payload.get("net_buy") or payload.get("value", 0))
        return _clamp(0.5 + net_buy / (abs(net_buy) + 1e-9) * 0.2, 0.3, 0.7)

    # vix — 恐慌指数(反比)
    if ind == "vix":
        vix_val = _to_float(payload.get("close") or payload.get("value", 20))
        # VIX 10~40 映射到 0.7~0.3
        return _clamp(0.7 - (vix_val - 10) / 30 * 0.4, 0.3, 0.7)

    # market_activity — 市场活跃度
    if ind in ("market_activity", "activity"):
        val = _to_float(payload.get("value", 0.5))
        return _clamp(val, 0.0, 1.0)

    # mock / eastmoney / 通用 — bullish 字段
    if "bullish" in payload:
        return _clamp(_to_float(payload["bullish"]), 0.0, 1.0)

    # 有 value 字段的通用 fallback
    if "value" in payload:
        return _clamp(_to_float(payload["value"]), 0.0, 1.0)

    return 0.5  # 无法识别的 indicator 给中性分


def merge_sentiment_scores(
    news_df: pl.DataFrame | None = None,
    social_df: pl.DataFrame | None = None,
    base_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """将 news_score 和 social_score 合并到 base_df (按 timestamp left join).

    如果 base_df 为 None, 则以 news_df 或 social_df 的 timestamp 为基准。
    """
    # 确定基准 DataFrame
    if base_df is not None:
        result = base_df
    elif news_df is not None and not news_df.is_empty():
        result = news_df.select("timestamp")
    elif social_df is not None and not social_df.is_empty():
        result = social_df.select("timestamp")
    else:
        return pl.DataFrame(schema={"timestamp": pl.Utf8, "news_score": pl.Float64, "social_score": pl.Float64})

    if news_df is not None and not news_df.is_empty():
        if "news_score" not in result.columns:
            result = result.join(news_df.select("timestamp", "news_score"), on="timestamp", how="left")

    if social_df is not None and not social_df.is_empty():
        if "social_score" not in result.columns:
            result = result.join(social_df.select("timestamp", "social_score"), on="timestamp", how="left")

    # 填充缺失列
    if "news_score" not in result.columns:
        result = result.with_columns(pl.lit(0.5).alias("news_score"))
    if "social_score" not in result.columns:
        result = result.with_columns(pl.lit(0.5).alias("social_score"))

    return result


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _to_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
