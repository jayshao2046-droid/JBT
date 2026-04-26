"""Strategy import queue – in-memory, thread-safe, priority-ordered."""

from __future__ import annotations

import re
import threading
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class QueueItem:
    queue_id: str
    strategy_id: str
    strategy_content: str
    status: str  # queued / running / completed / failed
    priority: int = 0
    callback_url: Optional[str] = None
    queued_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[dict] = field(default=None)

    def to_dict(self) -> dict:
        return asdict(self)


_STRATEGY_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,128}$")


class StrategyQueue:
    MAX_SIZE: int = 100

    def __init__(self) -> None:
        self._queue: deque[str] = deque()
        self._items: dict[str, QueueItem] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def enqueue(
        self,
        strategy_id: str,
        strategy_content: str,
        priority: int = 0,
        callback_url: Optional[str] = None,
    ) -> str:
        if not strategy_id or not _STRATEGY_ID_RE.match(strategy_id):
            raise ValueError(f"Invalid strategy_id: {strategy_id!r}")
        if not strategy_content:
            raise ValueError("strategy_content must not be empty")

        with self._lock:
            if len(self._queue) >= self.MAX_SIZE:
                raise OverflowError("Queue is full")

            queue_id = uuid.uuid4().hex[:16]
            item = QueueItem(
                queue_id=queue_id,
                strategy_id=strategy_id,
                strategy_content=strategy_content,
                status="queued",
                priority=priority,
                callback_url=callback_url,
                queued_at=datetime.now(timezone.utc).isoformat(),
            )
            self._items[queue_id] = item

            # Insert by priority (higher first).
            inserted = False
            for idx, existing_id in enumerate(self._queue):
                existing = self._items[existing_id]
                if priority > existing.priority:
                    self._queue.insert(idx, queue_id)
                    inserted = True
                    break
            if not inserted:
                self._queue.append(queue_id)

            return queue_id

    # ------------------------------------------------------------------
    def dequeue(self) -> Optional[QueueItem]:
        with self._lock:
            while self._queue:
                qid = self._queue.popleft()
                item = self._items.get(qid)
                if item and item.status == "queued":
                    item.status = "running"
                    item.started_at = datetime.now(timezone.utc).isoformat()
                    return item
            return None

    # ------------------------------------------------------------------
    def get_item(self, queue_id: str) -> Optional[QueueItem]:
        with self._lock:
            return self._items.get(queue_id)

    # ------------------------------------------------------------------
    def update_status(
        self,
        queue_id: str,
        status: str,
        result: Optional[dict] = None,
    ) -> None:
        with self._lock:
            item = self._items.get(queue_id)
            if item is None:
                raise KeyError(f"queue_id not found: {queue_id}")
            item.status = status
            if result is not None:
                item.result = result
            if status in ("completed", "failed"):
                item.completed_at = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    def get_all_items(self, status_filter: Optional[str] = None) -> list[QueueItem]:
        with self._lock:
            items = list(self._items.values())
        if status_filter:
            items = [i for i in items if i.status == status_filter]
        return items

    # ------------------------------------------------------------------
    def clear_queue(self) -> int:
        with self._lock:
            count = len(self._queue)
            # Only remove queued items; keep running/completed/failed for audit.
            removed_ids = [
                qid
                for qid in self._queue
                if self._items.get(qid) and self._items[qid].status == "queued"
            ]
            for qid in removed_ids:
                del self._items[qid]
            self._queue.clear()
            return count

    # ------------------------------------------------------------------
    def size(self) -> int:
        with self._lock:
            return len(self._queue)
