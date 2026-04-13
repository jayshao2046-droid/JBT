"""采集进度追踪器"""
from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Optional


class ProgressTracker:
    """采集进度追踪器"""

    def __init__(self) -> None:
        self._progress_store: dict[str, dict[str, Any]] = {}

    def start_collection(self, collection_id: str, total_items: int) -> None:
        """开始采集任务

        Args:
            collection_id: 采集任务 ID
            total_items: 总项目数
        """
        self._progress_store[collection_id] = {
            "collection_id": collection_id,
            "total_items": total_items,
            "completed_items": 0,
            "current_stage": "初始化",
            "progress_percent": 0.0,
            "start_time": time.time(),
            "estimated_completion": None,
            "status": "running",
        }

    def update_progress(
        self,
        collection_id: str,
        completed_items: int,
        current_stage: str,
    ) -> None:
        """更新采集进度

        Args:
            collection_id: 采集任务 ID
            completed_items: 已完成项目数
            current_stage: 当前阶段
        """
        if collection_id not in self._progress_store:
            return

        progress = self._progress_store[collection_id]
        progress["completed_items"] = completed_items
        progress["current_stage"] = current_stage

        total = progress["total_items"]
        if total > 0:
            progress["progress_percent"] = round((completed_items / total) * 100, 2)

        # 估算完成时间
        elapsed = time.time() - progress["start_time"]
        if completed_items > 0 and completed_items < total:
            avg_time_per_item = elapsed / completed_items
            remaining_items = total - completed_items
            estimated_seconds = remaining_items * avg_time_per_item
            progress["estimated_completion"] = time.time() + estimated_seconds

    def complete_collection(self, collection_id: str, success: bool = True) -> None:
        """完成采集任务

        Args:
            collection_id: 采集任务 ID
            success: 是否成功
        """
        if collection_id not in self._progress_store:
            return

        progress = self._progress_store[collection_id]
        progress["status"] = "completed" if success else "failed"
        progress["progress_percent"] = 100.0 if success else progress["progress_percent"]
        progress["estimated_completion"] = None

    def get_progress(self, collection_id: str) -> Optional[dict[str, Any]]:
        """获取采集进度

        Args:
            collection_id: 采集任务 ID

        Returns:
            进度信息字典，如果不存在返回 None
        """
        return self._progress_store.get(collection_id)

    async def stream_progress(
        self,
        collection_id: str,
        interval: float = 1.0,
    ) -> AsyncIterator[dict[str, Any]]:
        """流式推送采集进度（SSE）

        Args:
            collection_id: 采集任务 ID
            interval: 推送间隔（秒）

        Yields:
            进度信息字典
        """
        while True:
            progress = self.get_progress(collection_id)
            if progress is None:
                # 任务不存在，返回错误
                yield {
                    "error": "collection_not_found",
                    "message": f"采集任务 {collection_id} 不存在",
                }
                break

            yield progress

            # 如果任务已完成，停止推送
            if progress["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(interval)

    def cleanup_old_progress(self, max_age_seconds: float = 3600) -> int:
        """清理旧的进度记录

        Args:
            max_age_seconds: 最大保留时间（秒）

        Returns:
            清理的记录数
        """
        now = time.time()
        to_remove = []

        for collection_id, progress in self._progress_store.items():
            if progress["status"] in ("completed", "failed"):
                age = now - progress["start_time"]
                if age > max_age_seconds:
                    to_remove.append(collection_id)

        for collection_id in to_remove:
            del self._progress_store[collection_id]

        return len(to_remove)
