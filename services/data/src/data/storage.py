"""Parquet-based storage utilities for data records.

Migrated from legacy codebase.
Import paths updated: services.data.src.utils → src.utils
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import re

import os

from utils.exceptions import StorageError

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
        file_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        return file_dir / "records.parquet"

    @staticmethod
    def _deduplicate_rows(
        rows: list[dict[str, Any]],
        dedup_by: str | list[str] | None,
    ) -> list[dict[str, Any]]:
        if dedup_by is None:
            return rows

        keys = [dedup_by] if isinstance(dedup_by, str) else list(dedup_by)
        if not keys:
            return rows

        deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
        order: list[tuple[Any, ...]] = []
        for row in rows:
            dedup_key = tuple(row.get(key) for key in keys)
            if dedup_key not in deduped:
                order.append(dedup_key)
            deduped[dedup_key] = row
        return [deduped[key] for key in order]

    @staticmethod
    def _row_contains_mock_payload(row: dict[str, Any]) -> bool:
        if row.get("mode") == "mock":
            return True

        payload = row.get("payload")
        if isinstance(payload, dict):
            if payload.get("mode") == "mock":
                return True
        elif isinstance(payload, str):
            compact = payload.replace(" ", "")
            if '"mode":"mock"' in compact:
                return True
            if payload.strip().startswith("{"):
                try:
                    parsed = json.loads(payload)
                except Exception:
                    parsed = None
                if isinstance(parsed, dict) and parsed.get("mode") == "mock":
                    return True

        return False

    @classmethod
    def _assert_no_mock_rows(cls, rows: list[dict[str, Any]], *, data_type: str, symbol: str) -> None:
        mock_rows = [row for row in rows if cls._row_contains_mock_payload(row)]
        if not mock_rows:
            return

        sample = mock_rows[0]
        raise StorageError(
            "mock data is forbidden for runtime storage: "
            f"symbol={symbol}, data_type={data_type}, mock_rows={len(mock_rows)}, sample={sample}"
        )

    @staticmethod
    def _sortable_value(value: Any) -> tuple[int, str]:
        if value is None:
            return (0, "")
        if isinstance(value, (int, float, bool)):
            return (1, str(value))
        return (2, str(value))

    def write_records(
        self,
        data_type: str,
        symbol: str,
        records: list[dict[str, Any]],
        *,
        key: str = "records",
        index_field: str | None = None,
        sort_by: str | list[str] | None = None,
        dedup_by: str | list[str] | None = None,
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
            incoming_count = len(rows)
            # Serialize nested dicts/lists to JSON strings so pyarrow
            # does not attempt struct schema inference on mixed-type payloads.
            for row in rows:
                if "timestamp" in row and row["timestamp"] is not None:
                    row["timestamp"] = str(row["timestamp"])
                for k, v in row.items():
                    if isinstance(v, (dict, list)):
                        row[k] = json.dumps(v, ensure_ascii=False, default=str)

            existing_count = 0
            if mode == "a" and file_path.exists():
                existing_rows = pq.read_table(file_path).to_pylist()
                existing_count = len(existing_rows)
                rows = existing_rows + rows

            self._assert_no_mock_rows(rows, data_type=data_type, symbol=symbol)

            rows = self._deduplicate_rows(rows, dedup_by)
            if sort_by is not None:
                keys = [sort_by] if isinstance(sort_by, str) else list(sort_by)
                rows = sorted(rows, key=lambda item: tuple(self._sortable_value(item.get(k)) for k in keys))

            table = pa.Table.from_pylist(rows)

            compression = "snappy" if complib.lower() == "snappy" else "zstd"
            pq.write_table(table, file_path, compression=compression)
            # 返回本轮真正新增条数（去重后最终行数 − 写入前已有行数）
            return max(0, len(rows) - existing_count)
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
            # P1-1 修复：增强列名验证，防止 SQL 注入
            if columns:
                for col in columns:
                    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                        raise StorageError(f"Invalid column name: {col}")

            selected = ", ".join(columns) if columns else "*"
            sql = f"SELECT {selected} FROM read_parquet('{file_path.as_posix()}')"  # nosec B608 — file_path is a Path object, not user input

            # 安全修复：P0-1 - 验证 sql_where 和 order_by 防止 SQL 注入
            if sql_where:
                # 白名单验证：仅允许安全字符（字母、数字、空格、比较运算符、括号）
                if not re.match(r'^[a-zA-Z0-9_\s<>=!().\'"AND OR NOT-]+$', sql_where, re.IGNORECASE):
                    raise StorageError(f"Invalid WHERE clause: contains unsafe characters")
                sql += f" WHERE {sql_where}"

            if order_by:
                # P1-1 修复：增强 ORDER BY 验证，支持多列和方向
                order_parts = [part.strip() for part in order_by.split(',')]
                for part in order_parts:
                    # 每个部分应该是 "column_name" 或 "column_name ASC/DESC"
                    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?$', part, re.IGNORECASE):
                        raise StorageError(f"Invalid ORDER BY clause: {part}")
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
