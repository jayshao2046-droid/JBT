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
    """风控守卫 — 三类核心钩子：只减仓、灾难止损、告警通道。"""

    def check_reduce_only(self, order: dict, current_positions: list) -> bool:
        """
        只减仓模式检查。
        当账户处于 reduce_only 状态时，禁止新开仓。
        返回 True 表示该订单允许通过（减仓方向），False 表示拒绝（开仓方向）。

        CTP offset 映射：'0'=开仓, '1'=平仓, '3'=平今
        """
        offset = str(order.get("offset", "")).strip()

        # 开仓指令 → 拒绝
        if offset == "0":
            instrument = order.get("instrument_id", "")
            self.emit_alert("P1", f"只减仓模式：拒绝开仓指令 {instrument}", {
                "event_code": "RISK_REDUCE_ONLY_REJECT",
                "symbol": instrument,
                "source": "risk_guard",
            })
            return False

        # 平仓 / 平今 → 允许
        return True

    def check_disaster_stop(self, account_summary: dict) -> bool:
        """
        灾难止损检查。
        当净值回撤超过 RISK_NAV_DRAWDOWN_HALT 阈值时，触发全停。
        返回 True 表示系统可继续运行，False 表示触发熔断全停。
        """
        threshold = float(os.getenv("RISK_NAV_DRAWDOWN_HALT", "0.10"))

        balance = account_summary.get("balance", 0) or 0
        pre_balance = account_summary.get("pre_balance", 0) or 0

        if pre_balance <= 0:
            return True

        drawdown = (pre_balance - balance) / pre_balance

        if drawdown >= threshold:
            self.emit_alert("P0", f"灾难止损触发：回撤 {drawdown:.2%} ≥ 阈值 {threshold:.2%}", {
                "event_code": "RISK_DISASTER_STOP",
                "symbol": "",
                "source": "risk_guard",
            })
            return False

        return True

    def emit_alert(self, level: str, message: str, context: dict = None) -> None:
        """
        风控告警通道。
        level: 'P0' | 'P1' | 'P2'
        """
        return emit_alert(level, message, context)
