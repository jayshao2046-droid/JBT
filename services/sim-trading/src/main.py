import logging
import os
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

# --- 日志初始化 ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
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


async def _ctp_connection_guardian():
    """后台守护协程：首次自动连接，之后定期检查 CTP 状态，断开则自动重连（含退避）。"""
    import asyncio

    user_id = os.getenv("SIMNOW_USER_ID", "")
    if not user_id:
        logger.info("[guardian] SIMNOW_USER_ID not set, guardian disabled")
        return

    FAST_INTERVAL = 30      # 正常检查间隔（秒）
    SLOW_INTERVAL = 300     # 连续失败后退避间隔（秒）
    MAX_FAST_RETRIES = 3    # 快速重试次数上限
    _fail_count = 0

    # 首次连接 — 等待服务完全启动
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

    # 守护循环 — 定期检查连接，断开则重连
    while True:
        interval = FAST_INTERVAL if _fail_count < MAX_FAST_RETRIES else SLOW_INTERVAL
        await asyncio.sleep(interval)
        try:
            from src.api.router import _get_gateway, _system_state
            gw = _get_gateway()
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
                if st["md_connected"] and st["td_connected"]:
                    _fail_count = 0
                    continue

            logger.info("[guardian] CTP disconnected (md=%s td=%s), reconnecting... (attempt %d)",
                        _system_state.get("ctp_md_connected"),
                        _system_state.get("ctp_td_connected"),
                        _fail_count + 1)
            from src.api.router import ctp_connect
            result = await asyncio.get_running_loop().run_in_executor(None, ctp_connect)
            if result.get("md_connected") or result.get("td_connected"):
                _fail_count = 0
                logger.info("[guardian] reconnect succeeded: %s", result)
            else:
                _fail_count += 1
                logger.info("[guardian] reconnect pending (md=%s td=%s), next check in %ds",
                            result.get("md_connected"), result.get("td_connected"),
                            FAST_INTERVAL if _fail_count < MAX_FAST_RETRIES else SLOW_INTERVAL)
        except Exception as exc:
            _fail_count += 1
            logger.warning("[guardian] reconnect error (attempt %d, retry in %ds): %s",
                           _fail_count,
                           FAST_INTERVAL if _fail_count < MAX_FAST_RETRIES else SLOW_INTERVAL,
                           exc)


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8101"))
    logger.info("Starting sim-trading on port %d", port)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
