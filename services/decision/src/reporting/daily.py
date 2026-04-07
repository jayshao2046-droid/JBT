"""
DailyReporter — TASK-0021 F batch
决策服务日报生成器，汇总当日策略状态、信号计数、研究会话、模型指标。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta, date
from typing import Any, Dict, List, Optional

from ..notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


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
        # 运行期内存计数（可由各模块调用 increment_* 累计）
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

    def increment(self, key: str, value: int = 1) -> None:
        if key in self._counters:
            self._counters[key] += value

    def add_research_summary(self, summary: Dict[str, Any]) -> None:
        self._research_summaries.append(summary)

    def reset(self) -> None:
        for k in self._counters:
            self._counters[k] = 0
        self._research_summaries.clear()

    def generate(self, report_date: Optional[str] = None) -> DailyStats:
        now = datetime.now(_TZ_CST)
        if report_date is None:
            report_date = now.strftime("%Y-%m-%d")
        generated_at = now.strftime("%Y-%m-%d %H:%M:%S")

        stats = DailyStats(
            report_date=report_date,
            generated_at=generated_at,
            research_summaries=list(self._research_summaries),
            **self._counters,
        )
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
        self._dispatcher.dispatch(event)
        logger.info("Daily report sent for %s", stats.report_date)
        return stats
