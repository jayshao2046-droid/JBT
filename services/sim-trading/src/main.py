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


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8101"))
    logger.info("Starting sim-trading on port %d", port)
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
