"""Sentiment data collector using AkShare margin trading data."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from collectors.base import BaseCollector


class SentimentCollector(BaseCollector):
    """Collect market sentiment via margin trading data (AkShare)."""

    DEFAULT_SYMBOLS = ["margin_sh", "margin_sz", "north_flow", "vix", "market_activity"]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="sentiment", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, symbols: list[str] | None = None, sources: list[str] | None = None, as_of: str | None = None) -> list[dict[str, Any]]:
        _ = sources
        symbol_list = symbols or self.DEFAULT_SYMBOLS
        if self.use_mock:
            return self._mock_records(symbol_list=symbol_list, as_of=as_of)
        try:
            return self._fetch_live(symbol_list=symbol_list, as_of=as_of)
        except Exception as exc:
            self.logger.warning("sentiment live fetch failed: %s, falling back to mock", exc)
            return self._mock_records(symbol_list=symbol_list, as_of=as_of)

    def _fetch_live(self, *, symbol_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        import akshare as ak
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        # --- 融资融券 ---
        margin_fetchers = {
            "margin_sh": lambda: ak.macro_china_market_margin_sh(),
            "margin_sz": lambda: ak.macro_china_market_margin_sz(),
        }
        for name in symbol_list:
            fn = margin_fetchers.get(name)
            if fn:
                try:
                    df = fn()
                    time.sleep(0.5)
                    if df is not None and not df.empty:
                        valid = df.tail(30)
                        for _, row in valid.iterrows():
                            records.append({
                                "source_type": "sentiment",
                                "symbol_or_indicator": name,
                                "timestamp": str(row.get("日期", timestamp)),
                                "payload": {
                                    "indicator": name,
                                    "margin_buy": float(row.get("融资买入额", 0)),
                                    "margin_balance": float(row.get("融资余额", 0)),
                                    "short_sell": float(row.get("融券卖出量", 0)),
                                    "short_balance": float(row.get("融券余额", 0)),
                                    "total_balance": float(row.get("融资融券余额", 0)),
                                    "mode": "live",
                                },
                            })
                        self.logger.info("sentiment fetched: %s rows=%d", name, len(valid))
                except Exception as exc:
                    self.logger.warning("sentiment fetch failed for %s: %s", name, exc)

        # --- 北向资金 (stock_hsgt_fund_flow_summary_em) ---
        # 返回 4 行汇总: 沪股通/深股通/北向合计/南向合计
        # 列: 交易日, 类型, 成交净买额, 资金净流入, 当日资金余额 等
        if "north_flow" in symbol_list:
            try:
                df = ak.stock_hsgt_fund_flow_summary_em()
                time.sleep(0.5)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        date_val = row.get("交易日", row.get("日期", timestamp))
                        net_buy = 0.0
                        for col in ("成交净买额", "资金净流入", "当日净流入", "value"):
                            v = row.get(col)
                            if v is not None:
                                try:
                                    net_buy = float(v)
                                    break
                                except (ValueError, TypeError):
                                    continue
                        flow_type = str(row.get("类型", row.get("板块", "")))
                        records.append({
                            "source_type": "sentiment",
                            "symbol_or_indicator": "north_flow",
                            "timestamp": str(date_val),
                            "payload": {
                                "indicator": "north_flow",
                                "flow_type": flow_type,
                                "net_buy": net_buy,
                                "balance": float(row.get("当日资金余额", 0) or 0),
                                "mode": "live",
                            },
                        })
                    self.logger.info("sentiment fetched: north_flow rows=%d", len(df))
            except Exception as exc:
                self.logger.warning("sentiment fetch failed for north_flow: %s", exc)

        # --- 中国波动率 QVIX (50ETF期权) 替代 VIX ---
        if "vix" in symbol_list:
            try:
                df = ak.index_option_50etf_qvix()
                time.sleep(0.5)
                if df is not None and not df.empty:
                    valid = df.tail(30)
                    for _, row in valid.iterrows():
                        date_val = row.get("日期", row.get("date", timestamp))
                        close_val = row.get("close", row.get("收盘", row.get("qvix", 0)))
                        try:
                            close_val = float(close_val)
                        except (ValueError, TypeError):
                            close_val = 0.0
                        records.append({
                            "source_type": "sentiment",
                            "symbol_or_indicator": "vix",
                            "timestamp": str(date_val),
                            "payload": {
                                "indicator": "vix",
                                "open": float(row.get("open", row.get("开盘", 0))),
                                "high": float(row.get("high", row.get("最高", 0))),
                                "low": float(row.get("low", row.get("最低", 0))),
                                "close": close_val,
                                "mode": "live",
                            },
                        })
                    self.logger.info("sentiment fetched: qvix rows=%d", len(valid))
            except Exception as exc:
                self.logger.warning("sentiment fetch failed for vix/qvix: %s", exc)

        # --- 市场情绪综合（乐估网市场活跃度）---
        # 返回截面数据: 12 行 item/value 格式 (非时序)
        if "market_activity" in symbol_list:
            try:
                df = ak.stock_market_activity_legu()
                time.sleep(0.5)
                if df is not None and not df.empty:
                    # item/value 格式 → 每项生成一条记录
                    for _, row in df.iterrows():
                        item_name = str(row.get("item", row.get("指标", "")))
                        item_val = 0.0
                        for col in ("value", "数值", "大盘活跃度"):
                            v = row.get(col)
                            if v is not None:
                                try:
                                    item_val = float(v)
                                    break
                                except (ValueError, TypeError):
                                    continue
                        records.append({
                            "source_type": "sentiment",
                            "symbol_or_indicator": "market_activity",
                            "timestamp": timestamp,
                            "payload": {
                                "indicator": "market_activity",
                                "item": item_name,
                                "value": item_val,
                                "mode": "live",
                            },
                        })
                    self.logger.info("sentiment fetched: market_activity rows=%d", len(df))
            except Exception as exc:
                self.logger.warning("sentiment fetch failed for market_activity: %s", exc)

        if not records:
            raise RuntimeError("all sentiment fetchers failed")
        return records

    def _mock_records(self, *, symbol_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [{"source_type": "sentiment", "symbol_or_indicator": sym, "timestamp": timestamp,
                 "payload": {"symbol": sym, "bullish": 0.6, "bearish": 0.3, "neutral": 0.1, "mode": "mock"}}
                for sym in symbol_list]
