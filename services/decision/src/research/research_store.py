"""研报评级结果存储 — 供策略引擎和门控主动查询 researcher 事实库存证。

存储层同时保留两类视图：
1. 按 report_type 读取的原有评分结果视图
2. 按三类 researcher 事实分组读取的稳定库存证视图
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

_REPORT_TYPE_ALIASES = {
    "futures_report": "futures",
    "stocks_report": "stocks",
    "news_report": "news",
    "macro_report": "macro",
    "rss_report": "rss",
    "sentiment_report": "sentiment",
}

_FACT_GROUPS: dict[str, dict[str, Any]] = {
    "data": {
        "label": "数据研报",
        "report_types": ("futures", "stocks"),
        "primary_report_type": "futures",
    },
    "intelligence": {
        "label": "情报研报",
        "report_types": ("macro",),
        "primary_report_type": "macro",
    },
    "sentiment": {
        "label": "情绪研报",
        "report_types": ("news", "rss", "sentiment"),
        "primary_report_type": "news",
    },
}

_FACT_GROUP_ALIASES = {
    "data": "data",
    "data_research": "data",
    "intelligence": "intelligence",
    "intelligence_research": "intelligence",
    "macro": "intelligence",
    "macro_research": "intelligence",
    "sentiment": "sentiment",
    "sentiment_research": "sentiment",
    "emotion": "sentiment",
}

_COMMON_FACT_FIELDS = (
    "report_id",
    "title",
    "summary",
    "content",
    "symbol",
    "symbols",
    "key_points",
    "keywords",
    "sources",
    "source_count",
    "news_count",
    "trend",
    "macro_trend",
    "risk_level",
    "key_drivers",
    "recommended_sectors",
    "volatility_signal",
    "sentiment",
    "sentiment_score",
    "risk_note",
)


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
                normalized_records = [
                    self._normalize_record(report_type, record)
                    for record in records
                    if isinstance(record, dict)
                ]
                self._cache[report_type] = normalized_records[-_MAX_HISTORY:]
                logger.info("ResearchStore: 加载 %s %d 条", report_type, len(self._cache[report_type]))
            except Exception as e:
                logger.warning("ResearchStore: 加载 %s 失败: %s", report_type, e)

    @staticmethod
    def _normalize_report_type(report_type: str) -> str:
        return _REPORT_TYPE_ALIASES.get(report_type, report_type)

    @staticmethod
    def _resolve_fact_group(report_type: str) -> Optional[str]:
        canonical_type = ResearchStore._normalize_report_type(report_type)
        for fact_group, cfg in _FACT_GROUPS.items():
            if canonical_type in cfg["report_types"]:
                return fact_group
        return None

    @staticmethod
    def _resolve_fact_group_alias(fact_group: str) -> Optional[str]:
        return _FACT_GROUP_ALIASES.get(fact_group)

    @staticmethod
    def _parse_iso_datetime(value: Any) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _build_legacy_source_report(self, record: dict[str, Any]) -> dict[str, Any]:
        source_report: dict[str, Any] = {}
        for field in _COMMON_FACT_FIELDS:
            if field in record:
                source_report[field] = record[field]
        return source_report

    def _build_fact_record(
        self,
        report_type: str,
        record: dict[str, Any],
        source_report: dict[str, Any],
        batch_context: dict[str, Any],
    ) -> dict[str, Any]:
        fact_record: dict[str, Any] = {
            "report_id": source_report.get("report_id") or record.get("report_id"),
            "report_type": report_type,
            "fact_group": self._resolve_fact_group(report_type),
            "score": record.get("score"),
            "confidence": record.get("confidence"),
            "reasoning": record.get("reasoning", ""),
            "observed_content": record.get("observed_content", ""),
            "batch_id": batch_context.get("batch_id") or record.get("batch_id"),
            "date": batch_context.get("date") or record.get("date"),
            "hour": batch_context.get("hour") or record.get("hour"),
            "generated_at": (
                source_report.get("generated_at")
                or batch_context.get("generated_at")
                or record.get("generated_at")
            ),
        }

        for field in _COMMON_FACT_FIELDS:
            value = source_report.get(field)
            if value is not None:
                fact_record[field] = value

        return fact_record

    def _normalize_record(self, report_type: str, record: dict[str, Any]) -> dict[str, Any]:
        canonical_type = self._normalize_report_type(record.get("report_type") or report_type)
        normalized = dict(record)
        normalized["report_type"] = canonical_type

        source_report = normalized.get("source_report")
        if not isinstance(source_report, dict):
            source_report = self._build_legacy_source_report(normalized)

        batch_context = normalized.get("batch_context")
        if not isinstance(batch_context, dict):
            batch_context = {}

        fact_group = normalized.get("fact_group") or self._resolve_fact_group(canonical_type)
        if fact_group:
            normalized["fact_group"] = fact_group
            normalized["fact_group_label"] = _FACT_GROUPS[fact_group]["label"]

        normalized["source_report"] = source_report
        normalized["batch_context"] = batch_context
        normalized["fact_record"] = self._build_fact_record(
            canonical_type,
            normalized,
            source_report,
            batch_context,
        )
        normalized.setdefault("stored_at", datetime.now().isoformat())
        return normalized

    def _persist(self, report_type: str) -> None:
        """单类型落盘"""
        fp = self._persist_dir / f"{report_type}.json"
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(self._cache[report_type], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("ResearchStore: 持久化 %s 失败: %s", report_type, e)

    def save(
        self,
        report_type: str,
        record: dict[str, Any],
        *,
        source_report: Optional[dict[str, Any]] = None,
        batch_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """保存一条评级结果，并保留原始 researcher 事实库存证。"""
        canonical_type = self._normalize_report_type(report_type)
        merged_record = dict(record)
        if source_report is not None:
            merged_record["source_report"] = dict(source_report)
        if batch_context is not None:
            merged_record["batch_context"] = dict(batch_context)
        merged_record.setdefault("stored_at", datetime.now().isoformat())

        normalized = self._normalize_record(canonical_type, merged_record)
        self._cache[canonical_type].append(normalized)

        # 保留最近 N 条
        if len(self._cache[canonical_type]) > _MAX_HISTORY:
            self._cache[canonical_type] = self._cache[canonical_type][-_MAX_HISTORY:]

        # 时间维度清理：保留最近 N 天（默认 7 天）
        max_age_days = int(os.getenv("RESEARCH_STORE_MAX_AGE_DAYS", "7"))
        cutoff = datetime.now() - timedelta(days=max_age_days)
        self._cache[canonical_type] = [
            r for r in self._cache[canonical_type]
            if (self._parse_iso_datetime(r.get("stored_at")) or datetime.now()) > cutoff
        ]

        self._persist(canonical_type)
        logger.info("ResearchStore: 保存 %s (score=%.1f)", canonical_type, normalized.get("score", 0))
        return normalized

    def get_latest(self, report_type: str) -> Optional[dict[str, Any]]:
        """获取某类型最新一条评级"""
        canonical_type = self._normalize_report_type(report_type)
        records = self._cache.get(canonical_type, [])
        return records[-1] if records else None

    def get_history(self, report_type: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取某类型最近 N 条评级"""
        canonical_type = self._normalize_report_type(report_type)
        records = self._cache.get(canonical_type, [])
        return records[-limit:]

    def get_all_latest(self) -> dict[str, Optional[dict[str, Any]]]:
        """获取所有类型的最新评级"""
        return {rt: (records[-1] if records else None) for rt, records in self._cache.items()}

    def get_fact_group_snapshot(self, fact_group: str, limit: int = 10) -> dict[str, Any]:
        """获取 researcher 三类事实中的单类快照。"""
        resolved_group = self._resolve_fact_group_alias(fact_group)
        if resolved_group is None:
            return {"available": False, "fact_group": fact_group}

        cfg = _FACT_GROUPS[resolved_group]
        latest_by_report_type: dict[str, dict[str, Any]] = {}
        history: list[dict[str, Any]] = []

        for report_type in cfg["report_types"]:
            records = self._cache.get(report_type, [])
            if not records:
                continue
            latest_by_report_type[report_type] = records[-1]
            history.extend(records[-limit:])

        if not latest_by_report_type:
            return {
                "available": False,
                "fact_group": resolved_group,
                "label": cfg["label"],
                "primary_report_type": cfg["primary_report_type"],
                "source_report_types": [],
                "latest": None,
                "latest_primary": None,
                "latest_by_report_type": {},
                "history": [],
            }

        history.sort(
            key=lambda record: self._parse_iso_datetime(record.get("stored_at")) or datetime.min,
            reverse=True,
        )
        primary_type = cfg["primary_report_type"]
        latest_primary = latest_by_report_type.get(primary_type)
        latest = latest_primary or history[0]

        return {
            "available": True,
            "fact_group": resolved_group,
            "label": cfg["label"],
            "primary_report_type": primary_type,
            "source_report_types": list(latest_by_report_type.keys()),
            "latest": latest,
            "latest_primary": latest_primary,
            "latest_by_report_type": latest_by_report_type,
            "history": history[:limit],
        }

    def get_fact_overview(self, limit_per_group: int = 5) -> dict[str, dict[str, Any]]:
        """返回三类 researcher 事实的统一总览。"""
        return {
            fact_group: self.get_fact_group_snapshot(fact_group, limit=limit_per_group)
            for fact_group in _FACT_GROUPS
        }

    def get_macro_summary(self) -> dict[str, Any]:
        """获取最新宏观分析摘要（供策略引擎和门控使用）"""
        macro = self.get_latest("macro")
        if not macro:
            return {"available": False}

        fact_record = macro.get("fact_record", {}) if isinstance(macro.get("fact_record"), dict) else {}

        return {
            "available": True,
            "score": macro.get("score", fact_record.get("score", 0)),
            "macro_trend": fact_record.get("macro_trend", macro.get("macro_trend", "unknown")),
            "risk_level": fact_record.get("risk_level", macro.get("risk_level", "unknown")),
            "key_drivers": fact_record.get("key_drivers", macro.get("key_drivers", [])),
            "recommended_sectors": fact_record.get(
                "recommended_sectors",
                macro.get("recommended_sectors", []),
            ),
            "confidence": macro.get("confidence", fact_record.get("confidence", "low")),
            "report_id": fact_record.get("report_id", macro.get("report_id")),
            "generated_at": fact_record.get("generated_at", macro.get("generated_at")),
            "stored_at": macro.get("stored_at"),
        }
