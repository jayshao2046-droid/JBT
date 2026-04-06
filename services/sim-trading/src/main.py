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


@app.get("/health", tags=["infra"])
def health_check():
    """健康检查端点，供 Docker / 负载均衡探活使用。"""
    return {"status": "ok", "service": "sim-trading"}


@app.on_event("startup")
async def auto_connect_ctp():
    """启动时若环境变量中有 SimNow 凭证，自动尝试 CTP 连接（失败静默，不影响服务启动）。"""
    user_id = os.getenv("SIMNOW_USER_ID", "")
    if not user_id:
        logger.info("SIMNOW_USER_ID not set, skipping auto-connect")
        return
    try:
        from src.api.router import ctp_connect
        result = ctp_connect()
        logger.info("Auto CTP connect result: %s", result)
    except Exception as exc:
        logger.warning("Auto CTP connect failed (non-fatal): %s", exc)


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8101"))
    logger.info("Starting sim-trading on port %d", port)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
