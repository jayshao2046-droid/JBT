from __future__ import annotations

import hmac
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple, Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Header, Query, Request
from fastapi.security import APIKeyHeader

try:
    import yaml
except Exception:  # pragma: no cover - yaml is an optional runtime dependency in tests.
    yaml = None

SERVICE_NAME = "jbt-data"
SERVICE_VERSION = "1.0.0"
DEFAULT_STORAGE_ROOT = Path(os.environ.get("DATA_STORAGE_ROOT", str(Path(__file__).resolve().parents[2] / "runtime" / "data")))
MINUTE_DATA_SUBDIR = Path("futures_minute") / "1m"
BAR_COLUMNS = (
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "open_interest",
)
COLUMN_ALIASES = {
    "timestamp": "datetime",
    "vol": "volume",
    "oi": "open_interest",
    "openInterest": "open_interest",
    "open_interest1": "open_interest",
}
DATE_ONLY_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{8})$")
CONTINUOUS_DIR_PATTERN = re.compile(r"(?i)^KQ_m_([A-Za-z]+)_([A-Za-z]+)$")
CONTINUOUS_ALIAS_PATTERN = re.compile(r"(?i)^KQ\.m@([A-Za-z]+)\.([A-Za-z]+)$")
EXACT_SYMBOL_PATTERN = re.compile(r"(?i)^([A-Za-z]+)[._]([A-Za-z]+?)(\d+)?$")
STOCK_PURE_DIGITS_PATTERN = re.compile(r"^\d{6}$")
STOCK_PREFIX_PATTERN = re.compile(r"(?i)^(SH|SZ)(\d{6})$")
STOCK_SUFFIX_PATTERN = re.compile(r"(?i)^(\d{6})\.(SH|SZ)$")
STOCK_MINUTE_SUBDIR = "stock_minute"
SERVICE_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = SERVICE_ROOT / "configs" / "settings.yaml"
SCHEDULE_FILE = SERVICE_ROOT / "configs" / "collection_schedules.yaml"
COLLECTOR_STATUS_FILE = Path("logs") / "collector_status_latest.json"
SCHEDULER_LOG_FILE = Path("logs") / "scheduler.log"
NEWS_DIRECTORIES = ("news_collected", "news_api", "news_rss")
SOURCE_OUTPUT_DIRS = {
    "futures_minute": "futures_minute",
    "futures_eod": "futures_minute",
    "overseas_minute": "overseas_kline/1m",
    "overseas_daily": "overseas_kline/1d",
    "stock_minute": "stock_minute",
    "stock_realtime": "stock_minute",
    "watchlist": "logs",
    "macro_global": "macro_global",
    "news_rss": "news_rss",
    "position_daily": "position",
    "position_weekly": "position",
    "volatility_cboe": "volatility_index",
    "volatility_qvix": "volatility_index",
    "shipping": "shipping",
    "tushare": "tushare",
    "weather": "weather",
    "sentiment": "sentiment",
    "forex": "forex",
    "cftc": "cftc",
    "options": "options",
    "health_log": "logs",
}
SOURCE_SCHEDULE_HINTS = {
    "futures_minute": "*/1 * * * *",
    "futures_eod": "0 18 * * 1-5",
    "overseas_minute": "*/5 * * * *",
    "overseas_daily": "0 6 * * *",
    "stock_minute": "*/1 9-15 * * 1-5",
    "stock_realtime": "*/1 9-15 * * 1-5",
    "watchlist": "0 18 * * 1-5",
    "macro_global": "0 */4 * * *",
    "news_rss": "*/10 * * * *",
    "position_daily": "30 16 * * 1-5",
    "position_weekly": "0 8 * * 6",
    "volatility_cboe": "0 * * * *",
    "volatility_qvix": "0 * * * *",
    "shipping": "0 9 * * *",
    "tushare": "30 15 * * 1-5",
    "weather": "0 6 * * *",
    "sentiment": "*/1 * * * *",
    "forex": "0 6 * * *",
    "cftc": "0 8 * * 6",
    "options": "*/15 9-15 * * 1-5",
    "health_log": "*/5 * * * *",
}
SOURCE_PROVIDER_HINTS = {
    "futures_minute": "CTP",
    "futures_eod": "CTP",
    "overseas_minute": "yfinance",
    "overseas_daily": "yfinance",
    "stock_minute": "Tushare",
    "stock_realtime": "Tushare",
    "watchlist": "Internal",
    "macro_global": "AkShare",
    "news_rss": "RSS",
    "position_daily": "Internal",
    "position_weekly": "Internal",
    "volatility_cboe": "CBOE",
    "volatility_qvix": "Qvix",
    "shipping": "API",
    "tushare": "Tushare",
    "weather": "API",
    "sentiment": "Internal",
    "forex": "yfinance",
    "cftc": "CFTC",
    "options": "CTP",
    "health_log": "Internal",
}
SOURCE_CATEGORY_HINTS = {
    "futures_minute": "行情类",
    "futures_eod": "行情类",
    "overseas_minute": "行情类",
    "overseas_daily": "行情类",
    "stock_minute": "行情类",
    "stock_realtime": "行情类",
    "watchlist": "监控类",
    "macro_global": "宏观类",
    "news_rss": "新闻资讯类",
    "position_daily": "持仓类",
    "position_weekly": "持仓类",
    "volatility_cboe": "宏观类",
    "volatility_qvix": "宏观类",
    "shipping": "宏观类",
    "tushare": "行情类",
    "weather": "宏观类",
    "sentiment": "情绪类",
    "forex": "宏观类",
    "cftc": "宏观类",
    "options": "行情类",
    "health_log": "监控类",
}
COLLECTOR_LABELS = {
    "futures_minute": "内盘分钟K线",
    "futures_eod": "内盘日线K线",
    "overseas_minute": "外盘分钟K线",
    "overseas_daily": "外盘日线K线",
    "stock_minute": "A股分钟行情",
    "stock_realtime": "A股实时行情",
    "watchlist": "自选监控",
    "macro_global": "全球宏观数据",
    "news_rss": "RSS新闻聚合",
    "position_daily": "每日持仓仓单",
    "position_weekly": "每周持仓报告",
    "volatility_cboe": "CBOE波动率",
    "volatility_qvix": "QVIX波动率",
    "shipping": "海运物流指数",
    "tushare": "Tushare五合一",
    "weather": "天气数据",
    "sentiment": "市场情绪指数",
    "forex": "外汇日线",
    "cftc": "CFTC持仓报告",
    "options": "期权行情",
    "health_log": "健康监控日志",
}
_FRESHNESS_THRESHOLDS = {
    "futures_minute": 2.0, "futures_eod": 26.0, "overseas_minute": 6.0,
    "overseas_daily": 26.0, "stock_minute": 2.0, "stock_realtime": 2.0,
    "macro_global": 48.0, "news_rss": 1.0, "position_daily": 26.0,
    "position_weekly": 170.0, "volatility_cboe": 26.0, "volatility_qvix": 26.0,
    "shipping": 26.0, "tushare": 26.0, "weather": 48.0, "sentiment": 1.0,
    "forex": 26.0, "cftc": 170.0, "options": 26.0, "health_log": 1.0,
    "watchlist": 26.0,
}

# ── API Key 认证 ──────────────────────────────────────────
_DATA_API_KEY = os.environ.get("DATA_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_PUBLIC_PATHS = {"/health", "/api/v1/health", "/api/v1/version"}


async def _verify_api_key(request: Request, api_key: Optional[str] = Depends(_api_key_header)) -> None:
    if not _DATA_API_KEY:
        return
    if request.url.path in _PUBLIC_PATHS:
        return
    if not api_key or not hmac.compare_digest(api_key, _DATA_API_KEY):
        raise HTTPException(status_code=403, detail="invalid or missing API key")


app = FastAPI(title="JBT Data Service", version=SERVICE_VERSION, dependencies=[Depends(_verify_api_key)])

# 注册数据看板路由 (延迟导入避免循环依赖)
try:
    from api.routes.data_web import router as data_web_router
    app.include_router(data_web_router)
except ImportError:
    pass  # 开发环境可能未安装所有依赖

# 注册决策端上下文投喂路由
try:
    from api.routes.context_route import router as context_router
    app.include_router(context_router)
except ImportError:
    pass  # 开发环境可能未安装所有依赖


class ParsedTimeRange(NamedTuple):
    timestamp: pd.Timestamp
    date_only: bool


class SymbolRequest(NamedTuple):
    requested_symbol: str
    exact_symbol: Optional[str]
    continuous_symbol: str


@app.get("/health")
@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


@app.get("/api/v1/version")
def version() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


@app.get("/api/v1/symbols")
def list_symbols() -> dict[str, Any]:
    symbols = _list_available_symbols()
    return {"count": len(symbols), "symbols": symbols}


@app.get("/api/v1/bars")
def get_bars(
    symbol: str = Query(..., min_length=1),
    timeframe_minutes: int = Query(1, ge=1),
    start: str = Query(..., min_length=1),
    end: str = Query(..., min_length=1),
) -> dict[str, Any]:
    parsed_start = _parse_requested_time(start, field_name="start", is_end=False)
    parsed_end = _parse_requested_time(end, field_name="end", is_end=True)
    if parsed_end.timestamp < parsed_start.timestamp:
        raise HTTPException(status_code=422, detail="end must be greater than or equal to start")

    resolved_symbol, source_kind, frame = _resolve_symbol_frame(symbol, parsed_start)
    filtered = frame.loc[
        (frame["datetime"] >= parsed_start.timestamp)
        & (frame["datetime"] <= parsed_end.timestamp)
    ].copy()

    if timeframe_minutes > 1 and not filtered.empty:
        filtered = _resample_bars(filtered, timeframe_minutes)

    bars = _serialize_bars(filtered)
    return {
        "requested_symbol": symbol,
        "resolved_symbol": resolved_symbol,
        "source_kind": source_kind,
        "timeframe_minutes": timeframe_minutes,
        "count": len(bars),
        "bars": bars,
    }


@app.get("/api/v1/stocks/bars")
def get_stock_bars(
    symbol: str = Query(..., min_length=1),
    start: str = Query(..., min_length=1),
    end: str = Query(..., min_length=1),
    timeframe_minutes: int = Query(1, ge=1),
) -> dict[str, Any]:
    parsed_start = _parse_requested_time(start, field_name="start", is_end=False)
    parsed_end = _parse_requested_time(end, field_name="end", is_end=True)
    if parsed_end.timestamp < parsed_start.timestamp:
        raise HTTPException(status_code=422, detail="end must be greater than or equal to start")

    stock_code = _parse_stock_symbol(symbol)
    frame = _load_stock_frame(stock_code)

    filtered = frame.loc[
        (frame["datetime"] >= parsed_start.timestamp)
        & (frame["datetime"] <= parsed_end.timestamp)
    ].copy()

    if timeframe_minutes > 1 and not filtered.empty:
        filtered = _resample_bars(filtered, timeframe_minutes)

    bars = _serialize_bars(filtered)
    return {
        "requested_symbol": symbol,
        "resolved_symbol": stock_code,
        "source_kind": "stock_minute",
        "timeframe_minutes": timeframe_minutes,
        "count": len(bars),
        "bars": bars,
    }


def _storage_root() -> Path:
    raw_root = os.getenv("DATA_STORAGE_ROOT", str(DEFAULT_STORAGE_ROOT))
    return Path(raw_root).expanduser()


def _minute_root() -> Path:
    return _storage_root() / MINUTE_DATA_SUBDIR


def _stock_minute_root() -> Path:
    return _storage_root() / STOCK_MINUTE_SUBDIR


def _parse_stock_symbol(raw_symbol: str) -> str:
    """Parse stock symbol to a 6-digit code. Supports pure digits, SH/SZ prefix, and .SH/.SZ suffix."""
    symbol = raw_symbol.strip()
    if not symbol:
        raise HTTPException(status_code=422, detail="symbol is required")

    if STOCK_PURE_DIGITS_PATTERN.fullmatch(symbol):
        return symbol

    prefix_match = STOCK_PREFIX_PATTERN.fullmatch(symbol)
    if prefix_match:
        return prefix_match.group(2)

    suffix_match = STOCK_SUFFIX_PATTERN.fullmatch(symbol)
    if suffix_match:
        return suffix_match.group(1)

    raise HTTPException(status_code=422, detail=f"unsupported stock symbol format: {raw_symbol}")


def _load_stock_frame(stock_code: str) -> pd.DataFrame:
    stock_dir = _storage_root() / stock_code / "stock_minute"
    if not stock_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"no stock minute data found for {stock_code}",
        )
    try:
        return _load_symbol_frame(stock_dir)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"no parquet data found for stock {stock_code}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"failed to load stock data for {stock_code}: {exc}",
        ) from exc


def _list_available_symbols() -> list[str]:
    minute_root = _minute_root()
    if not minute_root.exists():
        return []
    return sorted(path.name for path in minute_root.iterdir() if path.is_dir())


def _parse_requested_time(raw_value: str, *, field_name: str, is_end: bool) -> ParsedTimeRange:
    value = raw_value.strip()
    if not value:
        raise HTTPException(status_code=422, detail=f"{field_name} is required")

    date_only = bool(DATE_ONLY_PATTERN.fullmatch(value))
    if len(value) == 8 and value.isdigit():
        value = f"{value[:4]}-{value[4:6]}-{value[6:8]}"

    try:
        timestamp = pd.Timestamp(value)
    except Exception as exc:  # pragma: no cover - pandas error messages are not stable.
        raise HTTPException(status_code=422, detail=f"invalid {field_name}: {raw_value}") from exc

    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert(None)
    if date_only:
        timestamp = timestamp.normalize()
        if is_end:
            timestamp = timestamp + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

    return ParsedTimeRange(timestamp=timestamp, date_only=date_only)


def _parse_symbol_request(requested_symbol: str) -> SymbolRequest:
    symbol = requested_symbol.strip()
    if not symbol:
        raise HTTPException(status_code=422, detail="symbol is required")

    continuous_dir_match = CONTINUOUS_DIR_PATTERN.fullmatch(symbol)
    if continuous_dir_match:
        exchange = continuous_dir_match.group(1).upper()
        product = continuous_dir_match.group(2).lower()
        return SymbolRequest(
            requested_symbol=requested_symbol,
            exact_symbol=None,
            continuous_symbol=f"KQ_m_{exchange}_{product}",
        )

    continuous_alias_match = CONTINUOUS_ALIAS_PATTERN.fullmatch(symbol)
    if continuous_alias_match:
        exchange = continuous_alias_match.group(1).upper()
        product = continuous_alias_match.group(2).lower()
        return SymbolRequest(
            requested_symbol=requested_symbol,
            exact_symbol=None,
            continuous_symbol=f"KQ_m_{exchange}_{product}",
        )

    exact_symbol_match = EXACT_SYMBOL_PATTERN.fullmatch(symbol)
    if exact_symbol_match:
        exchange = exact_symbol_match.group(1).upper()
        product = exact_symbol_match.group(2).lower()
        month = exact_symbol_match.group(3)
        return SymbolRequest(
            requested_symbol=requested_symbol,
            exact_symbol=f"{exchange}_{product}{month}" if month else None,
            continuous_symbol=f"KQ_m_{exchange}_{product}",
        )

    raise HTTPException(status_code=422, detail=f"unsupported symbol format: {requested_symbol}")


def _resolve_symbol_frame(
    requested_symbol: str,
    parsed_start: ParsedTimeRange,
) -> tuple[str, str, pd.DataFrame]:
    symbol_request = _parse_symbol_request(requested_symbol)
    minute_root = _minute_root()

    if symbol_request.exact_symbol:
        exact_dir = minute_root / symbol_request.exact_symbol
        if exact_dir.is_dir():
            try:
                exact_frame = _load_symbol_frame(exact_dir)
            except FileNotFoundError:
                exact_frame = None
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"failed to load exact data for {symbol_request.exact_symbol}: {exc}",
                ) from exc
            if exact_frame is not None and _covers_requested_start(exact_frame, parsed_start):
                return symbol_request.exact_symbol, "exact", exact_frame

    continuous_dir = minute_root / symbol_request.continuous_symbol
    if continuous_dir.is_dir():
        try:
            continuous_frame = _load_symbol_frame(continuous_dir)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"no parquet data found for {symbol_request.continuous_symbol}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"failed to load continuous data for {symbol_request.continuous_symbol}: {exc}",
            ) from exc
        return symbol_request.continuous_symbol, "continuous", continuous_frame

    raise HTTPException(
        status_code=404,
        detail=f"no minute data directory found for {requested_symbol}",
    )


def _covers_requested_start(frame: pd.DataFrame, parsed_start: ParsedTimeRange) -> bool:
    if frame.empty:
        return False

    first_timestamp = frame["datetime"].min()
    if parsed_start.date_only:
        return first_timestamp.date() <= parsed_start.timestamp.date()
    return first_timestamp <= parsed_start.timestamp


def _load_symbol_frame(symbol_dir: Path) -> pd.DataFrame:
    parquet_files = sorted(path for path in symbol_dir.rglob("*.parquet") if path.is_file())
    if not parquet_files:
        raise FileNotFoundError(f"no parquet files under {symbol_dir}")

    frames = [_normalize_bar_frame(pd.read_parquet(path)) for path in parquet_files]
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=BAR_COLUMNS)

    return combined.sort_values("datetime").drop_duplicates(
        subset=["datetime"],
        keep="last",
    ).reset_index(drop=True)


def _normalize_bar_frame(frame: pd.DataFrame) -> pd.DataFrame:
    # 展开调度器 payload 格式（股票分钟采集器内部格式）：{source_type, timestamp, payload(dict)}
    if "payload" in frame.columns:
        import json as _json
        rows = [r if isinstance(r, dict) else _json.loads(r) for r in frame["payload"]]
        expanded = pd.json_normalize(rows)
        if "timestamp" in frame.columns and "timestamp" not in expanded.columns:
            expanded["timestamp"] = frame["timestamp"].values
        frame = expanded
        if 'open_interest' not in frame.columns:
            frame = frame.copy()
            frame['open_interest'] = 0.0
    rename_map = {
        source: target
        for source, target in COLUMN_ALIASES.items()
        if source in frame.columns and target not in frame.columns
    }
    normalized = frame.rename(columns=rename_map).copy()

    missing_columns = [column for column in BAR_COLUMNS if column not in normalized.columns]
    if missing_columns:
        raise ValueError(f"missing required columns: {', '.join(missing_columns)}")

    normalized = normalized.loc[:, BAR_COLUMNS].copy()
    normalized["datetime"] = pd.to_datetime(normalized["datetime"], errors="coerce")
    if getattr(normalized["datetime"].dt, "tz", None) is not None:
        normalized["datetime"] = normalized["datetime"].dt.tz_convert(None)

    for column in BAR_COLUMNS[1:]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized[["volume", "open_interest"]] = normalized[["volume", "open_interest"]].fillna(0.0)
    normalized = normalized.dropna(subset=["datetime", "open", "high", "low", "close"])
    return normalized.reset_index(drop=True)


def _resample_bars(frame: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
    aggregated = frame.sort_values("datetime").set_index("datetime").resample(
        f"{timeframe_minutes}min"
    ).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "open_interest": "last",
        }
    )
    return aggregated.dropna(subset=["open", "high", "low", "close"]).reset_index()


def _serialize_bars(frame: pd.DataFrame) -> list[dict[str, Any]]:
    bars: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        timestamp = pd.Timestamp(row.datetime)
        bars.append(
            {
                "datetime": timestamp.isoformat(),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
                "open_interest": float(row.open_interest),
            }
        )
    return bars


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _settings_config() -> dict[str, Any]:
    return _load_yaml_file(SETTINGS_FILE)


def _schedule_config() -> dict[str, Any]:
    return _load_yaml_file(SCHEDULE_FILE)


def _safe_read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _dashboard_status_path() -> Path:
    return _storage_root() / COLLECTOR_STATUS_FILE


def _dashboard_scheduler_log_path() -> Path:
    return _storage_root() / SCHEDULER_LOG_FILE


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _timestamp_to_iso(value: float | int | None) -> Optional[str]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    return datetime.fromtimestamp(numeric).astimezone().isoformat(timespec="seconds")


def _human_bytes(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(max(size_bytes, 0))
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return "0B"


def _truncate_text(value: str, limit: int = 280) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 0)].rstrip() + "..."


def _flatten_schedule_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for collector_key, entries in _schedule_config().items():
        if not isinstance(entries, dict):
            continue
        for entry_name, payload in entries.items():
            if not isinstance(payload, dict):
                continue
            rows.append(
                {
                    "collector_key": collector_key,
                    "name": entry_name,
                    "schedule": str(payload.get("schedule") or ""),
                    "type": "cron",
                    "endpoint_count": len(payload.get("endpoints") or []),
                }
            )
    return rows


def _load_collector_snapshot() -> dict[str, Any]:
    snapshot = _safe_read_json(_dashboard_status_path(), {})
    if not isinstance(snapshot, dict):
        return {}
    sources = snapshot.get("sources")
    if not isinstance(sources, list):
        snapshot["sources"] = []
    return snapshot


def _latest_file_mtime(directory: Path, max_scan: int = 100) -> float:
    """Find the most recent file mtime in a directory (recursive)."""
    latest = 0.0
    count = 0
    try:
        for child in directory.rglob("*"):
            if child.is_file():
                try:
                    latest = max(latest, child.stat().st_mtime)
                except OSError:
                    pass
                count += 1
                if count >= max_scan:
                    break
    except OSError:
        pass
    return latest


def _fallback_collector_sources() -> list[dict[str, Any]]:
    """Build complete collector list from all known sources with real freshness."""
    sources: list[dict[str, Any]] = []
    root = _storage_root()
    now_ts = time.time()
    for name in SOURCE_SCHEDULE_HINTS:
        output_rel = SOURCE_OUTPUT_DIRS.get(name, name)
        output_dir = root / output_rel
        label = COLLECTOR_LABELS.get(name, name)
        threshold_h = _FRESHNESS_THRESHOLDS.get(name, 24.0)
        age_h: float = -1.0
        age_str = "目录不存在"
        ok = False
        if output_dir.exists():
            mtime = _latest_file_mtime(output_dir)
            if mtime > 0:
                age_h = round((now_ts - mtime) / 3600.0, 1)
                if age_h < 1:
                    age_str = f"{max(int(age_h * 60), 1)}分钟前"
                elif age_h < 24:
                    age_str = f"{age_h:.1f}小时前"
                else:
                    age_str = f"{age_h / 24:.1f}天前"
                ok = age_h <= threshold_h if threshold_h > 0 else True
            else:
                age_str = "目录为空"
        sources.append({
            "name": name,
            "label": label,
            "ok": ok,
            "age_h": age_h,
            "age_str": age_str,
            "threshold_h": threshold_h,
            "trading_only": name in {"futures_minute", "stock_minute", "stock_realtime", "options"},
            "skipped": False,
        })
    return sources


def _collector_sources() -> list[dict[str, Any]]:
    snapshot = _load_collector_snapshot()
    raw_sources = snapshot.get("sources") or []
    sources = [item for item in raw_sources if isinstance(item, dict)]
    if sources:
        return sources
    return _fallback_collector_sources()


def _collector_status(raw: dict[str, Any]) -> str:
    if raw.get("skipped"):
        return "idle"
    if not raw.get("ok"):
        return "failed"
    age_h = raw.get("age_h")
    threshold_h = raw.get("threshold_h")
    try:
        age_value = float(age_h)
        threshold_value = float(threshold_h)
    except (TypeError, ValueError):
        return "success"
    if age_value >= 0 and threshold_value > 0 and age_value > threshold_value * 0.5:
        return "delayed"
    return "success"


def _source_output_path(name: str) -> str:
    relative = SOURCE_OUTPUT_DIRS.get(name, name)
    return Path(relative).as_posix()


def _source_provider(name: str) -> str:
    return SOURCE_PROVIDER_HINTS.get(name, "Internal")


def _source_category(name: str) -> str:
    return SOURCE_CATEGORY_HINTS.get(name, "其他")


def _source_schedule(name: str) -> str:
    return SOURCE_SCHEDULE_HINTS.get(name, "")


def _source_schedule_type(schedule_expr: str) -> str:
    if schedule_expr in {"", "continuous"}:
        return "interval"
    return "cron"


def _collect_resource_usage(snapshot: dict[str, Any]) -> dict[str, Any]:
    cpu_percent = snapshot.get("cpu")
    mem_percent = snapshot.get("mem")
    disk_percent = snapshot.get("disk")
    memory_total_mb = 0
    memory_used_mb = 0
    logical_cores = os.cpu_count() or 1

    try:
        import psutil

        logical_cores = psutil.cpu_count(logical=True) or logical_cores
        if cpu_percent is None:
            cpu_percent = round(psutil.cpu_percent(interval=0.0), 1)
        virtual_memory = psutil.virtual_memory()
        memory_total_mb = int(virtual_memory.total // (1024 * 1024))
        memory_used_mb = int((virtual_memory.total - virtual_memory.available) // (1024 * 1024))
        if mem_percent is None:
            mem_percent = round(float(virtual_memory.percent), 1)
    except Exception:
        if cpu_percent is None:
            cpu_percent = -1.0
        if mem_percent is None:
            mem_percent = -1.0

    try:
        usage_root = _storage_root()
        if not usage_root.exists():
            usage_root = Path.home()
        total_bytes, used_bytes, free_bytes = shutil.disk_usage(usage_root)
        if disk_percent is None and total_bytes > 0:
            disk_percent = round(used_bytes / total_bytes * 100, 1)
    except Exception:
        total_bytes = 0
        used_bytes = 0
        free_bytes = 0
        if disk_percent is None:
            disk_percent = -1.0

    return {
        "cpu": {
            "usage_percent": float(cpu_percent),
            "logical_cores": logical_cores,
        },
        "memory": {
            "used_percent": float(mem_percent),
            "total_mb": memory_total_mb,
            "used_mb": memory_used_mb,
        },
        "disk": {
            "used_percent": float(disk_percent),
            "total_bytes": int(total_bytes),
            "used_bytes": int(used_bytes),
            "free_bytes": int(free_bytes),
        },
    }


def _service_info() -> dict[str, Any]:
    return {
        "name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "python_version": platform.python_version(),
        "runtime": os.getenv("BOTQUANT_DEVICE") or "data-service",
        "data_root": "DATA_STORAGE_ROOT",
        "api_port": int(os.getenv("JBT_SERVICE_PORT", os.getenv("SERVICE_PORT", "8105"))),
        "environment": os.getenv("JBT_ENV", os.getenv("ENV", "production")),
    }


def _recent_log_entries(limit: int = 40) -> list[dict[str, Any]]:
    path = _dashboard_scheduler_log_path()
    if not path.exists():
        return []
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    except Exception:
        return []

    entries: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        timestamp = None
        if len(line) >= 19 and line[:4].isdigit() and line[4] == "-":
            timestamp = line[:19]
        if "ERROR" in line or "❌" in line:
            level = "ERROR"
        elif "WARNING" in line or "WARN" in line or "⚠️" in line:
            level = "WARNING"
        else:
            level = "INFO"
        entries.append(
            {
                "timestamp": timestamp,
                "level": level,
                "source": "scheduler",
                "message": _sanitize_log_message(line),
            }
        )
    return entries


def _sanitize_log_message(line: str) -> str:
    sanitized = re.sub(r"https?://\S+", "[redacted-url]", line)
    sanitized = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[redacted-host]", sanitized)
    sanitized = re.sub(r"File \"[^\"]+\"", 'File "[redacted-path]"', sanitized)
    sanitized = re.sub(r"(?:/Users|/home|/tmp|~/)\S+", "[redacted-path]", sanitized)
    return _truncate_text(sanitized, limit=400)


def _process_entries(resources: dict[str, Any], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    scheduler_log = _dashboard_scheduler_log_path()
    scheduler_heartbeat = _timestamp_to_iso(scheduler_log.stat().st_mtime) if scheduler_log.exists() else None
    scheduler_status = "running" if scheduler_log.exists() else "warning"
    return [
        {
            "id": "data_api",
            "name": "数据 API",
            "status": "running",
            "pid": os.getpid(),
            "uptime": None,
            "cpu_usage": resources["cpu"]["usage_percent"],
            "mem_usage": resources["memory"]["used_percent"],
            "last_heartbeat": _now_iso(),
            "is_single_instance": True,
        },
        {
            "id": "data_scheduler",
            "name": "数据调度器",
            "status": scheduler_status,
            "pid": None,
            "uptime": None,
            "cpu_usage": float(snapshot.get("cpu", resources["cpu"]["usage_percent"])),
            "mem_usage": float(snapshot.get("mem", resources["memory"]["used_percent"])),
            "last_heartbeat": scheduler_heartbeat,
            "is_single_instance": True,
        },
    ]


def _notification_channels(settings: dict[str, Any]) -> list[dict[str, Any]]:
    monitor = settings.get("monitor") if isinstance(settings.get("monitor"), dict) else {}
    feishu = monitor.get("feishu") if isinstance(monitor.get("feishu"), dict) else {}
    email = monitor.get("email") if isinstance(monitor.get("email"), dict) else {}
    webhooks = feishu.get("webhooks") if isinstance(feishu.get("webhooks"), dict) else {}
    last_log = _recent_log_entries(limit=1)
    last_timestamp = last_log[-1]["timestamp"] if last_log else None
    channels: list[dict[str, Any]] = []
    for key, label in (("alert", "飞书报警"), ("news", "飞书新闻"), ("trade", "飞书交易")):
        raw_url = webhooks.get(key) or feishu.get("webhook_url") or ""
        channels.append(
            {
                "id": f"feishu-{key}",
                "name": label,
                "type": "feishu",
                "configured": bool(raw_url),
                "last_send_time": last_timestamp,
                "last_status": "success" if raw_url else "failed",
            }
        )
    channels.append(
        {
            "id": "email-default",
            "name": "邮件通知",
            "type": "email",
            "configured": bool(email.get("smtp_host") and email.get("username")),
            "last_send_time": last_timestamp,
            "last_status": "success" if email.get("smtp_host") else "failed",
        }
    )
    return channels


def _env_config(settings: dict[str, Any]) -> list[dict[str, Any]]:
    monitor = settings.get("monitor") if isinstance(settings.get("monitor"), dict) else {}
    feishu = monitor.get("feishu") if isinstance(monitor.get("feishu"), dict) else {}
    email = monitor.get("email") if isinstance(monitor.get("email"), dict) else {}
    data_sources = settings.get("data_sources") if isinstance(settings.get("data_sources"), dict) else {}
    tushare = data_sources.get("tushare") if isinstance(data_sources.get("tushare"), dict) else {}
    tqsdk = data_sources.get("tqsdk") if isinstance(data_sources.get("tqsdk"), dict) else {}
    entries = [
        ("TUSHARE_TOKEN", bool(tushare.get("token"))),
        ("TQSDK_USERNAME", bool(tqsdk.get("username"))),
        ("TQSDK_PASSWORD", bool(tqsdk.get("password"))),
        ("FEISHU_WEBHOOK_ALERT", bool(((feishu.get("webhooks") or {}) if isinstance(feishu.get("webhooks"), dict) else {}).get("alert"))),
        ("FEISHU_WEBHOOK_NEWS", bool(((feishu.get("webhooks") or {}) if isinstance(feishu.get("webhooks"), dict) else {}).get("news"))),
        ("FEISHU_WEBHOOK_TRADE", bool(((feishu.get("webhooks") or {}) if isinstance(feishu.get("webhooks"), dict) else {}).get("trade"))),
        ("SMTP_HOST", bool(email.get("smtp_host"))),
        ("SMTP_PORT", bool(email.get("smtp_port"))),
        ("SMTP_USER", bool(email.get("username"))),
        ("SMTP_PASSWORD", bool(email.get("password"))),
    ]
    return [
        {
            "key": key,
            "configured": configured,
        }
        for key, configured in entries
    ]


def _data_source_connections(settings: dict[str, Any]) -> list[dict[str, Any]]:
    data_sources = settings.get("data_sources") if isinstance(settings.get("data_sources"), dict) else {}
    monitor = settings.get("monitor") if isinstance(settings.get("monitor"), dict) else {}
    email = monitor.get("email") if isinstance(monitor.get("email"), dict) else {}
    return [
        {
            "name": "Tushare",
            "status": "connected" if (data_sources.get("tushare") or {}).get("enabled") else "disabled",
            "configured": bool((data_sources.get("tushare") or {}).get("token")),
        },
        {
            "name": "TqSdk",
            "status": "connected" if (data_sources.get("tqsdk") or {}).get("enabled") else "disabled",
            "configured": bool((data_sources.get("tqsdk") or {}).get("username")),
        },
        {
            "name": "AkShare",
            "status": "connected" if (data_sources.get("akshare") or {}).get("enabled") else "disabled",
            "configured": True,
        },
        {
            "name": "SMTP",
            "status": "connected" if email.get("smtp_host") else "disabled",
            "configured": bool(email.get("username")),
        },
        {
            "name": "飞书 Webhook",
            "status": "connected" if (monitor.get("feishu") or {}).get("webhooks") else "disabled",
            "configured": bool((monitor.get("feishu") or {}).get("webhooks")),
        },
    ]


def _directory_metrics(path: Path, max_scan: int = 2048) -> dict[str, Any]:
    if not path.exists():
        return {"size_bytes": 0, "file_count": 0, "dir_count": 0, "last_modified": None, "truncated": False}
    if path.is_file():
        stat = path.stat()
        return {
            "size_bytes": int(stat.st_size),
            "file_count": 1,
            "dir_count": 0,
            "last_modified": _timestamp_to_iso(stat.st_mtime),
            "truncated": False,
        }

    size_bytes = 0
    file_count = 0
    dir_count = 0
    last_modified: float = 0.0
    truncated = False
    for index, child in enumerate(path.rglob("*"), start=1):
        if index > max_scan:
            truncated = True
            break
        try:
            stat = child.stat()
        except OSError:
            continue
        last_modified = max(last_modified, stat.st_mtime)
        if child.is_dir():
            dir_count += 1
            continue
        file_count += 1
        size_bytes += int(stat.st_size)
    return {
        "size_bytes": size_bytes,
        "file_count": file_count,
        "dir_count": dir_count,
        "last_modified": _timestamp_to_iso(last_modified),
        "truncated": truncated,
    }


def _safe_storage_relative(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(_storage_root().resolve(strict=False)).as_posix()
    except ValueError:
        return path.name


def _tree_node(path: Path, *, max_depth: int, max_children: int) -> dict[str, Any]:
    metrics = _directory_metrics(path, max_scan=256)
    node: dict[str, Any] = {
        "name": path.name,
        "path": _safe_storage_relative(path),
        "type": "folder" if path.is_dir() else "file",
        "size_bytes": metrics["size_bytes"],
        "size_human": _human_bytes(metrics["size_bytes"]),
        "file_count": metrics["file_count"],
        "dir_count": metrics["dir_count"],
        "last_modified": metrics["last_modified"],
        "truncated": metrics["truncated"],
    }
    if path.is_file():
        node["suffix"] = path.suffix
        return node
    children: list[dict[str, Any]] = []
    if max_depth > 0 and path.exists():
        try:
            for child in sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))[:max_children]:
                children.append(_tree_node(child, max_depth=max_depth - 1, max_children=max_children))
        except OSError:
            children = []
    node["children"] = children
    return node


def _candidate_news_files(max_files: int = 40) -> list[Path]:
    files: list[Path] = []
    for directory_name in NEWS_DIRECTORIES:
        root = _storage_root() / directory_name
        if not root.exists():
            continue
        for pattern in ("*.json", "*.jsonl"):
            files.extend(path for path in root.rglob(pattern) if path.is_file())
    return sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)[:max_files]


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "y", "ok", "success", "sent"}


def _normalize_sentiment(value: Any) -> str:
    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric > 0.1:
            return "positive"
        if numeric < -0.1:
            return "negative"
        return "neutral"
    normalized = str(value or "").strip().lower()
    if normalized in {"positive", "bullish", "up"}:
        return "positive"
    if normalized in {"negative", "bearish", "down"}:
        return "negative"
    return "neutral"


def _normalize_keywords(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [item.strip() for item in re.split(r"\s+", value) if item.strip()]
    return []


def _extract_json_items(path: Path) -> list[dict[str, Any]]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    if path.suffix == ".jsonl":
        items: list[dict[str, Any]] = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except Exception:
                continue
            if isinstance(parsed, dict):
                items.append(parsed)
        return items
    try:
        parsed = json.loads(content)
    except Exception:
        return []
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        for key in ("items", "news", "records", "data"):
            candidate = parsed.get(key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        return [parsed]
    return []


def _normalize_news_item(raw: dict[str, Any], path: Path, index: int) -> Optional[dict[str, Any]]:
    # 展开调度器采集输出的嵌套 payload 格式
    data = raw
    if "payload" in raw and isinstance(raw["payload"], dict):
        data = {**raw, **raw["payload"]}
    title = str(data.get("title") or data.get("headline") or data.get("subject") or "").strip()
    if not title:
        return None
    # 解析发布时间（兼容 Unix 时间戳字符串）
    raw_time = (
        data.get("publish_time")
        or data.get("published_at")
        or data.get("time")
        or data.get("datetime")
        or data.get("timestamp")
    )
    if raw_time is not None:
        try:
            numeric = float(raw_time)
            if numeric > 1e9:
                publish_time = _timestamp_to_iso(numeric) or ""
            else:
                publish_time = str(raw_time)
        except (TypeError, ValueError):
            publish_time = str(raw_time)
    else:
        publish_time = _timestamp_to_iso(path.stat().st_mtime) or ""
    source = str(
        data.get("source") or data.get("provider") or data.get("channel")
        or data.get("feed") or data.get("symbol_or_indicator")
        or path.parent.name or "unknown"
    )
    summary = str(data.get("summary") or data.get("content") or data.get("abstract") or data.get("body") or data.get("full_text") or "")
    keywords = _normalize_keywords(data.get("keywords") or data.get("tags") or [])
    return {
        "id": str(data.get("id") or data.get("_uid") or f"{path.stem}-{index}"),
        "title": title,
        "source": source,
        "publish_time": publish_time,
        "summary": _truncate_text(summary, limit=300),
        "keywords": keywords,
        "sentiment": _normalize_sentiment(data.get("sentiment") or data.get("news_score") or data.get("sentiment_score")),
        "is_important": _coerce_bool(data.get("is_important") or data.get("important") or data.get("priority") == "high"),
        "is_pushed": _coerce_bool(data.get("is_pushed") or data.get("pushed") or data.get("push_status")),
        "file": _safe_storage_relative(path),
    }


def _news_items(limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in _candidate_news_files():
        for index, raw in enumerate(_extract_json_items(path)):
            normalized = _normalize_news_item(raw, path, index)
            if normalized is not None:
                items.append(normalized)
            if len(items) >= limit:
                return items
    return items


def _hot_keywords(items: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        for keyword in item.get("keywords", []):
            counts[keyword] = counts.get(keyword, 0) + 1
    ranked = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))
    return [{"word": word, "count": count} for word, count in ranked[:limit]]


def _source_breakdown(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        source = str(item.get("source") or "unknown")
        counts[source] = counts.get(source, 0) + 1
    ranked = sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))
    return [{"source": source, "count": count} for source, count in ranked]


def _sentiment_distribution(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for item in items:
        sentiment = str(item.get("sentiment") or "neutral")
        counts[sentiment] = counts.get(sentiment, 0) + 1
    return [{"sentiment": key, "count": value} for key, value in counts.items()]


@app.get("/api/v1/dashboard/system")
def dashboard_system() -> dict[str, Any]:
    settings = _settings_config()
    snapshot = _load_collector_snapshot()
    resources = _collect_resource_usage(snapshot)
    return {
        "generated_at": _now_iso(),
        "service": _service_info(),
        "resources": resources,
        "processes": _process_entries(resources, snapshot),
        "notifications": _notification_channels(settings),
        "sources": _collector_sources(),
        "settings": {
            "env": _env_config(settings),
            "connections": _data_source_connections(settings),
            "schedules": _flatten_schedule_rows(),
        },
        "logs": _recent_log_entries(),
    }


@app.get("/api/v1/dashboard/collectors")
def dashboard_collectors() -> dict[str, Any]:
    snapshot = _load_collector_snapshot()
    snapshot_time = snapshot.get("ts")
    collectors: list[dict[str, Any]] = []
    summary = {"total": 0, "success": 0, "failed": 0, "delayed": 0, "idle": 0}

    for source in _collector_sources():
        name = str(source.get("name") or "unknown")
        status = _collector_status(source)
        summary[status] += 1
        summary["total"] += 1
        schedule_expr = _source_schedule(name)
        collectors.append(
            {
                "id": name,
                "name": str(source.get("label") or name),
                "category": _source_category(name),
                "status": status,
                "last_result": status,
                "age_str": source.get("age_str"),
                "age_h": source.get("age_h"),
                "threshold_h": source.get("threshold_h"),
                "schedule_expr": schedule_expr,
                "schedule_type": _source_schedule_type(schedule_expr),
                "last_run_time": snapshot_time,
                "data_source": _source_provider(name),
                "output_dir": _source_output_path(name),
                "trading_only": bool(source.get("trading_only")),
                "skipped": bool(source.get("skipped")),
                "description": f"{str(source.get('label') or name)} 只读聚合状态",
                "errors": [] if status != "failed" else [{"message": str(source.get("age_str") or "采集异常")}],
            }
        )

    return {
        "generated_at": _now_iso(),
        "summary": summary,
        "collectors": collectors,
    }


@app.get("/api/v1/dashboard/storage")
def dashboard_storage(
    max_depth: int = Query(2, ge=1, le=3),
    max_children: int = Query(12, ge=1, le=25),
) -> dict[str, Any]:
    root = _storage_root()
    metrics = _directory_metrics(root, max_scan=4096)
    entries: list[dict[str, Any]] = []
    tree: list[dict[str, Any]] = []
    if root.exists():
        try:
            # 按类别排序：特殊目录 > 交易所合约 > 股票代码，避免被 5000+ 股票淹没
            def _dir_sort_key(item: Path) -> tuple:
                name = item.name
                if item.is_file():
                    return (3, 0, name.lower())
                if name[:1].isdigit() and len(name) == 6:
                    return (2, 0, name)  # 6位纯数字股票代码排最后
                if "." in name:  # 交易所.品种 格式
                    exchange = name.split(".")[0]
                    exchange_order = {
                        "SHFE": 0, "DCE": 1, "CZCE": 2, "INE": 3,
                        "CFFEX": 4, "GFEX": 5, "COMEX": 6, "NYMEX": 7,
                        "CBOT": 8, "CME": 9, "ICE": 10, "LME": 11, "SGX": 12,
                    }.get(exchange, 13)
                    return (1, exchange_order, name.lower())
                return (0, 0, name.lower())  # 特殊目录排最前
            top_level = sorted(root.iterdir(), key=_dir_sort_key)[:max_children]
        except OSError:
            top_level = []
        entries = [_tree_node(path, max_depth=1, max_children=max_children) for path in top_level]
        tree = [_tree_node(path, max_depth=max_depth, max_children=max_children) for path in top_level]
    return {
        "generated_at": _now_iso(),
        "root": "DATA_STORAGE_ROOT",
        "root_label": root.name or "storage",
        "exists": root.exists(),
        "totals": {
            "size_bytes": metrics["size_bytes"],
            "size_human": _human_bytes(metrics["size_bytes"]),
            "files": metrics["file_count"],
            "directories": metrics["dir_count"],
            "last_modified": metrics["last_modified"],
            "truncated": metrics["truncated"],
        },
        "directories": entries,
        "tree": tree,
    }


@app.get("/api/v1/dashboard/news")
def dashboard_news(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    items = _news_items(limit)
    pushed_items = [item for item in items if item["is_pushed"]]
    important_items = [item for item in items if item["is_important"]]
    return {
        "generated_at": _now_iso(),
        "summary": {
            "total_items": len(items),
            "important_count": len(important_items),
            "pushed_count": len(pushed_items),
            "source_count": len(_source_breakdown(items)),
        },
        "items": items,
        "hot_keywords": _hot_keywords(items),
        "source_breakdown": _source_breakdown(items),
        "push_records": [
            {
                "title": item["title"],
                "source": item["source"],
                "time": item["publish_time"],
            }
            for item in pushed_items[:10]
        ],
        "sentiment_distribution": _sentiment_distribution(items),
    }


# ─────────────────────────────────────────────
# 运维 API（P0 飞书按钮回调 + 手动触发）
# ─────────────────────────────────────────────
_OPS_SECRET = os.environ.get("DATA_OPS_SECRET", "")


def _verify_ops_token(token: Optional[str]) -> None:
    """校验运维操作令牌。"""
    if not _OPS_SECRET:
        raise HTTPException(status_code=503, detail="ops not configured")
    if not token or not hmac.compare_digest(token, _OPS_SECRET):
        raise HTTPException(status_code=403, detail="invalid ops token")


@app.post("/api/v1/ops/restart-collector")
def ops_restart_collector(
    collector: str = Query(..., min_length=1),
    x_ops_token: Optional[str] = Header(None, alias="X-Ops-Token"),
) -> dict[str, Any]:
    """重启指定采集器（通过 launchctl 重新加载 plist）。

    由飞书 P0 按钮触发或命令行手动调用。
    """
    _verify_ops_token(x_ops_token)

    # 安全白名单
    _PLIST_MAP = {
        "data_scheduler": "com.botquant.data_scheduler",
        "news": "com.botquant.news",
        "health": "com.botquant.health",
        "futures_minute": "com.botquant.futures.minute",
        "futures_eod": "com.botquant.futures.eod",
        "overseas_minute": "com.botquant.overseas.minute",
        "overseas_daily": "com.botquant.overseas.daily",
        "macro": "com.botquant.macro",
        "tushare": "com.botquant.tushare",
        "sentiment": "com.botquant.sentiment",
        "shipping": "com.botquant.shipping",
        "stock_minute": "com.botquant.stock.minute",
        "volatility_cboe": "com.botquant.volatility.cboe",
    }

    plist_id = _PLIST_MAP.get(collector)
    if not plist_id:
        raise HTTPException(status_code=422, detail=f"unknown collector: {collector}")

    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{plist_id}.plist"
    if not plist_path.exists():
        raise HTTPException(status_code=404, detail=f"plist not found: {plist_id}")

    # kickstart = unload + load
    try:
        subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{plist_id}"],
            capture_output=True, text=True, timeout=15,
        )
        return {"status": "ok", "collector": collector, "plist": plist_id, "action": "restart"}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="restart timed out")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/ops/auto-remediate")
def ops_auto_remediate(
    x_ops_token: Optional[str] = Header(None, alias="X-Ops-Token"),
) -> dict[str, Any]:
    """触发自动修复脚本。"""
    _verify_ops_token(x_ops_token)

    remediate_script = Path(__file__).resolve().parents[1] / "scripts" / "health_remediate.py"
    if not remediate_script.exists():
        raise HTTPException(status_code=404, detail="remediate script not found")

    try:
        import sys
        result = subprocess.run(
            [sys.executable, str(remediate_script)],
            capture_output=True, text=True, timeout=120,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout[-500:],
            "stderr": result.stderr[-200:],
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="remediation timed out")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    service_port = int(os.getenv("JBT_SERVICE_PORT", os.getenv("SERVICE_PORT", "8105")))
    uvicorn.run(app, host="0.0.0.0", port=service_port)