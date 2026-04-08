"""Volatility index collector using AkShare QVIX + CBOE VIX data."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


class VolatilityCollector(BaseCollector):
    """Collect volatility indices (QVIX + CBOE VIX) via AkShare and yfinance."""

    DEFAULT_INDICATORS = ["50etf_qvix", "300etf_qvix", "cboe_vix", "cboe_vxn"]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="volatility", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, indicators: list[str] | None = None, as_of: str | None = None, full_history: bool = False) -> list[dict[str, Any]]:
        indicator_list = indicators or self.DEFAULT_INDICATORS
        if self.use_mock:
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)
        try:
            return self._fetch_live(indicator_list=indicator_list, as_of=as_of, full_history=full_history)
        except Exception as exc:
            self.logger.warning("volatility live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)

    def _fetch_live(self, *, indicator_list: list[str], as_of: str | None, full_history: bool = False) -> list[dict[str, Any]]:
        import akshare as ak
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        # AkShare QVIX fetchers
        akshare_fetchers = {
            "50etf_qvix": lambda: ak.index_option_50etf_qvix(),
            "300etf_qvix": lambda: ak.index_option_300etf_qvix(),
        }

        # CBOE VIX via yfinance (ticker symbols)
        yfinance_tickers = {
            "cboe_vix": "^VIX",
            "cboe_vxn": "^VXN",
        }

        for name in indicator_list:
            # AkShare path
            ak_fn = akshare_fetchers.get(name)
            if ak_fn:
                try:
                    df = ak_fn()
                    time.sleep(0.5)
                    if df is not None and not df.empty:
                        _cleaned = df.dropna(subset=["close"])
                        valid = _cleaned if full_history else _cleaned.tail(30)
                        for _, row in valid.iterrows():
                            records.append({
                                "source_type": "volatility",
                                "symbol_or_indicator": name,
                                "timestamp": str(row.get("date", timestamp)),
                                "payload": {
                                    "indicator": name,
                                    "open": float(row.get("open", 0)),
                                    "high": float(row.get("high", 0)),
                                    "low": float(row.get("low", 0)),
                                    "close": float(row.get("close", 0)),
                                    "mode": "live",
                                },
                            })
                        self.logger.info("volatility fetched: %s rows=%d", name, len(valid))
                except Exception as exc:
                    self.logger.warning("volatility fetch failed for %s: %s", name, exc)
                continue

            # yfinance path for CBOE indices
            ticker = yfinance_tickers.get(name)
            if ticker:
                try:
                    records.extend(self._fetch_yfinance_vix(name=name, ticker=ticker, timestamp=timestamp, full_history=full_history))
                except Exception as exc:
                    self.logger.warning("volatility yfinance fetch failed for %s: %s", name, exc)

        if not records:
            raise RuntimeError("all volatility fetchers failed")
        return records

    def _fetch_yfinance_vix(self, *, name: str, ticker: str, timestamp: str, full_history: bool = False) -> list[dict[str, Any]]:
        """Fetch CBOE VIX/VXN via yfinance."""
        from services.data.src.utils.proxy import overseas_proxy_env
        try:
            import yfinance as yf
        except ImportError:
            self.logger.warning("yfinance not installed, skipping %s", name)
            return []
        _period = "max" if full_history else "1mo"
        with overseas_proxy_env():
            data = yf.download(ticker, period=_period, interval="1d", progress=False)
        if data is None or data.empty:
            return []
        # flatten MultiIndex columns from yfinance 1.x (e.g. ("Open", "^VIX") → "Open")
        import pandas as pd
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        records = []
        _rows = data if full_history else data.tail(30)
        for idx, row in _rows.iterrows():
            records.append({
                "source_type": "volatility",
                "symbol_or_indicator": name,
                "timestamp": str(idx.date()) if hasattr(idx, "date") else str(idx),
                "payload": {
                    "indicator": name,
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)),
                    "mode": "live",
                },
            })
        self.logger.info("volatility yfinance fetched: %s rows=%d", name, len(records))
        return records

    def _mock_records(self, *, indicator_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [{"source_type": "volatility", "symbol_or_indicator": ind, "timestamp": timestamp,
                 "payload": {"indicator": ind, "value": 20.0 + i, "mode": "mock"}}
                for i, ind in enumerate(indicator_list)]
