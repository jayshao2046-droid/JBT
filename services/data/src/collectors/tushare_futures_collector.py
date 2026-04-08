"""Tushare futures collector with real API integration."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


class TushareFuturesCollector(BaseCollector):
    """Collect Tushare futures endpoints with real Pro API."""

    UNIQUE_KEY_FIELDS = ("ts_code", "trade_date")
    EXCHANGE_MAP = {
        "SHFE": "SHF", "DCE": "DCE", "CZCE": "ZCE",
        "CFFEX": "CFX", "INE": "INE", "GFEX": "GFE",
    }

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="tushare_futures", **kwargs)
        data_sources = self.config.get("data_sources", {})
        self.token = str(data_sources.get("tushare", {}).get("token", "") or "")
        self.use_mock = use_mock

    def _get_pro(self):
        import tushare as ts
        return ts.pro_api(self.token)

    def _convert_symbol(self, symbol: str) -> str:
        if "." in symbol:
            parts = symbol.split(".", 1)
            exchange = parts[0]
            code = parts[1].upper()
            ts_exchange = self.EXCHANGE_MAP.get(exchange, exchange)
            return f"{code}.{ts_exchange}"
        return symbol

    def _safe_call(self, func, **kwargs) -> list[dict[str, Any]]:
        try:
            df = func(**kwargs)
            time.sleep(0.3)
            if df is None or df.empty:
                return []
            return df.to_dict("records")
        except Exception as exc:
            self.logger.warning("tushare futures call failed: %s", exc)
            return []

    def fut_basic(self, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        if self.use_mock or not self.token:
            return self._mock_endpoint("fut_basic", ts_code, trade_date)
        pro = self._get_pro()
        return self._safe_call(pro.fut_basic, exchange="", fut_type="1")

    def fut_daily(self, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        if self.use_mock or not self.token:
            return self._mock_endpoint("fut_daily", ts_code, trade_date)
        pro = self._get_pro()
        return self._safe_call(pro.fut_daily, ts_code=ts_code, trade_date=trade_date)

    def fut_holding(self, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        if self.use_mock or not self.token:
            return self._mock_endpoint("fut_holding", ts_code, trade_date)
        pro = self._get_pro()
        return self._safe_call(pro.fut_holding, symbol=ts_code.split(".")[0].lower(), trade_date=trade_date)

    def fut_wsr(self, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        if self.use_mock or not self.token:
            return self._mock_endpoint("fut_wsr", ts_code, trade_date)
        pro = self._get_pro()
        return self._safe_call(pro.fut_wsr, trade_date=trade_date)

    def fut_settle(self, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        if self.use_mock or not self.token:
            return self._mock_endpoint("fut_settle", ts_code, trade_date)
        pro = self._get_pro()
        return self._safe_call(pro.fut_settle, ts_code=ts_code, trade_date=trade_date)

    def collect(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        ts_code = str(kwargs.get("ts_code") or "IF9999.CFX")
        trade_date = str(kwargs.get("trade_date") or datetime.utcnow().strftime("%Y%m%d"))
        return self.collect_all(ts_code=ts_code, trade_date=trade_date)

    def collect_all(self, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        self.logger.info("tushare futures collecting: ts_code=%s trade_date=%s", ts_code, trade_date)
        records: list[dict[str, Any]] = []
        records.extend(self.fut_daily(ts_code, trade_date))
        records.extend(self.fut_holding(ts_code, trade_date))
        records.extend(self.fut_wsr(ts_code, trade_date))
        records.extend(self.fut_settle(ts_code, trade_date))
        self.logger.info("tushare futures total records: %d", len(records))
        return records

    def _mock_endpoint(self, endpoint: str, ts_code: str, trade_date: str) -> list[dict[str, Any]]:
        return [{
            "source_type": "tushare_futures",
            "symbol_or_indicator": f"{ts_code}.{endpoint}",
            "timestamp": trade_date,
            "payload": {"ts_code": ts_code, "trade_date": trade_date, "endpoint": endpoint, "mode": "mock"},
        }]
