"""Shipping index collector using AkShare + httpx fallback."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


class ShippingCollector(BaseCollector):
    """Collect ocean shipping indicators via AkShare + httpx scraping.

    AkShare 1.18.x 支持 4 个 Baltic 指数: bdi/bci/bpi/bcti
    SCFI/CCFI/BSI/BHSI/BDTI 已从 AkShare 移除，通过 httpx 备源采集。
    受限指标标注：SCFI/CCFI 需上海航运交易所付费 API 或手动更新。
    """

    DEFAULT_INDICATORS = ["bdi", "bci", "bpi", "bcti", "scfi", "ccfi"]

    # 受限指标说明
    RESTRICTED_INDICATORS = {
        "scfi": "上海出口集装箱运价指数 — 上海航运交易所(sse.net.cn)，免费延迟数据",
        "ccfi": "中国出口集装箱运价指数 — 上海航运交易所(sse.net.cn)，免费延迟数据",
    }

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="shipping", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, indicators: list[str] | None = None, as_of: str | None = None, full_history: bool = False) -> list[dict[str, Any]]:
        indicator_list = indicators or self.DEFAULT_INDICATORS
        if self.use_mock:
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)
        try:
            return self._fetch_live(indicator_list=indicator_list, as_of=as_of, full_history=full_history)
        except Exception as exc:
            self.logger.warning("shipping live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(indicator_list=indicator_list, as_of=as_of)

    def _fetch_live(self, *, indicator_list: list[str], as_of: str | None, full_history: bool = False) -> list[dict[str, Any]]:
        import akshare as ak
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        # AkShare Baltic indices
        akshare_fetchers = {
            "bdi": lambda: ak.macro_shipping_bdi(),
            "bci": lambda: ak.macro_shipping_bci(),
            "bpi": lambda: ak.macro_shipping_bpi(),
            "bcti": lambda: ak.macro_shipping_bcti(),
        }

        for name in indicator_list:
            fn = akshare_fetchers.get(name)
            if fn:
                try:
                    df = fn()
                    time.sleep(0.5)
                    if df is not None and not df.empty:
                        val_col = None
                        for c in ["最新值", "现值", "收盘价", "value"]:
                            if c in df.columns:
                                val_col = c
                                break
                        if not val_col:
                            self.logger.warning("shipping %s: 无法匹配值列, 列名=%s", name, list(df.columns))
                            continue
                        date_col = "日期" if "日期" in df.columns else ("时间" if "时间" in df.columns else None)
                        _cleaned = df.dropna(subset=[val_col])
                        valid = _cleaned if full_history else _cleaned.tail(30)
                        for _, row in valid.iterrows():
                            records.append({
                                "source_type": "shipping",
                                "symbol_or_indicator": name,
                                "timestamp": str(row[date_col]) if date_col else timestamp,
                                "payload": {
                                    "indicator": name,
                                    "value": float(row[val_col]),
                                    "change_pct": float(row.get("涨跌幅", 0)),
                                    "mode": "live",
                                },
                            })
                        self.logger.info("shipping fetched: %s rows=%d", name, len(valid))
                except Exception as exc:
                    self.logger.warning("shipping fetch failed for %s: %s", name, exc)
                continue

            # httpx 备源：受限指标通过公开页面解析
            if name in self.RESTRICTED_INDICATORS:
                try:
                    idx_records = self._fetch_restricted_index(name=name, timestamp=timestamp)
                    records.extend(idx_records)
                except Exception as exc:
                    self.logger.warning("shipping restricted fetch failed for %s: %s (note: %s)",
                                        name, exc, self.RESTRICTED_INDICATORS[name])

        if not records:
            raise RuntimeError("all shipping fetchers failed")
        return records

    def _fetch_restricted_index(self, *, name: str, timestamp: str) -> list[dict[str, Any]]:
        """Attempt to fetch SCFI/CCFI from Investing.com via httpx."""
        import httpx
        # Investing.com 提供 Baltic 和集装箱运价指数的公开页面
        ticker_map = {
            "scfi": "https://www.investing.com/indices/shanghai-containerized-freight",
            "ccfi": "https://www.investing.com/indices/china-containerized-freight",
        }
        url = ticker_map.get(name)
        if not url:
            return []
        resp = httpx.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
        resp.raise_for_status()

        import re
        # 从页面提取最新值
        match = re.search(r'data-test="instrument-price-last"[^>]*>([0-9,.]+)', resp.text)
        if not match:
            self.logger.warning("shipping %s: 无法从页面解析价格", name)
            return []
        value = float(match.group(1).replace(",", ""))
        self.logger.info("shipping restricted fetched: %s value=%.2f", name, value)
        return [{
            "source_type": "shipping",
            "symbol_or_indicator": name,
            "timestamp": timestamp,
            "payload": {
                "indicator": name,
                "value": value,
                "mode": "live_restricted",
                "note": self.RESTRICTED_INDICATORS.get(name, ""),
            },
        }]

    def _mock_records(self, *, indicator_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [{"source_type": "shipping", "symbol_or_indicator": ind, "timestamp": timestamp,
                 "payload": {"indicator": ind, "value": round(1000.0 + i * 100, 2), "mode": "mock"}}
                for i, ind in enumerate(indicator_list)]
