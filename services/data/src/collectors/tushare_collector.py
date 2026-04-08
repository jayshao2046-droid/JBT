"""Tushare daily collector with real API integration."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from services.data.src.collectors.base import BaseCollector


class TushareDailyCollector(BaseCollector):
    """Daily collector using Tushare Pro API with mock fallback."""

    def __init__(self, *, force_fail: bool = False, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="tushare", **kwargs)
        data_sources = self.config.get("data_sources", {})
        self.token = str(data_sources.get("tushare", {}).get("token", "") or "")
        self.force_fail = force_fail
        self.use_mock = use_mock

    def collect(
        self,
        *,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        freq: str = "daily",
    ) -> list[dict[str, Any]]:
        if self.force_fail:
            raise RuntimeError("forced primary failure for testing")
        if self.use_mock or not self.token:
            return self._mock_daily_records(symbol=symbol, start_date=start_date)
        _ = freq
        try:
            return self._fetch_live(symbol=symbol, start_date=start_date, end_date=end_date)
        except Exception as exc:
            self.logger.warning("tushare live fetch failed: %s, falling back to mock", exc)
            return self._mock_daily_records(symbol=symbol, start_date=start_date)

    def _convert_symbol(self, symbol: str) -> str:
        """Convert internal symbol to Tushare ts_code: SHFE.rb2405 -> RB2405.SHF"""
        exchange_map = {
            "SHFE": "SHF", "DCE": "DCE", "CZCE": "ZCE",
            "CFFEX": "CFX", "INE": "INE", "GFEX": "GFE",
        }
        if "." in symbol:
            parts = symbol.split(".", 1)
            exchange = parts[0]
            code = parts[1].upper()
            ts_exchange = exchange_map.get(exchange, exchange)
            return f"{code}.{ts_exchange}"
        return symbol

    def _fetch_live(self, *, symbol: str, start_date: str | None, end_date: str | None) -> list[dict[str, Any]]:
        import tushare as ts
        import time
        pro = ts.pro_api(self.token)
        ts_code = self._convert_symbol(symbol)
        sd = start_date or "20200101"
        ed = end_date or datetime.now().strftime("%Y%m%d")
        self.logger.info("tushare fetching daily: ts_code=%s start=%s end=%s", ts_code, sd, ed)
        df = pro.fut_daily(ts_code=ts_code, start_date=sd, end_date=ed)
        time.sleep(0.3)  # rate limit
        if df is None or df.empty:
            self.logger.warning("tushare returned empty for ts_code=%s", ts_code)
            return []
        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "symbol": symbol,
                "timestamp": str(row.get("trade_date", "")),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("vol", 0)),
                "oi": float(row.get("oi", 0)),
                "amount": float(row.get("amount", 0)),
            })
        self.logger.info("tushare daily fetched: symbol=%s records=%d", symbol, len(records))
        return records

    def _mock_daily_records(self, *, symbol: str, start_date: str | None) -> list[dict[str, Any]]:
        if start_date:
            base_dt = datetime.fromisoformat(start_date)
        else:
            base_dt = datetime(2026, 1, 1)
        records: list[dict[str, Any]] = []
        for i in range(3):
            ts = base_dt + timedelta(days=i)
            price = 10.0 + i * 0.2
            records.append({
                "symbol": symbol,
                "timestamp": ts.isoformat(),
                "open": round(price, 4),
                "high": round(price + 0.3, 4),
                "low": round(price - 0.25, 4),
                "close": round(price + 0.1, 4),
                "volume": float(50000 + i * 2000),
            })
        return records
