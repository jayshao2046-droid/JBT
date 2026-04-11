from fastapi import FastAPI

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


def create_app() -> FastAPI:
    app = FastAPI(
        title="JBT Decision Service",
        version="0.1.0",
        description="JBT 决策服务 — 编排因子、信号与审批流程，生成标准化交易指令",
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

    return app


app = create_app()
