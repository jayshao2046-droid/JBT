from datetime import datetime, timezone
from typing import Optional
from ..strategy.lifecycle import LifecycleStatus, transition, to_contract_state


class StrategyPackage:
    def __init__(
        self,
        strategy_id: str,
        strategy_name: str,
        strategy_version: str,
        template_id: str,
        package_hash: str,
        factor_version_hash: str,
        factor_sync_status: str,
        research_snapshot_id: str,
        backtest_certificate_id: str,
        risk_profile_hash: str,
        config_snapshot_ref: str,
        allowed_targets: list[str],
        live_visibility_mode: str = "locked_visible",
        publish_target: Optional[str] = None,
        reserved_at: Optional[str] = None,
        published_at: Optional[str] = None,
        retired_at: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.strategy_version = strategy_version
        self.template_id = template_id
        self.package_hash = package_hash
        self.factor_version_hash = factor_version_hash
        self.factor_sync_status = factor_sync_status
        self.research_snapshot_id = research_snapshot_id
        self.backtest_certificate_id = backtest_certificate_id
        self.risk_profile_hash = risk_profile_hash
        self.config_snapshot_ref = config_snapshot_ref
        self.lifecycle_status: LifecycleStatus = LifecycleStatus.imported
        self.allowed_targets = allowed_targets
        self.publish_target = publish_target
        self.live_visibility_mode = live_visibility_mode
        self.reserved_at = reserved_at
        self.published_at = published_at
        self.retired_at = retired_at
        self.created_at = now
        self.updated_at = now

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "template_id": self.template_id,
            "package_hash": self.package_hash,
            "factor_version_hash": self.factor_version_hash,
            "factor_sync_status": self.factor_sync_status,
            "research_snapshot_id": self.research_snapshot_id,
            "backtest_certificate_id": self.backtest_certificate_id,
            "risk_profile_hash": self.risk_profile_hash,
            "config_snapshot_ref": self.config_snapshot_ref,
            "lifecycle_status": self.lifecycle_status.value,
            "allowed_targets": self.allowed_targets,
            "publish_target": self.publish_target,
            "live_visibility_mode": self.live_visibility_mode,
            "reserved_at": self.reserved_at,
            "published_at": self.published_at,
            "retired_at": self.retired_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_contract_dict(self) -> dict:
        """返回面向 API 客户端的字典，lifecycle_status 使用契约规范值。

        内部流转请用 to_dict()；对外 API 响应必须用此方法，
        以确保状态字段与 shared/contracts/decision/strategy_package.md §3 一致。
        """
        d = self.to_dict()
        d["lifecycle_status"] = to_contract_state(self.lifecycle_status)
        return d


class StrategyRepository:
    def __init__(self) -> None:
        self._store: dict[str, StrategyPackage] = {}

    def create(self, pkg: StrategyPackage) -> StrategyPackage:
        self._store[pkg.strategy_id] = pkg
        return pkg

    def get(self, strategy_id: str) -> Optional[StrategyPackage]:
        return self._store.get(strategy_id)

    def list_all(self) -> list[StrategyPackage]:
        return list(self._store.values())

    def update(self, strategy_id: str, updates: dict) -> Optional[StrategyPackage]:
        pkg = self._store.get(strategy_id)
        if pkg is None:
            return None
        for key, value in updates.items():
            if hasattr(pkg, key):
                setattr(pkg, key, value)
        pkg.updated_at = datetime.now(timezone.utc).isoformat()
        return pkg

    def delete(self, strategy_id: str) -> bool:
        if strategy_id in self._store:
            del self._store[strategy_id]
            return True
        return False

    def transition_lifecycle(
        self, strategy_id: str, target: LifecycleStatus
    ) -> Optional[StrategyPackage]:
        pkg = self._store.get(strategy_id)
        if pkg is None:
            return None
        pkg.lifecycle_status = transition(pkg.lifecycle_status, target)
        pkg.updated_at = datetime.now(timezone.utc).isoformat()
        return pkg

    def list_by_status(self, status: LifecycleStatus) -> list[StrategyPackage]:
        return [p for p in self._store.values() if p.lifecycle_status == status]


_repository = StrategyRepository()


def get_repository() -> StrategyRepository:
    return _repository
