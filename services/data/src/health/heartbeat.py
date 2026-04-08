"""Heartbeat writer for JBT data service.

Migrated from Mini crontab: `* * * * * touch ~/.mini_heartbeat`
Now runs as a background thread within the data service process.
"""

from __future__ import annotations

import time
import threading
from datetime import datetime
from pathlib import Path

from services.data.src.utils.logger import get_logger

logger = get_logger("data.heartbeat")

_DEFAULT_HEARTBEAT_FILE = Path.home() / ".jbt_data_heartbeat"
_DEFAULT_INTERVAL_SEC = 60


class HeartbeatWriter:
    """Writes a heartbeat timestamp file at fixed intervals."""

    def __init__(
        self,
        *,
        heartbeat_file: Path | None = None,
        interval_sec: int = _DEFAULT_INTERVAL_SEC,
    ) -> None:
        self._file = heartbeat_file or _DEFAULT_HEARTBEAT_FILE
        self._interval = interval_sec
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start heartbeat writer in a daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("heartbeat already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="heartbeat-writer")
        self._thread.start()
        logger.info("heartbeat started: file=%s interval=%ds", self._file, self._interval)

    def stop(self) -> None:
        """Stop the heartbeat writer."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("heartbeat stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._file.write_text(datetime.now().isoformat(), encoding="utf-8")
            except Exception as exc:
                logger.error("heartbeat write failed: %s", exc)
            self._stop_event.wait(timeout=self._interval)

    def is_alive(self, stale_seconds: int = 120) -> bool:
        """Check if the heartbeat file was updated within stale_seconds."""
        if not self._file.exists():
            return False
        try:
            age = time.time() - self._file.stat().st_mtime
            return age < stale_seconds
        except OSError:
            return False
