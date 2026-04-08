"""AkShare backup collector with real API integration."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


# Mapping: internal symbol prefix -> AkShare sina symbol for continuous contract
_DOMESTIC_SYMBOL_MAP = {
    "SHFE.rb": "RB0", "SHFE.hc": "HC0", "SHFE.ru": "RU0", "SHFE.cu": "CU0",
    "SHFE.al": "AL0", "SHFE.zn": "ZN0", "SHFE.pb": "PB0", "SHFE.ni": "NI0",
    "SHFE.sn": "SN0", "SHFE.au": "AU0", "SHFE.ag": "AG0", "SHFE.bu": "BU0",
    "SHFE.sp": "SP0", "SHFE.ss": "SS0", "SHFE.fu": "FU0",
    "DCE.i": "I0", "DCE.m": "M0", "DCE.c": "C0", "DCE.y": "Y0",
    "DCE.p": "P0", "DCE.pp": "PP0", "DCE.v": "V0", "DCE.j": "J0",
    "DCE.jm": "JM0", "DCE.l": "L0", "DCE.eg": "EG0", "DCE.eb": "EB0",
    "CZCE.CF": "CF0", "CZCE.TA": "TA0", "CZCE.MA": "MA0", "CZCE.OI": "OI0",
    "CZCE.SR": "SR0", "CZCE.RM": "RM0", "CZCE.FG": "FG0", "CZCE.SA": "SA0",
    "CZCE.AP": "AP0", "CZCE.PF": "PF0", "CZCE.UR": "UR0",
    "INE.sc": "SC0", "CFFEX.IF": "IF0", "CFFEX.IC": "IC0", "CFFEX.IH": "IH0",
}


class AkshareBackupCollector(BaseCollector):
    """Backup collector using real AkShare API for domestic/overseas futures and stocks."""

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="akshare_backup", **kwargs)
        self.use_mock = use_mock

    def collect(
        self,
        *,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        freq: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Collect data via real AkShare API. No mock fallback."""
        if freq == "1min":
            return self._fetch_domestic_futures_minute(symbol=symbol, period="1")

        # Determine if stock or futures
        if symbol.endswith(".SZ") or symbol.endswith(".SH"):
            return self._fetch_stock_daily(symbol=symbol, start_date=start_date or start, end_date=end_date or end)

        # Try domestic futures first
        return self._fetch_domestic_futures_daily(symbol=symbol, start_date=start_date or start, end_date=end_date or end)

    def _fetch_domestic_futures_minute(
        self, *, symbol: str, period: str = "1"
    ) -> list[dict[str, Any]]:
        """Fetch domestic futures minute kline via ak.futures_zh_minute_sina.

        Parameters
        ----------
        symbol : str  e.g. "SHFE.rb2405"
        period : str  "1", "5", "15", "30", "60"
        """
        import akshare as ak

        sina_symbol = _DOMESTIC_SYMBOL_MAP.get(symbol)
        if not sina_symbol:
            parts = symbol.split(".")
            if len(parts) == 2:
                base_code = ""
                for ch in parts[1]:
                    if ch.isdigit():
                        break
                    base_code += ch
                sina_symbol = _DOMESTIC_SYMBOL_MAP.get(f"{parts[0]}.{base_code}")

        if not sina_symbol:
            self.logger.warning("akshare minute: no mapping for symbol %s", symbol)
            return []

        try:
            df = ak.futures_zh_minute_sina(symbol=sina_symbol, period=period)
            time.sleep(0.2)
        except Exception as exc:
            self.logger.error(
                "akshare futures_zh_minute_sina failed for %s (sina=%s): %s",
                symbol, sina_symbol, exc,
            )
            return []

        if df is None or df.empty:
            return []

        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "symbol": symbol,
                "timestamp": str(row.get("datetime", row.get("date", ""))),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("volume", 0)),
                "hold": float(row.get("hold", row.get("position", 0))),
            })
        self.logger.info(
            "akshare minute: symbol=%s sina=%s records=%d",
            symbol, sina_symbol, len(records),
        )
        return records

    def _fetch_domestic_futures_daily(self, *, symbol: str, start_date: str | None, end_date: str | None) -> list[dict[str, Any]]:
        """Fetch domestic futures daily via ak.futures_zh_daily_sina."""
        import akshare as ak

        # Convert symbol to AkShare format
        sina_symbol = _DOMESTIC_SYMBOL_MAP.get(symbol)
        if not sina_symbol:
            # Try to extract: "SHFE.rb2510" -> try "SHFE.rb" -> "RB0"
            parts = symbol.split(".")
            if len(parts) == 2:
                exchange = parts[0]
                code = parts[1]
                # Strip trailing digits to get base
                base_code = ""
                for ch in code:
                    if ch.isdigit():
                        break
                    base_code += ch
                sina_symbol = _DOMESTIC_SYMBOL_MAP.get(f"{exchange}.{base_code}")

        if not sina_symbol:
            self.logger.warning("akshare: no mapping for symbol %s", symbol)
            return []

        try:
            df = ak.futures_zh_daily_sina(symbol=sina_symbol)
            time.sleep(0.2)
        except Exception as exc:
            self.logger.error("akshare futures_zh_daily_sina failed for %s: %s", sina_symbol, exc)
            return []

        if df is None or df.empty:
            return []

        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            trade_date = str(row.get("date", ""))
            if start_date and trade_date < start_date:
                continue
            if end_date and trade_date > end_date:
                continue
            records.append({
                "symbol": symbol,
                "timestamp": trade_date,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("volume", 0)),
                "hold": float(row.get("hold", 0)),
                "settle": float(row.get("settle", 0)),
            })
        self.logger.info("akshare domestic futures: symbol=%s sina=%s records=%d", symbol, sina_symbol, len(records))
        return records

    def _fetch_stock_daily(self, *, symbol: str, start_date: str | None, end_date: str | None) -> list[dict[str, Any]]:
        """Fetch A-share stock daily via ak.stock_zh_a_hist."""
        import akshare as ak

        # Convert: 000001.SZ -> 000001
        stock_code = symbol.split(".")[0] if "." in symbol else symbol
        sd = start_date or "19910101"
        ed = end_date or datetime.now().strftime("%Y%m%d")
        # AkShare expects YYYYMMDD format
        sd_fmt = sd.replace("-", "")
        ed_fmt = ed.replace("-", "")

        try:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=sd_fmt, end_date=ed_fmt, adjust="qfq")
            time.sleep(0.2)
        except Exception as exc:
            self.logger.error("akshare stock_zh_a_hist failed for %s: %s", stock_code, exc)
            return []

        if df is None or df.empty:
            return []

        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "symbol": symbol,
                "timestamp": str(row.get("日期", "")),
                "open": float(row.get("开盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "close": float(row.get("收盘", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
            })
        self.logger.info("akshare stock daily: symbol=%s records=%d", symbol, len(records))
        return records

    def collect_overseas_futures(self, *, symbol: str) -> list[dict[str, Any]]:
        """Fetch overseas futures daily via ak.futures_foreign_hist."""
        import akshare as ak

        try:
            df = ak.futures_foreign_hist(symbol=symbol)
            time.sleep(0.3)
        except Exception as exc:
            self.logger.error("akshare futures_foreign_hist failed for %s: %s", symbol, exc)
            return []

        if df is None or df.empty:
            return []

        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "symbol": symbol,
                "timestamp": str(row.get("date", row.get("日期", ""))),
                "open": float(row.get("open", row.get("开盘", 0))),
                "high": float(row.get("high", row.get("最高", 0))),
                "low": float(row.get("low", row.get("最低", 0))),
                "close": float(row.get("close", row.get("收盘", 0))),
                "volume": float(row.get("volume", row.get("成交量", 0))),
            })
        self.logger.info("akshare overseas futures: symbol=%s records=%d", symbol, len(records))
        return records
