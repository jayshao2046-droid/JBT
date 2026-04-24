import collections
import hmac
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import APIKeyHeader

# --- 加载 .env（如存在）---
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file, override=False)

from src.api.router import router
from src.notifier.dispatcher import bootstrap_dispatcher

# 初始化系统启动时间
from src.api.router import _system_state
import time
_system_state["start_time"] = time.time()


# --- 内存日志 Handler ---
_MEMORY_LOG_MAX = 2000

class MemoryLogHandler(logging.Handler):
    """将日志记录保存到内存 deque，供只读 API 查询。"""

    def __init__(self, maxlen: int = _MEMORY_LOG_MAX):
        super().__init__()
        self.records: collections.deque = collections.deque(maxlen=maxlen)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append({
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "source": record.name,
            "message": self.format(record),
        })


memory_log_handler = MemoryLogHandler(maxlen=_MEMORY_LOG_MAX)
memory_log_handler.setFormatter(logging.Formatter("%(message)s"))


# --- 日志初始化 ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
# 注册内存 handler 到 root logger
logging.getLogger().addHandler(memory_log_handler)

logger = logging.getLogger("sim-trading")

# --- API Key 认证 ---
_SIM_API_KEY = os.environ.get("SIM_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_PUBLIC_PATHS = {"/health", "/api/v1/health", "/api/v1/version"}


async def _verify_api_key(request: Request, api_key: Optional[str] = Depends(_api_key_header)) -> None:
    """全局 API Key 认证中间件（P1-1 修复：生产环境强制验证）。"""
    if request.url.path in _PUBLIC_PATHS:
        return

    # P1-1 修复：生产环境必须配置 API Key
    env = os.environ.get("JBT_ENV", "development").lower()
    if not _SIM_API_KEY:
        if env == "production":
            raise HTTPException(
                status_code=503,
                detail="SIM_API_KEY not configured in production environment"
            )
        # 开发环境允许未配置 API Key
        return

    if not api_key or not hmac.compare_digest(api_key, _SIM_API_KEY):
        raise HTTPException(status_code=403, detail="invalid or missing API key")


# --- FastAPI 应用 ---
app = FastAPI(title="sim-trading", version="1.0.0", dependencies=[Depends(_verify_api_key)])

app.include_router(router)


def bootstrap_notifier_dispatcher(force: bool = False):
    """初始化通知 dispatcher，并挂到 app.state 供风险钩子/路由复用。"""
    dispatcher = bootstrap_dispatcher(force=force)
    app.state.notifier_dispatcher = dispatcher
    logger.info("Notifier dispatcher bootstrapped")
    return dispatcher


@app.get("/health", tags=["infra"])
def health_check():
    """健康检查端点，供 Docker / 负载均衡探活使用。"""
    return {"status": "ok", "service": "sim-trading"}


@app.on_event("startup")
def bootstrap_notifications():
    bootstrap_notifier_dispatcher(force=True)


@app.on_event("startup")
async def start_ctp_guardian():
    """启动 CTP 连接守护协程：自动连接 + 断开后定期重连。"""
    import asyncio
    asyncio.create_task(_ctp_connection_guardian())


@app.on_event("startup")
async def start_report_scheduler():
    """启动收盘报表定时调度协程（每日 23:10 UTC+8）。"""
    import asyncio
    asyncio.create_task(_report_scheduler())


@app.on_event("startup")
async def start_heartbeat_scheduler():
    """启动心跳健康报告调度协程（每 4 小时整点，08:00–24:00 推送）。"""
    import asyncio
    asyncio.create_task(_heartbeat_scheduler())


@app.on_event("shutdown")
def on_shutdown():
    """服务关闭时清理资源。"""
    logger.info("sim-trading shutting down")


async def _report_scheduler():
    """每日 23:10 UTC+8 触发收盘报表生成与邮件发送。"""
    import asyncio
    from datetime import datetime, timedelta, timezone

    TZ_CN = timezone(timedelta(hours=8))
    REPORT_HOUR = 23
    REPORT_MINUTE = 10

    logger.info("[scheduler] report scheduler started, target %02d:%02d UTC+8", REPORT_HOUR, REPORT_MINUTE)

    while True:
        now = datetime.now(TZ_CN)
        target = now.replace(hour=REPORT_HOUR, minute=REPORT_MINUTE, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        logger.info("[scheduler] next report at %s (%.0f seconds)", target.isoformat(), wait_seconds)
        await asyncio.sleep(wait_seconds)

        try:
            from src.ledger.service import LedgerService
            from src.notifier.email import send_daily_report_email

            ledger = LedgerService()
            report = ledger.generate_daily_report()
            result = send_daily_report_email(report)
            logger.info("[scheduler] daily report sent: %s", result)
        except Exception as exc:
            logger.error("[scheduler] daily report failed: %s", exc)


async def _heartbeat_scheduler():
    """每 4 小时整点触发心跳健康报告推送到飞书（00:11–07:59 静默，其余可推送）。"""
    import asyncio
    from datetime import datetime, timedelta

    logger.info("[heartbeat] scheduler started, interval=4h, push_window=08:00-24:10")

    # 等待到下一个 4 小时整点（08/12/16/20/00，00:00–00:10 允许，00:11–07:59 跳到 08:00）
    while True:
        now = datetime.now()
        current_hour = now.hour

        # 计算下一个 4 小时整点
        next_hour = ((current_hour // 4) * 4 + 4) % 24

        # 如果落在静默时段（04，04:00 即 00:11–07:59 范围内），跳到 08 点
        if 1 <= next_hour <= 7:
            next_hour = 8

        target = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)

        # 如果跨天或已过当前时间，加一天
        if target <= now:
            target += timedelta(days=1)
            # 跨天后如果是静默时段（01–07），跳到 8 点
            if 1 <= target.hour <= 7:
                target = target.replace(hour=8, minute=0, second=0, microsecond=0)

        wait_seconds = (target - now).total_seconds()
        logger.info("[heartbeat] next report at %s (%.0f seconds)", target.strftime("%Y-%m-%d %H:%M:%S"), wait_seconds)
        await asyncio.sleep(wait_seconds)

        try:
            from src.health.heartbeat import generate_heartbeat_report, send_heartbeat_to_feishu

            report = generate_heartbeat_report()
            success = send_heartbeat_to_feishu(report)
            if success:
                logger.info("[heartbeat] report sent: status=%s", report.get("status"))
            else:
                logger.warning("[heartbeat] report send failed")
        except Exception as exc:
            logger.error("[heartbeat] scheduler error: %s", exc)


async def _ctp_connection_guardian():
    """
    后台守护协程 — 单一时段真相源：
    - 交易时段（9:00-11:30 / 13:00-15:00 / 21:00-23:00）：快速监控 + 断线重连 + 告警
    - 盘前窗口：主动建连 + 检查点通知
    - 收盘后 5 分钟（11:35 / 15:05 / 23:05）：推送 Session 交易总结
    - 非交易时段（含周末）：完全静默
    """
    import asyncio
    from datetime import datetime, time as dtime
    from src.gateway.simnow import is_trading_session

    user_id = os.getenv("SIMNOW_USER_ID", "")
    if not user_id:
        logger.info("[guardian] SIMNOW_USER_ID not set, guardian disabled")
        return

    # --- 盘前检查点（仅工作日触发）---
    CHECKPOINTS = [
        dtime(8, 30), dtime(8, 50),
        dtime(12, 40), dtime(12, 50),
        dtime(20, 30), dtime(20, 50),
    ]
    # 盘前窗口：检查点时段 + 盘前准备
    _PRE_SESSION_WINDOWS = [
        (dtime(8, 25), dtime(9, 0)),
        (dtime(12, 35), dtime(13, 0)),
        (dtime(20, 25), dtime(21, 0)),
    ]
    # 收盘总结时间点（收盘后 5 分钟）
    _SESSION_CLOSE_SUMMARIES = [
        (dtime(11, 35), "上午盘"),
        (dtime(15, 5), "下午盘"),
        (dtime(23, 5), "夜盘"),
    ]
    # 开盘前 5 分钟检查点（check_time, open_time, label）
    _PREOPEN_CHECKS = [
        (dtime(8, 55),  dtime(9, 0),  "上午盘"),
        (dtime(12, 55), dtime(13, 0), "下午盘"),
        (dtime(20, 55), dtime(21, 0), "夜盘"),
    ]
    # 开盘通知时间点
    _SESSION_OPENS = [
        (dtime(9, 0),  "上午盘"),
        (dtime(13, 0), "下午盘"),
        (dtime(21, 0), "夜盘"),
    ]
    FAST_INTERVAL = 30          # 交易时段检查间隔（秒）
    PRE_INTERVAL = 60           # 盘前窗口检查间隔（秒）
    IDLE_INTERVAL = 300         # 非交易时段休眠间隔（秒）
    ACCOUNT_REFRESH = 120       # 账户刷新间隔（秒）
    MAX_FAST_RETRIES = 3
    RECONNECT_ALERT_COOLDOWN = 600      # 交易时段：断联超 10 分钟才发飞书报警（止噪）
    IDLE_DISCONNECT_ALERT_COOLDOWN = 1800  # 非交易时段：每 30 分钟发一次飞书断联通知
    _fail_count = 0
    _last_checkpoint = None     # 避免同一检查点重复通知
    _last_account_refresh = 0.0
    _last_summary_sent = None   # 避免同一收盘总结重复推送
    _last_preopen_sent = None   # 避免同一开盘前检查重复触发
    _last_open_sent = None      # 避免同一开盘通知重复推送
    _last_reconnect_alert_ts = 0.0
    _last_idle_disconnect_alert_ts = 0.0  # 非交易时段断联通知冷却
    _session_disconnect_ts: Optional[float] = None  # 交易时段首次断联时间戳

    def _in_pre_session():
        """工作日盘前窗口判定"""
        if datetime.now().weekday() >= 5:
            return False
        now_t = datetime.now().time()
        return any(s <= now_t < e for s, e in _PRE_SESSION_WINDOWS)

    def _check_checkpoint():
        """返回匹配的检查点 time 或 None（周末返回 None）"""
        if datetime.now().weekday() >= 5:
            return None
        now_t = datetime.now().time()
        for cp in CHECKPOINTS:
            cp_min = cp.hour * 60 + cp.minute
            now_min = now_t.hour * 60 + now_t.minute
            if abs(now_min - cp_min) <= 2:
                return cp
        return None

    def _check_session_close():
        """返回匹配的收盘总结 (time, label) 或 None"""
        if datetime.now().weekday() >= 5:
            return None
        now_t = datetime.now().time()
        for close_time, label in _SESSION_CLOSE_SUMMARIES:
            close_min = close_time.hour * 60 + close_time.minute
            now_min = now_t.hour * 60 + now_t.minute
            if abs(now_min - close_min) <= 2:
                return (close_time, label)
        return None

    def _check_preopen():
        """返回匹配的开盘前5分钟检查点 (check_time, open_time, label) 或 None"""
        if datetime.now().weekday() >= 5:
            return None
        now_t = datetime.now().time()
        for check_t, open_t, label in _PREOPEN_CHECKS:
            check_min = check_t.hour * 60 + check_t.minute
            now_min = now_t.hour * 60 + now_t.minute
            if abs(now_min - check_min) <= 2:
                return (check_t, open_t, label)
        return None

    def _check_open():
        """返回匹配的开盘时间点 (open_time, label) 或 None"""
        if datetime.now().weekday() >= 5:
            return None
        now_t = datetime.now().time()
        for open_t, label in _SESSION_OPENS:
            open_min = open_t.hour * 60 + open_t.minute
            now_min = now_t.hour * 60 + now_t.minute
            if abs(now_min - open_min) <= 2:
                return (open_t, label)
        return None

    def _send_guardian_alert(level: str, code: str, reason: str, category: str = ""):
        """通过 dispatcher 发送飞书/邮件通知"""
        try:
            from src.notifier.dispatcher import get_dispatcher, RiskEvent
            dp = get_dispatcher()
            if dp is None:
                return
            evt = RiskEvent(
                task_id="GUARDIAN",
                stage_preset="sim",
                risk_level=level,
                account_id=user_id,
                strategy_id="",
                symbol="",
                signal_id="",
                trace_id="",
                event_code=code,
                reason=reason,
                category=category,
            )
            dp.dispatch(evt)
        except Exception as exc:
            logger.warning("[guardian] alert dispatch error: %s", exc)

    def _send_session_summary(label: str):
        """推送收盘 Session 交易总结"""
        try:
            from src.ledger.service import get_ledger
            ledger = get_ledger()
            summary = ledger.get_account_summary()
            trades = summary.get("trades", [])
            trade_count = summary.get("trade_count", 0)
            total_pnl = summary.get("total_pnl", 0.0)
            win_count = summary.get("win_count", 0)

            if trade_count == 0:
                reason = f"📊 {label}收盘总结：无成交"
            else:
                win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0.0
                reason = (f"📊 {label}收盘总结：{trade_count}笔成交，"
                          f"盈亏 {total_pnl:+.2f}，胜率 {win_rate:.0f}%")

            _send_guardian_alert("P2", "SESSION_CLOSE_SUMMARY", reason, category="交易")
            logger.info("[guardian] session summary sent: %s", reason)
        except Exception as exc:
            logger.warning("[guardian] session summary error: %s", exc)

    def _send_preopen_check(label: str):
        """开盘前5分钟：检查 CTP 登录 + 账户数据回传；未就绪发 P0 告警。"""
        try:
            from src.api.router import _get_gateway
            gw = _get_gateway()
            if gw is None:
                _send_guardian_alert(
                    "P0", "PREOPEN_CTP_NOT_READY",
                    f"⚠️ {label}开盘前5分钟：CTP 网关未启动，请立即检查！", "SYSTEM"
                )
                return
            st = gw.status
            md_ok = st.get("md_connected", False)
            td_ok = st.get("td_connected", False)
            # 检查账户数据是否已回传
            has_account = False
            try:
                from src.ledger.service import get_ledger
                summary = get_ledger().get_account_summary()
                has_account = bool(summary and summary.get("balance") is not None)
            except Exception:
                pass
            if not td_ok or not md_ok:
                _send_guardian_alert(
                    "P0", "PREOPEN_CTP_NOT_READY",
                    f"⚠️ {label}开盘前5分钟：CTP 未登录（md={md_ok}, td={td_ok}），请立即处理！", "SYSTEM"
                )
            elif not has_account:
                _send_guardian_alert(
                    "P1", "PREOPEN_ACCOUNT_NOT_READY",
                    f"⚠️ {label}开盘前5分钟：CTP 已连接但账户数据未回传，请检查", "SYSTEM"
                )
            else:
                _send_guardian_alert(
                    "P2", "PREOPEN_READY",
                    f"✅ {label}开盘前5分钟检查通过：CTP 已登录，账户数据就绪", "交易"
                )
                logger.info("[guardian] preopen check OK: %s", label)
        except Exception as exc:
            logger.warning("[guardian] preopen check error: %s", exc)
            _send_guardian_alert(
                "P1", "PREOPEN_CHECK_ERROR",
                f"{label}开盘前5分钟检查异常: {exc}", "SYSTEM"
            )

    def _send_open_notification(label: str):
        """开盘时推送开盘飞书通知。"""
        try:
            from src.api.router import _get_gateway
            gw = _get_gateway()
            st = gw.status if gw else {}
            md_ok = st.get("md_connected", False)
            td_ok = st.get("td_connected", False)
            status_str = "CTP 已连接" if (md_ok and td_ok) else f"CTP 异常（md={md_ok}, td={td_ok}）"
            _send_guardian_alert(
                "P2", "SESSION_OPEN",
                f"🔔 {label}开盘 — {status_str}", "交易"
            )
            logger.info("[guardian] open notification sent: %s", label)
        except Exception as exc:
            logger.warning("[guardian] open notification error: %s", exc)

    async def _try_connect(silent: bool = True):
        """尝试 CTP 建连，返回 (md_ok, td_ok)"""
        nonlocal _fail_count
        try:
            from src.api.router import ctp_connect
            result = await asyncio.get_running_loop().run_in_executor(
                None, lambda: ctp_connect(silent=silent),
            )
            md_ok = result.get("md_connected", False)
            td_ok = result.get("td_connected", False)
            if md_ok or td_ok:
                _fail_count = 0
            else:
                _fail_count += 1
            return md_ok, td_ok
        except Exception as exc:
            _fail_count += 1
            logger.warning("[guardian] connect failed (attempt %d): %s", _fail_count, exc)
            return False, False

    # --- 首次连接：24h 保持连接，无条件建连 ---
    await asyncio.sleep(2)
    logger.info("[guardian] initial connect (24h keepalive mode)")
    await _try_connect(silent=False)

    # --- 守护循环 ---
    while True:
        in_session = is_trading_session()
        in_pre = _in_pre_session()

        if in_session:
            await asyncio.sleep(FAST_INTERVAL)
        elif in_pre:
            await asyncio.sleep(PRE_INTERVAL)
        else:
            # 非交易 + 非盘前 → 检查收盘总结 + 24h 保持 CTP 连接
            sc = _check_session_close()
            if sc is not None and sc[0] != _last_summary_sent:
                _last_summary_sent = sc[0]
                _send_session_summary(sc[1])
            # 24h 保持连接：非交易时段也检查并重连（断联每 30 分钟飞书通知一次）
            try:
                import time as _time
                from src.api.router import _get_gateway
                gw_idle = _get_gateway()
                if gw_idle is None:
                    logger.info("[guardian] idle: gateway not created, attempting connect")
                    await _try_connect(silent=True)
                else:
                    st_idle = gw_idle.status
                    if not st_idle.get("md_connected") or not st_idle.get("td_connected"):
                        logger.info("[guardian] idle: disconnected (md=%s td=%s), reconnecting",
                                    st_idle.get("md_connected"), st_idle.get("td_connected"))
                        md_r, td_r = await _try_connect(silent=True)
                        if not md_r or not td_r:
                            # 重连失败 → 每 30 分钟才发一次飞书通知，防止信息爆炸
                            now_idle_ts = _time.time()
                            if now_idle_ts - _last_idle_disconnect_alert_ts >= IDLE_DISCONNECT_ALERT_COOLDOWN:
                                _send_guardian_alert(
                                    "P1", "CTP_IDLE_DISCONNECTED",
                                    f"非交易时段 CTP 断联（md={st_idle.get('md_connected')}, "
                                    f"td={st_idle.get('td_connected')}），持续断联中，下次通知间隔 30 分钟",
                                    "SYSTEM"
                                )
                                _last_idle_disconnect_alert_ts = now_idle_ts
                        else:
                            # 重连成功，重置冷却（恢复不单独通知，避免扰动）
                            _last_idle_disconnect_alert_ts = 0.0
            except Exception as exc_idle:
                logger.warning("[guardian] idle reconnect error: %s", exc_idle)
            await asyncio.sleep(IDLE_INTERVAL)
            continue

        try:
            from src.api.router import _get_gateway, _system_state
            gw = _get_gateway()

            # --- gateway 未创建 → 尝试建连 ---
            if gw is None:
                logger.info("[guardian] gateway not created, attempting connect")
                await _try_connect(silent=not in_session)
                continue

            # --- 同步系统状态 ---
            st = gw.status
            _system_state["ctp_md_connected"] = st["md_connected"]
            _system_state["ctp_td_connected"] = st["td_connected"]
            if st.get("last_md_disconnect_reason") is not None:
                _system_state["last_disconnect_reason"] = st["last_md_disconnect_reason"]
                _system_state["last_disconnect_time"] = st.get("last_md_disconnect_time")
            if st.get("last_td_disconnect_reason") is not None:
                _system_state["last_disconnect_reason"] = st["last_td_disconnect_reason"]
                _system_state["last_disconnect_time"] = st.get("last_td_disconnect_time")

            md_ok = st["md_connected"]
            td_ok = st["td_connected"]

            # --- 盘前检查点（仅工作日）---
            cp = _check_checkpoint()
            if cp is not None and cp != _last_checkpoint:
                _last_checkpoint = cp
                cp_str = f"{cp.hour:02d}:{cp.minute:02d}"
                if not md_ok or not td_ok:
                    logger.info("[guardian] checkpoint %s: not fully connected, attempting connect", cp_str)
                    md_ok, td_ok = await _try_connect(silent=True)
                if not md_ok:
                    _send_guardian_alert("P1", "CTP_MD_DOWN", f"盘前检查({cp_str})：行情通道断开")
                if not td_ok:
                    _send_guardian_alert("P1", "CTP_TD_DOWN", f"盘前检查({cp_str})：交易通道断开")
                if md_ok and td_ok:
                    logger.info("[guardian] checkpoint %s: all OK", cp_str)

            # --- 开盘前 5 分钟预检（09:00/13:00/21:00 前 5 分钟）---
            po = _check_preopen()
            if po is not None and po[0] != _last_preopen_sent:
                _last_preopen_sent = po[0]
                _send_preopen_check(po[2])

            # --- 开盘通知（09:00/13:00/21:00）---
            op = _check_open()
            if op is not None and op[0] != _last_open_sent:
                _last_open_sent = op[0]
                _send_open_notification(op[1])

            # --- 收盘总结检查 ---
            sc = _check_session_close()
            if sc is not None and sc[0] != _last_summary_sent:
                _last_summary_sent = sc[0]
                _send_session_summary(sc[1])

            # --- 交易时段：连续监控 + 重连 ---
            if in_session:
                if md_ok and td_ok:
                    _fail_count = 0
                    _session_disconnect_ts = None  # 重置断联计时
                    # 定期刷新账户
                    import time as _time
                    now_ts = _time.time()
                    if now_ts - _last_account_refresh > ACCOUNT_REFRESH:
                        gw.query_account()
                        _last_account_refresh = now_ts
                    continue

                # 断开 → 记录首次断联时间戳
                import time as _time
                now_ts = _time.time()
                if _session_disconnect_ts is None:
                    _session_disconnect_ts = now_ts
                disconnect_duration = now_ts - _session_disconnect_ts

                # 尝试重连
                logger.info("[guardian] session monitor: md=%s td=%s, reconnecting (%.0fs since disconnect)",
                            md_ok, td_ok, disconnect_duration)
                md_ok, td_ok = await _try_connect(silent=True)
                if md_ok or td_ok:
                    _session_disconnect_ts = None  # 重连成功，清除计时
                    try:
                        from src.notifier.dispatcher import get_dispatcher
                        dp = get_dispatcher()
                        if dp:
                            dp.emit_recovery("CTP_FRONT_DISCONNECTED")
                    except Exception:
                        pass
                else:
                    # 3 分钟内未连回才发飞书报警，冷却期内不重复
                    if (disconnect_duration >= RECONNECT_ALERT_COOLDOWN
                            and now_ts - _last_reconnect_alert_ts >= RECONNECT_ALERT_COOLDOWN):
                        # 发送前再确认状态，避免抖动恢复后的误报
                        st2 = gw.status if gw else {}
                        md_still_down = not st2.get("md_connected", False)
                        td_still_down = not st2.get("td_connected", False)
                        if md_still_down and td_still_down:
                            _send_guardian_alert(
                                "P0", "CTP_RECONNECT_FAIL",
                                f"交易时段断联已 {disconnect_duration:.0f}s，持续重连失败，请立即检查"
                            )
                            _last_reconnect_alert_ts = now_ts

        except Exception as exc:
            _fail_count += 1
            logger.warning("[guardian] error (attempt %d): %s", _fail_count, exc)


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8101"))
    logger.info("Starting sim-trading on port %d", port)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)


@app.get("/api/v1/notify/health", tags=["notify"])
def notify_health():
    """
    通知通道健康检查端点。
    返回当前 dispatcher 风险状态与飞书三群 Webhook 配置情况。
    """
    from src.notifier.dispatcher import get_dispatcher
    dp = get_dispatcher()
    state = dp.state.value if dp else "NOT_INITIALIZED"

    feishu_enabled = os.environ.get("NOTIFY_FEISHU_ENABLED", "false").lower() == "true"
    email_enabled = os.environ.get("NOTIFY_EMAIL_ENABLED", "false").lower() == "true"

    webhooks = {
        "alert": bool(os.environ.get("FEISHU_ALERT_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL")),
        "trade": bool(os.environ.get("FEISHU_TRADE_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL")),
        "info":  bool(os.environ.get("FEISHU_INFO_WEBHOOK_URL") or os.environ.get("FEISHU_WEBHOOK_URL")),
    }

    return {
        "dispatcher_state": state,
        "feishu_enabled": feishu_enabled,
        "email_enabled": email_enabled,
        "webhooks_configured": webhooks,
        "service": "sim-trading",
    }
