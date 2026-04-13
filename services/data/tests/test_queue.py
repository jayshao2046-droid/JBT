"""任务队列管理器测试"""
from __future__ import annotations

import pytest

from src.queue.manager import QueueManager


def test_add_task():
    manager = QueueManager()
    task_id = manager.add_task("collection", {"source": "test"}, priority=1)
    assert task_id is not None
    task = manager.get_task(task_id)
    assert task is not None
    assert task["status"] == "pending"


def test_get_queue():
    manager = QueueManager()
    manager.add_task("collection", {"source": "test1"})
    manager.add_task("collection", {"source": "test2"})
    queue = manager.get_queue("pending")
    assert len(queue) == 2


def test_cancel_task():
    manager = QueueManager()
    task_id = manager.add_task("collection", {"source": "test"})
    success = manager.cancel_task(task_id)
    assert success is True
    task = manager.get_task(task_id)
    assert task["status"] == "cancelled"


def test_retry_task():
    manager = QueueManager()
    task_id = manager.add_task("collection", {"source": "test"})
    manager.complete_task(task_id, success=False, error="test error")
    success = manager.retry_task(task_id)
    assert success is True


def test_update_priority():
    manager = QueueManager()
    task_id = manager.add_task("collection", {"source": "test"}, priority=1)
    success = manager.update_priority(task_id, 5)
    assert success is True
    task = manager.get_task(task_id)
    assert task["priority"] == 5


def test_start_task():
    manager = QueueManager()
    task_id = manager.add_task("collection", {"source": "test"})
    success = manager.start_task(task_id)
    assert success is True
    task = manager.get_task(task_id)
    assert task["status"] == "running"


def test_complete_task():
    manager = QueueManager()
    task_id = manager.add_task("collection", {"source": "test"})
    manager.start_task(task_id)
    success = manager.complete_task(task_id, success=True, result={"count": 100})
    assert success is True
    task = manager.get_task(task_id)
    assert task["status"] == "completed"


def test_get_statistics():
    manager = QueueManager()
    manager.add_task("collection", {"source": "test1"})
    manager.add_task("collection", {"source": "test2"})
    stats = manager.get_statistics()
    assert stats["total"] == 2
    assert stats["pending"] == 2
