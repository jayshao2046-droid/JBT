import enum
import logging
import os
from typing import Any, Mapping, Optional

from src.notifier.dispatcher import RiskEvent, SystemRiskState, get_dispatcher


logger = logging.getLogger(__name__)


class RiskEventCategory(str, enum.Enum):
    """风险事件分类枚举。"""
    CTP_CONNECTION = "CTP_CONNECTION"
    CTP_AUTH = "CTP_AUTH"
    CTP_TRADING = "CTP_TRADING"
    RISK_LIMIT = "RISK_LIMIT"
    SYSTEM = "SYSTEM"


_PREFIX_CATEGORY_MAP = {
    "CTP_CONN": RiskEventCategory.CTP_CONNECTION,
    "CTP_AUTH": RiskEventCategory.CTP_AUTH,
    "CTP_TRADE": RiskEventCategory.CTP_TRADING,
    "CTP_ORDER": RiskEventCategory.CTP_TRADING,
    "RISK": RiskEventCategory.RISK_LIMIT,
    "SYS": RiskEventCategory.SYSTEM,
}


def infer_category(event_code: str) -> RiskEventCategory:
    """根据 event_code 前缀推断 RiskEventCategory。"""
    upper = event_code.upper()
    for prefix, cat in _PREFIX_CATEGORY_MAP.items():
        if upper.startswith(prefix):
            return cat
    return RiskEventCategory.SYSTEM


def _normalize_level(level: str) -> str:
    normalized = str(level or "P1").strip().upper()
    if normalized in {"P0", "P1", "P2"}:
        return normalized
    logger.warning("Unknown risk level '%s', fallback to P1", level)
    return "P1"


def _context_to_mapping(context: Optional[dict]) -> Mapping[str, Any]:
    if isinstance(context, dict):
        return context
    return {}


def _string_value(context: Mapping[str, Any], key: str, default: str = "") -> str:
    value = context.get(key, default)
    if value is None:
        return default
    return str(value)


def _resolve_stage_preset(context: Mapping[str, Any]) -> str:
    raw = context.get("stage_preset") or os.getenv("STAGE", "sim") or "sim"
    return str(raw).strip().lower() or "sim"


def emit_alert(level: str, message: str, context: dict = None) -> Optional[SystemRiskState]:
    """将最小风险事件映射到 dispatcher；未 bootstrap 时安全跳过。"""
    payload = _context_to_mapping(context)
    dispatcher = get_dispatcher()
    if dispatcher is None:
        logger.warning("Notifier dispatcher is not configured, skip risk alert: %s", message)
        return None

    event_code = _string_value(payload, "event_code", "RISK_ALERT")
    category = infer_category(event_code)

    event = RiskEvent(
        task_id=_string_value(payload, "task_id", "TASK-0014"),
        stage_preset=_resolve_stage_preset(payload),
        risk_level=_normalize_level(level),
        account_id=_string_value(payload, "account_id"),
        strategy_id=_string_value(payload, "strategy_id"),
        symbol=_string_value(payload, "symbol"),
        signal_id=_string_value(payload, "signal_id"),
        trace_id=_string_value(payload, "trace_id"),
        event_code=event_code,
        reason=str(message),
        source=_string_value(payload, "source", "risk_guard"),
        category=category.value,
    )
    return dispatcher.dispatch(event)


class RiskGuards:
    """风控守卫骨架。三类核心钩子占位，真实逻辑待 TASK-0013 统一补充。"""

    def check_reduce_only(self, order: dict, current_positions: list) -> bool:
        """
        只减仓模式检查。
        当账户处于 reduce_only 状态时，禁止新开仓。
        返回 True 表示该订单允许通过（减仓方向），False 表示拒绝（开仓方向）。
        # TODO: 实现 reduce_only 状态检测与方向判断
        """
        raise NotImplementedError("reduce_only hook not yet implemented")

    def check_disaster_stop(self, account_summary: dict) -> bool:
        """
        灾难止损检查。
        当净值回撤超过 RISK_NAV_DRAWDOWN_HALT 阈值时，触发全停。
        返回 True 表示系统可继续运行，False 表示触发熔断全停。
        # TODO: 实现净值回撤计算与熔断判定
        """
        raise NotImplementedError("disaster_stop hook not yet implemented")

    def emit_alert(self, level: str, message: str, context: dict = None) -> None:
        """
        风控告警通道。
        level: 'P0' | 'P1' | 'P2'
        """
        return emit_alert(level, message, context)
