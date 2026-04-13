"""
回测任务队列管理器
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BacktestTask:
    """回测任务"""
    task_id: str
    strategy_id: str
    config: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0  # 优先级，数字越大优先级越高
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 - 1.0


class QueueManager:
    """回测任务队列管理器"""

    def __init__(self, max_concurrent: int = 3):
        """
        初始化队列管理器

        Args:
            max_concurrent: 最大并发任务数
        """
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, BacktestTask] = {}
        self.pending_queue: List[str] = []  # 待执行任务ID列表
        self.running_tasks: Dict[str, asyncio.Task] = {}  # 正在运行的任务
        self._lock = asyncio.Lock()

    async def submit_task(
        self,
        strategy_id: str,
        config: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """
        提交回测任务

        Args:
            strategy_id: 策略ID
            config: 回测配置
            priority: 优先级

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        task = BacktestTask(
            task_id=task_id,
            strategy_id=strategy_id,
            config=config,
            priority=priority
        )

        async with self._lock:
            self.tasks[task_id] = task
            # 按优先级插入队列
            self._insert_by_priority(task_id)

        # 尝试启动任务
        await self._try_start_next()

        return task_id

    def _insert_by_priority(self, task_id: str):
        """按优先级插入任务到队列"""
        task = self.tasks[task_id]
        inserted = False

        for i, tid in enumerate(self.pending_queue):
            if self.tasks[tid].priority < task.priority:
                self.pending_queue.insert(i, task_id)
                inserted = True
                break

        if not inserted:
            self.pending_queue.append(task_id)

    async def _try_start_next(self):
        """尝试启动下一个任务"""
        async with self._lock:
            # 检查是否可以启动新任务
            if len(self.running_tasks) >= self.max_concurrent:
                return

            if not self.pending_queue:
                return

            # 获取下一个任务
            task_id = self.pending_queue.pop(0)
            task = self.tasks[task_id]

            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            # 启动任务
            asyncio_task = asyncio.create_task(self._run_task(task_id))
            self.running_tasks[task_id] = asyncio_task

    async def _run_task(self, task_id: str):
        """运行回测任务"""
        task = self.tasks[task_id]

        try:
            # 这里应该调用实际的回测引擎
            # 为了演示，我们模拟一个回测过程
            for i in range(10):
                await asyncio.sleep(0.5)
                task.progress = (i + 1) / 10

            # 模拟结果
            task.result = {
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.08
            }
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()

        finally:
            # 清理运行中的任务
            async with self._lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

            # 尝试启动下一个任务
            await self._try_start_next()

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        async with self._lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]

            # 如果任务在队列中，直接移除
            if task.status == TaskStatus.PENDING:
                if task_id in self.pending_queue:
                    self.pending_queue.remove(task_id)
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                return True

            # 如果任务正在运行，取消异步任务
            if task.status == TaskStatus.RUNNING and task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                return True

            return False

    def get_task(self, task_id: str) -> Optional[BacktestTask]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[BacktestTask]:
        """
        列出任务

        Args:
            status: 过滤状态
            limit: 最大返回数量

        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "total_tasks": len(self.tasks),
            "pending": len(self.pending_queue),
            "running": len(self.running_tasks),
            "completed": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]),
            "max_concurrent": self.max_concurrent
        }

    async def clear_completed(self, older_than_hours: int = 24):
        """
        清理已完成的任务

        Args:
            older_than_hours: 清理多少小时前的任务
        """
        async with self._lock:
            now = datetime.now()
            to_remove = []

            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task.completed_at:
                        hours_ago = (now - task.completed_at).total_seconds() / 3600
                        if hours_ago > older_than_hours:
                            to_remove.append(task_id)

            for task_id in to_remove:
                del self.tasks[task_id]


# 全局队列管理器实例
_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> QueueManager:
    """获取全局队列管理器实例"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager(max_concurrent=3)
    return _queue_manager
