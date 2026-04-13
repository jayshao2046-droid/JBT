"""
决策任务队列管理模块
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)


class QueueManager:
    """任务队列管理器"""

    def __init__(self):
        self._queue: List[Dict] = []

    def add_task(
        self,
        strategy_id: str,
        params: Dict,
        priority: int = 5,
        task_id: Optional[str] = None,
    ) -> str:
        """添加任务到队列"""
        if task_id is None:
            task_id = str(uuid.uuid4())

        task = {
            "task_id": task_id,
            "strategy_id": strategy_id,
            "params": params,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }

        self._queue.append(task)
        self._sort_queue()

        logger.info(f"Task {task_id} added to queue")
        return task_id

    def get_queue(self, status: Optional[str] = None) -> List[Dict]:
        """获取队列"""
        if status:
            return [t for t in self._queue if t["status"] == status]
        return self._queue.copy()

    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务"""
        for task in self._queue:
            if task["task_id"] == task_id:
                return task
        return None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.get_task(task_id)
        if not task:
            return False

        if task["status"] in ["completed", "failed", "cancelled"]:
            logger.warning(f"Cannot cancel task {task_id} with status {task['status']}")
            return False

        task["status"] = "cancelled"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Task {task_id} cancelled")
        return True

    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task = self.get_task(task_id)
        if not task:
            return False

        if task["status"] not in ["failed", "cancelled"]:
            logger.warning(f"Cannot retry task {task_id} with status {task['status']}")
            return False

        task["status"] = "pending"
        task["started_at"] = None
        task["completed_at"] = None
        task["error"] = None
        self._sort_queue()

        logger.info(f"Task {task_id} retried")
        return True

    def update_priority(self, task_id: str, priority: int) -> bool:
        """更新任务优先级"""
        task = self.get_task(task_id)
        if not task:
            return False

        if task["status"] != "pending":
            logger.warning(f"Cannot update priority for task {task_id} with status {task['status']}")
            return False

        task["priority"] = priority
        self._sort_queue()

        logger.info(f"Task {task_id} priority updated to {priority}")
        return True

    def start_task(self, task_id: str) -> bool:
        """标记任务开始"""
        task = self.get_task(task_id)
        if not task:
            return False

        task["status"] = "running"
        task["started_at"] = datetime.now(timezone.utc).isoformat()
        return True

    def complete_task(self, task_id: str, result: Dict) -> bool:
        """标记任务完成"""
        task = self.get_task(task_id)
        if not task:
            return False

        task["status"] = "completed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["result"] = result
        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        task = self.get_task(task_id)
        if not task:
            return False

        task["status"] = "failed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["error"] = error
        return True

    def _sort_queue(self) -> None:
        """按优先级排序队列（优先级高的在前）"""
        self._queue.sort(key=lambda t: (-t["priority"], t["created_at"]))

    def clear_completed(self) -> int:
        """清除已完成的任务"""
        before = len(self._queue)
        self._queue = [t for t in self._queue if t["status"] not in ["completed", "cancelled"]]
        after = len(self._queue)
        return before - after


# 全局队列管理器实例
_manager = QueueManager()


def get_queue_manager() -> QueueManager:
    """获取全局队列管理器"""
    return _manager
