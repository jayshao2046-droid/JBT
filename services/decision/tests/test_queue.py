"""
队列管理器单元测试
"""
import pytest
from src.task_queue.manager import QueueManager


class TestQueueManager:
    """队列管理器测试"""

    def test_add_task(self):
        manager = QueueManager()
        task_id = manager.add_task("strategy_001", {"param1": 100}, priority=5)
        assert task_id is not None
        assert len(manager.get_queue()) == 1

    def test_get_task(self):
        manager = QueueManager()
        task_id = manager.add_task("strategy_001", {"param1": 100})
        task = manager.get_task(task_id)
        assert task is not None
        assert task["strategy_id"] == "strategy_001"

    def test_cancel_task(self):
        manager = QueueManager()
        task_id = manager.add_task("strategy_001", {"param1": 100})
        result = manager.cancel_task(task_id)
        assert result is True
        task = manager.get_task(task_id)
        assert task["status"] == "cancelled"

    def test_retry_task(self):
        manager = QueueManager()
        task_id = manager.add_task("strategy_001", {"param1": 100})
        manager.fail_task(task_id, "Test error")
        result = manager.retry_task(task_id)
        assert result is True
        task = manager.get_task(task_id)
        assert task["status"] == "pending"

    def test_update_priority(self):
        manager = QueueManager()
        task_id = manager.add_task("strategy_001", {"param1": 100}, priority=5)
        result = manager.update_priority(task_id, 10)
        assert result is True
        task = manager.get_task(task_id)
        assert task["priority"] == 10

    def test_queue_sorting(self):
        manager = QueueManager()
        task1 = manager.add_task("strategy_001", {}, priority=3)
        task2 = manager.add_task("strategy_002", {}, priority=7)
        task3 = manager.add_task("strategy_003", {}, priority=5)

        queue = manager.get_queue()
        assert queue[0]["task_id"] == task2  # 最高优先级
        assert queue[1]["task_id"] == task3
        assert queue[2]["task_id"] == task1

    def test_clear_completed(self):
        manager = QueueManager()
        task1 = manager.add_task("strategy_001", {})
        task2 = manager.add_task("strategy_002", {})
        manager.complete_task(task1, {"result": "success"})
        manager.cancel_task(task2)

        cleared = manager.clear_completed()
        assert cleared == 2
        assert len(manager.get_queue()) == 0
