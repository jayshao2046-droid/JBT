"""Unified logger factory for JBT-DATA service.

Features:
- JSON structured logging for Docker/production (JBT_LOG_FORMAT=json)
- Human-readable text logging for local dev (default)
- TimedRotatingFileHandler with 14-day retention
- Log directory from JBT_DATA_LOG_DIR env or services/data/logs/
"""

from __future__ import annotations

import json as _json
import logging
import os
import traceback
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[2]  # services/data/
_LOG_DIR = Path(os.getenv("JBT_DATA_LOG_DIR", str(_SERVICE_ROOT / "logs")))
_LOG_FORMAT = os.getenv("JBT_LOG_FORMAT", "text")  # "json" or "text"
_TEXT_FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.utcfromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "service": "jbt-data",
        }
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = traceback.format_exception(*record.exc_info)
        return _json.dumps(entry, ensure_ascii=False)


def _get_formatter() -> logging.Formatter:
    return _JSONFormatter() if _LOG_FORMAT == "json" else _TEXT_FORMATTER


def _build_file_handler(file_path: Path, level: int) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        filename=str(file_path),
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(_get_formatter())
    return handler


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with console and date-based file outputs."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    expected_info = str((_LOG_DIR / f"info_{today}.log").resolve())
    expected_error = str((_LOG_DIR / f"error_{today}.log").resolve())

    existing_info = False
    existing_error = False
    has_console = False

    for handler in logger.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            current_file = str(Path(handler.baseFilename).resolve())
            if current_file == expected_info:
                existing_info = True
            elif current_file == expected_error:
                existing_error = True
        elif isinstance(handler, logging.StreamHandler):
            has_console = True

    if not existing_info:
        logger.addHandler(_build_file_handler(_LOG_DIR / f"info_{today}.log", logging.INFO))

    if not existing_error:
        logger.addHandler(_build_file_handler(_LOG_DIR / f"error_{today}.log", logging.ERROR))

    if not has_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(_get_formatter())
        logger.addHandler(console_handler)

    return logger
