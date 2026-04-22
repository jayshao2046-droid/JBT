"""期货 35 品种情绪聚合 — on-demand，依赖 Mini 本地最新研报

设计约定：
- 无新的调度任务，无新的 parquet 写入
- 每次 API 调用时实时读取 researcher_store.get_latest()
- 当研报不可用时，返回 stale=True + 空 data，绝不合成默认中性值
- symbol 标准化：KQ.m@SHFE.rb → rb（lowercase），CZCE 品种同样 lowercase
"""
from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 35 品种短码白名单（全部 lowercase，包含郑商所原大写品种小写化后）
FUTURES_35_SHORT: frozenset[str] = frozenset({
    # SHFE (10)
    "rb", "hc", "cu", "al", "zn", "au", "ag", "ru", "ss", "sp",
    # DCE (15)
    "i", "m", "pp", "v", "l", "c", "jd", "y", "p", "a", "jm", "j", "eb", "pg", "lh",
    # CZCE (10) — 原始大写，lowercase 后
    "ta", "ma", "cf", "sr", "oi", "rm", "fg", "sa", "pf", "ur",
})

# 趋势标签 → 量化情绪分（0.0 偏空 ~ 1.0 偏多，0.5 中性）
_TREND_SCORE: Dict[str, float] = {
    "偏多": 0.75,
    "强多": 0.90,
    "偏空": 0.25,
    "强空": 0.10,
    "震荡": 0.50,
    "观望": 0.50,
    "bullish": 0.75,
    "bearish": 0.25,
    "neutral": 0.50,
}


def _normalize_symbol(raw: str) -> str:
    """将各种格式的品种标识符归一化为 lowercase 短码。

    Examples:
        KQ.m@SHFE.rb  → rb
        KQ.m@CZCE.TA  → ta
        rb            → rb
        TA            → ta
    """
    if "@" in raw:
        # KQ.m@SHFE.rb → SHFE.rb → rb
        raw = raw.split("@", 1)[1]
    # SHFE.rb → rb  |  rb → rb
    return raw.split(".")[-1].lower()


def _trend_to_score(trend: str) -> float:
    return _TREND_SCORE.get(trend, 0.50)


def get_futures_sentiment(symbol: Optional[str] = None) -> Dict[str, Any]:
    """按需聚合期货 35 品种情绪，来源为 Mini 本地最新研报（researcher_store）。

    Args:
        symbol: 品种短码（如 ``rb``、``TA``），不区分大小写；None 则返回全 35 品种。

    Returns::

        {
            "data": [
                {
                    "symbol": "rb",
                    "trend": "偏空",
                    "confidence": 0.72,
                    "sentiment_score": 0.25,
                    "key_factors": ["铁矿供需宽松", ...]
                },
                ...
            ],
            "stale": False,
            "last_updated": "2026-04-23T10:00:00",
            "reason": None,
            "symbol_count": 35
        }

    当研报不可用时，返回::

        {"data": [], "stale": True, "last_updated": None, "reason": "no_report_available", "symbol_count": 0}

    注意：绝不合成中性默认值作为虚假信号。
    """
    try:
        # 在 services/data/src/ 根目录下直接 import（运行态 PYTHONPATH 包含 src/）
        import researcher_store as _rs  # type: ignore[import]
    except ImportError:
        try:
            # 相对 import（当以包形式运行时）
            from .. import researcher_store as _rs  # type: ignore[import,no-redef]
        except ImportError:
            logger.error("researcher_store 不可用，无法聚合期货情绪")
            return _stale_response("researcher_store_unavailable")

    report = _rs.get_latest()
    if report is None:
        return _stale_response("no_report_available")

    # 新鲜度判断：研报日期与今日不一致则标记 stale
    report_date = report.get("date", "")
    today_str = str(datetime.date.today())
    is_stale = bool(report_date) and (report_date != today_str)
    last_updated = report.get("generated_at") or report_date or None

    # 提取 futures_summary.symbols
    futures_summary = report.get("futures_summary", {})
    if not isinstance(futures_summary, dict):
        return _stale_response("invalid_report_structure")

    raw_symbols: Dict[str, Any] = futures_summary.get("symbols", {})
    if not isinstance(raw_symbols, dict):
        return _stale_response("invalid_symbols_structure")

    # 归一化所有 symbol key → {short_code: entry_dict}
    normalized: Dict[str, Dict[str, Any]] = {}
    for raw_key, val in raw_symbols.items():
        short = _normalize_symbol(raw_key)
        if short in FUTURES_35_SHORT:
            normalized[short] = val

    # 按目标 symbol 过滤
    if symbol is not None:
        target = symbol.lower()
        if target not in FUTURES_35_SHORT:
            return {
                "data": [],
                "stale": False,
                "last_updated": last_updated,
                "reason": f"symbol '{symbol}' not in 35-futures whitelist",
                "symbol_count": 0,
            }
        keys_to_return = [target] if target in normalized else []
    else:
        keys_to_return = sorted(normalized.keys())

    data: List[Dict[str, Any]] = []
    for sym in keys_to_return:
        entry = normalized[sym]
        trend = str(entry.get("trend", "unknown"))
        confidence = float(entry.get("confidence", 0.5))
        data.append({
            "symbol": sym,
            "trend": trend,
            "confidence": round(confidence, 4),
            "sentiment_score": _trend_to_score(trend),
            "key_factors": entry.get("key_factors", []),
        })

    return {
        "data": data,
        "stale": is_stale,
        "last_updated": last_updated,
        "reason": "stale_report" if is_stale else None,
        "symbol_count": len(data),
    }


def _stale_response(reason: str) -> Dict[str, Any]:
    """构造标准 stale 响应，不含任何合成数据。"""
    return {
        "data": [],
        "stale": True,
        "last_updated": None,
        "reason": reason,
        "symbol_count": 0,
    }
