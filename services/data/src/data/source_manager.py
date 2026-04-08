"""Manage failover between primary and secondary data sources.

Migrated from legacy J_BotQuant/src/data/source_manager.py.
Import paths updated: src.utils → services.data.src.utils
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from services.data.src.utils.exceptions import DataError
from services.data.src.utils.logger import get_logger


class DataSource(Protocol):
    """A data source must implement fetch."""

    def fetch(self, *args: Any, **kwargs: Any) -> Any:
        ...


class SourceManager:
    """Switch to backup source automatically when primary source fails.

    Supports any collector pair that implements ``fetch()`` (BaseCollector
    provides this as an alias for ``collect()``).  Backup is optional —
    when ``None``, failures on the primary propagate directly.
    """

    def __init__(
        self,
        primary_source: DataSource,
        backup_source: DataSource | None = None,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self.primary_source = primary_source
        self.backup_source = backup_source
        self.logger = logger or get_logger("data.source_manager")

    # ── public API ────────────────────────────────────────────
    def collect(self, *args: Any, **kwargs: Any) -> Any:
        """SourceManager-compatible entry point (alias for ``fetch``)."""
        return self.fetch(*args, **kwargs)

    def fetch(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch from primary source and fail over to backup on exception."""
        try:
            data = self.primary_source.fetch(*args, **kwargs)
            if data is not None:
                return data
        except Exception as primary_exc:
            if self.backup_source is None:
                self.logger.error("primary source failed, no backup configured: %s", primary_exc)
                raise
            self.logger.warning("primary source failed, switching to backup: %s", primary_exc)
            try:
                return self.backup_source.fetch(*args, **kwargs)
            except Exception as backup_exc:
                self.logger.error(
                    "backup source failed after switch, primary=%s backup=%s",
                    primary_exc,
                    backup_exc,
                )
                raise DataError(
                    f"both data sources failed: primary={primary_exc}; backup={backup_exc}"
                ) from backup_exc

        # primary returned None → try backup if available
        if self.backup_source is not None:
            self.logger.warning("primary source returned empty, trying backup")
            return self.backup_source.fetch(*args, **kwargs)
        return data
