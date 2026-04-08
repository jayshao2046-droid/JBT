"""Data collection pipelines for minute and daily bars."""

from __future__ import annotations

import logging
import os
from typing import Any

from services.data.src.collectors.akshare_backup import AkshareBackupCollector
from services.data.src.collectors.base import BaseCollector
from services.data.src.collectors.macro_collector import MacroCollector
from services.data.src.collectors.news_api_collector import NewsAPICollector
from services.data.src.collectors.news_translator import enrich_record_with_translation
from services.data.src.collectors.position_collector import PositionCollector
from services.data.src.collectors.rss_collector import RSSCollector
from services.data.src.collectors.sentiment_collector import SentimentCollector
from services.data.src.collectors.shipping_collector import ShippingCollector
from services.data.src.collectors.tqsdk_collector import TqSdkCollector
from services.data.src.collectors.tushare_futures_collector import TushareFuturesCollector
from services.data.src.collectors.tushare_collector import TushareDailyCollector
from services.data.src.collectors.volatility_collector import VolatilityCollector
from services.data.src.data.source_manager import SourceManager
from services.data.src.data.storage import HDF5Storage
from services.data.src.data.sentiment_mapper import map_news_to_score, map_sentiment_to_score
from services.data.src.utils.config import get_config

_logger = logging.getLogger(__name__)


def _build_storage(config: dict[str, Any]) -> HDF5Storage:
    storage_cfg = config.get("storage", {})
    base_path = storage_cfg.get("base_path")
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
        mode="w",
    )


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
    """D107: 外盘日线采集 (全部 30 品种, AkShare)."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    from services.data.src.collectors.overseas_minute_collector import OverseasMinuteCollector
    collector = OverseasMinuteCollector(config=resolved_config, storage=resolved_storage)

    result: dict[str, int] = {}
    try:
        records = collector.collect_daily_only()
        for rec in records:
            sym = rec.get("symbol_or_indicator", "unknown")
            if sym not in result:
                result[sym] = 0
            result[sym] += 1
        # Save grouped
        from collections import defaultdict
        by_sym: dict[str, list] = defaultdict(list)
        for rec in records:
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

    from services.data.src.collectors.overseas_minute_collector import OverseasMinuteCollector
    collector = OverseasMinuteCollector(config=resolved_config, storage=resolved_storage)

    result: dict[str, int] = {}
    try:
        records = collector.collect(period="1d", interval="1m")
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

    from services.data.src.collectors.stock_minute_collector import StockMinuteCollector
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
            from services.data.src.collectors.tushare_full_collector import TushareFullCollector
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

    # P1-002: 翻译字段补全 — enrich title_original / title_translated
    ds_key = os.environ.get("DEEPSEEK_API_KEY", "")
    ds_url = resolved_config.get("deepseek", {}).get(
        "base_url", "https://api.deepseek.com/v1"
    )
    enriched = 0
    for i, rec in enumerate(records):
        records[i] = enrich_record_with_translation(
            rec, api_key=ds_key or None, base_url=ds_url,
        )
        if records[i].get("payload", {}).get("title_original"):
            enriched += 1
    if records:
        _logger.info("news_api translation enrichment: %d/%d records", enriched, len(records))

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
            from services.data.src.collectors.tushare_full_collector import TushareFullCollector
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


def run_tushare_futures_pipeline(
    *,
    ts_code: str,
    trade_date: str,
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
    collector: TushareFuturesCollector | None = None,
    symbol: str = "futures",
) -> dict[str, int]:
    """Run Tushare futures collection and save to hdf5/{symbol}/futures/."""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)
    resolved_collector = collector or TushareFuturesCollector(
        config=resolved_config,
        storage=resolved_storage,
        use_mock=False,
    )

    records = resolved_collector.collect_all(ts_code=ts_code, trade_date=trade_date)
    written = _save_records(storage=resolved_storage, data_type="futures", symbol=symbol, records=records)
    return {symbol: written}
