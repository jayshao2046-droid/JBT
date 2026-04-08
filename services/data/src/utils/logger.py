"""Unified logger factory for JBT data service.

Migrated from legacy J_BotQuant/src/utils/logger.py with adaptations:
- Log directory defaults to services/data/logs/
- Supports LOG_DIR env override for Docker mount
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[2]  # services/data/
_LOG_DIR = Path(os.getenv("JBT_DATA_LOG_DIR", str(_SERVICE_ROOT / "logs")))
_FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def _build_file_handler(file_path: Path, level: int) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        filename=str(file_path),
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(_FORMATTER)
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
        console_handler.setFormatter(_FORMATTER)
        logger.addHandler(console_handler)

    return logger
