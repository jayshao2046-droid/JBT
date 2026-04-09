"""
DailyReporter — TASK-0021 F batch
决策服务日报生成器，汇总当日策略状态、信号计数、研究会话、模型指标。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher
from ..persistence.state_store import get_state_store
from ..strategy.repository import get_repository

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))
_reporter_singleton: Optional["DailyReporter"] = None


@dataclass
class DailyStats:
    report_date: str                 # YYYY-MM-DD
    generated_at: str                # YYYY-MM-DD HH:MM:SS

    # 策略统计
    strategies_total: int = 0
    strategies_active: int = 0
    strategies_pending: int = 0

    # 信号统计
    signals_generated: int = 0
    signals_approved: int = 0
    signals_rejected: int = 0
    signals_pending: int = 0

    # 研究统计
    research_sessions_total: int = 0
    research_sessions_completed: int = 0
    research_sessions_failed: int = 0

    # 发布统计
    publishes_to_sim: int = 0
    publishes_success: int = 0
    publishes_failed: int = 0

    # 研究摘要列表（可选，每条用 dict 表示）
    research_summaries: List[Dict[str, Any]] = field(default_factory=list)

    # 额外自定义字段
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_notify_body(self) -> str:
        lines = [
            f"**日报日期:** {self.report_date}",
            "",
            "**策略状态**",
            f"  总计 {self.strategies_total} | 活跃 {self.strategies_active} | 待审 {self.strategies_pending}",
            "",
            "**信号统计**",
            f"  生成 {self.signals_generated} | 审批通过 {self.signals_approved} | 拒绝 {self.signals_rejected} | 待审 {self.signals_pending}",
            "",
            "**研究会话**",
            f"  共 {self.research_sessions_total} 次 | 完成 {self.research_sessions_completed} | 失败 {self.research_sessions_failed}",
            "",
            "**发布链路**",
            f"  发起 {self.publishes_to_sim} | 成功 {self.publishes_success} | 失败 {self.publishes_failed}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_date": self.report_date,
            "generated_at": self.generated_at,
            "strategies_total": self.strategies_total,
            "strategies_active": self.strategies_active,
            "strategies_pending": self.strategies_pending,
            "signals_generated": self.signals_generated,
            "signals_approved": self.signals_approved,
            "signals_rejected": self.signals_rejected,
            "signals_pending": self.signals_pending,
            "research_sessions_total": self.research_sessions_total,
            "research_sessions_completed": self.research_sessions_completed,
            "research_sessions_failed": self.research_sessions_failed,
            "publishes_to_sim": self.publishes_to_sim,
            "publishes_success": self.publishes_success,
            "publishes_failed": self.publishes_failed,
            "research_summaries": self.research_summaries,
            "extra": self.extra,
        }


class DailyReporter:
    """日报生成器，汇总内存中统计数据并推送通知。"""

    def __init__(self) -> None:
        self._dispatcher = get_dispatcher()
        self._counters: Dict[str, int] = {
            "strategies_total": 0,
            "strategies_active": 0,
            "strategies_pending": 0,
            "signals_generated": 0,
            "signals_approved": 0,
            "signals_rejected": 0,
            "signals_pending": 0,
            "research_sessions_total": 0,
            "research_sessions_completed": 0,
            "research_sessions_failed": 0,
            "publishes_to_sim": 0,
            "publishes_success": 0,
            "publishes_failed": 0,
        }
        self._research_summaries: List[Dict[str, Any]] = []
        self._last_generated: Optional[DailyStats] = None
        self._history: List[Dict[str, Any]] = []

    def _list_decisions(self) -> list[dict]:
        from ..api.routes.signal import _decisions

        return list(_decisions.values())

    def _build_runtime_counts(self) -> tuple[dict[str, int], list[dict[str, Any]]]:
        strategies = get_repository().list_all()
        state_store = get_state_store()
        research_snapshots = state_store.list_records("research_snapshots")
        decisions = self._list_decisions()
        events = self._dispatcher.recent_events(limit=200)

        publish_events = [
            event for event in events
            if event.get("event_type") == "STRATEGY" and str(event.get("event_code", "")).startswith("PUBLISH-")
        ]

        research_summaries = [
            {
                "strategy_id": item.get("strategy_id"),
                "research_snapshot_id": item.get("research_snapshot_id"),
                "research_status": item.get("research_status"),
                "factor_version_hash": item.get("factor_version_hash"),
                "generated_at": item.get("generated_at"),
                "metrics": dict(item.get("metrics") or {}),
            }
            for item in sorted(
                research_snapshots,
                key=lambda record: record.get("generated_at") or "",
                reverse=True,
            )[:5]
        ]

        counts = {
            "strategies_total": len(strategies),
            "strategies_active": sum(1 for item in strategies if item.lifecycle_status.value == "in_production"),
            "strategies_pending": sum(
                1
                for item in strategies
                if item.lifecycle_status.value in {"backtest_confirmed", "pending_execution"}
            ),
            "signals_generated": len(decisions),
            "signals_approved": sum(1 for item in decisions if item.get("action") == "approve"),
            "signals_rejected": sum(
                1
                for item in decisions
                if item.get("eligibility_status") in {"blocked", "expired"}
            ),
            "signals_pending": sum(
                1
                for item in decisions
                if item.get("publish_workflow_status") == "ready_for_publish"
            ),
            "research_sessions_total": len(research_snapshots),
            "research_sessions_completed": sum(
                1 for item in research_snapshots if item.get("research_status") == "completed"
            ),
            "research_sessions_failed": sum(
                1 for item in research_snapshots if item.get("research_status") == "failed"
            ),
            "publishes_to_sim": len(publish_events),
            "publishes_success": sum(
                1 for item in publish_events if str(item.get("title", "")).startswith("✅")
            ),
            "publishes_failed": sum(
                1
                for item in publish_events
                if str(item.get("title", "")).startswith("❌")
                or str(item.get("title", "")).startswith("🚫")
            ),
        }
        return counts, research_summaries

    def increment(self, key: str, value: int = 1) -> None:
        if key in self._counters:
            self._counters[key] += value

    def add_research_summary(self, summary: Dict[str, Any]) -> None:
        self._research_summaries.append(summary)

    def reset(self) -> None:
        for key in self._counters:
            self._counters[key] = 0
        self._research_summaries.clear()
        self._last_generated = None
        self._history.clear()

    def generate(self, report_date: Optional[str] = None) -> DailyStats:
        now = datetime.now(_TZ_CST)
        if report_date is None:
            report_date = now.strftime("%Y-%m-%d")
        generated_at = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            runtime_counts, runtime_summaries = self._build_runtime_counts()
        except Exception:
            runtime_counts = {k: 0 for k in self._counters}
            runtime_summaries = []
        merged_counts = {
            key: self._counters[key] if self._counters[key] else runtime_counts.get(key, 0)
            for key in self._counters
        }

        summaries = list(self._research_summaries) or runtime_summaries
        stats = DailyStats(
            report_date=report_date,
            generated_at=generated_at,
            research_summaries=summaries,
            **merged_counts,
        )
        self._last_generated = stats
        return stats

    def send_daily_report(self, report_date: Optional[str] = None) -> DailyStats:
        """生成日报并发送通知。返回 DailyStats 对象。"""
        stats = self.generate(report_date)

        event = DecisionEvent(
            event_type="DAILY",
            notify_level=NotifyLevel.NOTIFY,
            event_code=f"DAILY-{stats.report_date}",
            title=f"{stats.report_date} 决策服务日报",
            body=stats.to_notify_body(),
        )
        dispatch_state = self._dispatcher.dispatch(event)
        self._history.insert(
            0,
            {
                "report_date": stats.report_date,
                "generated_at": stats.generated_at,
                "dispatch_state": dispatch_state.value if dispatch_state is not None else "unknown",
                "summary": stats.to_dict(),
            },
        )
        del self._history[30:]
        logger.info("Daily report sent for %s", stats.report_date)
        return stats

    def runtime_snapshot(self, limit: int = 7) -> dict[str, Any]:
        latest = self._last_generated or self.generate()
        return {
            "latest_report": latest.to_dict(),
            "last_sent_at": self._history[0]["generated_at"] if self._history else None,
            "history": [dict(item) for item in self._history[:limit]],
            "has_sent_history": bool(self._history),
        }

    def dashboard_reports(self, limit: int = 30) -> list[dict[str, Any]]:
        """最近日报摘要（只读聚合，供临时看板使用）。"""
        return [
            {
                "report_id": f"daily-{item.get('report_date', 'unknown')}",
                "date": item.get("report_date"),
                "type": "daily",
                "summary": item.get("summary", {}),
            }
            for item in self._history[:limit]
        ]


def get_daily_reporter() -> DailyReporter:
    global _reporter_singleton
    if _reporter_singleton is None:
        _reporter_singleton = DailyReporter()
    return _reporter_singleton
