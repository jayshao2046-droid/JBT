"""期权数据采集器 — 基于 AkShare 期权行情接口。

采集 50ETF/300ETF 期权行情、持仓量、隐含波动率等数据。
数据用于波动率曲面、PCR（Put/Call Ratio）等因子计算。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from src.collectors.base import BaseCollector


# 期权品种映射
OPTION_INDICATORS = {
    "sse_50etf":   {"name": "50ETF期权", "exchange": "SSE"},
    "sse_300etf":  {"name": "300ETF期权", "exchange": "SSE"},
    "sse_500etf":  {"name": "500ETF期权", "exchange": "SSE"},
    "szse_300etf": {"name": "深300ETF期权", "exchange": "SZSE"},
}

DEFAULT_INDICATORS = list(OPTION_INDICATORS.keys())


class OptionsCollector(BaseCollector):
    """Collect option market data via AkShare."""

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop("name", None)
        super().__init__(name="options", **kwargs)
        self.use_mock = use_mock

    def collect(
        self,
        *,
        indicators: list[str] | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        indicator_list = indicators or DEFAULT_INDICATORS
        if self.use_mock:
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)
        try:
            return self._fetch_live(indicator_list=indicator_list, as_of=as_of)
        except Exception as exc:
            self.logger.warning("options live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)

    def _fetch_live(
        self,
        *,
        indicator_list: list[str],
        as_of: str | None,
    ) -> list[dict[str, Any]]:
        import akshare as ak

        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        # 1) 综合 PCR 指标 — 认沽/认购比率 (全市场截面)
        try:
            df_pcr = ak.option_lhb_em()
            time.sleep(0.5)
            if df_pcr is not None and not df_pcr.empty:
                for _, row in df_pcr.iterrows():
                    records.append({
                        "source_type": "options",
                        "symbol_or_indicator": "pcr_summary",
                        "timestamp": timestamp,
                        "payload": {
                            "indicator": "pcr_summary",
                            "name": str(row.get("标的名称", row.get("name", ""))),
                            "pcr_volume": _to_float(row, "成交量PCR"),
                            "pcr_oi": _to_float(row, "持仓量PCR"),
                            "mode": "live",
                        },
                    })
                self.logger.info("options pcr fetched: rows=%d", len(df_pcr))
        except Exception as exc:
            self.logger.warning("options pcr fetch failed: %s", exc)

        # 2) 各品种期权行情
        for ind in indicator_list:
            meta = OPTION_INDICATORS.get(ind)
            if not meta:
                continue

            # 50ETF / 300ETF / 500ETF 期权行情 (上交所/深交所)
            try:
                if ind == "sse_50etf":
                    df = ak.option_current_em(symbol="50ETF期权", exchange="上海证券交易所")
                elif ind == "sse_300etf":
                    df = ak.option_current_em(symbol="沪深300ETF期权", exchange="上海证券交易所")
                elif ind == "sse_500etf":
                    df = ak.option_current_em(symbol="中证500ETF期权", exchange="上海证券交易所")
                elif ind == "szse_300etf":
                    df = ak.option_current_em(symbol="沪深300ETF期权", exchange="深圳证券交易所")
                else:
                    continue

                time.sleep(0.5)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        records.append({
                            "source_type": "options",
                            "symbol_or_indicator": ind,
                            "timestamp": timestamp,
                            "payload": {
                                "indicator": ind,
                                "name": meta["name"],
                                "contract": str(row.get("合约代码", row.get("code", ""))),
                                "last_price": _to_float(row, "最新价"),
                                "change_pct": _to_float(row, "涨跌幅"),
                                "volume": _to_float(row, "成交量"),
                                "oi": _to_float(row, "持仓量"),
                                "implied_vol": _to_float(row, "隐含波动率"),
                                "strike": _to_float(row, "行权价"),
                                "option_type": str(row.get("期权类型", row.get("type", ""))),
                                "mode": "live",
                            },
                        })
                    self.logger.info("options fetched: %s rows=%d", ind, len(df))
            except Exception as exc:
                self.logger.warning("options fetch failed for %s: %s", ind, exc)

        if not records:
            raise RuntimeError("all options indicators fetch failed")
        return records

    def _mock_records(self, *, indicator_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [
            {
                "source_type": "options",
                "symbol_or_indicator": ind,
                "timestamp": timestamp,
                "payload": {"indicator": ind, "last_price": 0.15 + i * 0.01, "mode": "mock"},
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
