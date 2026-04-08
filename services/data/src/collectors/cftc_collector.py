"""CFTC 持仓报告采集器 — 基于 AkShare macro_usa_cftc_* 接口。

采集美国商品期货交易委员会(CFTC)的 Commitments of Traders 报告，
包含商品净持仓、多空比等关键指标，用于全球大宗商品持仓情绪分析。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


# AkShare CFTC 品种映射
# macro_usa_cftc_nc_report(symbol)  — 非商业(投机)持仓报告
# macro_usa_cftc_c_report(symbol)   — 商业(套保)持仓报告
# macro_usa_cftc_merchant_currency_holding_all — 全球商业货币持仓
CFTC_SYMBOLS = {
    "cftc_gold":    {"name": "黄金", "ak_symbol": "黄金"},
    "cftc_silver":  {"name": "白银", "ak_symbol": "白银"},
    "cftc_copper":  {"name": "铜", "ak_symbol": "铜"},
    "cftc_crude":   {"name": "原油", "ak_symbol": "原油"},
    "cftc_natgas":  {"name": "天然气", "ak_symbol": "天然气"},
    "cftc_corn":    {"name": "玉米", "ak_symbol": "玉米"},
    "cftc_soy":     {"name": "大豆", "ak_symbol": "大豆"},
    "cftc_wheat":   {"name": "小麦", "ak_symbol": "小麦"},
    "cftc_sp500":   {"name": "S&P500", "ak_symbol": "S&P500"},
    "cftc_nasdaq":  {"name": "NASDAQ", "ak_symbol": "NASDAQ"},
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

        for ind in indicator_list:
            meta = CFTC_SYMBOLS.get(ind)
            if not meta:
                self.logger.warning("cftc: unknown indicator %s", ind)
                continue
            ak_symbol = meta["ak_symbol"]

            # 非商业(投机)持仓
            try:
                df = ak.macro_usa_cftc_nc_report(symbol=ak_symbol)
                time.sleep(0.5)
                if df is not None and not df.empty:
                    rows = df if full_history else df.tail(30)
                    date_col = next((c for c in ("日期", "date") if c in df.columns), None)
                    for _, row in rows.iterrows():
                        row_ts = str(row[date_col]) if date_col else timestamp
                        records.append({
                            "source_type": "cftc",
                            "symbol_or_indicator": ind,
                            "timestamp": row_ts,
                            "payload": {
                                "indicator": ind,
                                "name": meta["name"],
                                "report_type": "non_commercial",
                                "long": _to_float(row, "多头"),
                                "short": _to_float(row, "空头"),
                                "net": _to_float(row, "净多"),
                                "long_chg": _to_float(row, "多头变化"),
                                "short_chg": _to_float(row, "空头变化"),
                                "mode": "live",
                            },
                        })
                    self.logger.info("cftc nc fetched: %s rows=%d", ind, len(rows))
            except Exception as exc:
                self.logger.warning("cftc nc fetch failed for %s: %s", ind, exc)

            # 商业(套保)持仓
            try:
                df = ak.macro_usa_cftc_c_report(symbol=ak_symbol)
                time.sleep(0.5)
                if df is not None and not df.empty:
                    rows = df if full_history else df.tail(30)
                    date_col = next((c for c in ("日期", "date") if c in df.columns), None)
                    for _, row in rows.iterrows():
                        row_ts = str(row[date_col]) if date_col else timestamp
                        records.append({
                            "source_type": "cftc",
                            "symbol_or_indicator": ind,
                            "timestamp": row_ts,
                            "payload": {
                                "indicator": ind,
                                "name": meta["name"],
                                "report_type": "commercial",
                                "long": _to_float(row, "多头"),
                                "short": _to_float(row, "空头"),
                                "net": _to_float(row, "净多"),
                                "long_chg": _to_float(row, "多头变化"),
                                "short_chg": _to_float(row, "空头变化"),
                                "mode": "live",
                            },
                        })
                    self.logger.info("cftc c fetched: %s rows=%d", ind, len(rows))
            except Exception as exc:
                self.logger.warning("cftc c fetch failed for %s: %s", ind, exc)

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
