"""Position/warehouse data collector using Tushare Pro."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from collectors.base import BaseCollector


class PositionCollector(BaseCollector):
    """Collect futures position and warehouse data via Tushare."""

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="position", **kwargs)
        self.use_mock = use_mock
        data_sources = self.config.get("data_sources", {})
        self.token = str(data_sources.get("tushare", {}).get("token", "") or "")

    def collect(self, *, symbols: list[str] | None = None, trade_date: str | None = None) -> list[dict[str, Any]]:
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for position collector")
        if not self.token:
            raise RuntimeError("tushare token not configured for position collector")
        last_exc: Exception | None = None
        for candidate in self._candidate_trade_dates(trade_date):
            try:
                records = self._fetch_live(symbol_list=symbols, trade_date=candidate)
                if trade_date is None and candidate != datetime.now().strftime("%Y%m%d"):
                    self.logger.info("position fallback succeeded: trade_date=%s", candidate)
                return records
            except Exception as exc:
                last_exc = exc
                if trade_date is None:
                    self.logger.warning("position attempt failed for trade_date=%s: %s", candidate, exc)
        self.logger.error("position live fetch failed: %s", last_exc)
        raise last_exc or RuntimeError("all position fetchers failed")

    @staticmethod
    def _candidate_trade_dates(trade_date: str | None, lookback_days: int = 5) -> list[str]:
        if trade_date:
            return [trade_date]

        today = datetime.now()
        return [
            (today - timedelta(days=offset)).strftime("%Y%m%d")
            for offset in range(lookback_days + 1)
        ]

    def _fetch_live(self, *, symbol_list: list[str] | None, trade_date: str | None) -> list[dict[str, Any]]:
        import tushare as ts
        pro = ts.pro_api(self.token)
        td = trade_date or datetime.now().strftime("%Y%m%d")
        records: list[dict[str, Any]] = []
        # 获取主力合约持仓排名
        # 仅 SHFE 10个品种（Tushare fut_holding 仅对 SHFE 有历史数据）
        symbols_to_check = [
            "RB", "HC", "CU", "AL", "ZN", "AU", "AG", "RU", "SS", "SP",
        ]
        for sym in symbols_to_check:
            try:
                df = pro.fut_holding(symbol=sym.lower(), trade_date=td)
                time.sleep(0.3)
                if df is not None and not df.empty:
                    for _, row in df.head(20).iterrows():
                        records.append({
                            "source_type": "position",
                            "symbol_or_indicator": f"{sym}.holding",
                            "timestamp": td,
                            "payload": dict(row),
                        })
                    self.logger.info("position fetched: %s rows=%d", sym, min(20, len(df)))
            except Exception as exc:
                self.logger.warning("position fetch failed for %s: %s", sym, exc)
        if not records:
            raise RuntimeError("all position fetchers failed")
        return records

    def _mock_records(self, *, symbol_list: list[str], trade_date: str | None) -> list[dict[str, Any]]:
        timestamp = trade_date or datetime.utcnow().replace(microsecond=0).isoformat()
        symbols = symbol_list or ["SHFE.rb", "DCE.i", "DCE.m", "CZCE.CF", "SHFE.au"]
        records: list[dict[str, Any]] = []
        for sym in symbols:
            records.append({
                "source_type": "position",
                "symbol_or_indicator": f"{sym}.holding",
                "timestamp": timestamp,
                "payload": {"symbol": sym, "long_vol": 50000, "short_vol": 48000, "mode": "mock"},
            })
        return records
