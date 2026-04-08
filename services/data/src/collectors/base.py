"""Base abstractions for collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# TODO(A2): storage 模块将在 A2 批次迁移后启用
# from src.data.storage import HDF5Storage
from services.data.src.utils.config import get_config
from services.data.src.utils.exceptions import DataError
from services.data.src.utils.logger import get_logger


class BaseCollector(ABC):
    """Abstract collector with unified logging, retries and save flow."""

    def __init__(
        self,
        *,
        name: str,
        storage: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.logger = get_logger(f"data.collector.{name}")
        self.storage = storage  # TODO(A2): 默认使用 HDF5Storage()
        self.config = config or get_config()
        collection_cfg = self.config.get("collection", {})
        self.retry_times = int(collection_cfg.get("retry_times", 3))

    @abstractmethod
    def collect(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Collect data records in unified schema."""

    def fetch(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """SourceManager-compatible alias."""
        return self.collect(*args, **kwargs)

    def save(
        self,
        *,
        symbol: str,
        records: list[dict[str, Any]],
        data_type: str,
        key: str = "records",
    ) -> int:
        """Persist records via HDF5Storage."""
        if not records:
            self.logger.warning("no records to save: source=%s symbol=%s", self.name, symbol)
            return 0
        if self.storage is None:
            self.logger.warning("storage not initialized (A2 pending): source=%s symbol=%s, skipping save", self.name, symbol)
            return 0
        try:
            return self.storage.write_records(
                data_type=data_type,
                symbol=symbol,
                records=records,
                key=key,
                sort_by="timestamp",
                mode="a",
            )
        except Exception as exc:
            self.logger.error("save failed: source=%s symbol=%s error=%s", self.name, symbol, exc)
            raise DataError(f"save failed for source={self.name}, symbol={symbol}: {exc}") from exc

    def run(self, *, symbol: str, data_type: str, **kwargs: Any) -> tuple[list[dict[str, Any]], int]:
        """Collect then save with retries."""
        records = self._collect_with_retry(symbol=symbol, **kwargs)
        written = self.save(symbol=symbol, records=records, data_type=data_type)
        return records, written

    def _collect_with_retry(self, **kwargs: Any) -> list[dict[str, Any]]:
        last_exc: Exception | None = None
        attempts = max(self.retry_times, 1)
        for attempt in range(1, attempts + 1):
            try:
                records = self.collect(**kwargs)
                self.logger.info(
                    "collect success: source=%s attempt=%s records=%s",
                    self.name,
                    attempt,
                    len(records),
                )
                return records
            except Exception as exc:
                last_exc = exc
                self.logger.warning(
                    "collect attempt failed: source=%s attempt=%s error=%s",
                    self.name,
                    attempt,
                    exc,
                )
        raise DataError(f"collect failed after {attempts} attempts for source={self.name}: {last_exc}")
