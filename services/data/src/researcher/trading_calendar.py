"""中国期货 / A 股市场交易日历

规则：
- 周六、周日：非交易日（除非在 COMPENSATORY_WORKDAYS 中列为调休补班）
- 法定节假日中的工作日：非交易日（列于 HOLIDAYS）
- 其余工作日（周一至周五）：交易日

注意：
- 每年年初根据国务院《节假日安排通知》更新 HOLIDAYS_XXXX 和 COMPENSATORY_WORKDAYS_XXXX
- 夜盘判断：用 has_night_session_tomorrow() 判断次日是否开夜盘
  （若次日为节假日或周六，通常无夜盘；若次日为调休工作日或普通交易日，有夜盘）
- 期货调休补班日：期货交易所通常**不在调休补班日开市**（与 A 股不同），
  因此 COMPENSATORY_WORKDAYS 默认为空集合；如交易所另行公告，可手动添加。

更新记录：
  2026-04-18  初版，覆盖 2026 全年
"""

from datetime import date, datetime, timedelta
from typing import Union

# ──────────────────────────────────────────────────────────────────────────────
# 2026 年节假日
# 仅列**工作日**中因节假日调休导致的休市日（周末本身由 weekday 判断处理）
# ──────────────────────────────────────────────────────────────────────────────
HOLIDAYS_2026: set = {
    # 元旦 2026-01-01（周四）
    "2026-01-01",
    "2026-01-02",  # 周五（若官方调休延长，请核实）

    # 春节 2026-02-17（正月初一，周二）
    # 含除夕 02-16 至初七 02-23，周末已处理，仅列工作日
    "2026-02-16",  # 周一（除夕）
    "2026-02-17",  # 周二（初一）
    "2026-02-18",  # 周三（初二）
    "2026-02-19",  # 周四（初三）
    "2026-02-20",  # 周五（初四）
    "2026-02-23",  # 周一（初七，若为调休休市请核实）

    # 清明节 2026-04-05（周日）→ 04-06 周一补休
    "2026-04-06",  # 周一

    # 劳动节 2026-05-01（周五）
    "2026-05-01",  # 周五
    "2026-05-04",  # 周一（调休）
    "2026-05-05",  # 周二（调休，若官方安排如此）

    # 端午节 2026-06-19（周五）
    "2026-06-19",  # 周五
    "2026-06-22",  # 周一（若调休，请核实）

    # 中秋节（具体日期待国务院公告确认）
    # 占位：如 "2026-09-24", "2026-09-25"

    # 国庆节 2026-10-01（周四）至 10-07（周三）
    "2026-10-01",  # 周四
    "2026-10-02",  # 周五
    "2026-10-05",  # 周一
    "2026-10-06",  # 周二
    "2026-10-07",  # 周三
    "2026-10-08",  # 周四（若调休延长，请核实）
}

# ──────────────────────────────────────────────────────────────────────────────
# 2026 年调休工作日（周末变交易日）
# 期货市场调休补班日通常**不开市**，默认留空；如交易所公告开市则在此添加
# ──────────────────────────────────────────────────────────────────────────────
COMPENSATORY_WORKDAYS_2026: set = {
    # 示例（请以交易所公告为准）：
    # "2026-02-14",  # 周六，春节前调休补班（期货通常不开）
}


def _get_calendar(year: int) -> tuple:
    """返回对应年份的 (HOLIDAYS, COMPENSATORY_WORKDAYS)，目前仅内置 2026。"""
    if year == 2026:
        return HOLIDAYS_2026, COMPENSATORY_WORKDAYS_2026
    # 其他年份：仅依赖周末判断，无法处理节假日
    return set(), set()


def is_trading_day(dt: Union[date, datetime, None] = None) -> bool:
    """
    判断给定日期是否为交易日（中国期货 / A 股市场）。

    Args:
        dt: 日期或 datetime，默认为今天。

    Returns:
        True  — 交易日（可以开盘交易）
        False — 非交易日（周末或节假日）
    """
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt

    date_str = d.strftime("%Y-%m-%d")
    holidays, comp_workdays = _get_calendar(d.year)

    # 调休工作日（优先判断，周末也可能开市）
    if date_str in comp_workdays:
        return True

    # 周末
    if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False

    # 节假日（工作日中的休市）
    if date_str in holidays:
        return False

    return True


def is_trading_day_today() -> bool:
    """判断今天是否为交易日（快捷函数）。"""
    return is_trading_day(datetime.now())


def next_trading_day(dt: Union[date, datetime, None] = None) -> date:
    """返回给定日期之后（不含当天）的下一个交易日。"""
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt
    candidate = d + timedelta(days=1)
    for _ in range(30):  # 最多往后找 30 天（防死循环）
        if is_trading_day(candidate):
            return candidate
        candidate += timedelta(days=1)
    raise RuntimeError("未能在 30 天内找到下一个交易日，请检查日历配置")


def has_night_session(dt: Union[date, datetime, None] = None) -> bool:
    """
    判断给定日期是否有夜盘。

    规则：夜盘属于"当晚开盘，次日凌晨收盘"，因此：
    - 若**明天**是交易日 → 今晚有夜盘
    - 若明天是节假日或周末（且非调休补班）→ 今晚无夜盘

    例：周五晚上没有夜盘（周六休市），节假日前一天晚上没有夜盘。
    """
    if dt is None:
        dt = datetime.now()
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt
    tomorrow = d + timedelta(days=1)
    return is_trading_day(tomorrow)
