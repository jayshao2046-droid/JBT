"""
PublishGate — TASK-0021 G batch
策略发布资格门禁：校验策略包是否满足向 sim-trading 发布的前置条件。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..gating.execution_gate import check_execution_eligibility
from ..strategy.repository import get_repository

logger = logging.getLogger(__name__)


@dataclass
class PublishEligibility:
    eligible: bool
    strategy_id: str
    target: str
    reasons: list[str]

    @property
    def primary_reason(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "ok"


class PublishGate:
    """
    发布资格门禁。按顺序执行以下校验：
    1. 策略包存在且非 retired/archived
    2. backtestCert valid（backtest_gate already checked in research phase, here we re-verify）
    3. factor_sync_status == 'aligned'
    4. allowed_targets 包含目标
    5. execution_gate 通过（live-trading 已锁定）
    """

    def check(self, strategy_id: str, target: str = "sim-trading") -> PublishEligibility:
        reasons: list[str] = []

        # 1. 策略包存在
        repo = get_repository()
        pkg = repo.get(strategy_id)
        if pkg is None:
            return PublishEligibility(
                eligible=False,
                strategy_id=strategy_id,
                target=target,
                reasons=[f"strategy {strategy_id} not found"],
            )

        # 2. 非 retired/archived 状态
        if pkg.lifecycle_status.value in ("archived", "retired"):
            reasons.append(f"strategy is {pkg.lifecycle_status.value}, cannot publish")

        # 3. 因子同步状态
        if pkg.factor_sync_status != "aligned":
            reasons.append(f"factor_sync_status={pkg.factor_sync_status}, must be aligned")

        # 4. 允许目标
        if target not in (pkg.allowed_targets or []):
            reasons.append(f"target {target} not in allowed_targets={pkg.allowed_targets}")

        # 5. live-trading 锁定检查（execution gate — 对 live-trading 额外施加第一阶段锁）
        gate_result = check_execution_eligibility(strategy_id, target)
        if not gate_result["eligible"]:
            reasons.append(f"execution gate: {gate_result['reason']}")

        eligible = len(reasons) == 0
        logger.info(
            "PublishGate.check strategy=%s target=%s eligible=%s reasons=%s",
            strategy_id, target, eligible, reasons,
        )
        return PublishEligibility(
            eligible=eligible,
            strategy_id=strategy_id,
            target=target,
            reasons=reasons,
        )
