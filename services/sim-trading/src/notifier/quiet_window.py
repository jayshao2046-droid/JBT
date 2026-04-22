"""
quiet_window.py — TASK-NOTIFY-20260423-A
静默窗口工具：08:00–24:10（即 00:00–00:10 与 08:00–23:59）可推送，00:11–07:59 静默。
P0 / 成交回报 / 订单终态可穿透静默。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 中国标准时区（UTC+8）
CN_TZ = timezone(timedelta(hours=8))


def in_push_window(now: Optional[datetime] = None) -> bool:
    """
    判断当前是否在推送窗口内。
    推送窗口：08:00–23:59 或 00:00–00:10（即 24:00–24:10 延伸段）。
    静默时段：00:11–07:59。
    返回 True 表示当前可推送。
    """
    if now is None:
        now = datetime.now(CN_TZ)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=CN_TZ)

    # 换算成分钟数（0–1439）
    minutes = now.hour * 60 + now.minute
    # 可推送：480 分钟（08:00）到 1439 分钟（23:59），或 0–10 分钟（00:00–00:10）
    return minutes >= 480 or minutes <= 10


def should_bypass(*, level: str = "", category: str = "") -> bool:
    """
    判断事件是否应穿透静默窗口强制推送。
    P0 / 成交(TRADE) / 订单终态(ORDER) / 风控触发(RISK_LIMIT) 穿透静默。
    """
    if level == "P0":
        return True
    if category in ("TRADE", "ORDER", "RISK_LIMIT"):
        return True
    return False


def can_send(*, level: str = "", category: str = "", bypass: bool = False,
             now: Optional[datetime] = None) -> bool:
    """
    综合判断：是否应当发送通知。
    bypass=True 或 should_bypass 返回 True 时，忽略静默窗口。
    """
    if bypass or should_bypass(level=level, category=category):
        return True
    return in_push_window(now=now)
