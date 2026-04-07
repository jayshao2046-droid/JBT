"""
Legacy BotQuant 信号类型到 JBT 信号类型的兼容转换层（只读适配）。

禁止：引入 legacy 的交易/回测/订单逻辑，禁止 import services/** 代码。
"""

from __future__ import annotations


# Legacy → JBT 信号类型映射表（常量，不硬编码在方法体内）
SIGNAL_TYPE_MAP: dict[str, str] = {
    "BUY": "long",
    "SELL": "short",
    "HOLD": "neutral",
    "LONG": "long",
    "SHORT": "short",
    "NEUTRAL": "neutral",
    "OPEN_LONG": "long",
    "OPEN_SHORT": "short",
    "CLOSE": "neutral",
    "EXIT": "neutral",
}

# JBT 信号类型 → 整数方向（契约 signal 字段）
SIGNAL_DIRECTION_MAP: dict[str, int] = {
    "long": 1,
    "short": -1,
    "neutral": 0,
}


class LegacySignalCompat:
    """Legacy BotQuant 信号兼容转换工具（只读）。"""

    @staticmethod
    def normalize_signal_type(legacy_type: str) -> str:
        """将 legacy 信号类型字符串规范化为 JBT 标准字符串。

        Args:
            legacy_type: legacy 侧信号类型字符串，大小写不敏感。

        Returns:
            JBT 标准信号类型: "long" | "short" | "neutral"
            未知类型默认降级为 "neutral"。
        """
        normalized = SIGNAL_TYPE_MAP.get(legacy_type.upper())
        if normalized is None:
            return "neutral"
        return normalized

    @staticmethod
    def normalize_signal_direction(jbt_signal_type: str) -> int:
        """将 JBT 信号类型转换为整数信号方向（契约 signal 字段）。

        Returns:
            1 (long) | -1 (short) | 0 (neutral/unknown)
        """
        return SIGNAL_DIRECTION_MAP.get(jbt_signal_type, 0)

    @staticmethod
    def is_valid_legacy_signal(raw: dict) -> bool:
        """验证 legacy 信号字典是否满足最低可用条件。

        最低条件：包含 signal_type 或 direction 字段之一，且非空字符串/非 None。

        Args:
            raw: 来自 legacy BotQuant 的信号字典。

        Returns:
            True 表示字段存在且有意义；False 表示无效或结构不符。
        """
        if not isinstance(raw, dict):
            return False
        has_signal_type = bool(raw.get("signal_type"))
        has_direction = raw.get("direction") is not None
        return has_signal_type or has_direction
