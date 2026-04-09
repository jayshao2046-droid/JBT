import collections
import logging
import os
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# --- 加载 .env（如存在）---
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file, override=False)

from src.api.router import router
from src.notifier.dispatcher import bootstrap_dispatcher


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

# --- FastAPI 应用 ---
app = FastAPI(title="sim-trading", version="0.1.0-skeleton")

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


@app.on_event("shutdown")
def on_shutdown():
    """服务关闭时发送系统关闭事件。"""
    try:
        from src.risk.guards import emit_alert
        emit_alert("P2", "模拟交易服务正在关闭", {"event_code": "SYSTEM_SHUTDOWN", "source": "sim-trading"})
    except Exception:
        pass


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


async def _ctp_connection_guardian():
    """
    后台守护协程：
    - 盘前检查点发送连接状态通知（08:30/08:50/13:00/13:10/20:30/20:50）
    - 交易时段（09:00-11:30, 13:00-15:00, 21:00-23:00）连续监控 + 断开重连
    - 非交易时段低频巡查
    - 非交易日只检查行情，不检查交易通道
    - 定期刷新账户余额
    """
    import asyncio
    from datetime import datetime, time as dtime

    user_id = os.getenv("SIMNOW_USER_ID", "")
    if not user_id:
        logger.info("[guardian] SIMNOW_USER_ID not set, guardian disabled")
        return

    # --- 交易时段 & 检查点 ---
    SESSIONS = [
        (dtime(9, 0), dtime(11, 30)),
        (dtime(13, 0), dtime(15, 0)),
        (dtime(21, 0), dtime(23, 0)),
    ]
    CHECKPOINTS = [
        dtime(8, 30), dtime(8, 50),
        dtime(13, 0), dtime(13, 10),
        dtime(20, 30), dtime(20, 50),
    ]
    FAST_INTERVAL = 30          # 交易时段检查间隔（秒）
    SLOW_INTERVAL = 300         # 非交易时段检查间隔（秒）
    ACCOUNT_REFRESH = 120       # 账户刷新间隔（秒）
    MAX_FAST_RETRIES = 3
    _fail_count = 0
    _last_checkpoint = None     # 避免同一检查点重复通知
    _last_account_refresh = 0.0

    def _is_weekend():
        return datetime.now().weekday() >= 5

    def _in_session():
        now = datetime.now().time()
        return any(s <= now < e for s, e in SESSIONS)

    def _check_checkpoint():
        """返回匹配的检查点 time 或 None"""
        now = datetime.now().time()
        for cp in CHECKPOINTS:
            # 检查点 ±2 分钟内触发一次
            cp_min = cp.hour * 60 + cp.minute
            now_min = now.hour * 60 + now.minute
            if abs(now_min - cp_min) <= 2:
                return cp
        return None

    def _send_guardian_alert(level: str, code: str, reason: str):
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
            )
            dp.dispatch(evt)
        except Exception as exc:
            logger.warning("[guardian] alert dispatch error: %s", exc)

    # --- 首次连接 ---
    await asyncio.sleep(2)
    try:
        from src.api.router import ctp_connect
        result = await asyncio.get_running_loop().run_in_executor(None, ctp_connect)
        logger.info("[guardian] initial connect: %s", result)
        if result.get("md_connected") or result.get("td_connected"):
            _fail_count = 0
        else:
            _fail_count += 1
    except Exception as exc:
        logger.warning("[guardian] initial connect failed: %s", exc)
        _fail_count += 1

    # --- 守护循环 ---
    while True:
        in_session = _in_session()
        is_weekend = _is_weekend()
        interval = FAST_INTERVAL if in_session and not is_weekend else SLOW_INTERVAL
        await asyncio.sleep(interval)

        try:
            from src.api.router import _get_gateway, _system_state
            gw = _get_gateway()

            # --- 更新系统状态 ---
            if gw is not None:
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

                # --- 盘前检查点通知 ---
                cp = _check_checkpoint()
                if cp is not None and cp != _last_checkpoint:
                    _last_checkpoint = cp
                    cp_str = f"{cp.hour:02d}:{cp.minute:02d}"
                    if not md_ok:
                        _send_guardian_alert("P1", "CTP_MD_DOWN", f"盘前检查({cp_str})：行情通道断开")
                    if not td_ok and not is_weekend:
                        _send_guardian_alert("P1", "CTP_TD_DOWN", f"盘前检查({cp_str})：交易通道断开")
                    if md_ok and (td_ok or is_weekend):
                        logger.info("[guardian] checkpoint %s: all OK (weekend=%s)", cp_str, is_weekend)

                # --- 交易时段：连续监控 + 重连 ---
                if in_session and not is_weekend:
                    if md_ok and td_ok:
                        _fail_count = 0
                        # 定期刷新账户
                        import time as _time
                        now_ts = _time.time()
                        if now_ts - _last_account_refresh > ACCOUNT_REFRESH:
                            gw.query_account()
                            _last_account_refresh = now_ts
                        continue

                    # 断开 → 重连
                    logger.info("[guardian] session monitor: md=%s td=%s, reconnecting (attempt %d)",
                                md_ok, td_ok, _fail_count + 1)
                    from src.api.router import ctp_connect
                    result = await asyncio.get_running_loop().run_in_executor(None, lambda: ctp_connect(silent=True))
                    if result.get("md_connected") or result.get("td_connected"):
                        _fail_count = 0
                        try:
                            from src.notifier.dispatcher import get_dispatcher
                            dp = get_dispatcher()
                            if dp:
                                dp.emit_recovery("CTP_FRONT_DISCONNECTED")
                        except Exception:
                            pass
                    else:
                        _fail_count += 1
                        if _fail_count == MAX_FAST_RETRIES:
                            _send_guardian_alert("P0", "CTP_RECONNECT_FAIL",
                                                 f"交易时段连续{_fail_count}次重连失败")
                elif not in_session:
                    # 非交易时段：只补连，不强制报警
                    if not md_ok or (not td_ok and not is_weekend):
                        from src.api.router import ctp_connect
                        await asyncio.get_running_loop().run_in_executor(None, lambda: ctp_connect(silent=True))
                    _fail_count = 0
            else:
                # gateway 未创建
                _fail_count += 1

        except Exception as exc:
            _fail_count += 1
            logger.warning("[guardian] error (attempt %d): %s", _fail_count, exc)


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8101"))
    logger.info("Starting sim-trading on port %d", port)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
