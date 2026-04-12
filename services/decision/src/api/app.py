import hmac
import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import APIKeyHeader

from .routes.health import router as health_router
from .routes.strategy import router as strategy_router
from .routes.signal import router as signal_router
from .routes.approval import router as approval_router
from .routes.model import router as model_router
from .routes.strategy_import import router as strategy_import_router
from .routes.sandbox import router as sandbox_router
from .routes.report import router as report_router
from .routes.optimizer import router as optimizer_router
from .routes.screener import router as screener_router
from .routes.import_channel import router as import_channel_router
from .routes.stock_template import router as stock_template_router

_DECISION_API_KEY = os.environ.get("DECISION_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_PUBLIC_PATHS = {"/health", "/ready"}


async def _verify_api_key(
    request: Request, api_key: Optional[str] = Depends(_api_key_header)
) -> None:
    if not _DECISION_API_KEY:
        return
    if request.url.path in _PUBLIC_PATHS:
        return
    if not api_key or not hmac.compare_digest(api_key, _DECISION_API_KEY):
        raise HTTPException(status_code=403, detail="invalid or missing API key")


def create_app() -> FastAPI:
    app = FastAPI(
        title="JBT Decision Service",
        version="0.1.0",
        description="JBT 决策服务 — 编排因子、信号与审批流程，生成标准化交易指令",
        dependencies=[Depends(_verify_api_key)],
    )

    app.include_router(health_router)
    app.include_router(strategy_router)
    app.include_router(signal_router)
    app.include_router(approval_router)
    app.include_router(model_router)
    app.include_router(strategy_import_router)
    app.include_router(sandbox_router)
    app.include_router(report_router)
    app.include_router(optimizer_router)
    app.include_router(screener_router)
    app.include_router(import_channel_router)
    app.include_router(stock_template_router)

    return app


app = create_app()
