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

import enum
import os
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Iterable


# 环境变量: YYYY-MM-DD,YYYY-MM-DD（逗号分隔，追加到内置数据之上）
ENV_CN_HOLIDAYS = "JBT_CN_HOLIDAYS"
ENV_US_HOLIDAYS = "JBT_US_HOLIDAYS"
ENV_LME_HOLIDAYS = "JBT_LME_HOLIDAYS"
# 环境变量: start|end|reason;start|end|reason
# 例: 2026-04-08 10:15|2026-04-08 10:35|系统修盘
ENV_MAINTENANCE_WINDOWS = "JBT_MAINTENANCE_WINDOWS"


# ══════════════════════════════════════════════════════════════
# 市场类型枚举（以 CST 为基准时区）
# ══════════════════════════════════════════════════════════════

class MarketType(str, enum.Enum):
    """全球金融市场类型。所有开收盘时间均以 CST (UTC+8) 表达。"""
    CN_FUTURES = "cn_futures"  # 国内期货 (SHFE/DCE/CZCE/CFFEX)
    CN_STOCKS  = "cn_stocks"   # A股 (SSE/SZSE)
    NYSE       = "nyse"        # 纽交所 / 纳斯达克
    CME        = "cme"         # 芝商所期货 (近 24/5)
    LME        = "lme"         # 伦敦金属交易所
    FOREX      = "forex"       # 外汇市场 (24/5)
    ALWAYS     = "always"      # 不受市场日历控制


# ══════════════════════════════════════════════════════════════
# 内置节假日数据（YYYY-MM-DD，CST 本地日期）
# 2026/2027 年数据基于农历估算；以国务院官方公告为准，可通过环境变量追加修正。
# ══════════════════════════════════════════════════════════════

# ── 中国 A 股 / 期货（SSE / SZSE 官方停盘日）────────────────────
_CN_HOLIDAYS_BUILTIN: frozenset[str] = frozenset({
    # ── 2024 ──
    "2024-01-01",
    "2024-02-08", "2024-02-09", "2024-02-10", "2024-02-11",  # 春节 (CNY=Feb10)
    "2024-02-12", "2024-02-13", "2024-02-14",
    "2024-04-04", "2024-04-05", "2024-04-06",                # 清明
    "2024-05-01", "2024-05-02", "2024-05-03",                # 劳动节
    "2024-06-08", "2024-06-09", "2024-06-10",                # 端午
    "2024-09-16", "2024-09-17",                              # 中秋
    "2024-10-01", "2024-10-02", "2024-10-03", "2024-10-04",  # 国庆
    "2024-10-07",
    # ── 2025 (官方公布) ──
    "2025-01-01",
    "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",  # 春节 (CNY=Jan29)
    "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04",
    "2025-04-04", "2025-04-05", "2025-04-06",                # 清明
    "2025-05-01", "2025-05-02", "2025-05-05",                # 劳动节 (May4=Sun→May5补休)
    "2025-05-31", "2025-06-01", "2025-06-02",                # 端午
    "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-04",  # 国庆 + 中秋
    "2025-10-05", "2025-10-06", "2025-10-07", "2025-10-08",
    # ── 2026 (估算, CNY=Feb17) ──
    "2026-01-01",
    "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19",  # 春节
    "2026-02-20", "2026-02-21", "2026-02-22",
    "2026-04-04", "2026-04-05", "2026-04-06",                # 清明
    "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04",  # 劳动节
    "2026-05-05",
    "2026-06-19", "2026-06-20", "2026-06-21",                # 端午
    "2026-09-19", "2026-09-20", "2026-09-21",                # 中秋
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",  # 国庆
    "2026-10-05", "2026-10-06", "2026-10-07",
    # ── 2027 (估算, CNY=Feb6) ──
    "2027-01-01",
    "2027-02-05", "2027-02-06", "2027-02-07", "2027-02-08",  # 春节
    "2027-02-09", "2027-02-10", "2027-02-11",
    "2027-04-04", "2027-04-05", "2027-04-06",                # 清明
    "2027-05-01", "2027-05-02", "2027-05-03", "2027-05-04",  # 劳动节
    "2027-05-05",
    "2027-05-28", "2027-05-29", "2027-05-30",                # 端午 (估算)
    "2027-09-18", "2027-09-19", "2027-09-20",                # 中秋 (估算)
    "2027-10-01", "2027-10-02", "2027-10-03", "2027-10-04",  # 国庆
    "2027-10-05", "2027-10-06", "2027-10-07",
})

# ── 美国 NYSE / NASDAQ / CME 节假日 ─────────────────────────────
_US_HOLIDAYS_BUILTIN: frozenset[str] = frozenset({
    # ── 2024 ──
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29",
    "2024-05-27", "2024-06-19", "2024-07-04", "2024-09-02",
    "2024-11-28", "2024-12-25",
    # ── 2025 ──
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18",
    "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01",
    "2025-11-27", "2025-12-25",
    # ── 2026 ──
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-06-19",
    "2026-07-03",                                            # Independence Day (Jul4=Sat, observed Jul3)
    "2026-09-07", "2026-11-26", "2026-12-25",
    # ── 2027 ──
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
    "2027-05-31",
    "2027-06-18",                                            # Juneteenth (Jun19=Sat, observed Jun18)
    "2027-07-05",                                            # Independence Day (Jul4=Sun, observed Jul5)
    "2027-09-06", "2027-11-25",
    "2027-12-24",                                            # Christmas (Dec25=Sat, observed Dec24)
})

# ── 英国 LME 银行假日 ────────────────────────────────────────────
_LME_HOLIDAYS_BUILTIN: frozenset[str] = frozenset({
    # ── 2024 ──
    "2024-01-01", "2024-03-29", "2024-04-01",
    "2024-05-06", "2024-05-27", "2024-08-26",
    "2024-12-25", "2024-12-26",
    # ── 2025 ──
    "2025-01-01", "2025-04-18", "2025-04-21",
    "2025-05-05", "2025-05-26", "2025-08-25",
    "2025-12-25", "2025-12-26",
    # ── 2026 ──
    "2026-01-01", "2026-04-03", "2026-04-06",
    "2026-05-04", "2026-05-25", "2026-08-31",
    "2026-12-25", "2026-12-28",                              # Boxing Day (observed)
    # ── 2027 ──
    "2027-01-01", "2027-03-26", "2027-03-29",
    "2027-05-03", "2027-05-31", "2027-08-30",
    "2027-12-27", "2027-12-28",                              # Christmas/Boxing (observed)
})


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
    # 全球市场扩展字段（含默认值，向下兼容）
    nyse:  SessionState = field(default_factory=lambda: SessionState(False, "未采集"))
    cme:   SessionState = field(default_factory=lambda: SessionState(False, "未采集"))
    lme:   SessionState = field(default_factory=lambda: SessionState(False, "未采集"))
    forex: SessionState = field(default_factory=lambda: SessionState(False, "未采集"))


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
        # 仅周二至周五凌晨存在有效夜盘延续（对应前一日周一至周四夜盘）
        if wd not in (1, 2, 3, 4):
            return SessionState(False, "非夜盘延续时段")

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


# ══════════════════════════════════════════════════════════════
# NYSE / CME / LME / Forex session 函数（以 CST = UTC+8 为基准）
# ══════════════════════════════════════════════════════════════

def _nyse_session(now: datetime, us_holidays: set[str]) -> SessionState:
    """NYSE/NASDAQ 交易时段（CST）。
    EDT (3月第2周日–11月第1周日): 09:30-16:00 ET = 21:30-04:00 CST(次日)
    EST (11月第1周日–3月第2周日): 09:30-16:00 ET = 22:30-05:00 CST(次日)
    宽松覆盖: 21:00-05:30 CST，避免 DST 边界漏判。
    """
    wd = now.weekday()
    t = now.time()
    ds = now.strftime("%Y-%m-%d")

    if wd == 6:
        return SessionState(False, "周日休市")
    if wd == 5:
        return SessionState(False, "周六休市")

    # 凌晨 00:00-05:30 属于前一日延续
    if time(0, 0) <= t <= time(5, 30):
        if wd == 0:
            return SessionState(False, "周一凌晨(NYSE未开盘)")
        ref_ds = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        ref_wd = (now - timedelta(days=1)).weekday()
        if ref_wd >= 5:
            return SessionState(False, "周末休市")
        if _is_holiday(ref_ds, us_holidays):
            return SessionState(False, "美国假期休市")
        return SessionState(True, "NYSE收市前(CST凌晨)")

    # 晚间 21:00-23:59
    if t >= time(21, 0):
        if _is_holiday(ds, us_holidays):
            return SessionState(False, "美国假期休市")
        return SessionState(True, "NYSE开盘时段(CST晚)")

    return SessionState(False, "NYSE非交易时段")


def _cme_session(now: datetime, us_holidays: set[str]) -> SessionState:
    """CME 期货交易时段（CST）。
    近 24/5: 周一 07:00 – 周六 06:00 CST，每日 06:00-07:00 CST 维护窗口。
    """
    wd = now.weekday()
    t = now.time()

    if wd == 6:
        return SessionState(False, "周日休市")
    if wd == 5 and t >= time(6, 0):
        return SessionState(False, "周六休市")
    if wd == 0 and t < time(7, 0):
        return SessionState(False, "CME周一开盘前")
    if time(6, 0) <= t < time(7, 0):
        return SessionState(False, "CME每日维护窗口(06-07 CST)")

    ref_date = now if t >= time(7, 0) else now - timedelta(days=1)
    ref_ds = ref_date.strftime("%Y-%m-%d")
    ref_wd = ref_date.weekday()
    if ref_wd >= 5:
        return SessionState(False, "周末休市")
    if _is_holiday(ref_ds, us_holidays):
        return SessionState(False, "美国假期休市")
    return SessionState(True, "CME交易时段")


def _lme_session(now: datetime, lme_holidays: set[str]) -> SessionState:
    """LME 伦敦金属交易所交易时段（CST）。
    GMT (10月末周日–3月末周日): 11:40-17:00 London = 19:40-01:00 CST(次日)
    BST (3月末周日–10月末周日): 11:40-17:00 London = 18:40-00:00 CST(次日)
    宽松覆盖: 18:00-02:00 CST。
    """
    wd = now.weekday()
    t = now.time()

    if wd >= 5:
        return SessionState(False, "周末休市")

    # 凌晨 00:00-02:00 属于前一日延续
    if time(0, 0) <= t <= time(2, 0):
        if wd == 0:
            return SessionState(False, "周一凌晨(LME未开盘)")
        ref_ds = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        ref_wd = (now - timedelta(days=1)).weekday()
        if ref_wd >= 5:
            return SessionState(False, "周末休市")
        if _is_holiday(ref_ds, lme_holidays):
            return SessionState(False, "伦敦假期休市")
        return SessionState(True, "LME收市前(CST凌晨)")

    # 傍晚/夜间 18:00-23:59
    if t >= time(18, 0):
        ds = now.strftime("%Y-%m-%d")
        if _is_holiday(ds, lme_holidays):
            return SessionState(False, "伦敦假期休市")
        return SessionState(True, "LME电子盘交易时段(CST晚)")

    return SessionState(False, "LME非交易时段")


def _forex_session(now: datetime) -> SessionState:
    """外汇市场交易时段（CST，24/5）。
    周一 06:00 CST – 周六 06:00 CST 持续开盘，无节假日休市。
    """
    wd = now.weekday()
    t = now.time()

    if wd == 6:
        return SessionState(False, "外汇周末休市")
    if wd == 5 and t >= time(6, 0):
        return SessionState(False, "外汇周末休市")
    if wd == 0 and t < time(6, 0):
        return SessionState(False, "外汇周一开市前")
    return SessionState(True, "外汇交易时段(24/5)")


class GlobalTradingCalendar:
    """全球交易日历（可热更新：读取环境变量）。"""

    def __init__(self) -> None:
        self._reload()

    def _reload(self) -> None:
        # 内置节假日 + 环境变量追加（取并集）
        env_cn  = _parse_date_set(os.environ.get(ENV_CN_HOLIDAYS, ""))
        env_us  = _parse_date_set(os.environ.get(ENV_US_HOLIDAYS, ""))
        env_lme = _parse_date_set(os.environ.get(ENV_LME_HOLIDAYS, ""))
        self.cn_holidays  = _CN_HOLIDAYS_BUILTIN  | env_cn
        self.us_holidays  = _US_HOLIDAYS_BUILTIN  | env_us
        self.lme_holidays = _LME_HOLIDAYS_BUILTIN | env_lme
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
            return MarketSnapshot(
                futures_cn=closed, stocks_cn=closed, overseas=closed,
                nyse=closed, cme=closed, lme=closed, forex=closed,
            )

        futures_cn = _cn_futures_session(now, self.cn_holidays)
        stocks_cn  = _cn_stock_session(now, self.cn_holidays)
        overseas   = _overseas_session(now, self.us_holidays, self.lme_holidays)
        nyse       = _nyse_session(now, self.us_holidays)
        cme        = _cme_session(now, self.us_holidays)
        lme        = _lme_session(now, self.lme_holidays)
        forex      = _forex_session(now)
        return MarketSnapshot(
            futures_cn=futures_cn, stocks_cn=stocks_cn, overseas=overseas,
            nyse=nyse, cme=cme, lme=lme, forex=forex,
        )

    def is_market_open(self, market: MarketType, now: datetime | None = None) -> bool:
        """便捷方法：判断指定市场当前是否开市（以 CST 时间为准）。"""
        if market == MarketType.ALWAYS:
            return True
        snap = self.snapshot(now)
        mapping = {
            MarketType.CN_FUTURES: snap.futures_cn,
            MarketType.CN_STOCKS:  snap.stocks_cn,
            MarketType.NYSE:       snap.nyse,
            MarketType.CME:        snap.cme,
            MarketType.LME:        snap.lme,
            MarketType.FOREX:      snap.forex,
        }
        return mapping[market].is_open

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
        _cmp("A股",      prev.stocks_cn,  cur.stocks_cn)
        _cmp("外盘",     prev.overseas,   cur.overseas)
        _cmp("NYSE",     prev.nyse,       cur.nyse)
        _cmp("CME",      prev.cme,        cur.cme)
        _cmp("LME",      prev.lme,        cur.lme)
        _cmp("外汇",     prev.forex,      cur.forex)
        return out
