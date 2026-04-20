"""Data cleanup utilities for JBT data service.

Migrated from Mini shell scripts:
- _cleanup_botquandata.sh: remove old temp files and stale logs
- cleanup_data_tmp.sh: clean /tmp leftovers

In JBT Docker, cleanup runs as a scheduled job.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("data.ops.cleanup")


def cleanup_old_logs(
    *,
    log_dir: str | Path,
    max_age_days: int = 14,
) -> int:
    """Remove log files older than max_age_days."""
    log_path = Path(log_dir)
    if not log_path.exists():
        return 0

    cutoff = time.time() - max_age_days * 86400
    removed = 0
    for f in log_path.glob("*.log*"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
            logger.debug("removed old log: %s", f)

    logger.info("cleanup_old_logs: removed %d files from %s (age > %d days)", removed, log_path, max_age_days)
    return removed


def cleanup_temp_files(
    *,
    data_dir: str | Path,
    patterns: list[str] | None = None,
) -> int:
    """Remove temporary/partial files from data directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        return 0

    _patterns = patterns or ["*.tmp", "*.partial", "*.lock", ".*.swp"]
    removed = 0
    for pattern in _patterns:
        for f in data_path.rglob(pattern):
            f.unlink()
            removed += 1
            logger.debug("removed temp file: %s", f)

    logger.info("cleanup_temp_files: removed %d files from %s", removed, data_path)
    return removed
