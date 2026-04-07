from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, NamedTuple

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

SERVICE_NAME = "data"
SERVICE_VERSION = "0.1.0-minimal"
DEFAULT_STORAGE_ROOT = Path("/runtime/data")
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

app = FastAPI(title="JBT Data Service", version=SERVICE_VERSION)


class ParsedTimeRange(NamedTuple):
    timestamp: pd.Timestamp
    date_only: bool


class SymbolRequest(NamedTuple):
    requested_symbol: str
    exact_symbol: str | None
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


def _storage_root() -> Path:
    raw_root = os.getenv("DATA_STORAGE_ROOT", str(DEFAULT_STORAGE_ROOT))
    return Path(raw_root).expanduser()


def _minute_root() -> Path:
    return _storage_root() / MINUTE_DATA_SUBDIR


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


if __name__ == "__main__":
    import uvicorn

    service_port = int(os.getenv("JBT_SERVICE_PORT", os.getenv("SERVICE_PORT", "8105")))
    uvicorn.run(app, host="0.0.0.0", port=service_port)