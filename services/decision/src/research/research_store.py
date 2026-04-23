"""研报评级结果存储 — 供策略引擎和门控主动查询最新宏观判断

评级结果按 report_type 索引，保留最近 N 条历史。
支持内存缓存 + JSON 持久化双层。
"""
from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_MAX_HISTORY = 50  # 每类报告最多保留最近 50 条


class ResearchStore:
    """研报评级结果存储（进程内单例）"""

    _instance: Optional["ResearchStore"] = None
    _lock = threading.Lock()

    def __new__(cls, persist_dir: str = "runtime/research_store"):
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._persist_dir = Path(persist_dir)
                inst._persist_dir.mkdir(parents=True, exist_ok=True)
                inst._cache: dict[str, list[dict[str, Any]]] = defaultdict(list)
                inst._load_from_disk()
                cls._instance = inst
            return cls._instance

    def _load_from_disk(self) -> None:
        """启动时从磁盘加载历史评级"""
        for fp in self._persist_dir.glob("*.json"):
            report_type = fp.stem
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    records = json.load(f)
                self._cache[report_type] = records[-_MAX_HISTORY:]
                logger.info("ResearchStore: 加载 %s %d 条", report_type, len(self._cache[report_type]))
            except Exception as e:
                logger.warning("ResearchStore: 加载 %s 失败: %s", report_type, e)

    def _persist(self, report_type: str) -> None:
        """单类型落盘"""
        fp = self._persist_dir / f"{report_type}.json"
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(self._cache[report_type], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("ResearchStore: 持久化 %s 失败: %s", report_type, e)

    def save(self, report_type: str, record: dict[str, Any]) -> None:
        """保存一条评级结果"""
        record.setdefault("stored_at", datetime.now().isoformat())
        self._cache[report_type].append(record)

        # 保留最近 N 条
        if len(self._cache[report_type]) > _MAX_HISTORY:
            self._cache[report_type] = self._cache[report_type][-_MAX_HISTORY:]

        # 时间维度清理：保留最近 N 天（默认 7 天）
        max_age_days = int(os.getenv("RESEARCH_STORE_MAX_AGE_DAYS", "7"))
        cutoff = datetime.now() - timedelta(days=max_age_days)
        self._cache[report_type] = [
            r for r in self._cache[report_type]
            if datetime.fromisoformat(r.get("stored_at", "1970-01-01")) > cutoff
        ]

        self._persist(report_type)
        logger.info("ResearchStore: 保存 %s (score=%.1f)", report_type, record.get("score", 0))

    def get_latest(self, report_type: str) -> Optional[dict[str, Any]]:
        """获取某类型最新一条评级"""
        records = self._cache.get(report_type, [])
        return records[-1] if records else None

    def get_history(self, report_type: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取某类型最近 N 条评级"""
        records = self._cache.get(report_type, [])
        return records[-limit:]

    def get_all_latest(self) -> dict[str, Optional[dict[str, Any]]]:
        """获取所有类型的最新评级"""
        return {rt: (records[-1] if records else None) for rt, records in self._cache.items()}

    def get_macro_summary(self) -> dict[str, Any]:
        """获取最新宏观分析摘要（供策略引擎和门控使用）"""
        macro = self.get_latest("macro")
        if not macro:
            return {"available": False}

        return {
            "available": True,
            "score": macro.get("score", 0),
            "macro_trend": macro.get("macro_trend", "unknown"),
            "risk_level": macro.get("risk_level", "unknown"),
            "key_drivers": macro.get("key_drivers", []),
            "recommended_sectors": macro.get("recommended_sectors", []),
            "confidence": macro.get("confidence", "low"),
            "stored_at": macro.get("stored_at"),
        }
