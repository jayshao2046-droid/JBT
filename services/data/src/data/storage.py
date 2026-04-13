"""Parquet-based storage utilities for data records.

Migrated from legacy J_BotQuant/src/data/storage.py.
Import paths updated: services.data.src.utils → src.utils
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import os

from src.utils.exceptions import StorageError

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    duckdb = None

try:
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    pa = None
    pq = None


def _default_storage_root() -> Path:
    """Return the data storage root from env or fallback."""
    return Path(os.environ.get("DATA_STORAGE_ROOT", str(Path(__file__).resolve().parents[3] / "runtime" / "data")))


class ParquetStorage:
    """Provide read/write/query operations for records organized by symbol and data type."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        default_dir = _default_storage_root() / "parquet"
        self.base_dir = Path(base_dir).expanduser() if base_dir else default_dir

    def _build_file_path(self, data_type: str, symbol: str) -> Path:
        file_dir = self.base_dir / symbol / data_type
        file_dir.mkdir(parents=True, exist_ok=True)
        return file_dir / "records.parquet"

    def write_records(
        self,
        data_type: str,
        symbol: str,
        records: list[dict[str, Any]],
        *,
        key: str = "records",
        index_field: str | None = None,
        sort_by: str | list[str] | None = None,
        complevel: int = 5,
        complib: str = "snappy",
        mode: str = "a",
    ) -> int:
        """Write records into parquet and return number of written rows."""
        _ = key, index_field, complevel
        if not records:
            return 0
        if pa is None or pq is None:
            raise StorageError("pyarrow is required for parquet storage")
        try:
            file_path = self._build_file_path(data_type=data_type, symbol=symbol)
            rows = [dict(item) for item in records]
            if sort_by is not None:
                keys = [sort_by] if isinstance(sort_by, str) else list(sort_by)
                rows = sorted(rows, key=lambda item: tuple(item.get(k) for k in keys))

            incoming_table = pa.Table.from_pylist(rows)
            if mode == "a" and file_path.exists():
                existing_table = pq.read_table(file_path)
                table = pa.concat_tables([existing_table, incoming_table], promote_options="default")
            else:
                table = incoming_table

            compression = "snappy" if complib.lower() == "snappy" else "zstd"
            pq.write_table(table, file_path, compression=compression)
            return len(rows)
        except Exception as exc:
            raise StorageError(
                f"failed to write records for symbol={symbol}, data_type={data_type}: {exc}"
            ) from exc

    def read_records(
        self,
        data_type: str,
        symbol: str,
        *,
        key: str = "records",
        where: str | list[str] | None = None,
        columns: list[str] | None = None,
        start: int | None = None,
        stop: int | None = None,
        sort_by: str | list[str] | None = None,
        ascending: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Read records from parquet and return list of dictionaries."""
        _ = key, where
        if pa is None or pq is None:
            raise StorageError("pyarrow is required for parquet storage")
        try:
            file_path = self._build_file_path(data_type=data_type, symbol=symbol)
            if not file_path.exists():
                return []

            table = pq.read_table(file_path, columns=columns)
            rows = table.to_pylist()

            if start is not None or stop is not None:
                rows = rows[start:stop]

            if sort_by is not None:
                sort_keys = [sort_by] if isinstance(sort_by, str) else list(sort_by)
                rows = sorted(rows, key=lambda item: tuple(item.get(k) for k in sort_keys), reverse=not ascending)

            if limit is not None and limit >= 0:
                rows = rows[:limit]

            return [dict(item) for item in rows]
        except Exception as exc:
            raise StorageError(
                f"failed to read records for symbol={symbol}, data_type={data_type}: {exc}"
            ) from exc

    def query_records(
        self,
        data_type: str,
        symbol: str,
        *,
        sql_where: str | None = None,
        columns: list[str] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query parquet with DuckDB and return records."""
        file_path = self._build_file_path(data_type=data_type, symbol=symbol)
        if not file_path.exists():
            return []

        if duckdb is None:
            return self.read_records(data_type=data_type, symbol=symbol, columns=columns, limit=limit)

        try:
            selected = ", ".join(columns) if columns else "*"
            sql = f"SELECT {selected} FROM read_parquet('{file_path.as_posix()}')"  # nosec B608 — file_path is a Path object, not user input
            if sql_where:
                sql += f" WHERE {sql_where}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit is not None and limit >= 0:
                sql += f" LIMIT {int(limit)}"

            with duckdb.connect(database=":memory:") as conn:
                rows = conn.execute(sql).fetchall()
                names = [desc[0] for desc in conn.description or []]
            return [dict(zip(names, row)) for row in rows]
        except Exception as exc:
            raise StorageError(
                f"failed to query records for symbol={symbol}, data_type={data_type}: {exc}"
            ) from exc


class HDF5Storage(ParquetStorage):
    """Backward-compatible storage name; internally uses parquet implementation."""
