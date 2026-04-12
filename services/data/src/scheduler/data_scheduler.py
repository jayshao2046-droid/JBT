#!/usr/bin/env python3
"""
BotQuant 24h 数据调度主入口
===========================================
在 Mini 上以守护进程方式运行，按 cron 调度 11 个数据采集管道。

用法:
    python scripts/data_scheduler.py           # 前台运行
    python scripts/data_scheduler.py --daemon  # 守护进程（nohup 模式由 shell 脚本包装）

调度表:
    分钟内盘K线    每2分钟 (交易时段 9-11,13-15,21-23 周一到周五)
    日线K线        每日 17:00
    外盘K线        每日 17:00
    Tushare期货    每日 17:00
    宏观数据       每日 09:00
    持仓量/仓单    每日 15:30
    新闻API        每1分钟
    RSS聚合        每10分钟
    波动率         每日 17:00
    情绪指数       每5分钟
    海运物流       每日 09:00
    外汇日线       每日 17:20
    CFTC持仓报告   每周六 10:00
    期权行情       每日 15:30
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env (TUSHARE_TOKEN 等)
# PROJECT_ROOT = services/data/src/，.env 在 services/data/.env
_env_file = PROJECT_ROOT.parent / ".env"
if not _env_file.exists():
    _env_file = PROJECT_ROOT / ".env"  # fallback
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from services.data.src.utils.config import get_config
from services.data.src.utils.logger import get_logger
from services.data.src.utils.trading_calendar import GlobalTradingCalendar, MarketSnapshot

# ─────────────────────────────────────────────
# 全局状态
# ─────────────────────────────────────────────
_running = True
logger = get_logger("data_scheduler")
_notifier = None  # CollectionNotifier, 延迟初始化


def _get_notifier(config: dict[str, Any] | None = None) -> Any:
    """获取或初始化 CollectionNotifier (legacy, 已由 NotifierDispatcher 替代)."""
    return None


def get_factor_notifier() -> Any:
    """因子/信号通知器 — 通过 NotifierDispatcher 发送分时段报告到飞书。"""
    class _FactorNotifier:
        def send_session_summary(self, session: str) -> bool:
            try:
                from services.data.src.notify.dispatcher import (
                    DataEvent, NotifyType, get_dispatcher,
                )
                dispatcher = get_dispatcher()
                event = DataEvent(
                    event_code=f"factor_session_{session}",
                    notify_type=NotifyType.INFO,
                    title=f"因子/信号{session}报告",
                    body_md=f"**{session}因子扫描完成**\n数据端因子通知模块运行正常。",
                    source_name=f"factor_notifier:{session}",
                    channels={"feishu"},
                )
                return dispatcher.dispatch(event)
            except Exception as exc:
                logger.warning("因子通知发送失败: %s", exc)
                return False
    return _FactorNotifier()


def get_sla_tracker() -> Any:
    """SLA 追踪器 — 基于 health_check 的告警状态统计每日 SLA 报告。"""
    class _SlaTracker:
        def send_daily_sla_report(self) -> bool:
            try:
                from services.data.src.notify.dispatcher import (
                    DataEvent, NotifyType, get_dispatcher,
                )
                import json
                from pathlib import Path

                alarm_file = Path(os.environ.get("DATA_STORAGE_ROOT", os.path.expanduser("~/jbt-data"))) / "logs" / "collector_alarm_state.json"
                active_alarms = 0
                if alarm_file.exists():
                    try:
                        state = json.loads(alarm_file.read_text())
                        active_alarms = sum(1 for v in state.values() if isinstance(v, dict) and v.get("consecutive", 0) > 0)
                    except Exception:
                        pass

                status = "全部正常" if active_alarms == 0 else f"{active_alarms} 个采集源告警中"
                icon = "🟢" if active_alarms == 0 else "🔴"

                dispatcher = get_dispatcher()
                event = DataEvent(
                    event_code="sla_daily_report",
                    notify_type=NotifyType.INFO,
                    title=f"SLA 日报 — {icon} {status}",
                    body_md=f"**采集 SLA 日报**\n活跃告警: {active_alarms}\n状态: {status}",
                    source_name="sla_tracker:daily",
                    channels={"feishu"},
                    bypass_quiet_hours=True,
                )
                return dispatcher.dispatch(event)
            except Exception as exc:
                logger.warning("SLA 日报发送失败: %s", exc)
                return False

        def reset_daily(self) -> None:
            logger.info("SLA 计数器已重置（采集告警状态由 health_check 管理）")

    return _SlaTracker()


_dispatcher = None
# 24h 连续采集器不发启动/完成通知；外盘/国内分钟K线由自身 session 逻辑管理，不走 _safe_run 通知
_SILENT_COLLECTORS = {"新闻API", "RSS聚合", "飞书新闻推送", "情绪指数", "外盘分钟K线(yfinance)", "分钟内盘K线"}
_calendar = GlobalTradingCalendar()
_last_snapshot: MarketSnapshot | None = None
STOCK_MINUTE_ENABLED = False
NEWS_STORAGE_SYNC_LIMIT_PER_SOURCE = 5000

# ── 外盘分钟K线 session 跟踪（跨调度轮次持久化）─────────────────
_overseas_minute_session: dict[str, Any] = {
    "runs": 0,           # 本 session 总轮次
    "zero_runs": 0,      # 累计 0产出轮次
    "total_bars": 0,     # 累计 bar 数
    "consecutive_zeros": 0,  # 连续 0产出计数
    "alerted": False,    # 是否已发过连续0告警（防重复）
}

# ── 国内期货分钟K线 session 跟踪（日盘13:30-15:00 / 夜盘21:00-02:30）─────────────
_domestic_minute_session: dict[str, Any] = {
    "runs": 0,
    "zero_runs": 0,
    "total_bars": 0,
    "consecutive_zeros": 0,
    "alerted": False,
}


def _get_dispatcher() -> Any:
    """获取 NotifierDispatcher 单例。"""
    global _dispatcher
    if _dispatcher is None:
        try:
            from services.data.src.notify.dispatcher import get_dispatcher
            _dispatcher = get_dispatcher()
        except Exception as exc:
            logger.warning("NotifierDispatcher 初始化失败: %s", exc)
    return _dispatcher


def _extract_record_count(result: Any) -> int:
    """从采集返回值中提取记录数。"""
    if isinstance(result, dict):
        total = 0
        for value in result.values():
            if isinstance(value, (int, float)):
                total += int(value)
        return total
    if isinstance(result, (int, float)):
        return int(result)
    if isinstance(result, (list, tuple, set)):
        return len(result)
    return 0


def _enqueue_collection_result(
    dispatcher: Any,
    *,
    collector_name: str,
    record_count: int,
    elapsed_sec: float,
    status: str,
    error_msg: str = "",
) -> None:
    """将采集结果加入同窗摘要缓冲。"""
    if dispatcher is None:
        return

    enqueue = getattr(dispatcher, "record_collection_result", None)
    if not callable(enqueue):
        return

    enqueue(
        collector_name=collector_name,
        record_count=record_count,
        elapsed_sec=elapsed_sec,
        status=status,
        error_msg=error_msg,
    )


def _emit_market_transition_notifications() -> None:
    """检测开盘/休盘状态变更并推送飞书通知。

    规则：
    - 开盘：发送“开盘采集开始”
    - 休盘：发送“休盘完成采集”
    - 渠道：仅飞书（不发邮件）
    """
    global _last_snapshot

    d = _get_dispatcher()
    if not d:
        return

    try:
        from services.data.src.notify.dispatcher import DataEvent, NotifyType
        _calendar.refresh()
        cur = _calendar.snapshot(datetime.now())
        transitions = _calendar.detect_transitions(_last_snapshot, cur)

        for tr in transitions:
            if tr.to_open:
                title = f"{tr.market} 开盘采集开始"
                event_code = "market_session_open"
                body_rows = [
                    ("市场", tr.market),
                    ("状态", "开盘"),
                    ("动作", "启动分钟采集"),
                    ("原因", tr.reason),
                    ("时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                ]
            else:
                title = f"{tr.market} 休盘完成采集"
                event_code = "market_session_close"
                body_rows = [
                    ("市场", tr.market),
                    ("状态", "休盘"),
                    ("动作", "停止分钟采集，等待下一开盘"),
                    ("原因", tr.reason),
                    ("时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                ]

            d.dispatch(DataEvent(
                event_code=event_code,
                notify_type=NotifyType.NOTIFY,
                title=title,
                body_md=title,
                body_rows=body_rows,
                source_name=f"global_calendar:{tr.market}",
                channels={"feishu"},
                bypass_quiet_hours=True,
            ))

        _last_snapshot = cur
    except Exception as exc:
        logger.warning("市场状态提醒失败: %s", exc)


def _signal_handler(signum: int, frame: Any) -> None:
    """优雅退出信号处理。"""
    global _running
    logger.info("收到信号 %s，准备退出…", signum)
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


# ─────────────────────────────────────────────
# 调度器日志
# ─────────────────────────────────────────────
def _setup_scheduler_log() -> None:
    """额外添加 scheduler 专用日志文件输出。"""
    log_dir = Path(os.environ.get("DATA_STORAGE_ROOT", os.path.expanduser("~/jbt-data"))) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scheduler.log"

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger("data_scheduler").addHandler(fh)
    logger.info("调度日志 → %s", log_file)


# ─────────────────────────────────────────────
# 交易时段判断 (D107: 完善夜盘+外盘+A股)
# ─────────────────────────────────────────────
def _is_futures_day_session(now: datetime | None = None) -> bool:
    """国内期货日盘: 09:00-11:30, 13:30-15:00 (周一到周五)."""
    now = now or datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.hour * 60 + now.minute
    return (540 <= t <= 690) or (810 <= t <= 900)


def _is_futures_night_session(now: datetime | None = None) -> bool:
    """国内期货夜盘:
    - 21:00-23:00 (贵金属/有色/螺纹等)
    - 21:00-01:00 (铜/铝等)
    - 21:00-02:30 (原油/黄金等)
    采用宽泛时段 21:00-02:30 覆盖所有品种。
    注意: 周五夜盘不开盘。
    """
    now = now or datetime.now()
    t = now.hour * 60 + now.minute
    weekday = now.weekday()
    # 21:00-23:59 (周一到周四)
    if weekday <= 3 and 1260 <= t <= 1439:
        return True
    # 00:00-02:30 (周二到周五凌晨, 是前一天夜盘的延续)
    if 1 <= weekday <= 4 and 0 <= t <= 150:
        return True
    return False


def _is_trading_session(now: datetime | None = None) -> bool:
    """国内期货任意交易时段 (日盘+夜盘)."""
    now = now or datetime.now()
    _calendar.refresh()
    return _calendar.snapshot(now).futures_cn.is_open


def _is_stock_trading_session(now: datetime | None = None) -> bool:
    """A股交易时段: 09:30-11:30, 13:00-15:00 (周一到周五)."""
    now = now or datetime.now()
    _calendar.refresh()
    return _calendar.snapshot(now).stocks_cn.is_open


def _is_overseas_trading_hours(now: datetime | None = None) -> bool:
    """外盘主要交易时段 (北京时间, 覆盖美盘+欧盘):
    CME/COMEX/NYMEX: 06:00-05:00 (几乎24小时)
    ICE: 15:30-次日01:30
    CBOT: 08:00-02:20
    实际采用: 周一06:00 到 周六05:00 全时段采集。
    """
    now = now or datetime.now()
    _calendar.refresh()
    return _calendar.snapshot(now).overseas.is_open


# ─────────────────────────────────────────────
# 管道包装器（捕获异常）
# ─────────────────────────────────────────────
def _safe_run(name: str, func: Callable[..., Any], **kwargs: Any) -> None:
    """安全执行管道，捕获异常并记录日志 + 通知."""
    d = _get_dispatcher()
    silent = name in _SILENT_COLLECTORS

    # 发送启动通知（排除 24h 连续采集器）
    if d and not silent:
        try:
            from services.data.src.notify.dispatcher import DataEvent, NotifyType
            d.dispatch(DataEvent(
                event_code="collector_start",
                title=f"{name} 启动",
                notify_type=NotifyType.NOTIFY,
                body_md=f"{name} 启动",
                body_rows=[("采集器", name), ("启动时间", datetime.now().strftime("%H:%M:%S"))],
                source_name=name,
                channels={"feishu"},
            ))
        except Exception:
            pass

    try:
        logger.info("▶ 开始执行: %s", name)
        t0 = time.time()
        result = func(**kwargs)
        elapsed = round(time.time() - t0, 2)
        total = _extract_record_count(result)
        zero_output = total <= 0
        if zero_output:
            logger.warning("⚠️ %s 0产出: %d 条记录, 耗时 %ss", name, total, elapsed)
        else:
            logger.info("✅ %s 完成: %d 条记录, 耗时 %ss", name, total, elapsed)

        if not silent:
            _enqueue_collection_result(
                d,
                collector_name=name,
                record_count=total,
                elapsed_sec=elapsed,
                status="zero_output" if zero_output else "success",
            )

        # 记录到旧通知器
        n = _get_notifier(kwargs.get("config"))
        if n:
            n.record_result(
                name,
                records=total,
                elapsed=elapsed,
                success=not zero_output,
                error="zero_output" if zero_output else None,
            )
    except Exception:
        logger.error("❌ %s 失败:\n%s", name, traceback.format_exc())
        err_msg = traceback.format_exc()[-200:]

        # 发送失败告警（所有采集器都发）
        if d:
            try:
                from services.data.src.notify.dispatcher import DataEvent, NotifyType
                d.dispatch(DataEvent(
                    event_code="collector_failed",
                    title=f"{name} 采集失败",
                    notify_type=NotifyType.P2,
                    body_md=f"{name} 采集失败",
                    body_rows=[("采集器", name), ("错误", err_msg)],
                    source_name=name,
                    channels={"feishu", "email"},
                ))
            except Exception:
                pass

        if not silent:
            _enqueue_collection_result(
                d,
                collector_name=name,
                record_count=0,
                elapsed_sec=0,
                status="failed",
                error_msg=err_msg,
            )

        n = _get_notifier(kwargs.get("config"))
        if n:
            n.record_result(name, records=0, elapsed=0, success=False, error=err_msg)


# ─────────────────────────────────────────────
# 管道任务定义
# ─────────────────────────────────────────────
def _get_domestic_symbols() -> list[str]:
    """获取内盘全量 35 品种合约列表（主力+次主力，动态维护）。

    覆盖 35 个品种，每品种取 2 个活跃合约（近月+次主力），合计约 70 个合约。

    合约代码格式：
      SHFE/DCE  4位年月格式：rb2605 = 螺纹钢 2026年5月
      CZCE      3位格式：MA605 = 甲醇 2026年5月（年末尾数字 + 两位月份）

    35 品种（按交易所分组）：
      SHFE: rb(螺纹钢), hc(热卷), cu(铜), al(铝), zn(锌), au(黄金), ag(白银),
            ru(橡胶), ss(不锈钢), sp(纸浆)
      DCE:  i(铁矿石), m(豆粕), pp(聚丙烯), v(PVC), l(塑料), c(玉米), jd(鸡蛋),
            y(豆油), p(棕榈油), a(豆一), jm(焦煤), j(焦炭), eb(苯乙烯),
            pg(液化气), lh(生猪)
      CZCE: TA(PTA), MA(甲醇), CF(棉花), SR(白糖), OI(菜油), RM(菜粕),
            FG(玻璃), SA(纯碱), PF(短纤), UR(尿素)
    """
    return [
        # ── SHFE 上期所（10品种）────────────────────────────────────
        "SHFE.rb2605", "SHFE.rb2610",      # 螺纹钢
        "SHFE.hc2605", "SHFE.hc2610",      # 热卷板
        "SHFE.cu2605", "SHFE.cu2606",      # 铜
        "SHFE.al2605", "SHFE.al2606",      # 铝（新增）
        "SHFE.zn2605", "SHFE.zn2606",      # 锌（新增）
        "SHFE.au2606", "SHFE.au2612",      # 黄金（双月合约）
        "SHFE.ag2606", "SHFE.ag2612",      # 白银（双月合约）
        "SHFE.ru2605", "SHFE.ru2609",      # 橡胶（新增）
        "SHFE.ss2605", "SHFE.ss2606",      # 不锈钢（新增）
        "SHFE.sp2605", "SHFE.sp2609",      # 纸浆（新增）
        # ── DCE 大商所（15品种）─────────────────────────────────────
        "DCE.i2605",  "DCE.i2609",         # 铁矿石
        "DCE.m2605",  "DCE.m2609",         # 豆粕
        "DCE.pp2605", "DCE.pp2609",        # 聚丙烯（新增）
        "DCE.v2605",  "DCE.v2609",         # PVC（新增）
        "DCE.l2605",  "DCE.l2609",         # 塑料（新增）
        "DCE.c2605",  "DCE.c2609",         # 玉米
        "DCE.jd2605", "DCE.jd2606",        # 鸡蛋（月月合约，新增）
        "DCE.y2605",  "DCE.y2609",         # 豆油
        "DCE.p2605",  "DCE.p2609",         # 棕榈油
        "DCE.a2605",  "DCE.a2609",         # 豆一（新增）
        "DCE.jm2605", "DCE.jm2609",        # 焦煤（新增）
        "DCE.j2605",  "DCE.j2609",         # 焦炭（新增）
        "DCE.eb2605", "DCE.eb2609",        # 苯乙烯（新增）
        "DCE.pg2605", "DCE.pg2606",        # 液化气（新增）
        "DCE.lh2607", "DCE.lh2609",        # 生猪（奇数月合约，新增）
        # ── CZCE 郑商所（10品种）────────────────────────────────────
        "CZCE.TA605", "CZCE.TA609",        # PTA
        "CZCE.MA605", "CZCE.MA609",        # 甲醇
        "CZCE.CF605", "CZCE.CF609",        # 棉花
        "CZCE.SR605", "CZCE.SR609",        # 白糖（新增）
        "CZCE.OI605", "CZCE.OI609",        # 菜油（新增）
        "CZCE.RM605", "CZCE.RM609",        # 菜粕（新增）
        "CZCE.FG605", "CZCE.FG609",        # 玻璃（新增）
        "CZCE.SA605", "CZCE.SA609",        # 纯碱
        "CZCE.PF605", "CZCE.PF609",        # 短纤（新增）
        "CZCE.UR605", "CZCE.UR609",        # 尿素（新增）
    ]


def _get_domestic_symbols_tushare() -> list[str]:
    """返回全 35 品种的 Tushare 品种代码（用于 fut_holding / fut_wsr API）。

    格式为大写品种代码，不含交易所和合约月份。
    """
    return [
        # SHFE（10品种）
        "RB", "HC", "CU", "AL", "ZN", "AU", "AG", "RU", "SS", "SP",
        # DCE（15品种）
        "I", "M", "PP", "V", "L", "C", "JD", "Y", "P", "A", "JM", "J", "EB", "PG", "LH",
        # CZCE（10品种）
        "TA", "MA", "CF", "SR", "OI", "RM", "FG", "SA", "PF", "UR",
    ]


def _get_overseas_symbols() -> list[str]:
    """获取外盘合约列表（D109 扩展，覆盖 35 内盘品种的外盘对标）。

    分两类：
    1. YFINANCE_MINUTE_MAP 中的品种 — 支持分钟+日线（yfinance）
    2. DAILY_ONLY_MAP 中的品种   — 仅支持日线（LME via AkShare）

    外盘对标逻辑：
      贵金属：GC(AU) / SI(AG) / HG(CU+AL+ZN proxy for LME)
      能源：CL(TA/PP/V/L/EB/PG proxy) / NG(MA/UR proxy)
      农产品：ZS(A) / ZM(M/RM proxy) / ZL(Y/OI proxy) / ZC(C)
      软商品：CT(CF) / SB(SR) / RS(OI/RM)
      畜牧：HE(LH/JD)
      钢铁：HRC(RB/HC)
      LME 金属日线：AHD(AL) / ZSD(ZN) / NID(SS) / CAD(CU) / PBD / SND
    """
    return [
        # ── 能源（4）— proxy for TA/MA/PP/V/L/EB/PG/UR ────────────
        "NYMEX.CL",    # WTI原油（TA/PP/V/L/EB/PG 化工品上游）
        "ICE.B",       # 布伦特原油
        "NYMEX.NG",    # 天然气（MA/UR 上游）
        "NYMEX.HO",    # 取暖油
        # ── COMEX 金属（5）— 对标 AU/AG/CU/AL/ZN ─────────────────
        "COMEX.GC",    # 黄金（AU对标）
        "COMEX.SI",    # 白银（AG对标）
        "COMEX.HG",    # COMEX铜（CU对标）
        "NYMEX.PL",    # 铂（AG/AU 相关）
        "NYMEX.PA",    # 钯（贵金属群）
        # ── LME 金属日线（6）— 仅日线，AkShare ────────────────────
        "LME.AHD",     # LME铝（AL对标）
        "LME.ZSD",     # LME锌（ZN对标）
        "LME.NID",     # LME镍（SS不锈钢对标）
        "LME.CAD",     # LME铜（CU额外数据）
        "LME.PBD",     # LME铅
        "LME.SND",     # LME锡
        # ── CBOT 农产品（5）— 对标 A/M/RM/Y/C/OI ─────────────────
        "CBOT.ZS",     # 大豆（A对标）
        "CBOT.ZM",     # 豆粕（M/RM对标）
        "CBOT.ZL",     # 豆油（Y/OI对标）
        "CBOT.ZC",     # 玉米（C对标）
        "CBOT.ZW",     # 小麦（粮食群）
        # ── ICE 软商品（4）— 对标 CF/SR/OI/RM ────────────────────
        "ICE.CT",      # 棉花（CF对标）
        "ICE.SB",      # 白糖#11（SR对标）
        "ICE.KC",      # 咖啡
        "ICE.CC",      # 可可
        # ── CME 畜牧/钢铁（3）— 对标 LH/JD/RB/HC ─────────────────
        "CME.HE",      # 瘦肉猪（LH/JD对标，新增）
        "CME.HRC",     # HRC热轧卷板（RB/HC对标，新增）
        # ── 股指期货（4）— 市场情绪参考 ──────────────────────────
        "CME.ES",      # 标普500
        "CME.NQ",      # 纳斯达克100
        "CBOT.YM",     # 道琼斯
        "CME.RTY",     # 罗素2000
        # ── SGX（1）─────────────────────────────────────────────
        "SGX.CN",      # 富时中国A50
    ]


def job_minute_kline(config: dict[str, Any]) -> None:
    """分钟内盘K线 — 每 2 分钟，仅交易时段。

    通知策略:
    - 盘中每轮静默（不发启动/完成通知）
    - 连续 3 轮 0产出（约 6 分钟）→ 发一次 P2 告警
    - 有数据后自动重置连续计数
    - 收盘由 job_domestic_minute_day_close / job_domestic_minute_night_close 发摘要
    """
    if not _is_trading_session():
        return

    from services.data.src.scheduler.pipeline import run_minute_pipeline
    import time as _time

    symbols = _get_domestic_symbols()
    t0 = _time.time()
    try:
        result = run_minute_pipeline(symbols=symbols, config=config)
        bars = sum(result.values()) if isinstance(result, dict) else int(result or 0)
        elapsed = round(_time.time() - t0, 1)
    except Exception:
        bars, elapsed = 0, round(_time.time() - t0, 1)
        logger.error("国内期货分钟K线 pipeline 异常:\n%s", traceback.format_exc())

    # ── session 状态更新 ──────────────────────────────────────
    _domestic_minute_session["runs"] += 1
    _domestic_minute_session["total_bars"] += bars
    if bars == 0:
        _domestic_minute_session["zero_runs"] += 1
        _domestic_minute_session["consecutive_zeros"] += 1
    else:
        _domestic_minute_session["consecutive_zeros"] = 0
        _domestic_minute_session["alerted"] = False

    consecutive = _domestic_minute_session["consecutive_zeros"]
    logger.info(
        "国内期货分钟K线: bars=%d elapsed=%ss consecutive_zeros=%d",
        bars, elapsed, consecutive,
    )

    # ── 连续 3 轮 0产出 → 单次 P2 告警 ──────────────────────
    ZERO_ALERT_THRESHOLD = 3
    if consecutive >= ZERO_ALERT_THRESHOLD and not _domestic_minute_session["alerted"]:
        d = _get_dispatcher()
        if d:
            try:
                from services.data.src.notify.dispatcher import DataEvent, NotifyType
                d.dispatch(DataEvent(
                    event_code="domestic_minute_consecutive_zero",
                    title=f"国内期货分钟K线连续 {consecutive} 轮 0产出",
                    notify_type=NotifyType.P2,
                    body_md=(
                        f"🟡 国内期货分钟K线 已连续 **{consecutive}** 轮 0产出，"
                        f"可能存在数据源问题或行情异常。\n"
                        f"本 session 累计: {_domestic_minute_session['runs']} 轮 / "
                        f"{_domestic_minute_session['total_bars']:,} bars"
                    ),
                    body_rows=[
                        ("连续0产出", str(consecutive)),
                        ("session总轮次", str(_domestic_minute_session["runs"])),
                        ("累计bars", str(_domestic_minute_session["total_bars"])),
                        ("耗时(本轮)", f"{elapsed}s"),
                    ],
                    source_name="domestic_minute_kline",
                    channels={"feishu"},
                ))
                _domestic_minute_session["alerted"] = True
            except Exception:
                pass


def _domestic_minute_close_summary(session_name: str) -> None:
    """国内期货分钟K线收盘摘要（日盘/夜盘通用）。"""
    s = _domestic_minute_session
    runs = s["runs"]
    if runs == 0:
        return

    zero_runs = s["zero_runs"]
    total_bars = s["total_bars"]
    success_runs = runs - zero_runs
    completeness = round(success_runs / runs * 100, 1) if runs else 0
    status_icon = "🟢" if completeness >= 80 else ("🟡" if completeness >= 50 else "🔴")

    d = _get_dispatcher()
    if d:
        try:
            from services.data.src.notify.dispatcher import DataEvent, NotifyType
            d.dispatch(DataEvent(
                event_code="domestic_minute_session_close",
                title=f"{status_icon} 国内期货分钟K线{session_name}摘要 完整度 {completeness}%",
                notify_type=NotifyType.NOTIFY,
                body_md=(
                    f"{status_icon} **国内期货分钟K线** {session_name}已结束\n"
                    f"完整度: **{completeness}%** ({success_runs}/{runs} 轮有数据)\n"
                    f"累计采集: **{total_bars:,} bars** | 0产出轮次: {zero_runs}"
                ),
                body_rows=[
                    ("完整度", f"{completeness}%"),
                    ("有数据轮次", f"{success_runs}/{runs}"),
                    ("累计bars", f"{total_bars:,}"),
                    ("0产出轮次", str(zero_runs)),
                ],
                source_name="domestic_minute_kline",
                channels={"feishu"},
            ))
        except Exception:
            pass

    _domestic_minute_session.update({
        "runs": 0, "zero_runs": 0, "total_bars": 0,
        "consecutive_zeros": 0, "alerted": False,
    })
    logger.info("国内期货分钟K线 %s session 已重置", session_name)


def job_domestic_minute_day_close(config: dict[str, Any]) -> None:
    """国内期货分钟K线日盘收盘摘要 — 15:05 触发。"""
    _domestic_minute_close_summary("日盘")


def job_domestic_minute_night_close(config: dict[str, Any]) -> None:
    """国内期货分钟K线夜盘收盘摘要 — 02:35 触发。"""
    _domestic_minute_close_summary("夜盘")


def job_daily_kline(config: dict[str, Any]) -> None:
    """日线K线 — 每日 17:00。"""
    _calendar.refresh()
    ok, reason = _calendar.is_cn_trading_day(datetime.now())
    if not ok:
        logger.info("跳过日线K线: %s", reason)
        return
    from services.data.src.scheduler.pipeline import run_daily_pipeline
    symbols = _get_domestic_symbols()
    _safe_run("日线K线", run_daily_pipeline, symbols=symbols, config=config)


def job_overseas_kline(config: dict[str, Any]) -> None:
    """外盘日线（美/欧收盘后）— 每日 06:00 北京时间。

    覆盖: NYMEX/COMEX/CBOT/CME/ICE US 品种，对标35个内盘期货。
    06:00 北京 = 美国日盘 15:30-21:00 CT 结束后约1h。
    LME 金属单独由 job_overseas_kline_lme 在 02:00 采集。
    """
    _calendar.refresh()
    # 06:00 北京执行时，采的是“上一交易日”收盘数据（Tue-Sat 对应 Mon-Fri）。
    ref_now = datetime.now() - timedelta(days=1)
    ok, reason = _calendar.is_us_trading_day(ref_now)
    if not ok:
        logger.info("跳过外盘日线(美/欧): %s (ref=%s)", reason, ref_now.strftime("%Y-%m-%d"))
        return
    from services.data.src.scheduler.pipeline import run_overseas_daily_pipeline
    # 过滤掉 LME 品种（由 job_overseas_kline_lme 处理）
    all_syms = _get_overseas_symbols()
    us_syms = [s for s in all_syms if not s.startswith("LME.")]
    _safe_run("外盘日线(美/欧)", run_overseas_daily_pipeline, symbols=us_syms, config=config)


def job_overseas_kline_lme(config: dict[str, Any]) -> None:
    """LME金属日线（伦敦收盘后）— 每日 02:00 北京时间。

    伦敦金属交易所 Select (电子盘) 收盘 01:00 北京时间（17:00 London）。
    02:00 北京采集已是收盘后1h，数据已稳定。
    品种: AHD(铝/AL) / ZSD(锌/ZN) / NID(镍/SS不锈钢) / CAD(铜/CU) / PBD / SND
    """
    _calendar.refresh()
    # 02:00 北京执行时，采的是“上一交易日”伦敦收盘数据（Tue-Sat 对应 Mon-Fri）。
    ref_now = datetime.now() - timedelta(days=1)
    ok, reason = _calendar.is_lme_trading_day(ref_now)
    if not ok:
        logger.info("跳过LME金属日线: %s (ref=%s)", reason, ref_now.strftime("%Y-%m-%d"))
        return
    from services.data.src.scheduler.pipeline import run_overseas_daily_pipeline
    lme_syms = [s for s in _get_overseas_symbols() if s.startswith("LME.")]
    _safe_run("LME金属日线", run_overseas_daily_pipeline, symbols=lme_syms, config=config)


def job_overseas_minute_yf(config: dict[str, Any]) -> None:
    """外盘分钟K线 (yfinance) — 每5分钟, 仅外盘交易时段。

    通知策略:
    - 盘中每轮静默（不发启动/完成通知）
    - 连续 3 轮 0产出 → 发一次 P2 告警
    - 有数据后自动重置连续计数
    - 收盘由 job_overseas_minute_close_summary 发完整度摘要
    """
    if not _is_overseas_trading_hours():
        return

    from services.data.src.scheduler.pipeline import run_overseas_minute_yf_pipeline
    import time as _time

    t0 = _time.time()
    try:
        result = run_overseas_minute_yf_pipeline(config=config)
        bars = sum(result.values()) if isinstance(result, dict) else int(result or 0)
        elapsed = round(_time.time() - t0, 1)
    except Exception:
        bars, elapsed = 0, round(_time.time() - t0, 1)
        logger.error("外盘分钟K线 pipeline 异常:\n%s", traceback.format_exc())

    # ── session 状态更新 ──────────────────────────────────────
    _overseas_minute_session["runs"] += 1
    _overseas_minute_session["total_bars"] += bars
    if bars == 0:
        _overseas_minute_session["zero_runs"] += 1
        _overseas_minute_session["consecutive_zeros"] += 1
    else:
        _overseas_minute_session["consecutive_zeros"] = 0
        _overseas_minute_session["alerted"] = False

    consecutive = _overseas_minute_session["consecutive_zeros"]
    logger.info(
        "外盘分钟K线: bars=%d elapsed=%ss consecutive_zeros=%d",
        bars, elapsed, consecutive,
    )

    # ── 连续 3 轮 0产出 → 单次 P2 告警 ──────────────────────
    ZERO_ALERT_THRESHOLD = 3
    if consecutive >= ZERO_ALERT_THRESHOLD and not _overseas_minute_session["alerted"]:
        d = _get_dispatcher()
        if d:
            try:
                from services.data.src.notify.dispatcher import DataEvent, NotifyType
                d.dispatch(DataEvent(
                    event_code="overseas_minute_consecutive_zero",
                    title=f"外盘分钟K线连续 {consecutive} 轮 0产出",
                    notify_type=NotifyType.P2,
                    body_md=(
                        f"🟡 外盘分钟K线(yfinance) 已连续 **{consecutive}** 轮 0产出，"
                        f"可能存在限流或代理问题。\n"
                        f"本 session 累计: {_overseas_minute_session['runs']} 轮 / "
                        f"{_overseas_minute_session['total_bars']:,} bars"
                    ),
                    body_rows=[
                        ("连续0产出", str(consecutive)),
                        ("session总轮次", str(_overseas_minute_session["runs"])),
                        ("累计bars", str(_overseas_minute_session["total_bars"])),
                        ("耗时(本轮)", f"{elapsed}s"),
                    ],
                    source_name="overseas_minute_yf",
                    channels={"feishu"},
                ))
                _overseas_minute_session["alerted"] = True
            except Exception:
                pass


def job_overseas_minute_close_summary(config: dict[str, Any]) -> None:
    """外盘分钟K线收盘摘要 — 05:05 北京时间触发。

    汇报本 session 采集完整度，并重置 session 状态。
    """
    s = _overseas_minute_session
    runs = s["runs"]
    if runs == 0:
        # 当天未运行，跳过摘要
        return

    zero_runs = s["zero_runs"]
    total_bars = s["total_bars"]
    success_runs = runs - zero_runs
    completeness = round(success_runs / runs * 100, 1) if runs else 0
    status_icon = "🟢" if completeness >= 80 else ("🟡" if completeness >= 50 else "🔴")

    d = _get_dispatcher()
    if d:
        try:
            from services.data.src.notify.dispatcher import DataEvent, NotifyType
            d.dispatch(DataEvent(
                event_code="overseas_minute_session_close",
                title=f"{status_icon} 外盘分钟K线收盘摘要 完整度 {completeness}%",
                notify_type=NotifyType.NOTIFY,
                body_md=(
                    f"{status_icon} **外盘分钟K线** 本 session 已结束\n"
                    f"完整度: **{completeness}%** ({success_runs}/{runs} 轮有数据)\n"
                    f"累计采集: **{total_bars:,} bars** | 0产出轮次: {zero_runs}"
                ),
                body_rows=[
                    ("完整度", f"{completeness}%"),
                    ("有数据轮次", f"{success_runs}/{runs}"),
                    ("累计bars", f"{total_bars:,}"),
                    ("0产出轮次", str(zero_runs)),
                ],
                source_name="overseas_minute_yf",
                channels={"feishu"},
            ))
        except Exception:
            pass

    # 重置 session 状态
    _overseas_minute_session.update({
        "runs": 0, "zero_runs": 0, "total_bars": 0,
        "consecutive_zeros": 0, "alerted": False,
    })
    logger.info("外盘分钟K线 session 已重置")


def job_stock_minute(config: dict[str, Any]) -> None:
    """A股分钟K线 — 每2分钟, 仅A股交易时段。"""
    if not STOCK_MINUTE_ENABLED:
        logger.info("A股分钟K线任务已暂停，跳过执行")
        return
    if not _is_stock_trading_session():
        return
    from services.data.src.scheduler.pipeline import run_stock_minute_pipeline
    _safe_run("A股分钟K线", run_stock_minute_pipeline, config=config)


def _build_tushare_ts_codes() -> list[str]:
    """动态生成35个品种当前近月合约的 Tushare ts_code。

    格式规则:
      SHFE/DCE: {VARIETY}{YYMM}.{SHF|DCE}  — e.g. RB2605.SHF
      CZCE:    {VARIETY}{YMM}.ZCE           — e.g. MA605.ZCE (3位日期码)
    近月逻辑: 当月15日前取当月，否则取下月。
    黄金/白银/生猪: 取下一个偶数月。
    """
    now = datetime.now()
    y2 = now.year % 100   # e.g. 26
    mo = now.month

    # 近月: 15日前用当月，否则下月
    if now.day < 15:
        nm, ny = mo, y2
    else:
        nm = mo + 1 if mo < 12 else 1
        ny = y2 if mo < 12 else (y2 + 1)

    def _next_even(y: int, m: int) -> tuple[int, int]:
        """取下一个偶数月（含当月）。"""
        if m % 2 == 0:
            return y, m
        m2 = m + 1
        y2_ = y if m2 <= 12 else y + 1
        m2 = m2 if m2 <= 12 else 1
        return y2_, m2

    shfe_dce_mm = f"{ny:02d}{nm:02d}"
    ey, em = _next_even(ny, nm)
    even_mm = f"{ey:02d}{em:02d}"
    czce_ymm = f"{ny % 10}{nm:02d}"
    czce_even_ymm = f"{ey % 10}{em:02d}"

    result: list[str] = []
    # ── SHFE（10）──────────────────────────────────────────────────
    for sym in ["RB", "HC", "CU", "AL", "ZN", "RU", "SS", "SP"]:
        result.append(f"{sym}{shfe_dce_mm}.SHF")
    result.append(f"AU{even_mm}.SHF")   # 黄金 — 偶数月
    result.append(f"AG{even_mm}.SHF")   # 白银 — 偶数月
    # ── DCE（15）──────────────────────────────────────────────────
    for sym in ["I", "M", "PP", "V", "L", "C", "JD", "Y", "P", "A", "JM", "J", "EB", "PG"]:
        result.append(f"{sym}{shfe_dce_mm}.DCE")
    result.append(f"LH{even_mm}.DCE")   # 生猪 — 偶数月
    # ── CZCE（10）─────────────────────────────────────────────────
    for sym in ["TA", "MA", "CF", "SR", "OI", "RM", "FG", "SA", "PF", "UR"]:
        result.append(f"{sym}{czce_ymm}.ZCE")
    return result


def job_tushare_futures(config: dict[str, Any]) -> None:
    """Tushare期货五合一 — 每日 17:10，动态覆盖35个品种近月合约。

    数据内容: fut_daily / fut_holding / fut_wsr / fut_settle
    ts_code 由 _build_tushare_ts_codes() 按当前日期动态生成。
    """
    _calendar.refresh()
    ok, reason = _calendar.is_cn_trading_day(datetime.now())
    if not ok:
        logger.info("跳过Tushare期货五合一: %s", reason)
        return
    from services.data.src.scheduler.pipeline import run_tushare_futures_pipeline
    today = datetime.now().strftime("%Y%m%d")
    ts_codes = _build_tushare_ts_codes()
    for ts_code in ts_codes:
        _safe_run(
            f"Tushare期货({ts_code})",
            run_tushare_futures_pipeline,
            ts_code=ts_code,
            trade_date=today,
            config=config,
        )


def job_macro(config: dict[str, Any]) -> None:
    """宏观数据 — 每日 09:00。"""
    from services.data.src.scheduler.pipeline import run_macro_pipeline
    _safe_run("宏观数据", run_macro_pipeline, config=config)


def job_position(config: dict[str, Any]) -> None:
    """持仓/仓单 — 每日 15:30。"""
    _calendar.refresh()
    ok, reason = _calendar.is_cn_trading_day(datetime.now())
    if not ok:
        logger.info("跳过持仓/仓单: %s", reason)
        return
    from services.data.src.scheduler.pipeline import run_position_pipeline
    _safe_run("持仓仓单日报", run_position_pipeline, config=config)


def job_news_api(config: dict[str, Any]) -> None:
    """新闻API — 每1分钟。"""
    from services.data.src.scheduler.pipeline import run_news_api_pipeline
    _safe_run("新闻API", run_news_api_pipeline, config=config)


def job_rss(config: dict[str, Any]) -> None:
    """RSS聚合 — 每10分钟。"""
    from services.data.src.scheduler.pipeline import run_rss_pipeline
    _safe_run("RSS聚合", run_rss_pipeline, config=config)


def job_volatility(config: dict[str, Any]) -> None:
    """波动率 — 每日 17:00。"""
    from services.data.src.scheduler.pipeline import run_volatility_pipeline
    _safe_run("波动率指数", run_volatility_pipeline, config=config)


def job_sentiment(config: dict[str, Any]) -> None:
    """情绪指数 — 每5分钟。"""
    from services.data.src.scheduler.pipeline import run_sentiment_pipeline
    _safe_run("情绪指数", run_sentiment_pipeline, config=config)


def job_shipping(config: dict[str, Any]) -> None:
    """海运物流 — 每日 09:00。"""
    from services.data.src.scheduler.pipeline import run_shipping_pipeline
    _safe_run("海运物流", run_shipping_pipeline, config=config)


def job_forex(config: dict[str, Any]) -> None:
    """外汇日线 — 每日 17:20 (Tushare fx_daily)。"""
    _calendar.refresh()
    ok, reason = _calendar.is_cn_trading_day(datetime.now())
    if not ok:
        logger.info("跳过外汇日线: %s", reason)
        return
    from services.data.src.scheduler.pipeline import run_forex_pipeline
    _safe_run("外汇日线", run_forex_pipeline, config=config)


def job_cftc(config: dict[str, Any]) -> None:
    """CFTC持仓报告 — 每周六 10:00 (CFTC 周五发布)。"""
    from services.data.src.scheduler.pipeline import run_cftc_pipeline
    _safe_run("CFTC持仓报告", run_cftc_pipeline, config=config)


def job_options(config: dict[str, Any]) -> None:
    """期权行情 — 每日 15:30 (收盘后)。"""
    _calendar.refresh()
    ok, reason = _calendar.is_cn_trading_day(datetime.now())
    if not ok:
        logger.info("跳过期权行情: %s", reason)
        return
    from services.data.src.scheduler.pipeline import run_options_pipeline
    _safe_run("期权行情", run_options_pipeline, config=config)


def job_market_session_watch(config: dict[str, Any]) -> None:
    """每分钟检测一次全球市场开休盘状态并飞书提醒。"""
    _emit_market_transition_notifications()


def job_feishu_news_hourly(config: dict[str, Any]) -> None:
    """[DEPRECATED] 旧飞书新闻小时任务已收口到新闻批量推送。"""
    logger.info("[DEPRECATED] job_feishu_news_hourly 已停用，统一由 job_news_push_batch 负责新闻摘要推送")


def job_daily_summary(config: dict[str, Any]) -> None:
    """[DEPRECATED] 每日采集汇总 — 已被 heartbeat_card 替代，保留函数体以防残留调用。"""
    logger.info("[DEPRECATED] job_daily_summary 已被 2h 心跳卡片替代，跳过执行")


def job_evening_report(config: dict[str, Any]) -> None:
    """[DEPRECATED] 晚间审计日报 — 已被 heartbeat_card 替代，保留函数体以防残留调用。"""
    logger.info("[DEPRECATED] job_evening_report 已被 2h 心跳卡片替代，跳过执行")


def job_heartbeat(config: dict[str, Any]) -> None:
    """每 2 小时进程监控 — 推送 Mini 硬件 + JBT 进程状态 + 采集源新鲜度到飞书。"""
    try:
        logger.info("▶ 开始执行: 2h 进程监控")
        import os as _os
        import importlib.util
        import subprocess as _sp

        # ── JBT 进程定义（通过 ps 检测实际进程）──────────────────────
        _JBT_PROCS = [
            ("数据采集调度", "data_scheduler"),
            ("数据 API",     "services.data.src.main"),
        ]

        # ── 加载 health_check 模块 ────────────────────────────────────
        _hc_path = str(PROJECT_ROOT / "health" / "health_check.py")
        _spec = importlib.util.spec_from_file_location("health_check_mod", _hc_path)
        _mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]

        cpu = _mod.get_cpu_info()
        mem = _mod.get_memory_info()
        disks = _mod.get_disk_info()
        freshness = _mod.get_collector_freshness()

        mini_cpu = float(cpu.get("usage_percent", 0.0))
        mini_mem = float(mem.get("used_percent", 0.0))
        mini_disk = float(disks[0]["used_percent"]) if disks else 0.0

        # ── 通过 ps 检测 JBT 进程 ─────────────────────────────────────
        try:
            ps_out = _sp.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=10,
            ).stdout
        except Exception:
            ps_out = ""

        mini_processes = [
            {"label": label, "ok": keyword in ps_out}
            for label, keyword in _JBT_PROCS
        ]

        # ── 判断是否有异常 ─────────────────────────────────────────────
        has_issues = any(not s["ok"] and not s.get("skipped") for s in freshness)
        has_issues = has_issues or (mini_cpu >= 85) or (mini_mem >= 85)
        has_issues = has_issues or any(not p["ok"] for p in mini_processes)

        # ── 使用新通知系统 ─────────────────────────────────────────
        d = _get_dispatcher()
        if d:
            try:
                from services.data.src.notify import card_templates as ct

                card = ct.device_health_card(
                    cpu_pct=mini_cpu,
                    mem_pct=mini_mem,
                    disk_pct=mini_disk,
                    processes=mini_processes,
                    sources=freshness,
                    has_issues=has_issues,
                )
                from services.data.src.notify.feishu import FeishuSender
                sender = FeishuSender()
                webhook = (
                    _os.environ.get("FEISHU_ALERT_WEBHOOK_URL")
                    or _os.environ.get("FEISHU_WEBHOOK_URL")
                    or _os.environ.get("FEISHU_NEWS_WEBHOOK_URL")
                    or _os.environ.get("FEISHU_TRADING_WEBHOOK_URL")
                    or ""
                )
                if webhook:
                    sender.send_card(webhook, card)
                    logger.info("✅ 2h 进程监控已发送 (新通知系统)")
                else:
                    logger.warning("⚠️ 无飞书 webhook，跳过进程监控推送")
            except Exception as _e:
                logger.error("新通知系统发送失败: %s", _e)
        else:
            logger.warning("⚠️ dispatcher 不可用，跳过进程监控推送")
    except Exception:
        logger.error("❌ 2h 进程监控异常:\n%s", traceback.format_exc())


def _job_factor_session(config: dict[str, Any], session: str) -> None:
    """因子/信号分时段报告内部实现."""
    try:
        logger.info("▶ 开始执行: 因子/信号%s报告", session)
        n = get_factor_notifier()
        ok = n.send_session_summary(session)
        if ok:
            logger.info("✅ 因子/信号%s报告已发送", session)
        else:
            logger.warning("⚠️ 因子/信号%s报告发送失败", session)
    except Exception:
        logger.error("❌ 因子/信号%s报告异常:\n%s", session, traceback.format_exc())


def job_factor_signal_morning(config: dict[str, Any]) -> None:
    """因子/信号早盘报告 — 11:35."""
    _job_factor_session(config, "早盘")


def job_factor_signal_afternoon(config: dict[str, Any]) -> None:
    """因子/信号午盘报告 — 15:05."""
    _job_factor_session(config, "午盘")


def job_factor_signal_summary(config: dict[str, Any]) -> None:
    """因子/信号收盘报告 — 23:05（兼容旧名保留）."""
    _job_factor_session(config, "收盘")


def job_sla_report(config: dict[str, Any]) -> None:
    """告警 SLA 日报 — 23:15 发送飞书。"""
    try:
        logger.info("▶ 开始执行: 告警 SLA 日报")
        ok = get_sla_tracker().send_daily_sla_report()
        if ok:
            logger.info("✅ SLA 日报已发送")
        else:
            logger.warning("⚠️ SLA 日报发送失败")
    except Exception:
        logger.error("❌ SLA 日报异常:\n%s", traceback.format_exc())


def job_sla_reset(config: dict[str, Any]) -> None:
    """SLA 计数器重置 — 00:05。"""
    try:
        get_sla_tracker().reset_daily()
        logger.info("✅ SLA 计数器已重置")
    except Exception:
        logger.error("❌ SLA 重置异常:\n%s", traceback.format_exc())


def job_daily_reset(config: dict[str, Any]) -> None:
    """每日统计重置 — 00:00 清零当日计数器。"""
    n = _get_notifier(config)
    if n:
        n.reset_daily()
        logger.info("✅ 每日采集计数器已重置")


def job_daily_email_report(config: dict[str, Any]) -> None:
    """每日邮件日报 — 09:30 + 16:30，发送完整数据端健康报告。"""
    try:
        logger.info("▶ 开始执行: 邮件日报")
        import importlib.util
        from services.data.src.notify.email_notify import EmailSender, build_daily_report_html

        # 加载 health_check 获取设备指标
        _hc_path = str(PROJECT_ROOT / "health" / "health_check.py")
        _spec = importlib.util.spec_from_file_location("health_check_mod", _hc_path)
        _mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]

        cpu = _mod.get_cpu_info()
        mem = _mod.get_memory_info()
        disks = _mod.get_disk_info()
        freshness = _mod.get_collector_freshness() if _mod.IS_MINI else []

        sources_freshness = [
            {"label": s.get("label", s.get("name", "")), "ok": s.get("ok", False),
             "age_str": s.get("age_str", "")} for s in freshness
        ]

        # 进程状态 — 通过 ps 检测实际运行的 JBT 进程
        import subprocess as _sp
        try:
            ps_out = _sp.run(["ps", "aux"], capture_output=True, text=True, timeout=10).stdout
        except Exception:
            ps_out = ""
        procs = [
            {"label": label, "ok": keyword in ps_out, "uptime": ""}
            for label, keyword in [
                ("数据调度", "data_scheduler"),
                ("数据 API", "services.data.src.main"),
            ]
        ]

        ok_count = sum(1 for s in freshness if s.get("ok"))
        total = len(freshness)
        html = build_daily_report_html(
            total_rounds=total,
            success_rate=ok_count / max(total, 1) * 100,
            failed_collectors=[s.get("label", "") for s in freshness if not s.get("ok") and not s.get("skipped")],
            total_records=0,
            sources_freshness=sources_freshness,
            cpu_pct=float(cpu.get("usage_percent", 0)),
            mem_pct=float(mem.get("used_percent", 0)),
            disk_pct=float(disks[0]["used_percent"]) if disks else 0,
            process_status=procs,
            errors=[],
            news_collected=0,
            news_pushed=0,
            breaking_count=0,
            health_score=min(100, int(ok_count / max(total, 1) * 100)),
        )

        sender = EmailSender()
        period = "晨报" if datetime.now().hour < 12 else "午报"
        ok = sender.send_daily_report(html=html, report_type=period)
        if ok:
            logger.info("✅ 邮件日报(%s)已发送", period)
        else:
            logger.warning("⚠️ 邮件日报(%s)发送失败", period)
    except Exception:
        logger.error("❌ 邮件日报异常:\n%s", traceback.format_exc())


def job_news_push_batch(config: dict[str, Any]) -> None:
    """新闻批量推送 — 每30分钟，汇总重大新闻推送飞书。"""
    try:
        logger.info("▶ 开始执行: 新闻批量推送")
        from services.data.src.notify.news_pusher import NewsPusher
        pusher = NewsPusher()
        sync_stats = pusher.sync_from_storage(limit_per_source=NEWS_STORAGE_SYNC_LIMIT_PER_SOURCE)
        stats = pusher.flush()
        if stats and stats.get("deferred", 0) > 0:
            logger.info("✅ 新闻推送: 静默窗口内暂缓 %d 条", stats["deferred"])
        elif stats and stats.get("pushed", 0) > 0:
            logger.info("✅ 新闻推送: %d 条", stats["pushed"])
        elif sync_stats and sync_stats.get("new", 0) > 0:
            logger.info("✅ 新闻推送: 已同步 %d 条，当前无需推送", sync_stats["new"])
        else:
            logger.info("✅ 新闻推送: 无新内容")
    except Exception:
        logger.error("❌ 新闻推送异常:\n%s", traceback.format_exc())


def job_session_notify(config: dict[str, Any], session_name: str = "") -> None:
    """交易时段开始通知。"""
    n = _get_notifier(config)
    if n:
        try:
            n.send_session_start(session_name)
            logger.info("✅ 时段通知已发送: %s", session_name)
        except Exception:
            logger.error("❌ 时段通知发送失败:\n%s", traceback.format_exc())


def job_nas_backup(config: dict[str, Any]) -> None:
    """NAS 备份 — 每日 03:00, 调用 nas_backup.sh --auto."""
    import subprocess  # noqa: S404  # nosec B404
    script = str(PROJECT_ROOT / "scripts" / "nas_backup.sh")
    try:
        logger.info("▶ 开始执行: NAS 备份")
        t0 = time.time()
        result = subprocess.run(  # nosec B603 B607
            ["bash", script, "--auto"],
            capture_output=True, text=True, timeout=3600,
            cwd=str(PROJECT_ROOT),
        )
        elapsed = round(time.time() - t0, 2)
        if result.returncode == 0:
            logger.info("✅ NAS 备份完成, 耗时 %ss", elapsed)
        else:
            logger.error(
                "❌ NAS 备份失败 rc=%d\nstdout=%s\nstderr=%s",
                result.returncode, result.stdout[-500:], result.stderr[-500:],
            )
    except subprocess.TimeoutExpired:
        logger.error("❌ NAS 备份超时 (>3600s)")
    except Exception:
        logger.error("❌ NAS 备份异常:\n%s", traceback.format_exc())


# ─────────────────────────────────────────────
# APScheduler 调度模式
# ─────────────────────────────────────────────
def _run_with_apscheduler(config: dict[str, Any]) -> None:
    """使用 APScheduler 注册所有任务并运行。"""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # 预初始化通知器
    _get_notifier(config)

    # 初始化市场快照，并每分钟检测一次开/休盘状态变化。
    _emit_market_transition_notifications()
    scheduler.add_job(
        job_market_session_watch, IntervalTrigger(minutes=1),
        args=[config], id="market_session_watch", name="市场开休盘状态监听",
        next_run_time=datetime.now(),
    )

    # [DEPRECATED LIFTED] 分钟内盘K线: 每2分钟，交易时段门控在函数内。
    # 已迁回 JBT APScheduler，停用 com.botquant.futures.minute plist。
    # 通知策略: 盘中静默，连续3轮0产出发P2，日盘15:05/夜盘02:35发收盘摘要。
    scheduler.add_job(
        job_minute_kline, IntervalTrigger(minutes=2),
        args=[config], id="minute_kline", name="分钟内盘K线",
    )
    # 国内期货分钟K线收盘摘要: 日盘 15:05 / 夜盘 02:35
    scheduler.add_job(
        job_domestic_minute_day_close, CronTrigger(hour=15, minute=5, day_of_week="mon-fri"),
        args=[config], id="domestic_minute_day_close", name="国内期货日盘收盘摘要",
    )
    scheduler.add_job(
        job_domestic_minute_night_close, CronTrigger(hour=2, minute=35, day_of_week="tue-sat"),
        args=[config], id="domestic_minute_night_close", name="国内期货夜盘收盘摘要",
    )
    # 日线K线: 每日 17:00
    scheduler.add_job(
        job_daily_kline, CronTrigger(hour=17, minute=0, day_of_week="mon-fri"),
        args=[config], id="daily_kline", name="日线K线",
    )
    # [DEPRECATED LIFTED] 外盘日线（美/欧）: 每日 06:00（美盘收盘后1h）
    # 调整自旧 17:05 → 06:00，覆盖 NYMEX/COMEX/CBOT/CME/ICE US 全品种。
    scheduler.add_job(
        job_overseas_kline, CronTrigger(hour=6, minute=0, day_of_week="tue-sat"),
        args=[config], id="overseas_daily_us", name="外盘日线(美/欧)",
    )
    # LME 金属日线: 每日 02:00（伦敦收盘 01:00 后1h）— 新增
    scheduler.add_job(
        job_overseas_kline_lme, CronTrigger(hour=2, minute=0, day_of_week="tue-sat"),
        args=[config], id="overseas_daily_lme", name="LME金属日线",
    )
    # [DEPRECATED LIFTED] 外盘分钟K线: 每5分钟，境外交易时段门控在函数内。
    scheduler.add_job(
        job_overseas_minute_yf, IntervalTrigger(minutes=5),
        args=[config], id="overseas_minute_yf", name="外盘分钟K线(yfinance)",
    )
    # 外盘收盘摘要: 05:05 北京时间发送 session 完整度汇报并重置状态
    scheduler.add_job(
        job_overseas_minute_close_summary, CronTrigger(hour=5, minute=5),
        args=[config], id="overseas_minute_close_summary", name="外盘分钟K线收盘摘要",
    )
    if STOCK_MINUTE_ENABLED:
        scheduler.add_job(
            job_stock_minute, IntervalTrigger(minutes=2),
            args=[config], id="stock_minute", name="A股分钟K线",
        )
    else:
        logger.info("A股分钟K线任务当前已暂停，不注册 APScheduler 任务")
    # [DEPRECATED LIFTED] Tushare期货五合一: 17:10，动态35品种近月合约。
    scheduler.add_job(
        job_tushare_futures, CronTrigger(hour=17, minute=10, day_of_week="mon-fri"),
        args=[config], id="tushare_futures", name="Tushare期货五合一",
    )
    # [DEPRECATED LIFTED] 宏观数据: 09:00
    scheduler.add_job(
        job_macro, CronTrigger(hour=9, minute=0, day_of_week="mon-fri"),
        args=[config], id="macro", name="宏观数据",
    )
    # [DEPRECATED LIFTED] 持仓/仓单: 15:30（35品种全覆盖）
    scheduler.add_job(
        job_position, CronTrigger(hour=15, minute=30, day_of_week="mon-fri"),
        args=[config], id="position", name="持仓仓单日报",
    )
    # [DEPRECATED LIFTED] 新闻API: 每1分钟
    scheduler.add_job(
        job_news_api, IntervalTrigger(minutes=1),
        args=[config], id="news_api", name="新闻API",
    )
    # [DEPRECATED LIFTED] RSS聚合: 每10分钟
    scheduler.add_job(
        job_rss, IntervalTrigger(minutes=10),
        args=[config], id="rss", name="RSS聚合",
    )
    # [DEPRECATED LIFTED] 波动率: 17:15
    scheduler.add_job(
        job_volatility, CronTrigger(hour=17, minute=15, day_of_week="mon-fri"),
        args=[config], id="volatility", name="波动率指数",
    )
    # [DEPRECATED LIFTED] 情绪指数: 每5分钟
    scheduler.add_job(
        job_sentiment, IntervalTrigger(minutes=5),
        args=[config], id="sentiment", name="情绪指数",
    )
    # [DEPRECATED LIFTED] 海运物流: 09:10
    scheduler.add_job(
        job_shipping, CronTrigger(hour=9, minute=10, day_of_week="mon-fri"),
        args=[config], id="shipping", name="海运物流",
    )
    # 外汇日线: 17:20 (Tushare fx_daily, 交易日)
    scheduler.add_job(
        job_forex, CronTrigger(hour=17, minute=20, day_of_week="mon-fri"),
        args=[config], id="forex_daily", name="外汇日线",
    )
    # CFTC持仓报告: 每周六 10:00 (CFTC 周五发布, 周六采集)
    scheduler.add_job(
        job_cftc, CronTrigger(hour=10, minute=0, day_of_week="sat"),
        args=[config], id="cftc_weekly", name="CFTC持仓报告",
    )
    # 期权行情: 15:30 (收盘后, 交易日)
    scheduler.add_job(
        job_options, CronTrigger(hour=15, minute=30, day_of_week="mon-fri"),
        args=[config], id="options_daily", name="期权行情",
    )
    # ── 采集监控通知 ──
    # [DEPRECATED] 每日采集汇总: 23:00 — 已被 2h 心跳卡片替代
    # scheduler.add_job(
    #     job_daily_summary, CronTrigger(hour=23, minute=0),
    #     args=[config], id="daily_summary", name="每日采集汇总",
    # )
    # [DEPRECATED] 晚间审计日报: 23:05 — 已被 2h 心跳卡片替代
    # scheduler.add_job(
    #     job_evening_report, CronTrigger(hour=23, minute=5),
    #     args=[config], id="evening_report", name="晚间审计日报",
    # )
    # 2h 系统心跳: 每 2 小时推送飞书卡片 (00:00, 02:00, ..., 22:00)
    scheduler.add_job(
        job_heartbeat, IntervalTrigger(hours=2),
        args=[config], id="system_heartbeat", name="2h系统心跳",
        next_run_time=datetime.now(),  # 启动后立即推一次
    )
    # 因子/信号分时段报告: 早盘11:35 / 午盘15:05 / 收盘23:05
    scheduler.add_job(
        job_factor_signal_morning, CronTrigger(hour=11, minute=35, day_of_week="mon-fri"),
        args=[config], id="factor_signal_morning", name="因子/信号早盘报告",
    )
    scheduler.add_job(
        job_factor_signal_afternoon, CronTrigger(hour=15, minute=5, day_of_week="mon-fri"),
        args=[config], id="factor_signal_afternoon", name="因子/信号午盘报告",
    )
    scheduler.add_job(
        job_factor_signal_summary, CronTrigger(hour=23, minute=5),
        args=[config], id="factor_signal_summary", name="因子/信号收盘报告",
    )
    # 告警 SLA 日报: 23:15 [DISABLED]
    # scheduler.add_job(
    #     job_sla_report, CronTrigger(hour=23, minute=15),
    #     args=[config], id="sla_report", name="告警SLA日报",
    # )
    # 每日计数器重置: 00:00
    scheduler.add_job(
        job_daily_reset, CronTrigger(hour=0, minute=0),
        args=[config], id="daily_reset", name="每日计数器重置",
    )
    # SLA 计数器重置: 00:05
    scheduler.add_job(
        job_sla_reset, CronTrigger(hour=0, minute=5),
        args=[config], id="sla_reset", name="SLA计数器重置",
    )
    # 早盘开盘通知: 09:30 (周一到周五)
    scheduler.add_job(
        job_session_notify, CronTrigger(hour=9, minute=30, day_of_week="mon-fri"),
        args=[config], kwargs={"session_name": "早盘采集开始"},
        id="session_am", name="早盘开盘通知",
    )
    # 夜盘开盘通知: 21:00 (周一到周四)
    scheduler.add_job(
        job_session_notify, CronTrigger(hour=21, minute=0, day_of_week="mon-thu"),
        args=[config], kwargs={"session_name": "夜盘采集开始"},
        id="session_pm", name="夜盘开盘通知",
    )
    # NAS 备份: 每日 03:00
    scheduler.add_job(
        job_nas_backup, CronTrigger(hour=3, minute=0),
        args=[config], id="nas_backup", name="NAS备份",
    )
    # ── 新通知系统 ──
    # 邮件日报: 09:30 + 16:30
    scheduler.add_job(
        job_daily_email_report, CronTrigger(hour=9, minute=30, day_of_week="mon-fri"),
        args=[config], id="email_morning", name="邮件晨报",
    )
    scheduler.add_job(
        job_daily_email_report, CronTrigger(hour=16, minute=30, day_of_week="mon-fri"),
        args=[config], id="email_afternoon", name="邮件午报",
    )
    # 新闻批量推送: 每30分钟
    scheduler.add_job(
        job_news_push_batch, IntervalTrigger(minutes=30),
        args=[config], id="news_push_batch", name="新闻批量推送",
    )

    logger.info("=" * 60)
    logger.info("BotQuant 数据调度器启动 (APScheduler 模式)")
    logger.info("已注册 %d 个任务", len(scheduler.get_jobs()))
    for job in scheduler.get_jobs():
        logger.info("  📋 %s [%s] → %s", job.name, job.id, job.trigger)
    logger.info("=" * 60)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器收到退出信号，正在关闭…")
        scheduler.shutdown(wait=False)


# ─────────────────────────────────────────────
# 内置 time.sleep 循环（APScheduler 不可用时的 fallback）
# ─────────────────────────────────────────────

# 任务注册表: (名称, 函数, 间隔秒数, 每日固定时间HH:MM 或 None)
_FALLBACK_JOBS: list[tuple[str, Callable[..., Any], int | None, str | None]] = [
    ("市场开休盘状态监听",      job_market_session_watch,    60,   None),
    ("分钟内盘K线",             job_minute_kline,          120,   None),
    ("外盘分钟K线(yfinance)",  job_overseas_minute_yf,  300,   None),
    ("日线K线",                job_daily_kline,         None,  "17:00"),
    ("外盘日线(美/欧)",         job_overseas_kline,      None,  "06:00"),
    ("LME金属日线",            job_overseas_kline_lme,  None,  "02:00"),
    ("Tushare期货五合一",      job_tushare_futures,     None,  "17:10"),
    ("宏观数据",               job_macro,               None,  "09:00"),
    ("持仓仓单日报",           job_position,            None,  "15:30"),
    ("新闻API",               job_news_api,             60,   None),
    ("RSS聚合",               job_rss,                 600,   None),
    ("波动率指数",             job_volatility,          None,  "17:15"),
    ("情绪指数",               job_sentiment,           300,   None),
    ("海运物流",               job_shipping,            None,  "09:10"),
    ("外汇日线",               job_forex,               None,  "17:20"),
    ("CFTC持仓报告",           job_cftc,                None,  "10:00"),  # 周六
    ("期权行情",               job_options,             None,  "15:30"),
    # [DEPRECATED REMOVED] ("每日采集汇总", job_daily_summary)  — 已被 2h 心跳替代
    # [DEPRECATED REMOVED] ("晚间审计日报", job_evening_report) — 已被 2h 心跳替代
    ("因子/信号早盘报告",      job_factor_signal_morning,    None, "11:35"),
    ("因子/信号午盘报告",      job_factor_signal_afternoon,  None, "15:05"),
    ("因子/信号收盘报告",      job_factor_signal_summary,    None, "23:05"),
    ("告警SLA日报",            job_sla_report,          None,  "23:15"),
    ("每日计数器重置",         job_daily_reset,         None,  "00:00"),
    ("SLA计数器重置",          job_sla_reset,           None,  "00:05"),
    ("NAS备份",               job_nas_backup,          None,  "03:00"),
]


def _run_with_sleep_loop(config: dict[str, Any]) -> None:
    """Fallback: 使用 time.sleep 循环调度。"""
    logger.info("=" * 60)
    logger.info("BotQuant 数据调度器启动 (sleep-loop fallback 模式)")
    logger.info("已注册 %d 个任务", len(_FALLBACK_JOBS))
    logger.info("=" * 60)

    # 预初始化通知器
    _get_notifier(config)

    # 上次执行时间戳
    last_run: dict[str, float] = {}
    # 已执行的每日任务 (date_str -> set of job names)
    daily_done: dict[str, set[str]] = {}

    while _running:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        now_hm = now.strftime("%H:%M")
        now_ts = time.time()

        if today_str not in daily_done:
            daily_done.clear()
            daily_done[today_str] = set()

        for name, func, interval_sec, daily_time in _FALLBACK_JOBS:
            try:
                if interval_sec is not None:
                    # 间隔任务
                    prev = last_run.get(name, 0)
                    if now_ts - prev >= interval_sec:
                        func(config)
                        last_run[name] = now_ts
                elif daily_time is not None:
                    # 每日定时任务: 在指定时间后 5 分钟窗口内执行一次
                    if name not in daily_done[today_str] and now_hm >= daily_time:
                        func(config)
                        daily_done[today_str].add(name)
                        last_run[name] = now_ts
            except Exception:
                logger.error("任务 %s 异常:\n%s", name, traceback.format_exc())

        # 每 30 秒检查一次
        time.sleep(30)

    logger.info("调度器已退出。")


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="BotQuant 24h 数据调度器")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式（由 shell 脚本包装 nohup）")
    args = parser.parse_args()

    _setup_scheduler_log()
    config = get_config()

    logger.info("加载配置完成，存储路径: %s", config.get("storage", {}).get("base_path", "N/A"))
    logger.info("Python %s | PID %d | daemon=%s", sys.version.split()[0], os.getpid(), args.daemon)

    # 优先使用 APScheduler
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: F401
        logger.info("检测到 APScheduler，使用 cron 调度模式")
        _run_with_apscheduler(config)
    except ImportError:
        logger.warning("APScheduler 不可用，回退到 sleep-loop 模式")
        _run_with_sleep_loop(config)


if __name__ == "__main__":
    main()
