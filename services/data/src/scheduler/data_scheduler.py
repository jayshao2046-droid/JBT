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
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env (TUSHARE_TOKEN 等)
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from services.data.src.utils.config import get_config
from services.data.src.utils.logger import get_logger

# ─────────────────────────────────────────────
# 全局状态
# ─────────────────────────────────────────────
_running = True
logger = get_logger("data_scheduler")
_notifier = None  # CollectionNotifier, 延迟初始化


def _get_notifier(config: dict[str, Any] | None = None) -> Any:
    """获取或初始化 CollectionNotifier."""
    global _notifier
    if _notifier is None and config:
        try:
            # from src.monitor.collection_notifier import CollectionNotifier
            _notifier = CollectionNotifier(config=config)
        except Exception as exc:
            logger.warning("CollectionNotifier 初始化失败: %s", exc)
    return _notifier


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
    log_dir = Path(os.path.expanduser("~/J_BotQuant/BotQuan_Data/logs"))
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
    return _is_futures_day_session(now) or _is_futures_night_session(now)


def _is_stock_trading_session(now: datetime | None = None) -> bool:
    """A股交易时段: 09:30-11:30, 13:00-15:00 (周一到周五)."""
    now = now or datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.hour * 60 + now.minute
    return (570 <= t <= 690) or (780 <= t <= 900)


def _is_overseas_trading_hours(now: datetime | None = None) -> bool:
    """外盘主要交易时段 (北京时间, 覆盖美盘+欧盘):
    CME/COMEX/NYMEX: 06:00-05:00 (几乎24小时)
    ICE: 15:30-次日01:30
    CBOT: 08:00-02:20
    实际采用: 周一06:00 到 周六05:00 全时段采集。
    """
    now = now or datetime.now()
    # 周六05:00后和周日全天不交易
    if now.weekday() == 5 and now.hour >= 5:
        return False
    if now.weekday() == 6:
        return False
    return True


# ─────────────────────────────────────────────
# 管道包装器（捕获异常）
# ─────────────────────────────────────────────
def _safe_run(name: str, func: Callable[..., Any], **kwargs: Any) -> None:
    """安全执行管道，捕获异常并记录日志 + 通知."""
    try:
        logger.info("▶ 开始执行: %s", name)
        t0 = time.time()
        result = func(**kwargs)
        elapsed = round(time.time() - t0, 2)
        total = sum(result.values()) if isinstance(result, dict) else 0
        logger.info("✅ %s 完成: %d 条记录, 耗时 %ss", name, total, elapsed)
        # 记录到通知器
        n = _get_notifier(kwargs.get("config"))
        if n:
            n.record_result(name, records=total, elapsed=elapsed, success=True)
    except Exception:
        logger.error("❌ %s 失败:\n%s", name, traceback.format_exc())
        n = _get_notifier(kwargs.get("config"))
        if n:
            n.record_result(name, records=0, elapsed=0, success=False, error=traceback.format_exc()[-200:])


# ─────────────────────────────────────────────
# 管道任务定义
# ─────────────────────────────────────────────
def _get_domestic_symbols() -> list[str]:
    """获取内盘合约列表（可从 config 动态扩展）。

    覆盖 14 个核心品种（含主力+次主力合约共 16 个）：
    SHFE: rb(螺纹钢), cu(铜), au(黄金), ag(白银), hc(热卷)
    DCE:  i(铁矿石), m(豆粕), p(棕榈油), c(玉米), y(豆油)
    CZCE: MA(甲醇), SA(纯碱), CF(棉花), TA(PTA)

    合约代码说明：
      SHFE/DCE  4位年月格式：rb2605 = 螺纹钢 2026年5月
      CZCE      3位格式：MA605 = 甲醇 2026年5月（年末尾单位数字 + 两位月份）
    """
    return [
        # SHFE（上期所）— 2026年当前活跃合约
        "SHFE.rb2605", "SHFE.rb2610",
        "SHFE.cu2606",
        "SHFE.au2606",
        "SHFE.ag2606",
        "SHFE.hc2605", "SHFE.hc2610",
        # DCE（大商所）— 2026年当前活跃合约
        "DCE.i2605", "DCE.i2609",
        "DCE.m2605", "DCE.m2609",
        "DCE.p2605",
        "DCE.c2605",
        "DCE.y2605",
        # CZCE（郑商所）— 2026年当前活跃合约
        "CZCE.MA605", "CZCE.MA609",
        "CZCE.SA605",
        "CZCE.CF605",
        "CZCE.TA605",
    ]


def _get_overseas_symbols() -> list[str]:
    """获取外盘合约列表（D106 扩展至 30 个品种）。"""
    return [
        # 能源 (5)
        "NYMEX.CL", "ICE.B", "NYMEX.NG",
        "NYMEX.HO", "NYMEX.RB",
        # 金属 - COMEX (5)
        "COMEX.GC", "COMEX.SI", "COMEX.HG",
        "NYMEX.PL", "NYMEX.PA",
        # 金属 - LME (6) — D106 新增
        "LME.AHD", "LME.CAD", "LME.NID",
        "LME.PBD", "LME.SND", "LME.ZSD",
        # 农产品 (7)
        "CBOT.ZS", "CBOT.ZC", "CBOT.ZW",
        "CBOT.ZM", "CBOT.ZL",
        "ICE.CT", "ICE.SB",
        # 股指 (4)
        "CME.ES", "CME.NQ", "CBOT.YM",
        "SGX.CN",
        # 其他 (3) — D107 修复
        "ICE.KC", "ICE.CC", "CME.RTY",
    ]


def job_minute_kline(config: dict[str, Any]) -> None:
    """[DEPRECATED] 分钟内盘K线 — 已由 futures_minute_scheduler.py plist 接管。

    旧实现使用硬编码 2405 合约（已过期）+ 内部 APScheduler 每2分钟触发。
    新方案: com.botquant.futures.minute.plist (每60s) + com.botquant.futures.eod.plist
    => scripts/futures_minute_scheduler.py --live / --eod
    本函数保留但不再注册到 scheduler，见下方注释。
    """
    # [DEPRECATED] 保留以备回滚，使用前需更新 _get_domestic_symbols() 为动态发现
    if not _is_trading_session():
        return
    from services.data.src.scheduler.pipeline import run_minute_pipeline
    symbols = _get_domestic_symbols()
    _safe_run("分钟内盘K线", run_minute_pipeline, symbols=symbols, config=config)


def job_daily_kline(config: dict[str, Any]) -> None:
    """日线K线 — 每日 17:00。"""
    from services.data.src.scheduler.pipeline import run_daily_pipeline
    symbols = _get_domestic_symbols()
    _safe_run("日线K线", run_daily_pipeline, symbols=symbols, config=config)


def job_overseas_kline(config: dict[str, Any]) -> None:
    """外盘日线 — 每日 17:00 (全部 30 品种)。"""
    from services.data.src.scheduler.pipeline import run_overseas_daily_pipeline
    symbols = _get_overseas_symbols()
    _safe_run("外盘日线", run_overseas_daily_pipeline, symbols=symbols, config=config)


def job_overseas_minute_yf(config: dict[str, Any]) -> None:
    """外盘分钟K线 (yfinance) — 每5分钟, 仅外盘交易时段。"""
    if not _is_overseas_trading_hours():
        return
    from services.data.src.scheduler.pipeline import run_overseas_minute_yf_pipeline
    _safe_run("外盘分钟K线(yfinance)", run_overseas_minute_yf_pipeline, config=config)


def job_stock_minute(config: dict[str, Any]) -> None:
    """A股分钟K线 — 每2分钟, 仅A股交易时段。"""
    if not _is_stock_trading_session():
        return
    from services.data.src.scheduler.pipeline import run_stock_minute_pipeline
    _safe_run("A股分钟K线", run_stock_minute_pipeline, config=config)


def job_tushare_futures(config: dict[str, Any]) -> None:
    """Tushare期货五合一 — 每日 17:00。"""
    from services.data.src.scheduler.pipeline import run_tushare_futures_pipeline
    today = datetime.now().strftime("%Y%m%d")
    for ts_code in ["RB2405.SHF", "I2405.DCE", "M2405.DCE"]:
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


def job_feishu_news_hourly(config: dict[str, Any]) -> None:
    """飞书新闻推送 — 每小时。"""
    from scripts.feishu_news_hourly import job_feishu_news_hourly as _run
    try:
        logger.info("▶ 开始执行: 飞书新闻推送")
        _run(config)
        logger.info("✅ 飞书新闻推送完成")
    except Exception:
        logger.error("❌ 飞书新闻推送失败:\n%s", traceback.format_exc())


def job_daily_summary(config: dict[str, Any]) -> None:
    """[DEPRECATED] 每日采集汇总 — 已被 heartbeat_card 替代，保留函数体以防残留调用。"""
    logger.info("[DEPRECATED] job_daily_summary 已被 2h 心跳卡片替代，跳过执行")


def job_evening_report(config: dict[str, Any]) -> None:
    """[DEPRECATED] 晚间审计日报 — 已被 heartbeat_card 替代，保留函数体以防残留调用。"""
    logger.info("[DEPRECATED] job_evening_report 已被 2h 心跳卡片替代，跳过执行")


def job_heartbeat(config: dict[str, Any]) -> None:
    """每 2 小时进程监控 — 推送 Mini + Studio 硬件 + 全进程状态卡片到飞书。"""
    try:
        logger.info("▶ 开始执行: 2h 进程监控")
        import os as _os
        import importlib.util
        import subprocess as _sp
        import json as _json

        # ── Mini 进程定义（27 个 plist，全覆盖）────────────────────────
        _MINI_PROCS = [
            ("数据采集调度",  "data_scheduler.py",           "com.botquant.data_scheduler"),
            ("设备监控",      "mini_monitor.py",             "com.botquant.mini_monitor"),
            ("健康检查",      "health_check.py",             "com.botquant.health"),
            ("数据 API",      "data_api",                    "com.botquant.data_api"),
            ("数据服务",      "data_server",                 "com.botquant.data_server"),
            ("期货日线",      "futures_minute_scheduler.py", "com.botquant.futures.eod"),
            ("期货分钟线",    "futures_minute_scheduler.py", "com.botquant.futures.minute"),
            ("宏观数据",      "macro_scheduler.py",          "com.botquant.macro"),
            ("VPN 代理",      "vpn_proxy_manager.py",        "com.botquant.mihomo"),
            ("新闻采集",      "news_scheduler.py",           "com.botquant.news"),
            ("海外日线",      "overseas_minute_scheduler.py","com.botquant.overseas.daily"),
            ("海外分钟线",    "overseas_minute_scheduler.py","com.botquant.overseas.minute"),
            ("持仓日报",      "position_scheduler.py",       "com.botquant.position.daily"),
            ("持仓周报",      "position_scheduler.py",       "com.botquant.position.weekly"),
            ("情绪指数",      "sentiment_scheduler.py",      "com.botquant.sentiment"),
            ("海运运费",      "shipping_scheduler.py",       "com.botquant.shipping"),
            ("A股分钟线",     "stock_minute_scheduler.py",   "com.botquant.stock.minute"),
            ("A股实时",       "stock_minute_scheduler.py",   "com.botquant.stock.realtime"),
            ("存储告警",      "storage_alert.sh",            "com.botquant.storage.alert"),
            ("Tushare日线",   "tushare_daily_scheduler.py",  "com.botquant.tushare"),
            ("美股日线",      "us_stock_backfill.py",        "com.botquant.us_stock_daily"),
            ("波动率CBOE",    "volatility_scheduler.py",     "com.botquant.volatility.cboe"),
            ("波动率QVIX",    "volatility_scheduler.py",     "com.botquant.volatility.qvix"),
            ("自选股监控",    "watchlist_manager.py",        "com.botquant.watchlist"),
            ("天气数据",      "weather_scheduler.py",        "com.botquant.weather"),
            ("每周备份",      "mini_backup_weekly.sh",       "com.botquant.backup.weekly"),
            ("每日审计",      "daily_audit.py",              "com.botquant.daily_audit"),
        ]
        # ── Studio 进程定义 ───────────────────────────────────────────
        _STUDIO_PROCS = [
            ("量化交易",     "factor_live_trader.py",     "com.botquant.factor.trader"),
            ("决策引擎 API", "decision_api",              "com.botquant.decision_api"),
            ("风控监控",     "risk_monitor.py",           "com.botquant.risk_monitor"),
            ("交易接口 API", "trading_api",               "com.botquant.trading_api"),
            ("盘前预测",     "prediction_report.py",      "com.botquant.prediction"),
            ("每日审计",     "daily_audit.py",            "com.botquant.daily_audit"),
            ("存储告警",     "storage_alert",             "com.botquant.storage.alert"),
        ]

        # ── 加载 health_check 模块 ────────────────────────────────────
        _hc_path = str(PROJECT_ROOT / "scripts" / "health_check.py")
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

        # ── Mini launchctl ────────────────────────────────────────────
        try:
            plist_out = _sp.run(
                ["launchctl", "list"], capture_output=True, text=True, timeout=10,
            ).stdout
        except Exception:
            plist_out = ""

        mini_processes = [
            {"label": label, "script": script,
             "ok": plist_name in plist_out}
            for label, script, plist_name in _MINI_PROCS
        ]

        # ── Studio 采集（SSH，超时 15s）────────────────────────────────
        _studio_hw_cmd = (
            "/Users/jaybot/J_BotQuant/.venv/bin/python3 -c \""
            "import psutil,json;"
            "m=psutil.virtual_memory();"
            "d={p.mountpoint:round(psutil.disk_usage(p.mountpoint).percent,1)"
            " for p in psutil.disk_partitions(all=False)"
            " if p.mountpoint in ['/','/Volumes/BotQuantSSD']};"
            "print(json.dumps({'cpu':psutil.cpu_percent(0.3),'mem':m.percent,'disks':d}))"
            "\""
        )
        studio_available = False
        studio_cpu = studio_mem = studio_main_disk = studio_ext_disk = 0.0
        studio_processes: list[dict[str, Any]] = []

        _ssh_cmd = ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
                    "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=2"]
        for _attempt in range(2):  # 最多重试1次，规避瞬间抖动
            try:
                _hw_res = _sp.run(
                    _ssh_cmd + ["studio", _studio_hw_cmd],
                    capture_output=True, text=True, timeout=20,
                )
                if _hw_res.returncode == 0 and _hw_res.stdout.strip():
                    _hw = _json.loads(_hw_res.stdout.strip())
                    studio_cpu = float(_hw.get("cpu", 0.0))
                    studio_mem = float(_hw.get("mem", 0.0))
                    _disks = _hw.get("disks", {})
                    studio_main_disk = float(_disks.get("/", 0.0))
                    studio_ext_disk = float(_disks.get("/Volumes/BotQuantSSD", 0.0))

                    # Studio launchctl
                    _lc_res = _sp.run(
                        _ssh_cmd + ["studio", "launchctl list"],
                        capture_output=True, text=True, timeout=15,
                    )
                    studio_lc = _lc_res.stdout if _lc_res.returncode == 0 else ""
                    studio_processes = [
                        {"label": label, "script": script,
                         "ok": plist_name in studio_lc}
                        for label, script, plist_name in _STUDIO_PROCS
                    ]
                    studio_available = True
                    logger.info("✅ Studio 硬件及进程状态已获取 cpu=%.1f%% mem=%.1f%%",
                                studio_cpu, studio_mem)
                    break
                else:
                    raise RuntimeError(f"ssh returncode={_hw_res.returncode} stderr={_hw_res.stderr[:80]}")
            except Exception as _e:
                if _attempt == 0:
                    logger.warning("⚠️ Studio SSH 第1次失败，3s后重试: %s", _e)
                    import time as _time_mod
                    _time_mod.sleep(3)
                else:
                    logger.warning("⚠️ Studio SSH 连接失败（已重试）: %s", _e)

        # ── 判断是否有异常 ─────────────────────────────────────────────
        has_issues = any(not s["ok"] and not s.get("skipped") for s in freshness)
        has_issues = has_issues or (mini_cpu >= 85) or (mini_mem >= 85)
        has_issues = has_issues or any(not p["ok"] for p in mini_processes)
        if studio_available:
            has_issues = has_issues or any(not p["ok"] for p in studio_processes)
        else:
            has_issues = True  # SSH 失败也算异常

        # from src.monitor.feishu_card_templates import heartbeat_card
        # from src.monitor.notify_feishu import FeishuNotifier

        now_str = datetime.now().strftime("%H:%M")
        card = heartbeat_card(
            time_str=now_str,
            mini_cpu=mini_cpu,
            mini_mem=mini_mem,
            mini_disk=mini_disk,
            studio_available=studio_available,
            studio_cpu=studio_cpu,
            studio_mem=studio_mem,
            studio_main_disk=studio_main_disk,
            studio_ext_disk=studio_ext_disk,
            sources=freshness,
            mini_processes=mini_processes,
            studio_processes=studio_processes,
            has_issues=has_issues,
        )
        webhook = _os.environ.get("FEISHU_ALERT_WEBHOOK_URL") or _os.environ.get("FEISHU_WEBHOOK_URL") or ""
        if webhook:
            notifier = FeishuNotifier(webhook_url=webhook, keyword="BotQuant 报警", mock_mode=False)
            res = notifier.send_card(card)
            logger.info("✅ 2h 进程监控已发送: ok=%s", res.ok)
        else:
            logger.warning("⚠️ 无飞书 webhook，跳过进程监控推送")
    except Exception:
        logger.error("❌ 2h 进程监控异常:\n%s", traceback.format_exc())


def _job_factor_session(config: dict[str, Any], session: str) -> None:
    """因子/信号分时段报告内部实现."""
    try:
        logger.info("▶ 开始执行: 因子/信号%s报告", session)
        # from src.strategy.factor_notifier import get_factor_notifier
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
        # from src.monitor.alert_sla_tracker import get_sla_tracker
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
        # from src.monitor.alert_sla_tracker import get_sla_tracker
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


def job_force_close(config: dict[str, Any]) -> None:
    """强制平仓检查 — 日盘 14:55 / 夜盘 22:55.

    检查当前是否到达强平时间，若是则执行全仓平仓。
    包含重试机制（最多 3 次），失败后飞书告警。
    """
    try:
        logger.info("▶ 开始执行: 强制平仓检查")
        # from src.risk.force_close import ForceCloseManager

        fc = ForceCloseManager()
        should, reason = fc.should_force_close()
        if not should:
            logger.info("✅ 强制平仓检查: 未到强平时间")
            return

        # 强平执行 (含重试)
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            logger.critical("🚨 强制平仓第 %d 次尝试: %s", attempt, reason)
            results = fc.execute_force_close(reason)

            if not results:
                logger.info("✅ 无持仓需要平仓")
                break

            failed = {s: ok for s, ok in results.items() if not ok}
            if not failed:
                logger.info("✅ 强制平仓全部成功: %d 品种", len(results))
                break

            logger.error("❌ 强制平仓部分失败 (attempt %d): %s", attempt, list(failed.keys()))
            if attempt < max_retries:
                time.sleep(2)

        # 飞书通知
        n = _get_notifier(config)
        if n:
            failed_list = list(failed.keys()) if failed else []
            if failed_list:
                n.record_result(
                    "强制平仓", records=0, elapsed=0, success=False,
                    error=f"部分品种平仓失败: {failed_list}",
                )
            else:
                n.record_result("强制平仓", records=len(results), elapsed=0, success=True)

    except Exception:
        logger.error("❌ 强制平仓异常:\n%s", traceback.format_exc())
        n = _get_notifier(config)
        if n:
            n.record_result(
                "强制平仓", records=0, elapsed=0, success=False,
                error=traceback.format_exc()[-200:],
            )


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

    # [DEPRECATED] 分钟内盘K线已由 plist 接管，此处禁用。
    # 新方案: com.botquant.futures.minute.plist (every 60s) → futures_minute_scheduler.py --live
    #         com.botquant.futures.eod.plist (11:35/15:20/23:05) → futures_minute_scheduler.py --eod
    # scheduler.add_job(
    #     job_minute_kline, IntervalTrigger(minutes=2),
    #     args=[config], id="minute_kline", name="分钟内盘K线",
    # )
    # 日线K线: 每日 17:00
    scheduler.add_job(
        job_daily_kline, CronTrigger(hour=17, minute=0, day_of_week="mon-fri"),
        args=[config], id="daily_kline", name="日线K线",
    )
    # [DEPRECATED] 外盘日线已由 plist 接管，此处禁用。
    # 新方案: com.botquant.overseas.daily.plist (每日17:30) → overseas_minute_scheduler.py --daily
    # scheduler.add_job(
    #     job_overseas_kline, CronTrigger(hour=17, minute=5, day_of_week="mon-fri"),
    #     args=[config], id="overseas_daily", name="外盘日线",
    # )
    # [DEPRECATED] 外盘分钟K线已由 plist 接管，此处禁用。
    # 新方案: com.botquant.overseas.minute.plist (每5min) → overseas_minute_scheduler.py --live
    # scheduler.add_job(
    #     job_overseas_minute_yf, IntervalTrigger(minutes=5),
    #     args=[config], id="overseas_minute_yf", name="外盘分钟K线(yfinance)",
    # )
    # [DEPRECATED] A股分钟K线已由 plist 接管，pipeline 模块亦有 httpx 导入错误
    # 新方案: com.botquant.stock.minute.plist (15:35) → stock_minute_scheduler.py
    # scheduler.add_job(
    #     job_stock_minute, IntervalTrigger(minutes=2),
    #     args=[config], id="stock_minute", name="A股分钟K线",
    # )
    # [DEPRECATED] Tushare期货 pipeline 有 httpx 导入错误；由 com.botquant.tushare plist 接管
    # scheduler.add_job(
    #     job_tushare_futures, CronTrigger(hour=17, minute=10, day_of_week="mon-fri"),
    #     args=[config], id="tushare_futures", name="Tushare期货五合一",
    # )
    # [DEPRECATED] 宏观数据已由 com.botquant.macro plist 接管 (macro_scheduler.py KeepAlive)
    # scheduler.add_job(
    #     job_macro, CronTrigger(hour=9, minute=0, day_of_week="mon-fri"),
    #     args=[config], id="macro", name="宏观数据",
    # )
    # [DEPRECATED] 持仓/仓单已由 com.botquant.position.daily plist 接管
    # scheduler.add_job(
    #     job_position, CronTrigger(hour=15, minute=30, day_of_week="mon-fri"),
    #     args=[config], id="position", name="持仓仓单日报",
    # )
    # [DEPRECATED] 新闻API已由 com.botquant.news plist 接管 (news_scheduler.py KeepAlive)
    # scheduler.add_job(
    #     job_news_api, IntervalTrigger(minutes=1),
    #     args=[config], id="news_api", name="新闻API",
    # )
    # [DEPRECATED] RSS聚合已由 com.botquant.news plist 接管
    # scheduler.add_job(
    #     job_rss, IntervalTrigger(minutes=10),
    #     args=[config], id="rss", name="RSS聚合",
    # )
    # [DEPRECATED] 波动率已由 com.botquant.volatility plist 接管 (17:40)
    # scheduler.add_job(
    #     job_volatility, CronTrigger(hour=17, minute=15, day_of_week="mon-fri"),
    #     args=[config], id="volatility", name="波动率指数",
    # )
    # [DEPRECATED] 情绪指数已由 com.botquant.sentiment plist 接管 (16:35 + Sat)
    # scheduler.add_job(
    #     job_sentiment, IntervalTrigger(minutes=5),
    #     args=[config], id="sentiment", name="情绪指数",
    # )
    # [DEPRECATED] 海运物流已由 com.botquant.shipping plist 接管 (17:45)
    # scheduler.add_job(
    #     job_shipping, CronTrigger(hour=9, minute=10, day_of_week="mon-fri"),
    #     args=[config], id="shipping", name="海运物流",
    # )
    # [DEPRECATED] 飞书新闻推送已由 com.botquant.news plist 接管
    # scheduler.add_job(
    #     job_feishu_news_hourly, IntervalTrigger(hours=1),
    #     args=[config], id="feishu_news_hourly", name="飞书新闻推送",
    # )
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
    # 强制平仓 — 日盘 14:55 (周一到周五)
    scheduler.add_job(
        job_force_close, CronTrigger(hour=14, minute=55, day_of_week="mon-fri"),
        args=[config], id="force_close_day", name="强制平仓(日盘)",
    )
    # 强制平仓 — 夜盘 22:55 (周一到周四)
    scheduler.add_job(
        job_force_close, CronTrigger(hour=22, minute=55, day_of_week="mon-thu"),
        args=[config], id="force_close_night", name="强制平仓(夜盘)",
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
    # ("分钟内盘K线", job_minute_kline, 120, None),  # [DEPRECATED] 由 plist 接管
    ("A股分钟K线",             job_stock_minute,        120,   None),
    ("外盘分钟K线(yfinance)",  job_overseas_minute_yf,  300,   None),
    ("日线K线",                job_daily_kline,         None,  "17:00"),
    ("外盘日线",               job_overseas_kline,      None,  "17:05"),
    ("Tushare期货五合一",      job_tushare_futures,     None,  "17:10"),
    ("宏观数据",               job_macro,               None,  "09:00"),
    ("持仓仓单日报",           job_position,            None,  "15:30"),
    ("新闻API",               job_news_api,             60,   None),
    ("RSS聚合",               job_rss,                 600,   None),
    ("波动率指数",             job_volatility,          None,  "17:15"),
    ("情绪指数",               job_sentiment,           300,   None),
    ("海运物流",               job_shipping,            None,  "09:10"),
    ("飞书新闻推送",           job_feishu_news_hourly,  3600,  None),
    ("每日采集汇总",           job_daily_summary,       None,  "23:00"),
    ("晚间审计日报",           job_evening_report,      None,  "23:05"),
    ("因子/信号早盘报告",      job_factor_signal_morning,    None, "11:35"),
    ("因子/信号午盘报告",      job_factor_signal_afternoon,  None, "15:05"),
    ("因子/信号收盘报告",      job_factor_signal_summary,    None, "23:05"),
    ("告警SLA日报",            job_sla_report,          None,  "23:15"),
    ("每日计数器重置",         job_daily_reset,         None,  "00:00"),
    ("SLA计数器重置",          job_sla_reset,           None,  "00:05"),
    ("NAS备份",               job_nas_backup,          None,  "03:00"),
    ("强制平仓(日盘)",         job_force_close,         None,  "14:55"),
    ("强制平仓(夜盘)",         job_force_close,         None,  "22:55"),
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
