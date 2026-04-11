"""
策略导入解析器 — TASK-0051 C0-3
解析并导入策略定义，提供内存存储与验证逻辑。
"""
from __future__ import annotations

import enum
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


class LifecycleStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    archived = "archived"


@dataclass
class StrategyPackage:
    strategy_id: str
    name: str
    symbol: str
    exchange: str
    direction: str = "long"
    entry_rules: Dict[str, Any] = field(default_factory=dict)
    exit_rules: Dict[str, Any] = field(default_factory=dict)
    risk_params: Dict[str, Any] = field(default_factory=dict)
    source_type: str = "manual"
    content: str = ""
    created_at: str = ""
    updated_at: str = ""
    lifecycle_status: LifecycleStatus = LifecycleStatus.draft


class StrategyRepository:
    """内存策略存储。"""

    def __init__(self) -> None:
        self._store: Dict[str, StrategyPackage] = {}

    def save(self, pkg: StrategyPackage) -> StrategyPackage:
        self._store[pkg.strategy_id] = pkg
        return pkg

    def get(self, strategy_id: str) -> Optional[StrategyPackage]:
        return self._store.get(strategy_id)

    def list_all(self) -> List[StrategyPackage]:
        return list(self._store.values())

    def delete(self, strategy_id: str) -> bool:
        if strategy_id in self._store:
            del self._store[strategy_id]
            return True
        return False

    def exists(self, strategy_id: str) -> bool:
        return strategy_id in self._store


# 模块级单例
_default_repo: Optional[StrategyRepository] = None


def get_import_repository() -> StrategyRepository:
    global _default_repo
    if _default_repo is None:
        _default_repo = StrategyRepository()
    return _default_repo


def reset_import_repository() -> None:
    """测试时重置单例。"""
    global _default_repo
    _default_repo = None


def _validate_strategy_schema(data: Dict[str, Any]) -> List[str]:
    """校验必填字段，返回错误列表。"""
    errors: List[str] = []
    for field_name in ("name", "symbol", "exchange"):
        value = data.get(field_name)
        if not value or not isinstance(value, str) or not value.strip():
            errors.append(f"缺少必填字段: {field_name}")
    name = data.get("name", "")
    if isinstance(name, str) and name.strip():
        if len(name.strip()) > 128:
            errors.append("策略名称长度不能超过 128 个字符")
    return errors


def _generate_strategy_id(name: str, symbol: str, exchange: str) -> str:
    """基于 name+symbol+exchange 生成确定性唯一 ID。"""
    raw = f"{name}:{symbol}:{exchange}"
    return "strat-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def import_strategy(
    data: Dict[str, Any],
    *,
    validate_only: bool = False,
    repo: Optional[StrategyRepository] = None,
) -> Dict[str, Any]:
    """
    导入策略主入口。

    Args:
        data: 策略数据字典。
        validate_only: 若为 True，仅验证不保存。
        repo: 可选的 StrategyRepository 实例。

    Returns:
        结果字典，包含 strategy_id / status / message / validation_errors / strategy_data。
    """
    repo = repo or get_import_repository()

    # 1. 验证
    errors = _validate_strategy_schema(data)
    if errors:
        return {
            "strategy_id": None,
            "status": "validation_failed",
            "message": "策略验证未通过",
            "validation_errors": errors,
            "strategy_data": None,
        }

    # 2. 生成 ID
    strategy_id = _generate_strategy_id(
        data["name"].strip(),
        data["symbol"].strip(),
        data["exchange"].strip(),
    )

    # 3. 仅验证模式
    if validate_only:
        return {
            "strategy_id": strategy_id,
            "status": "validated",
            "message": "策略验证通过（未保存）",
            "validation_errors": [],
            "strategy_data": None,
        }

    # 4. 检查重复
    if repo.exists(strategy_id):
        return {
            "strategy_id": strategy_id,
            "status": "conflict",
            "message": "策略已存在",
            "validation_errors": [],
            "strategy_data": None,
        }

    # 5. 构建并保存
    now = datetime.now(_TZ_CST).isoformat()
    pkg = StrategyPackage(
        strategy_id=strategy_id,
        name=data["name"].strip(),
        symbol=data["symbol"].strip(),
        exchange=data["exchange"].strip(),
        direction=data.get("direction", "long"),
        entry_rules=data.get("entry_rules") or {},
        exit_rules=data.get("exit_rules") or {},
        risk_params=data.get("risk_params") or {},
        source_type=data.get("source_type", "manual"),
        content=data.get("content", ""),
        created_at=now,
        updated_at=now,
        lifecycle_status=LifecycleStatus.draft,
    )
    repo.save(pkg)
    logger.info("策略已导入: %s (%s)", pkg.strategy_id, pkg.name)

    return {
        "strategy_id": strategy_id,
        "status": "imported",
        "message": "策略导入成功",
        "validation_errors": [],
        "strategy_data": {
            "strategy_id": pkg.strategy_id,
            "name": pkg.name,
            "symbol": pkg.symbol,
            "exchange": pkg.exchange,
            "direction": pkg.direction,
            "lifecycle_status": pkg.lifecycle_status.value,
            "created_at": pkg.created_at,
        },
    }
