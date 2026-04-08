"""
PublishGate — TASK-0021 G batch
策略发布资格门禁：校验策略包是否满足向 sim-trading 发布的前置条件。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from ..gating.backtest_gate import get_backtest_gate
from ..gating.execution_gate import check_execution_eligibility
from ..gating.research_gate import get_research_gate
from ..strategy.lifecycle import LifecycleStatus, transition
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

    @staticmethod
    def _normalize_lifecycle_status(raw_status) -> LifecycleStatus:
        if isinstance(raw_status, LifecycleStatus):
            return raw_status
        return LifecycleStatus(str(raw_status))

    def _validate_publish_lifecycle(self, pkg, reasons: list[str]) -> None:
        current_status = self._normalize_lifecycle_status(pkg.lifecycle_status)

        # 允许首次发布走 backtest_confirmed -> pending_execution，
        # 同时允许 adapter 失败后从 pending_execution 原位重试。
        if current_status in (LifecycleStatus.archived, LifecycleStatus.pending_execution):
            return

        try:
            transition(current_status, LifecycleStatus.pending_execution)
        except ValueError:
            reasons.append(
                f"lifecycle_status={current_status.value} cannot enter publish flow; "
                "expected backtest_confirmed or pending_execution"
            )

    def _validate_backtest_certificate(self, pkg, reasons: list[str]):
        cert = get_backtest_gate().get_cert(pkg.strategy_id)
        if cert is None:
            reasons.append("backtest certificate missing")
            return None

        if cert.certificate_id != pkg.backtest_certificate_id:
            reasons.append("backtest certificate id mismatch")

        if cert.review_status == "expired" or datetime.now(timezone.utc) > cert.expires_at:
            reasons.append("backtest certificate expired")
        elif cert.review_status != "approved":
            reasons.append(f"backtest certificate status={cert.review_status}")

        if cert.factor_version_hash != pkg.factor_version_hash:
            reasons.append("backtest certificate factor_version_hash mismatch")
        return cert

    def _validate_research_snapshot(self, pkg, reasons: list[str]):
        snapshot = get_research_gate().get_snapshot(pkg.strategy_id)
        if snapshot is None:
            reasons.append("research snapshot missing")
            return None

        if snapshot.research_snapshot_id != pkg.research_snapshot_id:
            reasons.append("research snapshot id mismatch")

        if snapshot.research_status == "expired" or datetime.now(timezone.utc) > snapshot.valid_until:
            reasons.append("research snapshot expired")
        elif snapshot.research_status != "completed":
            reasons.append(f"research snapshot status={snapshot.research_status}")

        if snapshot.factor_version_hash != pkg.factor_version_hash:
            reasons.append("research snapshot factor_version_hash mismatch")
        return snapshot

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

        current_status = self._normalize_lifecycle_status(pkg.lifecycle_status)

        # 2. 非 retired/archived 状态
        if current_status.value in ("archived", "retired"):
            reasons.append(f"strategy is {current_status.value}, cannot publish")

        # 3. lifecycle 合法转移检查
        self._validate_publish_lifecycle(pkg, reasons)

        # 4. 重验持久化回测 / 研究资格
        backtest_cert = self._validate_backtest_certificate(pkg, reasons)
        research_snapshot = self._validate_research_snapshot(pkg, reasons)
        if (
            backtest_cert is not None
            and research_snapshot is not None
            and backtest_cert.factor_version_hash
            and research_snapshot.factor_version_hash
            and backtest_cert.factor_version_hash != research_snapshot.factor_version_hash
        ):
            reasons.append("eligibility factor_version_hash mismatch")

        # 5. 因子同步状态
        if pkg.factor_sync_status != "aligned":
            reasons.append(f"factor_sync_status={pkg.factor_sync_status}, must be aligned")

        # 6. 允许目标
        if target not in (pkg.allowed_targets or []):
            reasons.append(f"target {target} not in allowed_targets={pkg.allowed_targets}")

        # 7. live-trading 锁定检查（execution gate — 对 live-trading 额外施加第一阶段锁）
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
