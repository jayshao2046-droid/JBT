"""
决策进度追踪模块
"""
from typing import Dict, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """决策进度追踪器"""

    def __init__(self):
        self._progress: Dict[str, Dict] = {}

    def start(self, decision_id: str, total_steps: int = 5) -> None:
        """开始追踪决策进度"""
        self._progress[decision_id] = {
            "decision_id": decision_id,
            "total_steps": total_steps,
            "current_step": 0,
            "current_stage": "初始化",
            "progress_percent": 0.0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "estimated_completion": None,
            "status": "running",
        }

    def update(
        self, decision_id: str, current_step: int, stage: str, estimated_seconds: Optional[int] = None
    ) -> None:
        """更新决策进度"""
        if decision_id not in self._progress:
            logger.warning(f"决策 {decision_id} 未初始化")
            return

        progress = self._progress[decision_id]
        progress["current_step"] = current_step
        progress["current_stage"] = stage
        progress["progress_percent"] = round((current_step / progress["total_steps"]) * 100, 2)

        if estimated_seconds:
            from datetime import timedelta

            now = datetime.now(timezone.utc)
            estimated_completion = now + timedelta(seconds=estimated_seconds)
            progress["estimated_completion"] = estimated_completion.isoformat()

    def complete(self, decision_id: str) -> None:
        """标记决策完成"""
        if decision_id not in self._progress:
            return

        progress = self._progress[decision_id]
        progress["current_step"] = progress["total_steps"]
        progress["current_stage"] = "完成"
        progress["progress_percent"] = 100.0
        progress["status"] = "completed"
        progress["completed_at"] = datetime.now(timezone.utc).isoformat()

    def fail(self, decision_id: str, error: str) -> None:
        """标记决策失败"""
        if decision_id not in self._progress:
            return

        progress = self._progress[decision_id]
        progress["status"] = "failed"
        progress["error"] = error
        progress["failed_at"] = datetime.now(timezone.utc).isoformat()

    def get(self, decision_id: str) -> Optional[Dict]:
        """获取决策进度"""
        return self._progress.get(decision_id)

    def remove(self, decision_id: str) -> None:
        """移除决策进度记录"""
        if decision_id in self._progress:
            del self._progress[decision_id]


# 全局进度追踪器实例
_tracker = ProgressTracker()


def get_tracker() -> ProgressTracker:
    """获取全局进度追踪器"""
    return _tracker
