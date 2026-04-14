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
    """全局 API Key 认证中间件，与 data/backtest/decision 三端保持一致。"""
    if not _SIM_API_KEY:
        return
    if request.url.path in _PUBLIC_PATHS:
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
    后台守护协程 — 单一时段真相源：
    - 交易时段：快速监控（30s）+ 断线重连 + 飞书告警
    - 盘前窗口：主动建连 + 检查点通知
    - 非交易时段（含周末）：完全静默，不连接、不监控、不告警
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
        dtime(13, 0), dtime(13, 10),
        dtime(20, 30), dtime(20, 50),
    ]
    # 盘前窗口：覆盖检查点时段，用于提前建连（交易时段之外的准备期）
    _PRE_SESSION_WINDOWS = [
        (dtime(8, 25), dtime(8, 55)),
        (dtime(12, 55), dtime(13, 0)),
        (dtime(20, 25), dtime(20, 55)),
    ]
    FAST_INTERVAL = 30          # 交易时段检查间隔（秒）
    PRE_INTERVAL = 60           # 盘前窗口检查间隔（秒）
    IDLE_INTERVAL = 300         # 非交易时段休眠间隔（秒）
    ACCOUNT_REFRESH = 120       # 账户刷新间隔（秒）
    MAX_FAST_RETRIES = 3
    _fail_count = 0
    _last_checkpoint = None     # 避免同一检查点重复通知
    _last_account_refresh = 0.0

    def _in_pre_session():
        """工作日盘前窗口判定（交易时段之前的准备期）"""
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

    # --- 首次连接：仅在交易时段或盘前窗口 ---
    await asyncio.sleep(2)
    if is_trading_session() or _in_pre_session():
        logger.info("[guardian] initial connect (in session or pre-session)")
        await _try_connect(silent=False)
    else:
        logger.info("[guardian] skip initial connect (outside trading hours)")

    # --- 守护循环 ---
    while True:
        in_session = is_trading_session()
        in_pre = _in_pre_session()

        if in_session:
            await asyncio.sleep(FAST_INTERVAL)
        elif in_pre:
            await asyncio.sleep(PRE_INTERVAL)
        else:
            # 非交易 + 非盘前 → 完全静默
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
                # 若未连接，先尝试建连再判断
                if not md_ok or not td_ok:
                    logger.info("[guardian] checkpoint %s: not fully connected, attempting connect", cp_str)
                    md_ok, td_ok = await _try_connect(silent=True)
                if not md_ok:
                    _send_guardian_alert("P1", "CTP_MD_DOWN", f"盘前检查({cp_str})：行情通道断开")
                if not td_ok:
                    _send_guardian_alert("P1", "CTP_TD_DOWN", f"盘前检查({cp_str})：交易通道断开")
                if md_ok and td_ok:
                    logger.info("[guardian] checkpoint %s: all OK", cp_str)

            # --- 交易时段：连续监控 + 重连 ---
            if in_session:
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
                md_ok, td_ok = await _try_connect(silent=True)
                if md_ok or td_ok:
                    try:
                        from src.notifier.dispatcher import get_dispatcher
                        dp = get_dispatcher()
                        if dp:
                            dp.emit_recovery("CTP_FRONT_DISCONNECTED")
                    except Exception:
                        pass
                elif _fail_count >= MAX_FAST_RETRIES:
                    _send_guardian_alert("P0", "CTP_RECONNECT_FAIL",
                                         f"交易时段连续{_fail_count}次重连失败")

        except Exception as exc:
            _fail_count += 1
            logger.warning("[guardian] error (attempt %d): %s", _fail_count, exc)


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8101"))
    logger.info("Starting sim-trading on port %d", port)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
