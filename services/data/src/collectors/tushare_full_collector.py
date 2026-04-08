"""Tushare Pro 全量数据采集器 — 支持期货/股票/指数/基金/宏观全接口。"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from services.data.src.collectors.base import BaseCollector
from services.data.src.utils.logger import get_logger

logger = get_logger("tushare_full_collector")

# Tushare 交易所代码映射
EXCHANGE_MAP = {
    "SHFE": "SHF", "DCE": "DCE", "CZCE": "ZCE",
    "CFFEX": "CFX", "INE": "INE", "GFEX": "GFE",
}

# 主要指数列表
MAIN_INDICES = [
    "000001.SH",  # 上证指数
    "399001.SZ",  # 深证成指
    "399006.SZ",  # 创业板指
    "000300.SH",  # 沪深300
    "000905.SH",  # 中证500
    "000852.SH",  # 中证1000
    "000016.SH",  # 上证50
]


class TushareFullCollector(BaseCollector):
    """Tushare Pro 全量采集器，覆盖期货/股票/指数/基金/宏观等全部接口。"""

    RATE_LIMIT_SLEEP = 0.25  # 每次调用后等待（500次/分钟限制）
    BATCH_SIZE = 5000  # 分页批次大小

    def __init__(self, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="tushare_full", **kwargs)
        data_sources = self.config.get("data_sources", {})
        self.token = str(data_sources.get("tushare", {}).get("token", "") or "")
        # Try .env fallback
        if not self.token:
            self.token = os.environ.get("TUSHARE_TOKEN", "")
        if not self.token:
            env_path = Path(__file__).resolve().parents[3] / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("TUSHARE_TOKEN="):
                        self.token = line.split("=", 1)[1].strip()
        self._pro = None
        # Storage base
        storage_cfg = self.config.get("storage", {})
        self.base_path = Path(os.path.expanduser(
            storage_cfg.get("base_path", os.environ.get("DATA_STORAGE_ROOT", "~/jbt-data"))
        ))
        # Progress tracking
        self.progress_file = self.base_path / "tushare_full_progress.json"

    @property
    def pro(self):
        if self._pro is None:
            import tushare as ts
            self._pro = ts.pro_api(self.token)
        return self._pro

    def collect(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Required by BaseCollector — delegates to collect_all."""
        return self.collect_all(**kwargs)

    def collect_all(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Run all collection methods."""
        results = []
        results.extend(self.collect_fut_daily_all_exchanges())
        return results

    # ─── Helper: save to parquet ───

    def _save_df_parquet(self, df, category: str, sub_key: str, data_type: str) -> int:
        """Save a DataFrame to parquet under base_path/{category}/{sub_key}/{data_type}/records.parquet."""
        if df is None or (hasattr(df, "empty") and df.empty) or len(df) == 0:
            return 0
        out_dir = self.base_path / "parquet" / category / sub_key / data_type
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "records.parquet"

        table = pa.Table.from_pandas(df) if hasattr(df, "to_arrow") is False else pa.Table.from_pandas(df)
        if out_file.exists():
            existing = pq.read_table(out_file)
            table = pa.concat_tables([existing, table], promote_options="default")
        pq.write_table(table, out_file, compression="snappy")
        return len(df)

    def _save_records_parquet(self, records: list[dict], category: str, sub_key: str, data_type: str) -> int:
        """Save list of dicts to parquet."""
        if not records:
            return 0
        out_dir = self.base_path / "parquet" / category / sub_key / data_type
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "records.parquet"
        table = pa.Table.from_pylist(records)
        if out_file.exists():
            existing = pq.read_table(out_file)
            table = pa.concat_tables([existing, table], promote_options="default")
        pq.write_table(table, out_file, compression="snappy")
        return len(records)

    def _rate_limit(self):
        time.sleep(self.RATE_LIMIT_SLEEP)

    # ═══════════════════════════════════════════
    # A. 期货类
    # ═══════════════════════════════════════════

    def collect_fut_basic(self, exchange: str = "") -> list[dict[str, Any]]:
        """期货合约基本信息。"""
        t0 = time.time()
        df = self.pro.fut_basic(exchange=exchange, fut_type="1",
                                fields="ts_code,symbol,exchange,name,fut_code,multiplier,"
                                       "trade_unit,per_unit,quote_unit,quote_unit_desc,"
                                       "d_mode_desc,list_date,delist_date,d_month,last_ddate,"
                                       "trade_time_desc")
        self._rate_limit()
        records = df.to_dict("records") if df is not None and not df.empty else []
        saved = self._save_records_parquet(records, "futures", exchange or "ALL", "fut_basic")
        logger.info("fut_basic exchange=%s rows=%d saved=%d elapsed=%.1fs", exchange, len(records), saved, time.time() - t0)
        return records

    def collect_fut_daily(self, ts_code: str = "", trade_date: str = "",
                          start_date: str = "20150101", end_date: str = "") -> list[dict[str, Any]]:
        """期货日K线。支持 ts_code 或 trade_date 查询。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        all_records: list[dict[str, Any]] = []

        if ts_code:
            # By single ts_code, paginate
            offset = 0
            while True:
                df = self.pro.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date,
                                        limit=self.BATCH_SIZE, offset=offset)
                self._rate_limit()
                if df is None or df.empty:
                    break
                batch = df.to_dict("records")
                all_records.extend(batch)
                if len(batch) < self.BATCH_SIZE:
                    break
                offset += self.BATCH_SIZE
            saved = self._save_records_parquet(all_records, "futures", ts_code, "fut_daily")
        elif trade_date:
            df = self.pro.fut_daily(trade_date=trade_date)
            self._rate_limit()
            if df is not None and not df.empty:
                all_records = df.to_dict("records")
            saved = self._save_records_parquet(all_records, "futures", f"date_{trade_date}", "fut_daily")
        else:
            saved = 0

        logger.info("fut_daily ts_code=%s trade_date=%s rows=%d elapsed=%.1fs",
                     ts_code, trade_date, len(all_records), time.time() - t0)
        return all_records

    def collect_fut_daily_all_exchanges(self, start_date: str = "20150101") -> list[dict[str, Any]]:
        """采集全交易所活跃合约的期货日K线。"""
        all_records: list[dict[str, Any]] = []
        exchanges = ["SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX"]
        today = datetime.now().strftime("%Y%m%d")

        for exchange in exchanges:
            try:
                ts_exchange = EXCHANGE_MAP.get(exchange, exchange)
                basics = self.collect_fut_basic(exchange=exchange)
                # Get unique product codes (continuous contracts)
                seen_products = set()
                for item in basics:
                    delist = item.get("delist_date", "")
                    if delist and delist >= today:
                        fut_code = item.get("fut_code", "")
                        if fut_code and fut_code not in seen_products:
                            seen_products.add(fut_code)
                            ts_code = item.get("ts_code", "")
                            if ts_code:
                                try:
                                    recs = self.collect_fut_daily(ts_code=ts_code, start_date=start_date)
                                    all_records.extend(recs)
                                except Exception as exc:
                                    logger.warning("fut_daily failed for %s: %s", ts_code, exc)
            except Exception as exc:
                logger.error("fut_basic failed for exchange %s: %s", exchange, exc)

        logger.info("fut_daily_all_exchanges total=%d", len(all_records))
        return all_records

    def collect_fut_holding(self, symbol: str = "", trade_date: str = "",
                            start_date: str = "20200101", end_date: str = "") -> list[dict[str, Any]]:
        """期货持仓排名（需2000积分）。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.fut_holding(symbol=symbol, trade_date=trade_date,
                                      start_date=start_date, end_date=end_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fut_holding failed: %s", exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "futures", symbol or f"date_{trade_date}", "fut_holding")
        logger.info("fut_holding symbol=%s rows=%d elapsed=%.1fs", symbol, len(records), time.time() - t0)
        return records

    def collect_fut_wsr(self, trade_date: str = "", start_date: str = "20200101",
                        end_date: str = "") -> list[dict[str, Any]]:
        """仓单日报（需2000积分）。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.fut_wsr(trade_date=trade_date, start_date=start_date, end_date=end_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fut_wsr failed: %s", exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "futures", f"wsr_{trade_date or 'all'}", "fut_wsr")
        logger.info("fut_wsr rows=%d elapsed=%.1fs", len(records), time.time() - t0)
        return records

    def collect_fut_settle(self, ts_code: str = "", trade_date: str = "",
                           start_date: str = "20200101", end_date: str = "") -> list[dict[str, Any]]:
        """结算价（需2000积分）。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.fut_settle(ts_code=ts_code, trade_date=trade_date,
                                     start_date=start_date, end_date=end_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fut_settle failed: %s", exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "futures", ts_code or f"date_{trade_date}", "fut_settle")
        logger.info("fut_settle rows=%d elapsed=%.1fs", len(records), time.time() - t0)
        return records

    # ═══════════════════════════════════════════
    # B. 股票类
    # ═══════════════════════════════════════════

    def collect_stock_basic(self) -> list[dict[str, Any]]:
        """A股基本信息。"""
        t0 = time.time()
        df = self.pro.stock_basic(exchange="", list_status="L",
                                  fields="ts_code,symbol,name,area,industry,market,list_date")
        self._rate_limit()
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", "ALL", "stock_basic")
        logger.info("stock_basic rows=%d elapsed=%.1fs", len(records), time.time() - t0)
        return records

    def collect_stock_daily(self, ts_code: str, start_date: str = "20100101",
                            end_date: str = "") -> list[dict[str, Any]]:
        """A股日K。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        all_records: list[dict[str, Any]] = []
        offset = 0
        while True:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date,
                                limit=self.BATCH_SIZE, offset=offset)
            self._rate_limit()
            if df is None or df.empty:
                break
            batch = df.to_dict("records")
            all_records.extend(batch)
            if len(batch) < self.BATCH_SIZE:
                break
            offset += self.BATCH_SIZE
        self._save_records_parquet(all_records, "stock", ts_code, "daily")
        logger.info("stock_daily ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(all_records), time.time() - t0)
        return all_records

    def collect_stock_daily_basic(self, trade_date: str) -> list[dict[str, Any]]:
        """每日基本面指标（PE/PB/PS/换手率）。"""
        t0 = time.time()
        try:
            df = self.pro.daily_basic(trade_date=trade_date,
                                      fields="ts_code,trade_date,close,turnover_rate,"
                                             "volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,"
                                             "dv_ratio,dv_ttm,total_share,float_share,"
                                             "total_mv,circ_mv")
            self._rate_limit()
        except Exception as exc:
            logger.warning("daily_basic failed for %s: %s", trade_date, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", f"date_{trade_date}", "daily_basic")
        logger.info("daily_basic date=%s rows=%d elapsed=%.1fs", trade_date, len(records), time.time() - t0)
        return records

    def collect_adj_factor(self, ts_code: str, start_date: str = "20100101",
                           end_date: str = "") -> list[dict[str, Any]]:
        """复权因子。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        df = self.pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
        self._rate_limit()
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", ts_code, "adj_factor")
        logger.info("adj_factor ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_income(self, ts_code: str) -> list[dict[str, Any]]:
        """利润表。"""
        t0 = time.time()
        try:
            df = self.pro.income(ts_code=ts_code)
            self._rate_limit()
        except Exception as exc:
            logger.warning("income failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", ts_code, "income")
        logger.info("income ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_balancesheet(self, ts_code: str) -> list[dict[str, Any]]:
        """资产负债表。"""
        t0 = time.time()
        try:
            df = self.pro.balancesheet(ts_code=ts_code)
            self._rate_limit()
        except Exception as exc:
            logger.warning("balancesheet failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", ts_code, "balancesheet")
        logger.info("balancesheet ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_cashflow(self, ts_code: str) -> list[dict[str, Any]]:
        """现金流量表。"""
        t0 = time.time()
        try:
            df = self.pro.cashflow(ts_code=ts_code)
            self._rate_limit()
        except Exception as exc:
            logger.warning("cashflow failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", ts_code, "cashflow")
        logger.info("cashflow ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_fina_indicator(self, ts_code: str) -> list[dict[str, Any]]:
        """财务指标。"""
        t0 = time.time()
        try:
            df = self.pro.fina_indicator(ts_code=ts_code)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fina_indicator failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", ts_code, "fina_indicator")
        logger.info("fina_indicator ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_moneyflow(self, trade_date: str) -> list[dict[str, Any]]:
        """个股资金流（需300积分）。"""
        t0 = time.time()
        try:
            df = self.pro.moneyflow(trade_date=trade_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("moneyflow failed for %s: %s", trade_date, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", f"date_{trade_date}", "moneyflow")
        logger.info("moneyflow date=%s rows=%d elapsed=%.1fs", trade_date, len(records), time.time() - t0)
        return records

    def collect_margin(self, trade_date: str) -> list[dict[str, Any]]:
        """融资融券汇总。"""
        t0 = time.time()
        try:
            df = self.pro.margin(trade_date=trade_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("margin failed for %s: %s", trade_date, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", f"date_{trade_date}", "margin")
        logger.info("margin date=%s rows=%d elapsed=%.1fs", trade_date, len(records), time.time() - t0)
        return records

    def collect_stk_limit(self, trade_date: str) -> list[dict[str, Any]]:
        """涨跌停。"""
        t0 = time.time()
        try:
            df = self.pro.stk_limit(trade_date=trade_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("stk_limit failed for %s: %s", trade_date, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", f"date_{trade_date}", "stk_limit")
        logger.info("stk_limit date=%s rows=%d elapsed=%.1fs", trade_date, len(records), time.time() - t0)
        return records

    def collect_dividend(self, ts_code: str) -> list[dict[str, Any]]:
        """分红送转。"""
        t0 = time.time()
        try:
            df = self.pro.dividend(ts_code=ts_code)
            self._rate_limit()
        except Exception as exc:
            logger.warning("dividend failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", ts_code, "dividend")
        logger.info("dividend ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_suspend_d(self, trade_date: str) -> list[dict[str, Any]]:
        """停复牌。"""
        t0 = time.time()
        try:
            df = self.pro.suspend_d(trade_date=trade_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("suspend_d failed for %s: %s", trade_date, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "stock", f"date_{trade_date}", "suspend_d")
        logger.info("suspend_d date=%s rows=%d elapsed=%.1fs", trade_date, len(records), time.time() - t0)
        return records

    # ═══════════════════════════════════════════
    # C. 指数类
    # ═══════════════════════════════════════════

    def collect_index_daily(self, ts_code: str, start_date: str = "20100101",
                            end_date: str = "") -> list[dict[str, Any]]:
        """指数日K线。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        all_records: list[dict[str, Any]] = []
        offset = 0
        while True:
            df = self.pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date,
                                      limit=self.BATCH_SIZE, offset=offset)
            self._rate_limit()
            if df is None or df.empty:
                break
            batch = df.to_dict("records")
            all_records.extend(batch)
            if len(batch) < self.BATCH_SIZE:
                break
            offset += self.BATCH_SIZE
        self._save_records_parquet(all_records, "index", ts_code, "index_daily")
        logger.info("index_daily ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(all_records), time.time() - t0)
        return all_records

    def collect_index_weight(self, index_code: str, trade_date: str = "") -> list[dict[str, Any]]:
        """指数权重。"""
        t0 = time.time()
        trade_date = trade_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.index_weight(index_code=index_code, trade_date=trade_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("index_weight failed for %s: %s", index_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "index", index_code, "index_weight")
        logger.info("index_weight index=%s rows=%d elapsed=%.1fs", index_code, len(records), time.time() - t0)
        return records

    # ═══════════════════════════════════════════
    # D. 基金类
    # ═══════════════════════════════════════════

    def collect_fund_basic(self, market: str = "E") -> list[dict[str, Any]]:
        """基金基本信息。"""
        t0 = time.time()
        try:
            df = self.pro.fund_basic(market=market)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fund_basic failed: %s", exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "fund", market, "fund_basic")
        logger.info("fund_basic market=%s rows=%d elapsed=%.1fs", market, len(records), time.time() - t0)
        return records

    def collect_fund_nav(self, ts_code: str) -> list[dict[str, Any]]:
        """基金净值。"""
        t0 = time.time()
        try:
            df = self.pro.fund_nav(ts_code=ts_code)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fund_nav failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "fund", ts_code, "fund_nav")
        logger.info("fund_nav ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    def collect_fund_daily(self, ts_code: str, start_date: str = "20150101",
                           end_date: str = "") -> list[dict[str, Any]]:
        """基金日行情。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("fund_daily failed for %s: %s", ts_code, exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "fund", ts_code, "fund_daily")
        logger.info("fund_daily ts_code=%s rows=%d elapsed=%.1fs", ts_code, len(records), time.time() - t0)
        return records

    # ═══════════════════════════════════════════
    # E. 宏观经济类
    # ═══════════════════════════════════════════

    def collect_shibor(self, start_date: str = "20150101", end_date: str = "") -> list[dict[str, Any]]:
        """Shibor利率。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.shibor(start_date=start_date, end_date=end_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("shibor failed: %s", exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "macro", "shibor", "shibor")
        logger.info("shibor rows=%d elapsed=%.1fs", len(records), time.time() - t0)
        return records

    def collect_shibor_lpr(self, start_date: str = "20150101", end_date: str = "") -> list[dict[str, Any]]:
        """LPR利率。"""
        t0 = time.time()
        end_date = end_date or datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.shibor_lpr(start_date=start_date, end_date=end_date)
            self._rate_limit()
        except Exception as exc:
            logger.warning("shibor_lpr failed: %s", exc)
            return []
        records = df.to_dict("records") if df is not None and not df.empty else []
        self._save_records_parquet(records, "macro", "lpr", "shibor_lpr")
        logger.info("shibor_lpr rows=%d elapsed=%.1fs", len(records), time.time() - t0)
        return records
