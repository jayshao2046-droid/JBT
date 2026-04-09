"""
NotifierDispatcher — TASK-0014 P1 / A3
Dual-channel dispatch with risk state tracking, dedup/suppression/recovery/escalation.
"""
import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .feishu import FeishuNotifier
from .email import EmailNotifier

logger = logging.getLogger(__name__)

_dispatcher_singleton: Optional["NotifierDispatcher"] = None


@dataclass
class RiskEvent:
    task_id: str
    stage_preset: str   # "sim" | "live"
    risk_level: str     # "P0" | "P1" | "P2"
    account_id: str
    strategy_id: str
    symbol: str
    signal_id: str
    trace_id: str
    event_code: str
    reason: str
    # A3 additions
    source: str = ""
    message: str = ""
    timestamp: float = 0.0
    extra: dict = field(default_factory=dict)
    category: str = ""

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if not self.message:
            self.message = self.reason


class SystemRiskState(enum.Enum):
    NORMAL = "NORMAL"
    FEISHU_FAILED = "FEISHU_FAILED"
    EMAIL_FAILED = "EMAIL_FAILED"
    ORDERS_BLOCKED = "ORDERS_BLOCKED"   # both channels failed


class _DedupEntry:
    """Tracks dedup state for a single event_code."""
    __slots__ = ("last_sent", "suppressed")

    def __init__(self, last_sent: float):
        self.last_sent = last_sent
        self.suppressed = 0


class NotifierDispatcher:
    """调度双通道通知，跟踪系统风险状态，去重/抑制/恢复/升级。"""

    def __init__(
        self,
        feishu: FeishuNotifier,
        email: EmailNotifier,
        *,
        dedup_window_s: float = 60.0,
        escalation_threshold: int = 5,
        escalation_window_s: float = 300.0,
    ) -> None:
        self._feishu = feishu
        self._email = email
        self._state = SystemRiskState.NORMAL
        self._dedup_window_s = dedup_window_s
        self._escalation_threshold = escalation_threshold
        self._escalation_window_s = escalation_window_s
        self._dedup: Dict[str, _DedupEntry] = {}
        self._escalation_history: Dict[str, List[float]] = {}

    @property
    def state(self) -> SystemRiskState:
        return self._state

    # ---- escalation ----

    def _check_escalation(self, event: RiskEvent, now: float) -> None:
        """同一 event_code 在 escalation_window 内触发 >= threshold 次时，P1 升级为 P0。"""
        code = event.event_code
        history = self._escalation_history.setdefault(code, [])
        history.append(now)
        cutoff = now - self._escalation_window_s
        self._escalation_history[code] = [t for t in history if t >= cutoff]
        if (
            len(self._escalation_history[code]) >= self._escalation_threshold
            and event.risk_level == "P1"
        ):
            logger.warning(
                "Escalation: event %s triggered %d times in %.0fs, upgrading P1→P0",
                code, len(self._escalation_history[code]), self._escalation_window_s,
            )
            event.risk_level = "P0"

    # ---- dedup / suppression ----

    def _is_suppressed(self, event_code: str, now: float) -> bool:
        """在去重窗口内的重复事件返回 True（不实际发送）。"""
        entry = self._dedup.get(event_code)
        if entry is None:
            return False
        if (now - entry.last_sent) < self._dedup_window_s:
            entry.suppressed += 1
            return True
        return False

    def get_suppressed_count(self, event_code: str) -> int:
        """返回某 event_code 自上次实际发送以来的抑制次数。"""
        entry = self._dedup.get(event_code)
        return entry.suppressed if entry else 0

    # ---- recovery ----

    def check_recovery(self, event_code: str) -> bool:
        """event_code 在去重窗口过期后未再触发 → 视为已恢复。"""
        entry = self._dedup.get(event_code)
        if entry is None:
            return False
        return (time.time() - entry.last_sent) > self._dedup_window_s

    def emit_recovery(self, event_code: str) -> Optional[SystemRiskState]:
        """发送恢复通知（仅当 check_recovery 为 True 时）。"""
        if not self.check_recovery(event_code):
            return None
        entry = self._dedup.pop(event_code, None)
        self._escalation_history.pop(event_code, None)
        recovery_event = RiskEvent(
            task_id="SYSTEM",
            stage_preset="sim",
            risk_level="P2",
            account_id="",
            strategy_id="",
            symbol="",
            signal_id="",
            trace_id="",
            event_code=f"{event_code}_RECOVERED",
            reason=f"{event_code} has recovered (suppressed {entry.suppressed if entry else 0} during window)",
            source="dispatcher",
            category="SYSTEM",
        )
        return self._do_dispatch(recovery_event)

    # ---- dispatch core ----

    def dispatch(self, event: RiskEvent) -> SystemRiskState:
        """
        调用双通道并更新系统风险状态。
        包含去重、升级逻辑；被抑制的事件不实际发送。
        """
        now = time.time()

        # Escalation check (before dedup, so all occurrences count)
        self._check_escalation(event, now)

        # Dedup check
        if self._is_suppressed(event.event_code, now):
            logger.debug(
                "Suppressed duplicate event %s (window=%.0fs)",
                event.event_code, self._dedup_window_s,
            )
            return self._state

        # Carry forward suppressed count into extra for summary notification
        old_entry = self._dedup.get(event.event_code)
        if old_entry and old_entry.suppressed > 0:
            event.extra["suppressed_count"] = old_entry.suppressed

        self._dedup[event.event_code] = _DedupEntry(now)

        return self._do_dispatch(event)

    def _do_dispatch(self, event: RiskEvent) -> SystemRiskState:
        """实际执行双通道发送。"""
        feishu_ok = False
        email_ok = False

        try:
            feishu_ok = self._feishu.send(event)
        except Exception as exc:
            logger.error("FeishuNotifier raised unexpected exception: %s", exc)
            feishu_ok = False

        try:
            email_ok = self._email.send(event)
        except Exception as exc:
            logger.error("EmailNotifier raised unexpected exception: %s", exc)
            email_ok = False

        if feishu_ok and email_ok:
            self._state = SystemRiskState.NORMAL
        elif not feishu_ok and email_ok:
            logger.error("Feishu channel failed for event %s", event.event_code)
            self._state = SystemRiskState.FEISHU_FAILED
        elif feishu_ok and not email_ok:
            logger.error("Email channel failed for event %s", event.event_code)
            self._state = SystemRiskState.EMAIL_FAILED
        else:
            logger.error(
                "BOTH notification channels failed for event %s — ORDERS_BLOCKED",
                event.event_code,
            )
            self._state = SystemRiskState.ORDERS_BLOCKED

        return self._state

    def is_orders_blocked(self) -> bool:
        """当双通道均失败时返回 True，上层调用方应拒绝新开仓。"""
        return self._state == SystemRiskState.ORDERS_BLOCKED


def register_dispatcher(dispatcher: "NotifierDispatcher") -> "NotifierDispatcher":
    """注册进程内 dispatcher，供风控钩子复用。"""
    global _dispatcher_singleton
    _dispatcher_singleton = dispatcher
    return dispatcher


def get_dispatcher() -> Optional["NotifierDispatcher"]:
    """获取当前进程内 dispatcher；未 bootstrap 时返回 None。"""
    return _dispatcher_singleton


def clear_dispatcher() -> None:
    """测试或重建场景下清空进程内 dispatcher。"""
    global _dispatcher_singleton
    _dispatcher_singleton = None


def bootstrap_dispatcher(*, force: bool = False) -> "NotifierDispatcher":
    """按环境变量初始化双通道 dispatcher，并注册为进程内单例。"""
    current = get_dispatcher()
    if current is not None and not force:
        return current
    dispatcher = NotifierDispatcher(FeishuNotifier(), EmailNotifier())
    return register_dispatcher(dispatcher)
