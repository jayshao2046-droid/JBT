"""Macro data collector using AkShare real API."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from src.collectors.base import BaseCollector


class MacroCollector(BaseCollector):
    """Collect macro indicators via AkShare (CPI/PPI/PMI/GDP)."""

    DEFAULT_COUNTRIES = ["CN", "US", "EU", "JP", "UK", "AU", "CA"]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="macro", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, countries: list[str] | None = None, as_of: str | None = None, full_history: bool = False) -> list[dict[str, Any]]:
        country_list = countries or self.DEFAULT_COUNTRIES
        if self.use_mock:
            return self._mock_records(country_list=country_list, as_of=as_of)
        try:
            return self._fetch_live(country_list=country_list, as_of=as_of, full_history=full_history)
        except Exception as exc:
            self.logger.warning("macro live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(country_list=country_list, as_of=as_of)

    def _fetch_live(self, *, country_list: list[str], as_of: str | None, full_history: bool = False) -> list[dict[str, Any]]:
        import akshare as ak
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()

        # AkShare macro functions return different column names:
        #   CN/US/EU: 商品, 日期, 今值, 预测值, 前值
        #   JP/UK/AU/CA: 时间, 现值, 前值, 发布日期
        VALUE_COLS = ["今值", "现值", "最新值", "value", "actual"]
        DATE_COLS = ["日期", "时间", "date"]
        FORECAST_COLS = ["预测值", "预期值", "forecast"]
        PREVIOUS_COLS = ["前值", "previous"]

        def _find_col(df_cols: list[str], candidates: list[str]) -> str | None:
            for c in candidates:
                if c in df_cols:
                    return c
            return None

        fetchers: dict[str, Any] = {
            # --- CN ---
            "CN.cpi_yoy": lambda: ak.macro_china_cpi_yearly(),
            "CN.ppi_yoy": lambda: ak.macro_china_ppi_yearly(),
            # --- US ---
            "US.cpi_yoy": lambda: ak.macro_usa_cpi_monthly(),
            "US.ppi_yoy": lambda: ak.macro_usa_ppi(),
            "US.pmi": lambda: ak.macro_usa_ism_pmi(),
            # --- EU ---
            "EU.cpi_yoy": lambda: ak.macro_euro_cpi_mom(),
            "EU.ppi_mom": lambda: ak.macro_euro_ppi_mom(),
            "EU.gdp_yoy": lambda: ak.macro_euro_gdp_yoy(),
            # --- JP ---
            "JP.cpi_yoy": lambda: ak.macro_japan_cpi_yearly(),
            "JP.unemployment": lambda: ak.macro_japan_unemployment_rate(),
            # --- UK ---
            "UK.cpi_yoy": lambda: ak.macro_uk_cpi_yearly(),
            "UK.gdp_yoy": lambda: ak.macro_uk_gdp_yearly(),
            "UK.unemployment": lambda: ak.macro_uk_unemployment_rate(),
            # --- AU ---
            "AU.cpi_yoy": lambda: ak.macro_australia_cpi_quarterly(),
            "AU.unemployment": lambda: ak.macro_australia_unemployment_rate(),
            # --- CA ---
            "CA.cpi_yoy": lambda: ak.macro_canada_cpi_monthly(),
            "CA.unemployment": lambda: ak.macro_canada_unemployment_rate(),
        }

        for key, fn in fetchers.items():
            country_code = key.split(".")[0]
            if country_code not in country_list:
                continue
            try:
                df = fn()
                time.sleep(0.5)
                if df is not None and not df.empty:
                    cols = list(df.columns)
                    val_col = _find_col(cols, VALUE_COLS)
                    date_col = _find_col(cols, DATE_COLS)
                    forecast_col = _find_col(cols, FORECAST_COLS)
                    prev_col = _find_col(cols, PREVIOUS_COLS)

                    if not val_col:
                        self.logger.warning("macro %s: 无法匹配值列, 列名=%s", key, cols)
                        continue

                    _cleaned = df.dropna(subset=[val_col])
                    valid = _cleaned if full_history else _cleaned.tail(30)
                    for _, row in valid.iterrows():
                        ts = str(row[date_col]) if date_col else timestamp
                        val = row[val_col]
                        forecast = None
                        previous = None
                        if forecast_col and str(row.get(forecast_col, "")) != "nan":
                            try:
                                forecast = float(row[forecast_col])
                            except (ValueError, TypeError):
                                pass
                        if prev_col and str(row.get(prev_col, "")) != "nan":
                            try:
                                previous = float(row[prev_col])
                            except (ValueError, TypeError):
                                pass
                        records.append({
                            "source_type": "macro",
                            "symbol_or_indicator": key,
                            "timestamp": ts,
                            "payload": {
                                "country": country_code,
                                "indicator": key,
                                "value": float(val),
                                "forecast": forecast,
                                "previous": previous,
                                "mode": "live",
                            },
                        })
                    self.logger.info("macro fetched: %s rows=%d", key, len(valid))
            except Exception as exc:
                self.logger.warning("macro fetch failed for %s: %s", key, exc)

        if not records:
            raise RuntimeError("all macro fetchers failed")
        return records

    def _mock_records(self, *, country_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        indicators = ["cpi_yoy", "ppi_yoy"]
        return [{"source_type": "macro", "symbol_or_indicator": f"{c}.{ind}", "timestamp": timestamp,
                 "payload": {"country": c, "indicator": ind, "value": 2.0, "unit": "pct", "mode": "mock"}}
                for c in country_list for ind in indicators]
