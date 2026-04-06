"""
NotifierDispatcher — TASK-0014 P1
Dual-channel dispatch with risk state tracking.
"""
import enum
import logging
from dataclasses import dataclass

from .feishu import FeishuNotifier
from .email import EmailNotifier

logger = logging.getLogger(__name__)


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


class SystemRiskState(enum.Enum):
    NORMAL = "NORMAL"
    FEISHU_FAILED = "FEISHU_FAILED"
    EMAIL_FAILED = "EMAIL_FAILED"
    ORDERS_BLOCKED = "ORDERS_BLOCKED"   # both channels failed


class NotifierDispatcher:
    """调度双通道通知，跟踪系统风险状态。"""

    def __init__(self, feishu: FeishuNotifier, email: EmailNotifier) -> None:
        self._feishu = feishu
        self._email = email
        self._state = SystemRiskState.NORMAL

    @property
    def state(self) -> SystemRiskState:
        return self._state

    def dispatch(self, event: RiskEvent) -> SystemRiskState:
        """
        调用双通道并更新系统风险状态。
        - 全成功 → NORMAL
        - 仅飞书失败 → FEISHU_FAILED
        - 仅邮件失败 → EMAIL_FAILED
        - 双失败 → ORDERS_BLOCKED（拒绝新开仓）
        """
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
