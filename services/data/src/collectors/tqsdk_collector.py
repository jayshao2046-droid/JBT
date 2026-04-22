"""TqSdk minute K-line collector for domestic futures."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import pandas as pd

from collectors.base import BaseCollector


class TqSdkCollector(BaseCollector):
    """Collect minute K-line data via TqSdk API (free version: 1 concurrent connection)."""

    DEFAULT_SYMBOLS = [
        "SHFE.rb2510", "SHFE.hc2510", "SHFE.ru2509", "SHFE.cu2507",
        "DCE.i2509", "DCE.m2509", "DCE.c2509", "DCE.pp2509",
        "CZCE.CF510", "CZCE.TA510", "CZCE.MA510", "CZCE.OI510",
        "INE.sc2508", "CFFEX.IF2506",
    ]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="tqsdk_minute", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, symbols: list[str] | None = None, duration: int = 60, as_of: str | None = None) -> list[dict[str, Any]]:
        symbol_list = symbols or self.DEFAULT_SYMBOLS
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for tqsdk collector")
        try:
            return self._fetch_live(symbol_list=symbol_list, duration=duration, as_of=as_of)
        except Exception as exc:
            self.logger.error("tqsdk live fetch failed: %s", exc)
            raise

    def _fetch_live(self, *, symbol_list: list[str], duration: int, as_of: str | None) -> list[dict[str, Any]]:
        from tqsdk import TqApi, TqAuth
        phone = os.getenv("TQSDK_PHONE", "")
        password = os.getenv("TQSDK_PASSWORD", "")
        if not phone or not password:
            raise RuntimeError("TQSDK_PHONE or TQSDK_PASSWORD not set in .env")

        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        api = TqApi(auth=TqAuth(phone, password))
        try:
            klines_map = {}
            for sym in symbol_list:
                try:
                    klines_map[sym] = api.get_kline_serial(sym, duration_seconds=duration, data_length=200)
                except Exception as exc:
                    err_str = str(exc)
                    if "non-existent" in err_str:
                        self.logger.warning("tqsdk skip non-existent instrument: %s", sym)
                        continue
                    self.logger.warning("tqsdk get_kline_serial failed for %s: %s", sym, exc)

            # 带超时的 wait_update，防止单合约卡死拖垮全链
            try:
                api.wait_update(deadline=time.time() + 15)
            except Exception as exc:
                self.logger.warning("tqsdk wait_update error: %s, proceeding with available data", exc)
            time.sleep(1)

            for sym, klines in klines_map.items():
                try:
                    df = klines.copy()
                    if df is not None and len(df) > 0:
                        for idx in range(len(df)):
                            row = df.iloc[idx]
                            dt_val = self._normalize_timestamp(row.get("datetime", timestamp), timestamp)
                            records.append({
                                "source_type": "tqsdk_minute",
                                "symbol_or_indicator": sym,
                                "timestamp": dt_val,
                                "payload": {
                                    "symbol": sym,
                                    "open": float(row.get("open", 0)),
                                    "high": float(row.get("high", 0)),
                                    "low": float(row.get("low", 0)),
                                    "close": float(row.get("close", 0)),
                                    "volume": int(row.get("volume", 0)),
                                    "open_oi": int(row.get("open_oi", 0)),
                                    "duration": duration,
                                    "mode": "live",
                                },
                            })
                        self.logger.info("tqsdk fetched: %s rows=%d", sym, len(df))
                except Exception as exc:
                    self.logger.warning("tqsdk parse failed for %s: %s", sym, exc)
        finally:
            api.close()

        if not records:
            raise RuntimeError("tqsdk fetched no data for any symbol")
        return records

    @staticmethod
    def _normalize_timestamp(raw_value: Any, fallback: str) -> str:
        def _to_shanghai_iso(value: Any) -> str | None:
            parsed = pd.to_datetime(value, errors="coerce")
            if pd.isna(parsed):
                return None
            if getattr(parsed, "tzinfo", None) is None:
                return parsed.isoformat()
            return parsed.tz_convert("Asia/Shanghai").tz_localize(None).isoformat()

        if raw_value is None:
            return fallback

        try:
            if hasattr(raw_value, "item"):
                raw_value = raw_value.item()
        except Exception:
            pass

        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if not stripped:
                return fallback
            if any(sep in stripped for sep in ("-", ":", "T")):
                normalized = _to_shanghai_iso(stripped)
                return normalized or fallback
            try:
                raw_value = int(float(stripped))
            except (TypeError, ValueError):
                return fallback

        if isinstance(raw_value, (int, float)):
            parsed = pd.to_datetime(int(raw_value), unit="ns", utc=True, errors="coerce")
            if pd.isna(parsed):
                return fallback
            return parsed.tz_convert("Asia/Shanghai").tz_localize(None).isoformat()

        normalized = _to_shanghai_iso(raw_value)
        return normalized or fallback

    def _mock_records(self, *, symbol_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [{"source_type": "tqsdk_minute", "symbol_or_indicator": sym, "timestamp": timestamp,
                 "payload": {"symbol": sym, "open": 4000.0, "high": 4050.0, "low": 3980.0,
                             "close": 4020.0, "volume": 10000, "open_oi": 50000, "duration": 60, "mode": "mock"}}
                for sym in symbol_list]
