"""Global trading calendar helpers for JBT data scheduler.

目标：
1) 严格区分交易日 / 假期 / 修盘窗口
2) 为内盘、A股、外盘提供统一的开收盘判定
3) 提供“状态变更事件”以触发飞书提醒（开盘开始采集、休盘完成采集）

说明：
- 默认仅内置周末规则 + 可配置修盘窗口。
- 法定节假日与交易所休市可通过环境变量注入，便于每日更新。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Iterable


# 环境变量: YYYY-MM-DD,YYYY-MM-DD
ENV_CN_HOLIDAYS = "JBT_CN_HOLIDAYS"
ENV_US_HOLIDAYS = "JBT_US_HOLIDAYS"
ENV_LME_HOLIDAYS = "JBT_LME_HOLIDAYS"
# 环境变量: start|end|reason;start|end|reason
# 例: 2026-04-08 10:15|2026-04-08 10:35|系统修盘
ENV_MAINTENANCE_WINDOWS = "JBT_MAINTENANCE_WINDOWS"


@dataclass(frozen=True)
class SessionState:
    """一次时点判定结果。"""

    is_open: bool
    reason: str


@dataclass(frozen=True)
class MarketSnapshot:
    """市场状态快照，用于状态变更检测。"""

    futures_cn: SessionState
    stocks_cn: SessionState
    overseas: SessionState


@dataclass(frozen=True)
class StatusTransition:
    """状态变更信息。"""

    market: str
    from_open: bool
    to_open: bool
    reason: str


def _parse_date_set(raw: str) -> set[str]:
    return {x.strip() for x in raw.split(",") if x.strip()}


def _parse_windows(raw: str) -> list[tuple[datetime, datetime, str]]:
    items: list[tuple[datetime, datetime, str]] = []
    if not raw.strip():
        return items

    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split("|")]
        if len(parts) < 2:
            continue
        reason = parts[2] if len(parts) >= 3 else "维护窗口"
        try:
            start = datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
            end = datetime.strptime(parts[1], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if end <= start:
            continue
        items.append((start, end, reason))
    return items


def _in_maintenance(now: datetime, windows: Iterable[tuple[datetime, datetime, str]]) -> tuple[bool, str]:
    for start, end, reason in windows:
        if start <= now <= end:
            return True, reason
    return False, ""


def _is_holiday(date_str: str, holiday_set: set[str]) -> bool:
    return date_str in holiday_set


def _in_any(t: time, ranges: list[tuple[time, time]]) -> bool:
    for s, e in ranges:
        if s <= t <= e:
            return True
    return False


def _cn_futures_session(now: datetime, cn_holidays: set[str]) -> SessionState:
    ds = now.strftime("%Y-%m-%d")
    wd = now.weekday()

    t = now.time()
    day_ranges = [(time(9, 0), time(11, 30)), (time(13, 30), time(15, 0))]
    night_ranges = [(time(21, 0), time(23, 59)), (time(0, 0), time(2, 30))]

    # 周一凌晨 00:00-02:30 并非有效夜盘延续（周日夜盘不开盘）
    if wd == 0 and time(0, 0) <= t <= time(2, 30):
        return SessionState(False, "周一凌晨休市")

    # 凌晨夜盘延续（00:00-02:30）按“前一自然日”判断是否交易日/假期
    if time(0, 0) <= t <= time(2, 30):
        ref = now - timedelta(days=1)
        ref_ds = ref.strftime("%Y-%m-%d")
        ref_wd = ref.weekday()
        if ref_wd >= 5:
            return SessionState(False, "前一交易日为周末")
        if _is_holiday(ref_ds, cn_holidays):
            return SessionState(False, "前一交易日假期休市")
        return SessionState(True, "夜盘延续时段")

    # 白天与晚盘（21:00-23:59）按“当天”判断交易日/假期
    if wd >= 5:
        return SessionState(False, "周末休市")
    if _is_holiday(ds, cn_holidays):
        return SessionState(False, "国内假期休市")

    if _in_any(t, day_ranges):
        return SessionState(True, "日盘交易时段")
    if _in_any(t, night_ranges):
        # 周五晚 21:00 不开夜盘，周五凌晨 00:00-02:30 允许（周四夜盘延续）
        if wd == 4 and time(21, 0) <= t <= time(23, 59):
            return SessionState(False, "周五夜盘休市")
        return SessionState(True, "夜盘交易时段")

    return SessionState(False, "非交易时段")


def _cn_stock_session(now: datetime, cn_holidays: set[str]) -> SessionState:
    ds = now.strftime("%Y-%m-%d")
    wd = now.weekday()
    if wd >= 5:
        return SessionState(False, "周末休市")
    if _is_holiday(ds, cn_holidays):
        return SessionState(False, "国内假期休市")

    t = now.time()
    ranges = [(time(9, 30), time(11, 30)), (time(13, 0), time(15, 0))]
    if _in_any(t, ranges):
        return SessionState(True, "A股交易时段")
    return SessionState(False, "非交易时段")


def _overseas_session(now: datetime, us_holidays: set[str], lme_holidays: set[str]) -> SessionState:
    # 统一用“可采集时段”定义：周一 07:00 至 周六 06:00，北京时间
    wd = now.weekday()
    t = now.time()

    # 周日全天休市
    if wd == 6:
        return SessionState(False, "周日休市")

    # 周一 07:00 前不开
    if wd == 0 and t < time(7, 0):
        return SessionState(False, "周一开盘前")

    # 周六 06:00 后不开
    if wd == 5 and t >= time(6, 0):
        return SessionState(False, "周末休市")

    # 假期判断：凌晨窗口归属前一交易日（避免假期跨日误开盘）
    # 示例：周一假期时，周二 01:00 应仍视作休市。
    ref_date = now
    if t < time(7, 0):
        ref_date = now - timedelta(days=1)
    ref_ds = ref_date.strftime("%Y-%m-%d")

    if _is_holiday(ref_ds, us_holidays):
        return SessionState(False, "美国假期休市")
    if _is_holiday(ref_ds, lme_holidays):
        return SessionState(False, "伦敦假期休市")

    return SessionState(True, "外盘交易时段")


class GlobalTradingCalendar:
    """全球交易日历（可热更新：读取环境变量）。"""

    def __init__(self) -> None:
        self._reload()

    def _reload(self) -> None:
        self.cn_holidays = _parse_date_set(os.environ.get(ENV_CN_HOLIDAYS, ""))
        self.us_holidays = _parse_date_set(os.environ.get(ENV_US_HOLIDAYS, ""))
        self.lme_holidays = _parse_date_set(os.environ.get(ENV_LME_HOLIDAYS, ""))
        self.windows = _parse_windows(os.environ.get(ENV_MAINTENANCE_WINDOWS, ""))

    def refresh(self) -> None:
        self._reload()

    def is_maintenance(self, now: datetime | None = None) -> tuple[bool, str]:
        now = now or datetime.now()
        return _in_maintenance(now, self.windows)

    def is_cn_trading_day(self, now: datetime | None = None) -> tuple[bool, str]:
        now = now or datetime.now()
        in_maint, maint_reason = self.is_maintenance(now)
        if in_maint:
            return False, f"维护中: {maint_reason}"

        ds = now.strftime("%Y-%m-%d")
        wd = now.weekday()
        if wd >= 5:
            return False, "周末休市"
        if _is_holiday(ds, self.cn_holidays):
            return False, "国内假期休市"
        return True, "交易日"

    def is_us_trading_day(self, now: datetime | None = None) -> tuple[bool, str]:
        now = now or datetime.now()
        in_maint, maint_reason = self.is_maintenance(now)
        if in_maint:
            return False, f"维护中: {maint_reason}"

        ds = now.strftime("%Y-%m-%d")
        wd = now.weekday()
        if wd >= 5:
            return False, "周末休市"
        if _is_holiday(ds, self.us_holidays):
            return False, "美国假期休市"
        return True, "交易日"

    def is_lme_trading_day(self, now: datetime | None = None) -> tuple[bool, str]:
        now = now or datetime.now()
        in_maint, maint_reason = self.is_maintenance(now)
        if in_maint:
            return False, f"维护中: {maint_reason}"

        ds = now.strftime("%Y-%m-%d")
        wd = now.weekday()
        if wd >= 5:
            return False, "周末休市"
        if _is_holiday(ds, self.lme_holidays):
            return False, "伦敦假期休市"
        return True, "交易日"

    def snapshot(self, now: datetime | None = None) -> MarketSnapshot:
        now = now or datetime.now()
        in_maint, maint_reason = _in_maintenance(now, self.windows)
        if in_maint:
            closed = SessionState(False, f"维护中: {maint_reason}")
            return MarketSnapshot(futures_cn=closed, stocks_cn=closed, overseas=closed)

        futures_cn = _cn_futures_session(now, self.cn_holidays)
        stocks_cn = _cn_stock_session(now, self.cn_holidays)
        overseas = _overseas_session(now, self.us_holidays, self.lme_holidays)
        return MarketSnapshot(futures_cn=futures_cn, stocks_cn=stocks_cn, overseas=overseas)

    def detect_transitions(
        self,
        prev: MarketSnapshot | None,
        cur: MarketSnapshot,
    ) -> list[StatusTransition]:
        if prev is None:
            return []

        out: list[StatusTransition] = []

        def _cmp(name: str, p: SessionState, c: SessionState) -> None:
            if p.is_open != c.is_open:
                out.append(
                    StatusTransition(
                        market=name,
                        from_open=p.is_open,
                        to_open=c.is_open,
                        reason=c.reason,
                    )
                )

        _cmp("内盘期货", prev.futures_cn, cur.futures_cn)
        _cmp("A股", prev.stocks_cn, cur.stocks_cn)
        _cmp("外盘", prev.overseas, cur.overseas)
        return out
