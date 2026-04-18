"""Data collection pipelines for minute and daily bars."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from collectors.akshare_backup import AkshareBackupCollector
from collectors.base import BaseCollector
from collectors.cftc_collector import CftcCollector
from collectors.watchlist_client import WatchlistClient
from collectors.forex_collector import ForexCollector
from collectors.macro_collector import MacroCollector
from collectors.news_api_collector import NewsAPICollector
from collectors.options_collector import OptionsCollector
from collectors.position_collector import PositionCollector
from collectors.rss_collector import RSSCollector
from collectors.sentiment_collector import SentimentCollector
from collectors.shipping_collector import ShippingCollector
from collectors.weather_collector import WeatherCollector
from collectors.tqsdk_collector import TqSdkCollector
from collectors.tushare_futures_collector import TushareFuturesCollector
from collectors.tushare_collector import TushareDailyCollector
from collectors.volatility_collector import VolatilityCollector
from data.source_manager import SourceManager
from data.storage import HDF5Storage
from data.sentiment_mapper import map_news_to_score, map_sentiment_to_score
from utils.config import get_config

_logger = logging.getLogger(__name__)


def _build_storage(config: dict[str, Any]) -> HDF5Storage:
    storage_cfg = config.get("storage", {})
    base_path = os.environ.get("DATA_STORAGE_ROOT") or storage_cfg.get("base_path")
    return HDF5Storage(base_dir=base_path)


def _save_records(
    *,
    storage: HDF5Storage,
    data_type: str,
    symbol: str,
    records: list[dict[str, Any]],
) -> int:
    return storage.write_records(
        data_type=data_type,
        symbol=symbol,
        records=records,
        key="records",
        sort_by="timestamp",
        mode="a",  # 修复：改为追加模式，避免覆盖历史数据
    )


def _sync_minute_to_bars_dir(
    records_by_symbol: dict[str, list[dict[str, Any]]],
) -> None:
    """同步分钟数据到 bars API 目录: futures_minute/1m/{symbol}/YYYYMM.parquet"""
    import pandas as pd

    storage_root = os.environ.get("DATA_STORAGE_ROOT", "")
    if not storage_root:
        return

    bars_root = Path(storage_root) / "futures_minute" / "1m"

    for sym, records in records_by_symbol.items():
        try:
            rows = []
            for rec in records:
                payload = rec.get("payload", {})
                if isinstance(payload, str):
                    payload = json.loads(payload)
                rows.append({
                    "datetime": rec.get("timestamp") or payload.get("datetime", ""),
                    "open": float(payload.get("open", 0)),
                    "high": float(payload.get("high", 0)),
                    "low": float(payload.get("low", 0)),
                    "close": float(payload.get("close", 0)),
                    "volume": int(payload.get("volume", 0)),
                    "open_interest": int(payload.get("open_oi", 0)),
                })

            if not rows:
                continue

            df = pd.DataFrame(rows)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").drop_duplicates(
                subset=["datetime"], keep="last"
            )

            dirname = sym.replace(".", "_").replace("@", "_")
            sym_dir = bars_root / dirname
            sym_dir.mkdir(parents=True, exist_ok=True)

            for period, group in df.groupby(df["datetime"].dt.to_period("M")):
                month_str = period.strftime("%Y%m")
                fpath = sym_dir / f"{month_str}.parquet"
                if fpath.exists():
                    old = pd.read_parquet(fpath)
                    old["datetime"] = pd.to_datetime(old["datetime"])
                    combined = pd.concat([old, group], ignore_index=True)
                    combined = combined.sort_values("datetime").drop_duplicates(
                        subset=["datetime"], keep="last"
                    )
                else:
                    combined = group
                combined.to_parquet(fpath, index=False, engine="pyarrow")

            _logger.info("bars-sync minute: %s → %d bars", dirname, len(df))
        except Exception as exc:
            _logger.warning("bars-sync minute failed for %s: %s", sym, exc)


def _sync_daily_to_bars_dir(
    symbol: str,
    records: list[dict[str, Any]],
) -> None:
    """同步日K数据到统一目录: futures_daily/{symbol}/daily.parquet"""
    import pandas as pd

    storage_root = os.environ.get("DATA_STORAGE_ROOT", "")
    if not storage_root:
        return

    try:
        daily_root = Path(storage_root) / "futures_daily"
        rows = []
        for rec in records:
            rows.append({
                "trade_date": rec.get("timestamp", ""),
                "open": float(rec.get("open", 0)),
                "high": float(rec.get("high", 0)),
                "low": float(rec.get("low", 0)),
                "close": float(rec.get("close", 0)),
                "volume": float(rec.get("volume", 0)),
                "oi": float(rec.get("oi", 0)),
                "amount": float(rec.get("amount", 0)),
            })

        if not rows:
            return

        dirname = symbol.replace(".", "_").replace("@", "_")
        sym_dir = daily_root / dirname
        sym_dir.mkdir(parents=True, exist_ok=True)
        fpath = sym_dir / "daily.parquet"

        df = pd.DataFrame(rows)
        if fpath.exists():
            old = pd.read_parquet(fpath)
            df = pd.concat([old, df], ignore_index=True)
            df = df.sort_values("trade_date").drop_duplicates(
                subset=["trade_date"], keep="last"
            )
        else:
            df = df.sort_values("trade_date")

        df.to_parquet(fpath, index=False, engine="pyarrow")
        _logger.info("bars-sync daily: %s → %d rows", dirname, len(df))
    except Exception as exc:
        _logger.warning("bars-sync daily failed for %s: %s", symbol, exc)


def run_minute_pipeline(
    symbols: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    primary_collector: BaseCollector | None = None,
    backup_collector: BaseCollector | None = None,
) -> dict[str, int]:
    """Run minute-kline collection and save to hdf5/{symbol}/1min/.

    D106: 双源 — 主源 TqSdk（批量），备用 AkShare futures_zh_minute_sina（逐品种）。
    """
    from collections import defaultdict

    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    collector = primary_collector or TqSdkCollector(config=resolved_config, storage=resolved_storage)
    backup = backup_collector or AkshareBackupCollector(config=resolved_config, storage=resolved_storage)

    # 主源 TqSdk — 批量采集
    all_records: list[dict[str, Any]] = []
    try:
        all_records = collector.collect(symbols=symbols, duration=60, as_of=end)
    except Exception as exc:
        _logger.warning("minute primary (TqSdk) failed: %s, switching to AkShare backup", exc)
        # 备用 AkShare — 逐品种 1min
        for sym in symbols:
            try:
                recs = backup.collect(symbol=sym, start=start, end=end, freq="1min")
                all_records.extend(recs)
            except Exception as backup_exc:
                _logger.error("minute backup also failed for %s: %s", sym, backup_exc)

    # Group records by symbol and save
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in all_records:
        sym = rec.get("symbol_or_indicator") or rec.get("symbol") or rec.get("payload", {}).get("symbol", "unknown")
        by_symbol[sym].append(rec)

    result: dict[str, int] = {}
    for sym, recs in by_symbol.items():
        written = _save_records(storage=resolved_storage, data_type="1min", symbol=sym, records=recs)
        result[sym] = written

    # 同步到 bars API 目录 (futures_minute/1m/)
    _sync_minute_to_bars_dir(by_symbol)
    return result


def run_daily_pipeline(
    symbols: list[str],
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    primary_collector: BaseCollector | None = None,
    backup_collector: BaseCollector | None = None,
) -> dict[str, int]:
    """Run daily collection and save to hdf5/{symbol}/daily/."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    primary = primary_collector or TushareDailyCollector(config=resolved_config, storage=resolved_storage)
    backup = backup_collector or AkshareBackupCollector(config=resolved_config, storage=resolved_storage)
    manager = SourceManager(primary_source=primary, backup_source=backup)

    result: dict[str, int] = {}
    for symbol in symbols:
        records = manager.fetch(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            freq="daily",
        )
        written = _save_records(storage=resolved_storage, data_type="daily", symbol=symbol, records=records)
        result[symbol] = written
        # 同步到统一日K目录 (futures_daily/)
        _sync_daily_to_bars_dir(symbol, records)
    return result


def run_overseas_minute_pipeline(
    symbols: list[str],
    *,
    start: str | None = None,
    end: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: BaseCollector | None = None,
) -> dict[str, int]:
    """Run overseas minute-kline collection and save to hdf5/{symbol}/1min/.

    D106: 双源 — 主源 AkShare futures_global_hist_em，备用 futures_foreign_hist。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or AkshareBackupCollector(
        config=resolved_config,
        storage=resolved_storage,
        use_mock=False,
    )

    result: dict[str, int] = {}
    for symbol in symbols:
        records: list[dict[str, Any]] = []
        try:
            records = resolved_collector.collect(symbol=symbol, start=start, end=end, freq="1min")
        except Exception as exc:
            _logger.warning("overseas minute primary failed for %s: %s, trying backup", symbol, exc)
            try:
                records = resolved_collector.collect_overseas_futures(symbol=symbol)
            except Exception as backup_exc:
                _logger.error("overseas minute backup also failed for %s: %s", symbol, backup_exc)

        result[symbol] = _save_records(
            storage=resolved_storage, data_type="1min", symbol=symbol, records=records,
        )
    return result


def run_overseas_daily_pipeline(
    symbols: list[str],
    *,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
) -> dict[str, int]:
    """D107: 外盘日线采集 (全部 31 品种, yfinance + AkShare)."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    from collectors.overseas_minute_collector import OverseasMinuteCollector
    collector = OverseasMinuteCollector(config=resolved_config, storage=resolved_storage)

    result: dict[str, int] = {}
    try:
        # 1. 采集 yfinance 品种日线 (COMEX/NYMEX/CBOT/ICE/CME)
        yf_records = collector.collect_yfinance_daily(symbols=symbols)

        # 2. 采集 AkShare 品种日线 (LME/SGX)
        ak_records = collector.collect_daily_only()

        # 3. 合并所有记录
        all_records = yf_records + ak_records

        for rec in all_records:
            sym = rec.get("symbol_or_indicator", "unknown")
            if sym not in result:
                result[sym] = 0
            result[sym] += 1

        # Save grouped by symbol
        from collections import defaultdict
        by_sym: dict[str, list] = defaultdict(list)
        for rec in all_records:
            by_sym[rec.get("symbol_or_indicator", "unknown")].append(rec)
        for sym, recs in by_sym.items():
            _save_records(storage=resolved_storage, data_type="daily", symbol=sym, records=recs)
    except Exception as exc:
        _logger.error("overseas daily pipeline failed: %s", exc)

    return result


def run_overseas_minute_yf_pipeline(
    *,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
) -> dict[str, int]:
    """D107: 外盘分钟采集 (yfinance, 21 品种)."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    from collectors.overseas_minute_collector import OverseasMinuteCollector
    collector = OverseasMinuteCollector(config=resolved_config, storage=resolved_storage)

    result: dict[str, int] = {}
    try:
        records = collector.collect(period="2d", interval="1m")
        from collections import defaultdict
        by_sym: dict[str, list] = defaultdict(list)
        for rec in records:
            by_sym[rec.get("symbol_or_indicator", "unknown")].append(rec)
        for sym, recs in by_sym.items():
            written = _save_records(storage=resolved_storage, data_type="1min", symbol=sym, records=recs)
            result[sym] = written
    except Exception as exc:
        _logger.error("overseas minute yfinance pipeline failed: %s", exc)

    return result


def run_stock_minute_pipeline(
    *,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
) -> dict[str, int]:
    """D107: A股分钟采集 (盘中实时, 全量 5489 只)."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    from collectors.stock_minute_collector import StockMinuteCollector
    collector = StockMinuteCollector(
        config=resolved_config,
        storage=resolved_storage,
        batch_size=500,
        batch_sleep=10.0,
        per_stock_sleep=0.3,
    )

    # 获取全量 A 股代码
    try:
        all_codes = collector.get_all_a_stock_codes()
    except Exception as exc:
        _logger.error("无法获取 A 股代码列表: %s", exc)
        return {}

    result: dict[str, int] = {}
    try:
        records = collector.collect(symbols=all_codes, period="1")
        from collections import defaultdict
        by_sym: dict[str, list] = defaultdict(list)
        for rec in records:
            by_sym[rec.get("symbol_or_indicator", "unknown")].append(rec)
        for sym, recs in by_sym.items():
            written = _save_records(storage=resolved_storage, data_type="stock_minute", symbol=sym, records=recs)
            result[sym] = written
    except Exception as exc:
        _logger.error("stock minute pipeline failed: %s", exc)

    return result


def run_stock_daily_pipeline(
    *,
    trade_date: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
) -> dict[str, int]:
    """A股全量日线采集 — 每日收盘后按 trade_date 拉取一次全市场，
    落盘到 DATA_STORAGE_ROOT/stock_daily/YYYYMM.parquet（按月分文件）。

    使用 Tushare pro.daily(trade_date=...) 一次 API 拉取全市场 ~5500 行，
    远比按个股逐只拉取高效。同时采集6个主要指数。
    """
    import pandas as pd
    import time as _time

    _ = storage  # 本管道直接写文件，不走 HDF5Storage.write_records

    storage_root = os.environ.get("DATA_STORAGE_ROOT", "")
    if not storage_root:
        _logger.error("DATA_STORAGE_ROOT 未设置，跳过股票日线采集")
        return {}

    stock_dir = Path(storage_root) / "stock_daily"
    stock_dir.mkdir(parents=True, exist_ok=True)

    resolved_config = config or get_config()
    data_sources = resolved_config.get("data_sources", {})
    token = str(data_sources.get("tushare", {}).get("token", "") or "")
    if not token:
        token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        _logger.error("TUSHARE_TOKEN 未配置，跳过股票日线采集")
        return {}

    try:
        import tushare as ts
        ts.set_token(token)
        pro = ts.pro_api()
    except Exception as exc:
        _logger.error("Tushare 初始化失败: %s", exc)
        return {}

    today = trade_date or _time.strftime("%Y%m%d")
    month_key = today[:6]  # YYYYMM

    result: dict[str, int] = {}

    # 1. 全市场个股日线
    try:
        df = pro.daily(trade_date=today)
        _time.sleep(0.3)
        if df is not None and not df.empty:
            month_file = stock_dir / f"{month_key}.parquet"
            if month_file.exists():
                old = pd.read_parquet(month_file)
                df = pd.concat([old, df], ignore_index=True)
                df = df.sort_values(["ts_code", "trade_date"]).drop_duplicates(
                    subset=["ts_code", "trade_date"], keep="last"
                )
            else:
                df = df.sort_values(["ts_code", "trade_date"])
            df.to_parquet(month_file, index=False, engine="pyarrow")
            result["stock_daily"] = len(df)
            _logger.info("A股日线: trade_date=%s → %d行 → %s", today, len(df), month_file.name)
        else:
            _logger.warning("A股日线: trade_date=%s 无数据", today)
    except Exception as exc:
        _logger.error("A股日线采集失败 trade_date=%s: %s", today, exc)

    # 2. 主要指数
    index_dir = stock_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    INDEX_CODES = [
        "000001.SH", "399001.SZ", "399006.SZ",
        "000300.SH", "000905.SH", "000852.SH",
    ]
    for idx_code in INDEX_CODES:
        try:
            idf = pro.index_daily(ts_code=idx_code, trade_date=today)
            _time.sleep(0.2)
            if idf is not None and not idf.empty:
                fname = idx_code.replace(".", "_")
                ifile = index_dir / f"{fname}.parquet"
                if ifile.exists():
                    old_i = pd.read_parquet(ifile)
                    idf = pd.concat([old_i, idf], ignore_index=True)
                    idf = idf.sort_values("trade_date").drop_duplicates(
                        subset=["trade_date"], keep="last"
                    )
                idf.to_parquet(ifile, index=False, engine="pyarrow")
                result[idx_code] = len(idf)
        except Exception as exc:
            _logger.warning("指数日线 %s 失败: %s", idx_code, exc)

    return result


def run_macro_pipeline(
    *,
    countries: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: MacroCollector | None = None,
    symbol: str = "macro_global",
) -> dict[str, int]:
    """Run macro collection and save to hdf5/{symbol}/macro/.

    D106: 双源 — 主源 AkShare macro，备用 Tushare shibor/lpr。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or MacroCollector(config=resolved_config, storage=resolved_storage, use_mock=False)

    try:
        records = resolved_collector.collect(countries=countries, as_of=as_of)
    except Exception as exc:
        _logger.warning("macro primary (AkShare) failed: %s, trying Tushare backup", exc)
        try:
            from collectors.tushare_full_collector import TushareFullCollector
            ts_col = TushareFullCollector(config=resolved_config)
            shibor = ts_col.collect_shibor()
            records = [{"symbol": symbol, "indicator": "shibor", "value": r} for r in shibor]
        except Exception as backup_exc:
            _logger.error("macro backup (Tushare) also failed: %s", backup_exc)
            records = []

    written = _save_records(storage=resolved_storage, data_type="macro", symbol=symbol, records=records)
    return {symbol: written}


def run_position_pipeline(
    *,
    symbols: list[str] | None = None,
    trade_date: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: PositionCollector | None = None,
    symbol: str = "position_daily",
) -> dict[str, int]:
    """Run position/warehouse collection and save to hdf5/{symbol}/position/."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or PositionCollector(config=resolved_config, storage=resolved_storage, use_mock=False)

    records = resolved_collector.collect(symbols=symbols, trade_date=trade_date)
    written = _save_records(storage=resolved_storage, data_type="position", symbol=symbol, records=records)
    return {symbol: written}


def run_volatility_pipeline(
    *,
    indicators: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: VolatilityCollector | None = None,
    symbol: str = "volatility_index",
) -> dict[str, int]:
    """Run volatility collection and save to hdf5/{symbol}/volatility/.

    D106: 单源（AkShare），无可用备源，添加 try/except 保护。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or VolatilityCollector(
        config=resolved_config,
        storage=resolved_storage,
        use_mock=False,
    )

    try:
        records = resolved_collector.collect(indicators=indicators, as_of=as_of)
    except Exception as exc:
        _logger.error("volatility pipeline failed (no backup available): %s", exc)
        records = []

    written = _save_records(storage=resolved_storage, data_type="volatility", symbol=symbol, records=records)
    return {symbol: written}


def run_news_api_pipeline(
    *,
    sources: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: NewsAPICollector | None = None,
    symbol: str = "news_api",
) -> dict[str, int]:
    """Run news API collection and save to hdf5/{symbol}/news_api/.

    D106: 双源 — 主源 NewsAPI，备用 RSS。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or NewsAPICollector(config=resolved_config, storage=resolved_storage, use_mock=False)

    try:
        records = resolved_collector.collect(sources=sources, as_of=as_of)
    except Exception as exc:
        _logger.warning("news_api primary failed: %s, falling back to RSS", exc)
        try:
            rss_collector = RSSCollector(config=resolved_config, storage=resolved_storage, use_mock=False)
            records = rss_collector.collect(feeds=None, as_of=as_of)
        except Exception as backup_exc:
            _logger.error("news RSS backup also failed: %s", backup_exc)
            records = []

    # P1-010: 生成 news_score 扁平化数据
    try:
        score_df = map_news_to_score(records)
        if not score_df.is_empty():
            _save_records(storage=resolved_storage, data_type="news_score", symbol=symbol, records=score_df.to_dicts())
            _logger.info("news_score mapping: %d records", score_df.height)
    except Exception as exc:
        _logger.warning("news_score mapping failed: %s", exc)

    written = _save_records(storage=resolved_storage, data_type="news_api", symbol=symbol, records=records)
    return {symbol: written}


def run_rss_pipeline(
    *,
    sources: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: RSSCollector | None = None,
    symbol: str = "news_rss",
) -> dict[str, int]:
    """Run RSS aggregation and save to hdf5/{symbol}/rss/.

    D106: 双源 — 主源 RSS，备用 NewsAPI。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or RSSCollector(config=resolved_config, storage=resolved_storage, use_mock=False)

    try:
        records = resolved_collector.collect(feeds=None, as_of=as_of)
    except Exception as exc:
        _logger.warning("RSS primary failed: %s, falling back to NewsAPI", exc)
        try:
            news_collector = NewsAPICollector(config=resolved_config, storage=resolved_storage, use_mock=False)
            records = news_collector.collect(sources=sources, as_of=as_of)
        except Exception as backup_exc:
            _logger.error("NewsAPI backup also failed: %s", backup_exc)
            records = []

    written = _save_records(storage=resolved_storage, data_type="rss", symbol=symbol, records=records)
    return {symbol: written}


def run_sentiment_pipeline(
    *,
    symbols: list[str] | None = None,
    sources: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: SentimentCollector | None = None,
    symbol: str = "sentiment",
) -> dict[str, int]:
    """Run sentiment collection and save to hdf5/{symbol}/sentiment/.

    D106: 双源 — 主源 AkShare sentiment，备用 Tushare margin/融资融券。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or SentimentCollector(
        config=resolved_config,
        storage=resolved_storage,
        use_mock=False,
    )

    try:
        records = resolved_collector.collect(symbols=symbols, sources=sources, as_of=as_of)
    except Exception as exc:
        _logger.warning("sentiment primary (AkShare) failed: %s, trying Tushare backup", exc)
        try:
            from collectors.tushare_full_collector import TushareFullCollector
            ts_col = TushareFullCollector(config=resolved_config)
            margin = ts_col.collect_margin_detail() if hasattr(ts_col, "collect_margin_detail") else []
            records = [{"symbol": symbol, "indicator": "margin", "value": r} for r in margin]
        except Exception as backup_exc:
            _logger.error("sentiment backup (Tushare) also failed: %s", backup_exc)
            records = []

    # P1-010: 生成 social_score 扁平化数据
    try:
        score_df = map_sentiment_to_score(records)
        if not score_df.is_empty():
            _save_records(storage=resolved_storage, data_type="social_score", symbol=symbol, records=score_df.to_dicts())
            _logger.info("social_score mapping: %d records", score_df.height)
    except Exception as exc:
        _logger.warning("social_score mapping failed: %s", exc)

    written = _save_records(storage=resolved_storage, data_type="sentiment", symbol=symbol, records=records)
    return {symbol: written}


def run_shipping_pipeline(
    *,
    indicators: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: ShippingCollector | None = None,
    symbol: str = "shipping",
) -> dict[str, int]:
    """Run shipping collection and save to hdf5/{symbol}/shipping/.

    D106: 单源（AkShare），无可用备源，添加 try/except 保护。
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or ShippingCollector(config=resolved_config, storage=resolved_storage, use_mock=False)

    try:
        records = resolved_collector.collect(indicators=indicators, as_of=as_of)
    except Exception as exc:
        _logger.error("shipping pipeline failed (no backup available): %s", exc)
        records = []

    written = _save_records(storage=resolved_storage, data_type="shipping", symbol=symbol, records=records)
    return {symbol: written}


def run_weather_pipeline(
    *,
    locations: list[str] | None = None,
    as_of: str | None = None,
    days: int = 7,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: WeatherCollector | None = None,
    symbol: str = "weather",
) -> dict[str, int]:
    """Run weather collection and save to hdf5/{symbol}/weather/.

    采集全球15个关键期货影响地点的天气数据，支持策略决策。
    数据源：Open-Meteo Forecast (免费免Key)
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or WeatherCollector(config=resolved_config, storage=resolved_storage, use_mock=False)

    try:
        records = resolved_collector.collect(locations=locations, as_of=as_of, days=days)
    except Exception as exc:
        _logger.error("weather pipeline failed: %s", exc)
        records = []

    written = _save_records(storage=resolved_storage, data_type="weather", symbol=symbol, records=records)
    return {symbol: written}


def run_tushare_futures_pipeline(
    *,
    ts_code: str,
    trade_date: str,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: TushareFuturesCollector | None = None,
    symbol: str = "futures",
) -> dict[str, int]:
    """Run Tushare futures collection and save to separate directories.

    Data types:
    - daily: fut_daily (日K线) -> hdf5/{symbol}/futures_daily/
    - holding: fut_holding (持仓排名) -> hdf5/{symbol}/futures_holding/
    - wsr: fut_wsr (仓单日报) -> hdf5/{symbol}/futures_wsr/
    - settle: fut_settle (结算参数) -> hdf5/{symbol}/futures_settle/
    """
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or TushareFuturesCollector(
        config=resolved_config,
        storage=resolved_storage,
        use_mock=False,
    )

    data_by_type = resolved_collector.collect_all(ts_code=ts_code, trade_date=trade_date)

    result: dict[str, int] = {}
    for data_type, records in data_by_type.items():
        if records:
            written = _save_records(
                storage=resolved_storage,
                data_type=f"futures_{data_type}",
                symbol=symbol,
                records=records,
            )
            result[f"{symbol}_{data_type}"] = written

    return result


def run_forex_pipeline(
    *,
    pairs: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: ForexCollector | None = None,
    symbol: str = "forex",
) -> dict[str, int]:
    """Run Tushare FX daily collection and save to hdf5/{symbol}/forex/."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or ForexCollector(
        config=resolved_config, storage=resolved_storage, use_mock=False,
    )
    try:
        records = resolved_collector.collect(pairs=pairs, as_of=as_of)
    except Exception as exc:
        _logger.error("forex pipeline failed: %s", exc)
        records = []
    written = _save_records(storage=resolved_storage, data_type="forex", symbol=symbol, records=records)
    return {symbol: written}


def run_cftc_pipeline(
    *,
    indicators: list[str] | None = None,
    as_of: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: CftcCollector | None = None,
    symbol: str = "cftc",
) -> dict[str, int]:
    """Run CFTC COT report collection and save to hdf5/{symbol}/cftc/."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or CftcCollector(
        config=resolved_config, storage=resolved_storage, use_mock=False,
    )
    try:
        records = resolved_collector.collect(indicators=indicators, as_of=as_of)
    except Exception as exc:
        _logger.error("cftc pipeline failed: %s", exc)
        records = []
    written = _save_records(storage=resolved_storage, data_type="cftc", symbol=symbol, records=records)
    return {symbol: written}


def run_options_pipeline(
    *,
    exchanges: list[str] | None = None,
    trade_date: str | None = None,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: OptionsCollector | None = None,
    symbol: str = "options",
) -> dict[str, int]:
    """Run options market data collection and save to hdf5/{symbol}/options/."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    # Get Tushare token from config
    tushare_token = resolved_config.get("data_sources", {}).get("tushare", {}).get("token", "")

    resolved_collector = collector or OptionsCollector(
        config=resolved_config, storage=resolved_storage, use_mock=False, token=tushare_token,
    )
    try:
        records = resolved_collector.collect(exchanges=exchanges, trade_date=trade_date)
    except Exception as exc:
        _logger.error("options pipeline failed: %s", exc)
        records = []
    written = _save_records(storage=resolved_storage, data_type="options", symbol=symbol, records=records)
    return {symbol: written}


def run_watchlist_minute_pipeline(
    *,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    decision_url: str | None = None,
) -> dict[str, int]:
    """CB5: 从决策服务 watchlist API 动态获取股票列表，采集分钟 K 线。"""
    from collections import defaultdict

    from collectors.stock_minute_collector import StockMinuteCollector

    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    url = decision_url or os.environ.get("DECISION_SERVICE_URL", "http://localhost:8104")
    wl_client = WatchlistClient(decision_service_url=url)

    watchlist = wl_client.fetch_watchlist()
    if not watchlist:
        _logger.warning("watchlist 为空，跳过 watchlist minute pipeline")
        return {}

    _logger.info("watchlist minute pipeline: %d 只股票", len(watchlist))

    collector = StockMinuteCollector(
        config=resolved_config,
        storage=resolved_storage,
        watchlist_client=wl_client,
    )

    records = collector.collect(symbols=watchlist, period="1")

    by_sym: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        sym = rec.get("symbol_or_indicator") or rec.get("symbol") or "unknown"
        by_sym[sym].append(rec)

    result: dict[str, int] = {}
    for sym, recs in by_sym.items():
        written = _save_records(
            storage=resolved_storage,
            data_type="stock_minute",
            symbol=sym,
            records=recs,
        )
        result[sym] = written
    return result
