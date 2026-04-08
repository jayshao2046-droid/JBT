"""A-share stock minute K-line collector using AkShare.

D107 重写:
  - 主源: ak.stock_zh_a_hist_min_em (东方财富), ~100次/分钟
  - 备源: ak.stock_zh_a_minute (新浪), 历史更长(8天)
  - 覆盖: 全量 A 股 5489 只
  - 模式: 盘中实时采集(每2分钟) + 盘后增量 + 历史回补(2016起)
  - 不使用 Tushare 分钟数据 (付费)
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from services.data.src.collectors.base import BaseCollector


class StockMinuteCollector(BaseCollector):
    """Collect A-share minute K-line data via AkShare.

    Primary: ak.stock_zh_a_hist_min_em (东方财富)
    Backup:  ak.stock_zh_a_minute (新浪)
    """

    def __init__(
        self,
        *,
        symbols: list[str] | None = None,
        period: str = "1",
        batch_size: int = 100,
        batch_sleep: float = 30.0,
        per_stock_sleep: float = 0.5,
        **kwargs: Any,
    ) -> None:
        kwargs.pop('name', None)
        super().__init__(name="stock_minute", **kwargs)
        self.symbols = symbols or []
        self.period = period  # "1", "5", "15", "30", "60"
        self.batch_size = batch_size
        self.batch_sleep = batch_sleep
        self.per_stock_sleep = per_stock_sleep

    def collect(
        self,
        *,
        symbols: list[str] | None = None,
        period: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        """采集指定股票列表的分钟 K 线数据。"""
        symbol_list = symbols or self.symbols
        cur_period = period or self.period
        return self._fetch_batch(
            symbol_list=symbol_list,
            period=cur_period,
            start_date=start_date,
            end_date=end_date,
        )

    def _fetch_batch(
        self,
        *,
        symbol_list: list[str],
        period: str,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, Any]]:
        """分批采集，避免被封 IP。"""
        all_records: list[dict[str, Any]] = []

        for i, symbol in enumerate(symbol_list):
            rows = self._fetch_one_stock(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
            )
            if rows:
                all_records.extend(rows)

            time.sleep(self.per_stock_sleep)

            # 每批次暂停
            if (i + 1) % self.batch_size == 0 and i + 1 < len(symbol_list):
                self.logger.info(
                    "批次暂停: 已完成 %d/%d 只, 休息 %.0fs",
                    i + 1, len(symbol_list), self.batch_sleep,
                )
                time.sleep(self.batch_sleep)

        self.logger.info(
            "采集完成: %d 只股票, 共 %d 条记录",
            len(symbol_list), len(all_records),
        )
        return all_records

    def _fetch_one_stock(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, Any]]:
        """采集单只股票分钟数据：主源东方财富，备源新浪。"""
        rows = self._fetch_eastmoney(
            symbol=symbol, period=period,
            start_date=start_date, end_date=end_date,
        )
        if rows:
            return rows

        # 备源: 新浪
        rows = self._fetch_sina(symbol=symbol, period=period)
        return rows

    def _fetch_eastmoney(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, Any]]:
        """主源: ak.stock_zh_a_hist_min_em (东方财富)."""
        try:
            import akshare as ak

            kwargs: dict[str, Any] = {
                "symbol": symbol,
                "period": period,
                "adjust": "",
            }
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date

            df = ak.stock_zh_a_hist_min_em(**kwargs)
            if df is None or df.empty:
                return []

            rows: list[dict[str, Any]] = []
            for _, row in df.iterrows():
                rows.append(self._make_record(
                    symbol=symbol,
                    ts=str(row.get("时间", "")),
                    open_=float(row.get("开盘", 0)),
                    high=float(row.get("最高", 0)),
                    low=float(row.get("最低", 0)),
                    close=float(row.get("收盘", 0)),
                    volume=float(row.get("成交量", 0)),
                    amount=float(row.get("成交额", 0)),
                    source="akshare_eastmoney",
                ))
            self.logger.info("东方财富采集: %s period=%s rows=%d", symbol, period, len(rows))
            return rows
        except Exception as exc:
            self.logger.debug("东方财富采集失败 %s: %s", symbol, exc)
            return []

    def _fetch_sina(
        self, *, symbol: str, period: str
    ) -> list[dict[str, Any]]:
        """备源: ak.stock_zh_a_minute (新浪)."""
        try:
            import akshare as ak

            # 新浪格式: sh600519 / sz000001
            prefix = "sh" if symbol.startswith("6") else "sz"
            sina_symbol = f"{prefix}{symbol}"

            df = ak.stock_zh_a_minute(symbol=sina_symbol, period=period, adjust="")
            if df is None or df.empty:
                return []

            rows: list[dict[str, Any]] = []
            for _, row in df.iterrows():
                rows.append(self._make_record(
                    symbol=symbol,
                    ts=str(row.get("day", "")),
                    open_=float(row.get("open", 0)),
                    high=float(row.get("high", 0)),
                    low=float(row.get("low", 0)),
                    close=float(row.get("close", 0)),
                    volume=float(row.get("volume", 0)),
                    amount=float(row.get("amount", 0)),
                    source="akshare_sina",
                ))
            self.logger.info("新浪采集: %s period=%s rows=%d", symbol, period, len(rows))
            return rows
        except Exception as exc:
            self.logger.debug("新浪采集失败 %s: %s", symbol, exc)
            return []

    @staticmethod
    def _make_record(
        *,
        symbol: str,
        ts: str,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        amount: float,
        source: str,
    ) -> dict[str, Any]:
        return {
            "source_type": "stock_minute",
            "symbol_or_indicator": symbol,
            "timestamp": ts,
            "payload": {
                "symbol": symbol,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "amount": amount,
                "source": source,
                "mode": "live",
            },
        }

    @staticmethod
    def get_all_a_stock_codes() -> list[str]:
        """获取全部 A 股代码列表 (约 5489 只)。
        主源: 东方财富 (ak.stock_zh_a_spot_em)
        备源: Tushare stock_basic (仅代码列表，不涉及分钟数据)
        """
        import akshare as ak
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                codes = df["代码"].tolist()
                return [str(c) for c in codes]
        except Exception:
            pass

        # 备源: Tushare
        try:
            import os
            import tushare as ts
            token = os.environ.get("TUSHARE_TOKEN", "")
            pro = ts.pro_api(token=token)
            df = pro.stock_basic(exchange="", list_status="L", fields="ts_code")
            if df is not None and not df.empty:
                return sorted(df["ts_code"].str[:6].tolist())
        except Exception:
            pass

        return []
