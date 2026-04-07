"""
Legacy BotQuant 字段名到 JBT 契约字段名的映射层（只读适配）。

禁止：引入 legacy 的交易/回测/订单逻辑，禁止 import services/** 代码。
"""

from __future__ import annotations

from typing import Any


# 策略字段映射表：legacy 字段名 → JBT 契约字段名
STRATEGY_FIELD_MAP: dict[str, str] = {
    "strategy_id": "strategy_id",
    "strategy_name": "strategy_id",   # legacy 可能用 name 代替 id
    "name": "strategy_id",
    "version": "strategy_version",
    "strategy_version": "strategy_version",
    "status": "status",
    "symbol": "symbol",
    "instrument": "symbol",           # legacy 别名
    "code": "symbol",
}

# 信号字段映射表：legacy 字段名 → JBT 契约字段名
SIGNAL_FIELD_MAP: dict[str, str] = {
    "signal_type": "signal_type",
    "direction": "signal_type",       # legacy 可能用 direction 表达方向
    "signal": "signal_type",
    "strength": "signal_strength",
    "signal_strength": "signal_strength",
    "confidence": "signal_strength",  # legacy 置信度 → JBT signal_strength
    "factor_values": "factors",
    "factor_value": "factors",
    "factors": "factors",
}


class LegacyInputMapper:
    """Legacy BotQuant 字段名映射器（只读）。"""

    @staticmethod
    def map_strategy_fields(raw: dict[str, Any]) -> dict[str, Any]:
        """将 legacy 策略字段名映射为 JBT 契约字段名。

        Args:
            raw: legacy 策略 dict（来源于 legacy BotQuant JSON/数据库读取）。

        Returns:
            字段名已重命名的 JBT 口径 dict；未在映射表中的字段原样保留。
            若多个 legacy 字段映射到同一目标键，先出现的优先。
        """
        result: dict[str, Any] = {}
        for key, value in raw.items():
            mapped_key = STRATEGY_FIELD_MAP.get(key, key)
            if mapped_key not in result:
                result[mapped_key] = value
        return result

    @staticmethod
    def map_signal_fields(raw: dict[str, Any]) -> dict[str, Any]:
        """将 legacy 信号字段名映射为 JBT 契约字段名。

        Args:
            raw: legacy 信号 dict。

        Returns:
            字段名已重命名的 JBT 口径 dict；未在映射表中的字段原样保留。
            若多个 legacy 字段映射到同一目标键，先出现的优先。
        """
        result: dict[str, Any] = {}
        for key, value in raw.items():
            mapped_key = SIGNAL_FIELD_MAP.get(key, key)
            if mapped_key not in result:
                result[mapped_key] = value
        return result
