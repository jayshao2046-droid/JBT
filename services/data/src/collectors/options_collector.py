"""期权数据采集器 — 基于 Tushare 期权行情接口。

采集上交所、深交所、中金所期权日线行情数据。
数据用于波动率曲面、PCR（Put/Call Ratio）等因子计算。
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from collectors.base import BaseCollector


# 期权交易所映射
OPTION_EXCHANGES = {
    "sse": {"name": "上交所期权", "exchange": "SSE"},
    "szse": {"name": "深交所期权", "exchange": "SZSE"},
    "cffex": {"name": "中金所期权", "exchange": "CFFEX"},
}

DEFAULT_EXCHANGES = list(OPTION_EXCHANGES.keys())


class OptionsCollector(BaseCollector):
    """Collect option market data via Tushare."""

    def __init__(self, *, use_mock: bool = False, token: str | None = None, **kwargs: Any) -> None:
        kwargs.pop("name", None)
        super().__init__(name="options", **kwargs)
        self.use_mock = use_mock
        self.token = token
        self._pro = None

    @property
    def pro(self):
        if self._pro is None:
            import tushare as ts
            ts.set_token(self.token or "")
            self._pro = ts.pro_api()
        return self._pro

    def collect(
        self,
        *,
        exchanges: list[str] | None = None,
        trade_date: str | None = None,
    ) -> list[dict[str, Any]]:
        exchange_list = exchanges or DEFAULT_EXCHANGES
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for options collector")
        last_exc: Exception | None = None
        for candidate in self._candidate_trade_dates(trade_date):
            try:
                records = self._fetch_live(exchange_list=exchange_list, trade_date=candidate)
                if trade_date is None and candidate != datetime.now().strftime("%Y%m%d"):
                    self.logger.info("options fallback succeeded: trade_date=%s", candidate)
                return records
            except Exception as exc:
                last_exc = exc
                if trade_date is None:
                    self.logger.warning("options attempt failed for trade_date=%s: %s", candidate, exc)
        self.logger.error("options live fetch failed: %s", last_exc)
        raise last_exc or RuntimeError("all options exchanges fetch failed")

    @staticmethod
    def _candidate_trade_dates(trade_date: str | None, lookback_days: int = 5) -> list[str]:
        if trade_date:
            return [trade_date]

        today = datetime.now()
        return [
            (today - timedelta(days=offset)).strftime("%Y%m%d")
            for offset in range(lookback_days + 1)
        ]

    def _fetch_live(
        self,
        *,
        exchange_list: list[str],
        trade_date: str | None,
    ) -> list[dict[str, Any]]:
        from datetime import datetime

        records: list[dict[str, Any]] = []
        timestamp = trade_date or datetime.now().strftime("%Y%m%d")

        for exch_key in exchange_list:
            meta = OPTION_EXCHANGES.get(exch_key)
            if not meta:
                continue

            try:
                df = self.pro.opt_daily(trade_date=timestamp, exchange=meta["exchange"])
                time.sleep(0.3)

                if df is not None and not df.empty:
                    # Fill NaN values
                    for col in df.columns:
                        if df[col].dtype in ["float64", "int64"]:
                            df[col] = df[col].fillna(0)
                        else:
                            df[col] = df[col].fillna("")

                    for _, row in df.iterrows():
                        records.append({
                            "source_type": "options",
                            "symbol_or_indicator": exch_key,
                            "timestamp": timestamp,
                            "payload": {
                                "ts_code": str(row.get("ts_code", "")),
                                "trade_date": str(row.get("trade_date", "")),
                                "exchange": meta["exchange"],
                                "pre_close": float(row.get("pre_close", 0)),
                                "open": float(row.get("open", 0)),
                                "high": float(row.get("high", 0)),
                                "low": float(row.get("low", 0)),
                                "close": float(row.get("close", 0)),
                                "settle": float(row.get("settle", 0)),
                                "vol": float(row.get("vol", 0)),
                                "amount": float(row.get("amount", 0)),
                                "oi": float(row.get("oi", 0)),
                                "mode": "live",
                            },
                        })
                    self.logger.info("options fetched: %s rows=%d", exch_key, len(df))
            except Exception as exc:
                self.logger.warning("options fetch failed for %s: %s", exch_key, exc)

        if not records:
            raise RuntimeError("all options exchanges fetch failed")
        return records

    def _mock_records(self, *, exchange_list: list[str], trade_date: str | None) -> list[dict[str, Any]]:
        from datetime import datetime
        timestamp = trade_date or datetime.now().strftime("%Y%m%d")
        return [
            {
                "source_type": "options",
                "symbol_or_indicator": exch,
                "timestamp": timestamp,
                "payload": {"exchange": exch, "close": 0.15 + i * 0.01, "mode": "mock"},
            }
            for i, exch in enumerate(exchange_list)
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
