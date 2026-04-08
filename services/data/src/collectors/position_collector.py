"""Position/warehouse data collector using Tushare Pro."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


class PositionCollector(BaseCollector):
    """Collect futures position and warehouse data via Tushare."""

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="position", **kwargs)
        self.use_mock = use_mock
        data_sources = self.config.get("data_sources", {})
        self.token = str(data_sources.get("tushare", {}).get("token", "") or "")

    def collect(self, *, symbols: list[str] | None = None, trade_date: str | None = None) -> list[dict[str, Any]]:
        if self.use_mock or not self.token:
            return self._mock_records(symbol_list=symbols or [], trade_date=trade_date)
        try:
            return self._fetch_live(symbol_list=symbols, trade_date=trade_date)
        except Exception as exc:
            self.logger.warning("position live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(symbol_list=symbols or [], trade_date=trade_date)

    def _fetch_live(self, *, symbol_list: list[str] | None, trade_date: str | None) -> list[dict[str, Any]]:
        import tushare as ts
        pro = ts.pro_api(self.token)
        td = trade_date or datetime.now().strftime("%Y%m%d")
        records: list[dict[str, Any]] = []
        # 获取主力合约持仓排名
        symbols_to_check = ["RB", "HC", "I", "M", "C", "CF", "Y", "P", "OI", "TA", "MA", "PP", "V", "RU"]
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
        # 获取仓单数据
        try:
            df_wsr = pro.fut_wsr(trade_date=td)
            time.sleep(0.3)
            if df_wsr is not None and not df_wsr.empty:
                for _, row in df_wsr.iterrows():
                    records.append({
                        "source_type": "position",
                        "symbol_or_indicator": "warehouse_receipt",
                        "timestamp": td,
                        "payload": dict(row),
                    })
                self.logger.info("warehouse receipt fetched: rows=%d", len(df_wsr))
        except Exception as exc:
            self.logger.warning("warehouse receipt fetch failed: %s", exc)
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
