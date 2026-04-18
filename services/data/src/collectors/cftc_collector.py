"""CFTC 持仓报告采集器 — 基于 AkShare macro_usa_cftc_* 接口。

采集美国商品期货交易委员会(CFTC)的 Commitments of Traders 报告，
包含商品净持仓、多空比等关键指标，用于全球大宗商品持仓情绪分析。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from collectors.base import BaseCollector


# AkShare CFTC 品种映射（akshare ≥ 1.18 宽格式 API）
# macro_usa_cftc_merchant_goods_holding() — 商品持仓（商业）
# macro_usa_cftc_c_holding()             — 商品持仓（商业，同上）
# 列名格式: "{品种}-多头仓位" / "{品种}-空头仓位" / "{品种}-净仓位"
CFTC_SYMBOLS = {
    "cftc_gold":    {"name": "黄金", "col_prefix": "黄金"},
    "cftc_silver":  {"name": "白银", "col_prefix": "白银"},
    "cftc_crude":   {"name": "原油", "col_prefix": "纽约原油"},
    "cftc_natgas":  {"name": "天然气", "col_prefix": "纽约天然气"},
    "cftc_corn":    {"name": "玉米", "col_prefix": "玉米"},
    "cftc_soy":     {"name": "大豆", "col_prefix": "大豆"},
    "cftc_cotton":  {"name": "棉花", "col_prefix": "棉花"},
    "cftc_sugar":   {"name": "原糖", "col_prefix": "原糖"},
}

DEFAULT_INDICATORS = list(CFTC_SYMBOLS.keys())


class CftcCollector(BaseCollector):
    """Collect CFTC Commitments of Traders reports via AkShare."""

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop("name", None)
        super().__init__(name="cftc", **kwargs)
        self.use_mock = use_mock

    def collect(
        self,
        *,
        indicators: list[str] | None = None,
        as_of: str | None = None,
        full_history: bool = False,
    ) -> list[dict[str, Any]]:
        indicator_list = indicators or DEFAULT_INDICATORS
        if self.use_mock:
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)
        try:
            return self._fetch_live(indicator_list=indicator_list, as_of=as_of, full_history=full_history)
        except Exception as exc:
            self.logger.warning("cftc live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)

    def _fetch_live(
        self,
        *,
        indicator_list: list[str],
        as_of: str | None,
        full_history: bool = False,
    ) -> list[dict[str, Any]]:
        import akshare as ak

        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        # akshare ≥ 1.18: 批量宽格式 API，一次获取全部品种
        df = ak.macro_usa_cftc_merchant_goods_holding()
        time.sleep(0.5)
        if df is None or df.empty:
            raise RuntimeError("macro_usa_cftc_merchant_goods_holding returned empty")

        rows = df if full_history else df.tail(30)

        for ind in indicator_list:
            meta = CFTC_SYMBOLS.get(ind)
            if not meta:
                self.logger.warning("cftc: unknown indicator %s", ind)
                continue
            prefix = meta["col_prefix"]
            long_col = f"{prefix}-多头仓位"
            short_col = f"{prefix}-空头仓位"
            net_col = f"{prefix}-净仓位"

            if long_col not in df.columns:
                self.logger.warning("cftc: column %s not found in API response", long_col)
                continue

            for _, row in rows.iterrows():
                row_ts = str(row["日期"]) if "日期" in df.columns else timestamp
                records.append({
                    "source_type": "cftc",
                    "symbol_or_indicator": ind,
                    "timestamp": row_ts,
                    "payload": {
                        "indicator": ind,
                        "name": meta["name"],
                        "report_type": "commercial",
                        "long": _to_float(row, long_col),
                        "short": _to_float(row, short_col),
                        "net": _to_float(row, net_col),
                        "mode": "live",
                    },
                })
            self.logger.info("cftc fetched: %s rows=%d", ind, len(rows))

        if not records:
            raise RuntimeError("all CFTC indicators fetch failed")
        return records

    def _mock_records(self, *, indicator_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [
            {
                "source_type": "cftc",
                "symbol_or_indicator": ind,
                "timestamp": timestamp,
                "payload": {"indicator": ind, "report_type": "non_commercial", "net": 10000 + i * 500, "mode": "mock"},
            }
            for i, ind in enumerate(indicator_list)
        ]


def _to_float(row: Any, col_name: str) -> float:
    """Safely extract float from a DataFrame row."""
    val = row.get(col_name, 0)
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0
