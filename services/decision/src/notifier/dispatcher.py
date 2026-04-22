"""
NotifierDispatcher — TASK-0021 F batch + TASK-0025 failover integration + 静默窗口
决策服务双通道通知调度器（飞书 + 邮件）+ SimNow 备用方案。
"""
from __future__ import annotations

import enum
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from .email import DecisionEmailNotifier
from .feishu import DecisionFeishuNotifier

logger = logging.getLogger(__name__)

_dispatcher_singleton: Optional["NotifierDispatcher"] = None
_TZ_CST = timezone(timedelta(hours=8))

# 告警日志路径
_ALARM_LOG = Path(os.environ.get("NOTIFY_ALARM_LOG", "/data/logs/notify_alarm.log"))


def _is_quiet_hours(now: datetime | None = None) -> bool:
    """静默时段：00:11–07:59，即推送窗口为 08:00–24:10。"""
    now = now or datetime.now(_TZ_CST)
    minutes = now.hour * 60 + now.minute
    return 11 <= minutes < 480


def _should_bypass_quiet(level: "NotifyLevel") -> bool:
    """判断是否绕过静默窗口：P0/P1/SIGNAL 常通。"""
    level_str = level.value if hasattr(level, "value") else str(level)
    return level_str in ("P0", "P1", "SIGNAL")


def _append_alarm_log(event: "DecisionEvent") -> None:
    """双通道全失时写入本地告警日志，下次推送成功时附带 pending 标帜。"""
    try:
        _ALARM_LOG.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(_TZ_CST).isoformat(),
            "event_code": event.event_code,
            "level": event.notify_level.value if hasattr(event.notify_level, "value") else str(event.notify_level),
            "title": event.title,
        }
        with _ALARM_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("告警日志写入失败: %s", exc)


class NotifyLevel(str, enum.Enum):
    P0 = "P0"       # 系统崩溃/数据丢失
    P1 = "P1"       # 研究失败/模型异常
    P2 = "P2"       # 低优先级预警
    SIGNAL = "SIGNAL"     # 信号审批/触发
    RESEARCH = "RESEARCH" # 研究完成摘要
    NOTIFY = "NOTIFY"     # 系统通知/日报


@dataclass
class DecisionEvent:
    event_type: str          # RESEARCH | SIGNAL | STRATEGY | DAILY | SYSTEM
    notify_level: NotifyLevel
    event_code: str
    title: str
    body: str                # Markdown 正文
    strategy_id: str = ""
    model_id: str = ""
    signal_id: str = ""
    session_id: str = ""
    trace_id: str = ""
    extra: dict = field(default_factory=dict)


class DispatchState(enum.Enum):
    NORMAL = "NORMAL"
    FEISHU_FAILED = "FEISHU_FAILED"
    EMAIL_FAILED = "EMAIL_FAILED"
    BOTH_FAILED = "BOTH_FAILED"


class NotifierDispatcher:
    """决策服务双通道通知调度器 + SimNow 备用方案集成。"""

    def __init__(
        self,
        feishu: DecisionFeishuNotifier,
        email: DecisionEmailNotifier,
        failover_manager: Optional[Any] = None,
    ) -> None:
        self._feishu = feishu
        self._email = email
        self._failover = failover_manager
        self._state = DispatchState.NORMAL
        self._event_history: list[dict[str, Any]] = []
        self._channel_stats: dict[str, dict[str, Any]] = {
            "feishu": self._build_channel_stats("feishu"),
            "email": self._build_channel_stats("email"),
        }

    @property
    def state(self) -> DispatchState:
        return self._state

    def _is_channel_enabled(self, channel: str) -> bool:
        if channel == "feishu":
            return bool(getattr(self._feishu, "_enabled", False))
        return bool(getattr(self._email, "_enabled", False))

    def _is_channel_configured(self, channel: str) -> bool:
        if channel == "feishu":
            if not self._is_channel_enabled(channel):
                return False
            return bool(getattr(self._feishu, "_webhook_url", ""))

        if not self._is_channel_enabled(channel):
            return False
        required = (
            getattr(self._email, "_smtp_host", ""),
            getattr(self._email, "_smtp_user", ""),
            getattr(self._email, "_smtp_password", ""),
            getattr(self._email, "_from_addr", ""),
            getattr(self._email, "_to_addr", ""),
        )
        return all(bool(value) for value in required)

    def _build_channel_stats(self, channel: str) -> dict[str, Any]:
        return {
            "channel": channel,
            "enabled": self._is_channel_enabled(channel),
            "configured": self._is_channel_configured(channel),
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "last_attempt_at": None,
            "last_success_at": None,
            "last_result": None,
            "last_event_code": None,
            "last_title": None,
            "last_error": None,
        }

    def _record_channel_attempt(
        self,
        channel: str,
        success: bool,
        event: DecisionEvent,
        attempted_at: str,
    ) -> None:
        stats = self._channel_stats[channel]
        stats["enabled"] = self._is_channel_enabled(channel)
        stats["configured"] = self._is_channel_configured(channel)
        stats["attempts"] += 1
        stats["last_attempt_at"] = attempted_at
        stats["last_result"] = success
        stats["last_event_code"] = event.event_code
        stats["last_title"] = event.title

        if success:
            stats["successes"] += 1
            stats["last_success_at"] = attempted_at
            stats["last_error"] = None
        else:
            stats["failures"] += 1
            if not stats["enabled"]:
                stats["last_error"] = "channel disabled"
            elif not stats["configured"]:
                stats["last_error"] = "channel misconfigured"
            else:
                stats["last_error"] = "delivery failed"

    def _append_event(
        self,
        event: DecisionEvent,
        dispatched_at: str,
        feishu_ok: bool,
        email_ok: bool,
    ) -> None:
        record = {
            "event_code": event.event_code,
            "event_type": event.event_type,
            "notify_level": event.notify_level.value,
            "title": event.title,
            "strategy_id": event.strategy_id or None,
            "model_id": event.model_id or None,
            "signal_id": event.signal_id or None,
            "session_id": event.session_id or None,
            "trace_id": event.trace_id or None,
            "dispatched_at": dispatched_at,
            "dispatch_state": self._state.value,
            "channels": {
                "feishu": feishu_ok,
                "email": email_ok,
            },
            "extra": dict(event.extra or {}),
        }
        self._event_history.insert(0, record)
        del self._event_history[50:]

    def _channel_statuses(self) -> list[dict[str, Any]]:
        statuses: list[dict[str, Any]] = []
        for name, stats in self._channel_stats.items():
            attempts = int(stats["attempts"])
            successes = int(stats["successes"])
            success_rate = round((successes / attempts) * 100, 1) if attempts else None

            if not stats["enabled"]:
                status = "disabled"
            elif not stats["configured"]:
                status = "misconfigured"
            elif stats["last_result"] is None:
                status = "idle"
            elif stats["last_result"]:
                status = "healthy"
            else:
                status = "degraded"

            statuses.append(
                {
                    "channel": name,
                    "status": status,
                    "enabled": bool(stats["enabled"]),
                    "configured": bool(stats["configured"]),
                    "attempts": attempts,
                    "successes": successes,
                    "failures": int(stats["failures"]),
                    "success_rate": success_rate,
                    "last_attempt_at": stats["last_attempt_at"],
                    "last_success_at": stats["last_success_at"],
                    "last_event_code": stats["last_event_code"],
                    "last_title": stats["last_title"],
                    "last_error": stats["last_error"],
                }
            )

        return statuses

    def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        return [dict(item) for item in self._event_history[:limit]]

    def runtime_snapshot(self, recent_limit: int = 10) -> dict[str, Any]:
        snapshot = {
            "dispatcher_state": self._state.value,
            "recent_events": self.recent_events(recent_limit),
            "channels": self._channel_statuses(),
        }
        if self._failover:
            snapshot["failover"] = self._failover.get_status()
        return snapshot

    def dashboard_notifications(self, limit: int = 50) -> list[dict[str, Any]]:
        """最近通知列表（只读聚合，供临时看板使用）。"""
        return [
            {
                "type": item.get("event_type"),
                "title": item.get("title"),
                "timestamp": item.get("dispatched_at"),
                "status": item.get("dispatch_state"),
            }
            for item in self._event_history[:limit]
        ]

    def dispatch(self, event: DecisionEvent) -> DispatchState:
        # 静默窗口检查：00:11–07:59 静默，P0/P1/SIGNAL 绕过
        if _is_quiet_hours() and not _should_bypass_quiet(event.notify_level):
            logger.debug(
                "dispatch skipped (quiet hours) event=%s level=%s",
                event.event_code, event.notify_level,
            )
            return self._state

        dispatched_at = datetime.now(timezone.utc).isoformat()
        feishu_ok = self._feishu.send(event)
        email_ok = self._email.send(event)

        if feishu_ok and email_ok:
            self._state = DispatchState.NORMAL
        elif feishu_ok and not email_ok:
            self._state = DispatchState.EMAIL_FAILED
        elif not feishu_ok and email_ok:
            self._state = DispatchState.FEISHU_FAILED
        else:
            self._state = DispatchState.BOTH_FAILED

        self._record_channel_attempt("feishu", feishu_ok, event, dispatched_at)
        self._record_channel_attempt("email", email_ok, event, dispatched_at)
        self._append_event(event, dispatched_at, feishu_ok, email_ok)

        # TASK-0025: 如果通知失败且配置了 failover，记录事件
        if self._failover and not (feishu_ok or email_ok):
            self._failover.record_notification_failure(
                event_code=event.event_code,
                title=event.title,
                body=event.body,
            )

        # 双通道全失败时写入本地告警日志
        if not feishu_ok and not email_ok:
            _append_alarm_log(event)

        logger.info(
            "dispatch event=%s level=%s state=%s feishu=%s email=%s",
            event.event_code,
            event.notify_level,
            self._state,
            feishu_ok,
            email_ok,
        )
        return self._state


def get_dispatcher() -> NotifierDispatcher:
    global _dispatcher_singleton
    if _dispatcher_singleton is None:
        _dispatcher_singleton = NotifierDispatcher(
            feishu=DecisionFeishuNotifier(),
            email=DecisionEmailNotifier(),
        )
    return _dispatcher_singleton
