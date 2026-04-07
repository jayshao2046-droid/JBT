"""
PublishExecutor — TASK-0021 G batch
统一发布执行器：门禁校验 → 状态迁移 → HTTP 推送 → 通知。
"""
from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from ..strategy.repository import get_repository
from ..strategy.lifecycle import LifecycleStatus
from .gate import PublishGate
from .sim_adapter import SimTradingAdapter
from ..notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


class PublishStatus(str, enum.Enum):
    SUCCESS = "success"
    GATE_REJECTED = "gate_rejected"
    ADAPTER_FAILED = "adapter_failed"
    STRATEGY_NOT_FOUND = "strategy_not_found"


@dataclass
class PublishResult:
    status: PublishStatus
    strategy_id: str
    target: str
    message: str
    strategy_snapshot: Dict[str, Any] = field(default_factory=dict)
    adapter_response: Dict[str, Any] = field(default_factory=dict)


class PublishExecutor:
    """
    策略发布执行器。流程：
    1. PublishGate.check → 门禁通过才继续
    2. 更新策略状态 = pending_execution
    3. SimTradingAdapter.publish → 推送策略包
    4. 根据推送结果更新策略状态 (in_production / pending_execution 维持)
    5. 发送飞书/邮件通知
    """

    def __init__(
        self,
        gate: Optional[PublishGate] = None,
        adapter: Optional[SimTradingAdapter] = None,
    ) -> None:
        self._gate = gate or PublishGate()
        self._adapter = adapter or SimTradingAdapter()
        self._dispatcher = get_dispatcher()

    def execute(self, strategy_id: str, target: str = "sim-trading") -> PublishResult:
        repo = get_repository()
        pkg = repo.get(strategy_id)
        if pkg is None:
            return PublishResult(
                status=PublishStatus.STRATEGY_NOT_FOUND,
                strategy_id=strategy_id,
                target=target,
                message=f"Strategy {strategy_id} not found",
            )

        # 1. 门禁校验
        eligibility = self._gate.check(strategy_id, target)
        if not eligibility.eligible:
            self._notify(
                strategy_id=strategy_id,
                target=target,
                success=False,
                message=f"门禁拒绝: {eligibility.primary_reason}",
                is_gate_rejection=True,
            )
            return PublishResult(
                status=PublishStatus.GATE_REJECTED,
                strategy_id=strategy_id,
                target=target,
                message=eligibility.primary_reason,
            )

        # 2. 迁移状态 → pending_execution
        now_iso = datetime.now(_TZ_CST).isoformat()
        repo.update(strategy_id, {
            "lifecycle_status": LifecycleStatus.pending_execution,
            "publish_target": target,
            "published_at": now_iso,
            "updated_at": now_iso,
        })
        pkg = repo.get(strategy_id)  # reload after update

        # 3. 推送策略包
        snapshot = pkg.to_contract_dict()
        adapter_result = self._adapter.publish(snapshot)

        # 4. 根据推送结果更新状态
        if adapter_result["success"]:
            repo.update(strategy_id, {"lifecycle_status": LifecycleStatus.in_production})
            pub_status = PublishStatus.SUCCESS
            msg = f"Strategy {strategy_id} published to {target} successfully"
        else:
            pub_status = PublishStatus.ADAPTER_FAILED
            msg = f"Adapter failed: {adapter_result.get('response', '')}"

        # 5. 通知
        self._notify(
            strategy_id=strategy_id,
            target=target,
            success=adapter_result["success"],
            message=msg,
        )

        logger.info("PublishExecutor.execute strategy=%s target=%s status=%s", strategy_id, target, pub_status)
        return PublishResult(
            status=pub_status,
            strategy_id=strategy_id,
            target=target,
            message=msg,
            strategy_snapshot=snapshot,
            adapter_response=adapter_result,
        )

    def _notify(
        self,
        strategy_id: str,
        target: str,
        success: bool,
        message: str,
        is_gate_rejection: bool = False,
    ) -> None:
        level = NotifyLevel.NOTIFY if success else (NotifyLevel.P1 if is_gate_rejection else NotifyLevel.P2)
        status_label = "✅ 发布成功" if success else ("🚫 门禁拒绝" if is_gate_rejection else "❌ 推送失败")
        event = DecisionEvent(
            event_type="STRATEGY",
            notify_level=level,
            event_code=f"PUBLISH-{strategy_id}-{target.upper()}",
            title=f"{status_label}: {strategy_id} → {target}",
            body=f"**策略:** {strategy_id}\n**目标:** {target}\n**状态:** {status_label}\n**说明:** {message}",
            strategy_id=strategy_id,
        )
        try:
            self._dispatcher.dispatch(event)
        except Exception as exc:
            logger.error("PublishExecutor notify failed: %s", exc)
