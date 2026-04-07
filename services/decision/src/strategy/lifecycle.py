from enum import Enum


class LifecycleStatus(str, Enum):
    imported = "imported"
    reserved = "reserved"
    researching = "researching"
    research_complete = "research_complete"
    backtest_confirmed = "backtest_confirmed"
    pending_execution = "pending_execution"
    in_production = "in_production"
    archived = "archived"


# ---------------------------------------------------------------------------
# 内部状态 vs 契约状态
# ---------------------------------------------------------------------------
# 内部枚举保持 8 个细粒度状态，用于 decision 内部状态机流转。
# 对外 API 响应必须使用契约规范值（shared/contracts/decision/strategy_package.md §3）。
# 三个终态名称在内部与契约间存在差异，通过下方映射层统一转换。
#   - pending_execution → publish_pending  （内部待发布 → 契约发布待定）
#   - in_production     → published        （内部生产中  → 契约已发布）
#   - archived          → retired          （内部已归档  → 契约已退役）
# 三个中间态（researching / research_complete / backtest_confirmed）契约允许透传，
# 不作为终态，后续可根据契约演进调整。
_INTERNAL_TO_CONTRACT: dict[str, str] = {
    "imported": "imported",
    "reserved": "reserved",
    "researching": "researching",
    "research_complete": "research_complete",
    "backtest_confirmed": "backtest_confirmed",
    "pending_execution": "publish_pending",
    "in_production": "published",
    "archived": "retired",
}


def to_contract_state(status: "LifecycleStatus") -> str:
    """将内部生命周期状态转换为契约规范值，用于所有 API 对外响应。

    内部状态（LifecycleStatus 枚举）提供细粒度流转控制；
    契约状态（返回字符串）是对下游服务和客户端暴露的规范值，
    定义于 shared/contracts/decision/strategy_package.md §3。
    """
    return _INTERNAL_TO_CONTRACT[status.value]


# Valid forward/backward transitions
_ALLOWED_TRANSITIONS: dict[LifecycleStatus, set[LifecycleStatus]] = {
    LifecycleStatus.imported: {LifecycleStatus.reserved, LifecycleStatus.researching, LifecycleStatus.archived},
    LifecycleStatus.reserved: {LifecycleStatus.researching, LifecycleStatus.archived},
    LifecycleStatus.researching: {LifecycleStatus.research_complete, LifecycleStatus.archived},
    LifecycleStatus.research_complete: {LifecycleStatus.backtest_confirmed, LifecycleStatus.archived},
    LifecycleStatus.backtest_confirmed: {LifecycleStatus.pending_execution, LifecycleStatus.archived},
    LifecycleStatus.pending_execution: {LifecycleStatus.in_production, LifecycleStatus.archived},
    LifecycleStatus.in_production: {LifecycleStatus.archived},
    LifecycleStatus.archived: set(),
}


def transition(current: LifecycleStatus, target: LifecycleStatus) -> LifecycleStatus:
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid lifecycle transition: {current.value} → {target.value}. "
            f"Allowed targets from {current.value}: {[s.value for s in allowed]}"
        )
    return target
