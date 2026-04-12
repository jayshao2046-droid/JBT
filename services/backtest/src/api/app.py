from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

if __package__:
    from ..core.settings import get_settings
    from .routes.approval import approval_router
    from .routes.backtest import router as backtest_router
    from .routes.health import router as health_router
    from .routes.jobs import router as jobs_router
    from .routes.queue import router as queue_router
    from .routes.stock_approval import stock_approval_router
    from .routes.strategy import router as strategy_router
    from .routes.support import ensure_compat_state
    from .routes.support import router as support_router
else:
    from api.routes.approval import approval_router
    from api.routes.backtest import router as backtest_router
    from api.routes.health import router as health_router
    from api.routes.jobs import router as jobs_router
    from api.routes.queue import router as queue_router
    from api.routes.stock_approval import stock_approval_router
    from api.routes.strategy import router as strategy_router
    from api.routes.support import ensure_compat_state
    from api.routes.support import router as support_router
    from core.settings import get_settings

_BACKTEST_API_KEY = os.environ.get("BACKTEST_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_PUBLIC_PATHS = {"/api/health", "/api/v1/health", "/api/v1/version"}


async def _verify_api_key(
    request: Request, api_key: Optional[str] = Depends(_api_key_header)
) -> None:
    if not _BACKTEST_API_KEY:
        return
    if request.url.path in _PUBLIC_PATHS:
        return
    if not api_key or not hmac.compare_digest(api_key, _BACKTEST_API_KEY):
        raise HTTPException(status_code=403, detail="invalid or missing API key")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="JBT Backtest Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        dependencies=[Depends(_verify_api_key)],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins or ["http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ensure_compat_state(app)
    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(backtest_router)
    app.include_router(strategy_router)
    app.include_router(support_router)
    app.include_router(queue_router)
    app.include_router(approval_router)
    app.include_router(stock_approval_router)
    return app


app = create_app()