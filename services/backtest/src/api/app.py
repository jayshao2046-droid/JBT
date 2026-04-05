from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if __package__:
    from ..core.settings import get_settings
    from .routes.backtest import router as backtest_router
    from .routes.health import router as health_router
    from .routes.jobs import router as jobs_router
    from .routes.strategy import router as strategy_router
    from .routes.support import ensure_compat_state
    from .routes.support import router as support_router
else:
    from api.routes.backtest import router as backtest_router
    from api.routes.health import router as health_router
    from api.routes.jobs import router as jobs_router
    from api.routes.strategy import router as strategy_router
    from api.routes.support import ensure_compat_state
    from api.routes.support import router as support_router
    from core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="JBT Backtest Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
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
    return app


app = create_app()