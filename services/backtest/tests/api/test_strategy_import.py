"""Tests for strategy import queue (TASK-0052 CG1)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Use repo-root-based full package paths (matches existing test pattern).
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.strategy_queue import StrategyQueue  # noqa: E402


# ── Unit tests for StrategyQueue ──────────────────────────────────────

class TestStrategyQueueUnit:
    def _make_queue(self) -> StrategyQueue:
        return StrategyQueue()

    # 1. 成功入队
    def test_enqueue_success(self):
        q = self._make_queue()
        qid = q.enqueue("strat_001", "content_a")
        assert isinstance(qid, str) and len(qid) == 16
        item = q.get_item(qid)
        assert item is not None
        assert item.strategy_id == "strat_001"
        assert item.status == "queued"

    # 2. 优先级排序
    def test_priority_ordering(self):
        q = self._make_queue()
        id_low = q.enqueue("low", "c", priority=0)
        id_high = q.enqueue("high", "c", priority=10)
        first = q.dequeue()
        assert first is not None
        assert first.queue_id == id_high

    # 3. 队列满拒绝 (429 场景)
    def test_queue_full_overflow(self):
        q = self._make_queue()
        q.MAX_SIZE = 3
        for i in range(3):
            q.enqueue(f"s{i}", "c")
        with pytest.raises(OverflowError):
            q.enqueue("overflow", "c")

    # 4. 缺失 strategy_id
    def test_invalid_strategy_id(self):
        q = self._make_queue()
        with pytest.raises(ValueError):
            q.enqueue("", "content")

    # 5. 缺失 strategy_content
    def test_empty_strategy_content(self):
        q = self._make_queue()
        with pytest.raises(ValueError):
            q.enqueue("valid_id", "")

    # 6. 清空队列
    def test_clear_queue(self):
        q = self._make_queue()
        for i in range(5):
            q.enqueue(f"s{i}", "c")
        cleared = q.clear_queue()
        assert cleared == 5
        assert q.size() == 0

    # 7. 状态过滤
    def test_get_all_items_with_filter(self):
        q = self._make_queue()
        q.enqueue("a", "c")
        q.enqueue("b", "c")
        q.dequeue()  # moves one to running
        assert len(q.get_all_items(status_filter="running")) == 1
        assert len(q.get_all_items(status_filter="queued")) == 1

    # 8. update_status 不存在 → KeyError
    def test_update_status_missing(self):
        q = self._make_queue()
        with pytest.raises(KeyError):
            q.update_status("nonexistent", "failed")


# ── Integration tests via FastAPI TestClient ──────────────────────────

from fastapi.testclient import TestClient  # noqa: E402

from services.backtest.src.api.app import create_app  # noqa: E402
from services.backtest.src.api.routes import queue as _queue_mod  # noqa: E402

_sq = _queue_mod.get_queue()


@pytest.fixture(autouse=True)
def _reset_queue():
    """Clear the module-level queue singleton before each test."""
    _sq._queue.clear()
    _sq._items.clear()
    yield


class TestQueueAPI:
    client = TestClient(create_app())

    # 9. POST enqueue → 201
    def test_enqueue_api(self):
        resp = self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "test_strat", "strategy_content": "yaml_here"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["strategy_id"] == "test_strat"
        assert data["status"] == "queued"

    # 10. GET status → 200
    def test_status_api(self):
        self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "s1", "strategy_content": "c"},
        )
        resp = self.client.get("/api/v1/strategy-queue/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 1
        assert data["queued_count"] == 1

    # 11. DELETE clear → 200
    def test_clear_api(self):
        for i in range(3):
            self.client.post(
                "/api/v1/strategy-queue/enqueue",
                json={"strategy_id": f"s{i}", "strategy_content": "c"},
            )
        resp = self.client.delete("/api/v1/strategy-queue/clear")
        assert resp.status_code == 200
        assert resp.json()["cleared_count"] == 3

    # 12. 缺失字段 → 422
    def test_missing_fields_422(self):
        resp = self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "x"},
        )
        assert resp.status_code == 422

    # 13. 非法 strategy_id → 422
    def test_invalid_id_422(self):
        resp = self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "bad id!@#", "strategy_content": "c"},
        )
        assert resp.status_code == 422

    # 14. 队列满 → 429
    def test_queue_full_429(self):
        _sq.MAX_SIZE = 2
        for i in range(2):
            self.client.post(
                "/api/v1/strategy-queue/enqueue",
                json={"strategy_id": f"s{i}", "strategy_content": "c"},
            )
        resp = self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "overflow", "strategy_content": "c"},
        )
        assert resp.status_code == 429
        _sq.MAX_SIZE = 100  # restore

    # 15. 状态过滤查询
    def test_status_filter(self):
        self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "a", "strategy_content": "c"},
        )
        resp = self.client.get("/api/v1/strategy-queue/status?status=running")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    # 16. 优先级通过 API 入队后排序正确
    def test_priority_via_api(self):
        self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "low", "strategy_content": "c", "priority": 0},
        )
        self.client.post(
            "/api/v1/strategy-queue/enqueue",
            json={"strategy_id": "high", "strategy_content": "c", "priority": 5},
        )
        resp = self.client.get("/api/v1/strategy-queue/status?status=queued")
        items = resp.json()["items"]
        # Sort by priority descending to verify high-priority item exists
        by_priority = sorted(items, key=lambda x: x["priority"], reverse=True)
        assert by_priority[0]["strategy_id"] == "high"
        assert by_priority[1]["strategy_id"] == "low"
