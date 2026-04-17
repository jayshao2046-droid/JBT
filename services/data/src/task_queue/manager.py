"""任务队列管理器"""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional


class QueueManager:
    """任务队列管理器"""

    def __init__(self) -> None:
        self._queue: list[dict[str, Any]] = []
        self._completed: list[dict[str, Any]] = []
        self._max_completed = 100  # 最多保留100个已完成任务

    def add_task(
        self,
        task_type: str,
        params: dict[str, Any],
        priority: int = 0,
    ) -> str:
        """添加任务到队列

        Args:
            task_type: 任务类型 (collection/validation/optimization)
            params: 任务参数
            priority: 优先级 (数字越大优先级越高)

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "params": params,
            "priority": priority,
            "status": "pending",
            "created_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }

        self._queue.append(task)
        # 按优先级排序（优先级高的在前）
        self._queue.sort(key=lambda x: (-x["priority"], x["created_at"]))

        return task_id

    def get_queue(self, status: Optional[str] = None) -> list[dict[str, Any]]:
        """获取队列

        Args:
            status: 过滤状态 (pending/running/completed/failed)，None 表示所有

        Returns:
            任务列表
        """
        if status is None:
            return self._queue + self._completed

        if status in ("pending", "running"):
            return [t for t in self._queue if t["status"] == status]
        elif status in ("completed", "failed"):
            return [t for t in self._completed if t["status"] == status]
        else:
            return []

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            任务字典，如果不存在返回 None
        """
        for task in self._queue:
            if task["task_id"] == task_id:
                return task

        for task in self._completed:
            if task["task_id"] == task_id:
                return task

        return None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        for i, task in enumerate(self._queue):
            if task["task_id"] == task_id:
                if task["status"] == "pending":
                    task["status"] = "cancelled"
                    task["completed_at"] = time.time()
                    self._completed.append(task)
                    del self._queue[i]
                    self._cleanup_completed()
                    return True
                else:
                    # 正在运行的任务不能取消
                    return False

        return False

    def retry_task(self, task_id: str) -> bool:
        """重试任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功重试
        """
        for task in self._completed:
            if task["task_id"] == task_id:
                if task["status"] == "failed":
                    # 重新添加到队列
                    new_task = {
                        "task_id": str(uuid.uuid4()),
                        "task_type": task["task_type"],
                        "params": task["params"],
                        "priority": task["priority"],
                        "status": "pending",
                        "created_at": time.time(),
                        "started_at": None,
                        "completed_at": None,
                        "result": None,
                        "error": None,
                        "retry_of": task_id,
                    }
                    self._queue.append(new_task)
                    self._queue.sort(key=lambda x: (-x["priority"], x["created_at"]))
                    return True

        return False

    def update_priority(self, task_id: str, new_priority: int) -> bool:
        """调整任务优先级

        Args:
            task_id: 任务ID
            new_priority: 新优先级

        Returns:
            是否成功调整
        """
        for task in self._queue:
            if task["task_id"] == task_id:
                if task["status"] == "pending":
                    task["priority"] = new_priority
                    self._queue.sort(key=lambda x: (-x["priority"], x["created_at"]))
                    return True
                else:
                    return False

        return False

    def start_task(self, task_id: str) -> bool:
        """标记任务开始执行

        Args:
            task_id: 任务ID

        Returns:
            是否成功标记
        """
        for task in self._queue:
            if task["task_id"] == task_id:
                if task["status"] == "pending":
                    task["status"] = "running"
                    task["started_at"] = time.time()
                    return True

        return False

    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> bool:
        """标记任务完成

        Args:
            task_id: 任务ID
            success: 是否成功
            result: 任务结果
            error: 错误信息

        Returns:
            是否成功标记
        """
        for i, task in enumerate(self._queue):
            if task["task_id"] == task_id:
                task["status"] = "completed" if success else "failed"
                task["completed_at"] = time.time()
                task["result"] = result
                task["error"] = error

                # 移动到已完成列表
                self._completed.append(task)
                del self._queue[i]
                self._cleanup_completed()
                return True

        return False

    def get_statistics(self) -> dict[str, Any]:
        """获取队列统计信息

        Returns:
            统计信息字典
        """
        pending_count = sum(1 for t in self._queue if t["status"] == "pending")
        running_count = sum(1 for t in self._queue if t["status"] == "running")
        completed_count = sum(1 for t in self._completed if t["status"] == "completed")
        failed_count = sum(1 for t in self._completed if t["status"] == "failed")
        cancelled_count = sum(1 for t in self._completed if t["status"] == "cancelled")

        return {
            "total": len(self._queue) + len(self._completed),
            "pending": pending_count,
            "running": running_count,
            "completed": completed_count,
            "failed": failed_count,
            "cancelled": cancelled_count,
        }

    def _cleanup_completed(self) -> None:
        """清理已完成任务（保留最近的N个）"""
        if len(self._completed) > self._max_completed:
            # 按完成时间排序，保留最新的
            self._completed.sort(key=lambda x: x.get("completed_at", 0), reverse=True)
            self._completed = self._completed[:self._max_completed]
