"""Tushare 外汇日线采集器 — fx_daily / fx_obasic."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

from collectors.base import BaseCollector


# 主要货币对 (与期货品种高度相关)
# Tushare fx_daily 使用 FXCM 风格 ts_code。
DEFAULT_PAIR_CODES = {
    "USDCNH": "USDCNH.FXCM",  # 美元/离岸人民币
    "USDJPY": "USDJPY.FXCM",
    "EURUSD": "EURUSD.FXCM",
    "GBPUSD": "GBPUSD.FXCM",
    "AUDUSD": "AUDUSD.FXCM",
    "USDCAD": "USDCAD.FXCM",
    "USDHKD": "USDHKD.FXCM",
}


class ForexCollector(BaseCollector):
    """Collect FX daily rates via Tushare Pro fx_daily API."""

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop("name", None)
        super().__init__(name="forex", **kwargs)
        data_sources = self.config.get("data_sources", {})
        self.token = str(data_sources.get("tushare", {}).get("token", "") or "")
        if not self.token:
            self.token = os.environ.get("TUSHARE_TOKEN", "")
        self.use_mock = use_mock

    def collect(
        self,
        *,
        pairs: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        pair_codes = self._resolve_pair_codes(pairs)
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for forex collector")
        if not self.token:
            raise RuntimeError("TUSHARE_TOKEN not set for forex collector")
        try:
            return self._fetch_live(pair_codes=pair_codes, start_date=start_date, end_date=end_date)
        except Exception as exc:
            self.logger.error("forex live fetch failed: %s", exc)
            raise

    @staticmethod
    def _resolve_pair_codes(pairs: list[str] | None) -> dict[str, str]:
        if not pairs:
            return dict(DEFAULT_PAIR_CODES)

        resolved: dict[str, str] = {}
        for pair in pairs:
            alias = pair.strip().upper()
            if not alias:
                continue
            if "." in alias:
                resolved[alias] = alias
            else:
                resolved[alias] = DEFAULT_PAIR_CODES.get(alias, f"{alias}.FXCM")
        return resolved

    def _fetch_live(
        self,
        *,
        pair_codes: dict[str, str],
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, Any]]:
        import tushare as ts

        pro = ts.pro_api(self.token)
        records: list[dict[str, Any]] = []
        sd = start_date or datetime.now().strftime("%Y%m01")
        ed = end_date or datetime.now().strftime("%Y%m%d")

        for pair_label, ts_code in pair_codes.items():
            try:
                df = pro.fx_daily(ts_code=ts_code, start_date=sd, end_date=ed)
                time.sleep(0.3)
                if df is None or df.empty:
                    self.logger.warning("forex: %s (%s) returned empty", pair_label, ts_code)
                    continue
                for _, row in df.iterrows():
                    records.append({
                        "source_type": "forex",
                        "symbol_or_indicator": pair_label,
                        "timestamp": str(row.get("trade_date", "")),
                        "payload": {
                            "pair": pair_label,
                            "ts_code": ts_code,
                            "bid_open": float(row.get("bid_open", 0)),
                            "bid_close": float(row.get("bid_close", 0)),
                            "bid_high": float(row.get("bid_high", 0)),
                            "bid_low": float(row.get("bid_low", 0)),
                            "ask_open": float(row.get("ask_open", 0)),
                            "ask_close": float(row.get("ask_close", 0)),
                            "ask_high": float(row.get("ask_high", 0)),
                            "ask_low": float(row.get("ask_low", 0)),
                            "tick_qty": int(row.get("tick_qty", 0)),
                            "exchange": str(row.get("exchange", "")),
                            "mode": "live",
                        },
                    })
                self.logger.info("forex fetched: %s (%s) rows=%d", pair_label, ts_code, len(df))
            except Exception as exc:
                self.logger.warning("forex fetch failed for %s (%s): %s", pair_label, ts_code, exc)

        if not records:
            raise RuntimeError("all forex pairs fetch failed")
        return records

    def _mock_records(self, *, pair_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [
            {
                "source_type": "forex",
                "symbol_or_indicator": pair,
                "timestamp": timestamp,
                "payload": {"pair": pair, "bid_close": 7.25 + i * 0.01, "mode": "mock"},
            }
            for i, pair in enumerate(pair_list)
        ]
