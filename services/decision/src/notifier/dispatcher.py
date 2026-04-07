"""
NotifierDispatcher — TASK-0021 F batch
决策服务双通道通知调度器（飞书 + 邮件）。
"""
import enum
import logging
from dataclasses import dataclass, field
from typing import Optional

from .feishu import DecisionFeishuNotifier
from .email import DecisionEmailNotifier

logger = logging.getLogger(__name__)

_dispatcher_singleton: Optional["NotifierDispatcher"] = None


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
    """决策服务双通道通知调度器。"""

    def __init__(
        self,
        feishu: DecisionFeishuNotifier,
        email: DecisionEmailNotifier,
    ) -> None:
        self._feishu = feishu
        self._email = email
        self._state = DispatchState.NORMAL

    @property
    def state(self) -> DispatchState:
        return self._state

    def dispatch(self, event: DecisionEvent) -> DispatchState:
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

        logger.info(
            "dispatch event=%s level=%s state=%s feishu=%s email=%s",
            event.event_code, event.notify_level, self._state,
            feishu_ok, email_ok,
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
