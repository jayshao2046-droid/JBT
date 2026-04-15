from __future__ import annotations

import copy
import json
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

from ..core.settings import get_settings

StateBucket = Literal[
    "strategies",
    "approvals",
    "backtest_certs",
    "research_snapshots",
]

_STATE_BUCKETS: tuple[StateBucket, ...] = (
    "strategies",
    "approvals",
    "backtest_certs",
    "research_snapshots",
)


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "strategies": {},
        "approvals": {},
        "backtest_certs": {},
        "research_snapshots": {},
    }


def _merge_state(raw: Optional[dict[str, Any]]) -> dict[str, Any]:
    state = _default_state()
    if not isinstance(raw, dict):
        return state

    state["version"] = raw.get("version", state["version"])
    for bucket in _STATE_BUCKETS:
        bucket_data = raw.get(bucket, {})
        if isinstance(bucket_data, dict):
            state[bucket] = bucket_data
    return state


class MemoryStateStore:
    def __init__(self, initial_state: Optional[dict[str, Any]] = None) -> None:
        self._lock = threading.RLock()
        self._state = copy.deepcopy(_merge_state(initial_state))

    def read_state(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    def list_records(self, bucket: StateBucket) -> list[dict[str, Any]]:
        state = self.read_state()
        return [copy.deepcopy(record) for record in state[bucket].values()]

    def get_record(self, bucket: StateBucket, record_id: str) -> Optional[dict[str, Any]]:
        state = self.read_state()
        record = state[bucket].get(record_id)
        return copy.deepcopy(record) if record is not None else None

    def upsert_record(self, bucket: StateBucket, record_id: str, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._state[bucket][record_id] = copy.deepcopy(record)
            return copy.deepcopy(self._state[bucket][record_id])

    def delete_record(self, bucket: StateBucket, record_id: str) -> bool:
        with self._lock:
            existed = record_id in self._state[bucket]
            if existed:
                del self._state[bucket][record_id]
            return existed


class FileStateStore:
    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)
        self._lock_path = self._file_path.with_suffix(f"{self._file_path.suffix}.lock")
        self._lock = threading.RLock()

    @property
    def file_path(self) -> Path:
        return self._file_path

    def read_state(self) -> dict[str, Any]:
        with self._locked_io():
            return self._read_state_unlocked()

    def list_records(self, bucket: StateBucket) -> list[dict[str, Any]]:
        state = self.read_state()
        return [copy.deepcopy(record) for record in state[bucket].values()]

    def get_record(self, bucket: StateBucket, record_id: str) -> Optional[dict[str, Any]]:
        state = self.read_state()
        record = state[bucket].get(record_id)
        return copy.deepcopy(record) if record is not None else None

    def upsert_record(self, bucket: StateBucket, record_id: str, record: dict[str, Any]) -> dict[str, Any]:
        with self._locked_io():
            state = self._read_state_unlocked()
            state[bucket][record_id] = copy.deepcopy(record)
            self._write_state_unlocked(state)
            return copy.deepcopy(state[bucket][record_id])

    def delete_record(self, bucket: StateBucket, record_id: str) -> bool:
        with self._locked_io():
            state = self._read_state_unlocked()
            existed = state[bucket].pop(record_id, None) is not None
            if existed:
                self._write_state_unlocked(state)
            return existed

    @contextmanager
    def _locked_io(self):
        with self._lock:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            if fcntl is None:
                yield
                return

            with self._lock_path.open("a+", encoding="utf-8") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read_state_unlocked(self) -> dict[str, Any]:
        if not self._file_path.exists():
            state = _default_state()
            self._write_state_unlocked(state)
            return state

        try:
            raw = json.loads(self._file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"State store file is not valid JSON: {self._file_path}") from exc

        return _merge_state(raw)

    def _write_state_unlocked(self, state: dict[str, Any]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._file_path.with_suffix(f"{self._file_path.suffix}.tmp")
        tmp_path.write_text(
            json.dumps(state, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        # 安全修复：P1-3 - 设置严格文件权限（仅所有者可读写）
        tmp_path.chmod(0o600)
        tmp_path.replace(self._file_path)
        self._file_path.chmod(0o600)


_state_store: Optional[FileStateStore] = None
_state_store_path: Optional[Path] = None


def get_state_store() -> FileStateStore:
    global _state_store, _state_store_path

    file_path = get_settings().resolved_decision_state_file
    if _state_store is None or _state_store_path != file_path:
        _state_store = FileStateStore(file_path)
        _state_store_path = file_path
    return _state_store