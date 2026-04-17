"""队列管理器 - 管理研究报告的待读/处理/完成状态

职责：
1. 维护报告队列（pending/processing/completed）
2. 提供状态查询和更新接口
3. 支持并发安全的状态转换
4. 记录详细的状态变更日志

队列文件格式（JSONL）：
{
  "report_id": "RPT-20260417-14-futures",
  "file_path": "D:\\researcher_reports\\2026-04-17\\futures_14.json",
  "added_at": "2026-04-17T14:05:23",
  "status": "pending",
  "updated_at": "2026-04-17T14:05:23"
}
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class QueueManager:
    """报告队列管理器"""

    def __init__(self, queue_dir: str):
        """
        初始化队列管理器

        Args:
            queue_dir: 队列目录路径（如 D:\\researcher_reports\\.queue）
        """
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

        self.pending_file = self.queue_dir / "pending.jsonl"
        self.processing_file = self.queue_dir / "processing.jsonl"
        self.completed_file = self.queue_dir / "completed.jsonl"

        # 线程锁（保证并发安全）
        self._lock = Lock()

        # 确保文件存在
        for f in [self.pending_file, self.processing_file, self.completed_file]:
            f.touch(exist_ok=True)

        logger.info(f"队列管理器初始化: {self.queue_dir}")

    def add_to_queue(self, report_id: str, file_path: str, metadata: Optional[Dict] = None) -> bool:
        """
        添加报告到待读队列

        Args:
            report_id: 报告ID
            file_path: 报告文件路径
            metadata: 可选的元数据

        Returns:
            True 表示添加成功
        """
        with self._lock:
            try:
                # 检查是否已存在
                if self._exists_in_any_queue(report_id):
                    logger.warning(f"[QUEUE] 报告已存在于队列中: {report_id}")
                    return False

                # 创建队列记录
                record = {
                    "report_id": report_id,
                    "file_path": str(file_path),
                    "added_at": datetime.now().isoformat(),
                    "status": "pending",
                    "updated_at": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }

                # 追加到 pending 队列
                with open(self.pending_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                logger.info(f"[QUEUE] 添加到待读队列: {report_id} -> {file_path}")
                return True

            except Exception as e:
                logger.error(f"[QUEUE] 添加失败: {report_id}, {e}", exc_info=True)
                return False

    def mark_processing(self, report_id: str) -> bool:
        """
        标记报告为处理中

        Args:
            report_id: 报告ID

        Returns:
            True 表示标记成功
        """
        with self._lock:
            try:
                # 从 pending 移除
                record = self._remove_from_queue(self.pending_file, report_id)
                if not record:
                    logger.warning(f"[QUEUE] 报告不在待读队列中: {report_id}")
                    return False

                # 更新状态
                record["status"] = "processing"
                record["updated_at"] = datetime.now().isoformat()
                record["processing_started_at"] = datetime.now().isoformat()

                # 添加到 processing 队列
                with open(self.processing_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                logger.info(f"[QUEUE] 标记为处理中: {report_id}")
                return True

            except Exception as e:
                logger.error(f"[QUEUE] 标记处理中失败: {report_id}, {e}", exc_info=True)
                return False

    def mark_completed(self, report_id: str, result: Optional[Dict] = None) -> bool:
        """
        标记报告为已完成

        Args:
            report_id: 报告ID
            result: 可选的处理结果（如评分、耗时等）

        Returns:
            True 表示标记成功
        """
        with self._lock:
            try:
                # 从 processing 移除
                record = self._remove_from_queue(self.processing_file, report_id)
                if not record:
                    logger.warning(f"[QUEUE] 报告不在处理中队列: {report_id}")
                    return False

                # 更新状态
                record["status"] = "completed"
                record["updated_at"] = datetime.now().isoformat()
                record["completed_at"] = datetime.now().isoformat()
                if result:
                    record["result"] = result

                # 添加到 completed 队列
                with open(self.completed_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                logger.info(f"[QUEUE] 标记为已完成: {report_id}")
                return True

            except Exception as e:
                logger.error(f"[QUEUE] 标记完成失败: {report_id}, {e}", exc_info=True)
                return False

    def get_pending(self, limit: int = 100) -> List[Dict]:
        """
        获取待读队列

        Args:
            limit: 最大返回数量

        Returns:
            待读报告列表
        """
        with self._lock:
            try:
                records = []
                with open(self.pending_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
                            if len(records) >= limit:
                                break
                return records

            except Exception as e:
                logger.error(f"[QUEUE] 读取待读队列失败: {e}", exc_info=True)
                return []

    def get_processing(self) -> List[Dict]:
        """获取处理中队列"""
        with self._lock:
            try:
                records = []
                with open(self.processing_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
                return records

            except Exception as e:
                logger.error(f"[QUEUE] 读取处理中队列失败: {e}", exc_info=True)
                return []

    def get_status(self, report_id: str) -> Optional[str]:
        """
        查询报告状态

        Args:
            report_id: 报告ID

        Returns:
            状态字符串（pending/processing/completed）或 None
        """
        with self._lock:
            for queue_file, status in [
                (self.pending_file, "pending"),
                (self.processing_file, "processing"),
                (self.completed_file, "completed")
            ]:
                if self._exists_in_queue(queue_file, report_id):
                    return status
            return None

    def cleanup_old_completed(self, days: int = 7) -> int:
        """
        清理旧的已完成记录

        Args:
            days: 保留天数

        Returns:
            清理的记录数
        """
        with self._lock:
            try:
                from datetime import timedelta
                cutoff = datetime.now() - timedelta(days=days)

                records = []
                removed_count = 0

                with open(self.completed_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            completed_at = datetime.fromisoformat(record.get("completed_at", ""))
                            if completed_at > cutoff:
                                records.append(record)
                            else:
                                removed_count += 1

                # 重写文件
                with open(self.completed_file, "w", encoding="utf-8") as f:
                    for record in records:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")

                logger.info(f"[QUEUE] 清理旧记录: 移除 {removed_count} 条，保留 {len(records)} 条")
                return removed_count

            except Exception as e:
                logger.error(f"[QUEUE] 清理失败: {e}", exc_info=True)
                return 0

    def _exists_in_any_queue(self, report_id: str) -> bool:
        """检查报告是否存在于任意队列"""
        for queue_file in [self.pending_file, self.processing_file, self.completed_file]:
            if self._exists_in_queue(queue_file, report_id):
                return True
        return False

    def _exists_in_queue(self, queue_file: Path, report_id: str) -> bool:
        """检查报告是否存在于指定队列"""
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record.get("report_id") == report_id:
                            return True
            return False
        except Exception:
            return False

    def _remove_from_queue(self, queue_file: Path, report_id: str) -> Optional[Dict]:
        """从队列中移除记录并返回"""
        try:
            records = []
            removed_record = None

            with open(queue_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record.get("report_id") == report_id:
                            removed_record = record
                        else:
                            records.append(record)

            # 重写文件
            with open(queue_file, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

            return removed_record

        except Exception as e:
            logger.error(f"[QUEUE] 移除记录失败: {report_id}, {e}", exc_info=True)
            return None
