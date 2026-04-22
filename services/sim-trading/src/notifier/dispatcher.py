"""
NotifierDispatcher — TASK-NOTIFY-20260423-A
双通道调度 + 静默窗口 + alarm.log 反馈 + 3群路由。
"""
import enum
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from .feishu import FeishuNotifier
from .email import EmailNotifier
from .quiet_window import can_send

logger = logging.getLogger(__name__)

_dispatcher_singleton: Optional["NotifierDispatcher"] = None
CN_TZ = timezone(timedelta(hours=8))

# alarm.log 路径
_ALARM_LOG = os.environ.get("NOTIFY_ALARM_LOG", "/data/logs/notify_alarm.log")


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
        # alarm.log 失败计数：{event_code: (count, first_ts)}
        self._alarm_pending: Dict[str, tuple] = {}

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
        包含去重、升级、静默窗口逻辑；被抑制 / 静默的事件不实际发送。
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

        # 静默窗口检查：P0 / TRADE / ORDER 穿透；其余静默期丢弃
        if not can_send(level=event.risk_level, category=event.category):
            logger.debug("[dispatcher] 静默期，跳过事件 %s", event.event_code)
            return self._state

        # Carry forward suppressed count into extra for summary notification
        old_entry = self._dedup.get(event.event_code)
        if old_entry and old_entry.suppressed > 0:
            event.extra["suppressed_count"] = old_entry.suppressed

        self._dedup[event.event_code] = _DedupEntry(now)

        return self._do_dispatch(event)

    def _do_dispatch(self, event: RiskEvent) -> SystemRiskState:
        """实际执行双通道发送，记录 alarm.log，并附带 pending_banner。"""
        feishu_ok = False
        email_ok = False

        # 构建 pending_banner（上次失败后首次成功时提示）
        pending_banner = self._pop_pending_banner(event.event_code)

        try:
            feishu_ok = self._feishu.send(event, pending_banner=pending_banner)
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
            self._append_alarm_log(event, "feishu_failed")
            self._mark_alarm_pending(event.event_code)
            self._state = SystemRiskState.FEISHU_FAILED
        elif feishu_ok and not email_ok:
            logger.error("Email channel failed for event %s", event.event_code)
            self._append_alarm_log(event, "email_failed")
            self._state = SystemRiskState.EMAIL_FAILED
        else:
            logger.error(
                "BOTH notification channels failed for event %s — ORDERS_BLOCKED",
                event.event_code,
            )
            self._append_alarm_log(event, "both_failed")
            self._mark_alarm_pending(event.event_code)
            self._state = SystemRiskState.ORDERS_BLOCKED

        return self._state

    # ---- alarm.log 反馈机制 ----

    def _append_alarm_log(self, event: RiskEvent, reason: str) -> None:
        """向 alarm.log 追加 JSONL 失败记录。"""
        try:
            ts = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
            record = json.dumps({
                "ts": ts, "event_code": event.event_code,
                "reason": reason, "risk_level": event.risk_level,
                "category": event.category,
            }, ensure_ascii=False)
            log_path = _ALARM_LOG
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(record + "\n")
        except Exception as exc:
            logger.warning("[dispatcher] alarm.log 写入失败: %s", exc)

    def _mark_alarm_pending(self, event_code: str) -> None:
        """标记该 event_code 有待通知的失败。"""
        now_ts = datetime.now(CN_TZ).strftime("%H:%M:%S")
        if event_code not in self._alarm_pending:
            self._alarm_pending[event_code] = (1, now_ts)
        else:
            cnt, first_ts = self._alarm_pending[event_code]
            self._alarm_pending[event_code] = (cnt + 1, first_ts)

    def _pop_pending_banner(self, event_code: str) -> str:
        """若存在待通知的失败记录，消费并返回 banner 文本。"""
        pending = self._alarm_pending.pop(event_code, None)
        if pending:
            cnt, first_ts = pending
            return f"⚠️ 上次推送失败累计 {cnt} 条，最早 {first_ts}"
        return ""

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
