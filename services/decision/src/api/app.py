import hmac
import logging
import os
import time
from collections import defaultdict
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
from .routes.researcher_evaluate import router as researcher_evaluate_router
# Phase C routes
from .routes.stock_pool import router as stock_pool_router
from .routes.intraday import router as intraday_router
from .routes.post_market import router as post_market_router
from .routes.evening_rotation import router as evening_rotation_router
from .routes.pbo import router as pbo_router
from .routes.local_sim import router as local_sim_router
# Decision Web routes
from .routes.decision_web import router as decision_web_router
# TASK-0116: 因子挖掘与验证路由
from .routes.factor import router as factor_router
# LLM 计费 API
from .routes.billing import router as billing_router

logger = logging.getLogger(__name__)

_DECISION_API_KEY = os.environ.get("DECISION_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_PUBLIC_PATHS = {"/health", "/ready"}

# P2-4 安全修复：速率限制（简单滑动窗口）
_rate_limit_window = 60  # 秒
_rate_limit_max_requests = int(os.environ.get("DECISION_RATE_LIMIT", "100"))
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_id: str) -> bool:
    """检查速率限制（简单滑动窗口实现）。

    Args:
        client_id: 客户端标识（IP 或 API Key）

    Returns:
        True 表示未超限，False 表示超限
    """
    now = time.time()
    window_start = now - _rate_limit_window

    # 清理过期记录
    _rate_limit_store[client_id] = [
        ts for ts in _rate_limit_store[client_id] if ts > window_start
    ]

    # 检查是否超限
    if len(_rate_limit_store[client_id]) >= _rate_limit_max_requests:
        return False

    # 记录本次请求
    _rate_limit_store[client_id].append(now)
    return True


async def _verify_api_key(
    request: Request, api_key: Optional[str] = Depends(_api_key_header)
) -> None:
    """验证 API Key（P1-1 修复：生产环境强制验证）。"""
    if request.url.path in _PUBLIC_PATHS:
        return

    # P1-1 修复：生产环境必须配置 API Key
    env = os.environ.get("JBT_ENV", "development").lower()
    if not _DECISION_API_KEY:
        if env == "production":
            raise HTTPException(
                status_code=503,
                detail="DECISION_API_KEY not configured in production environment"
            )
        # 开发环境允许未配置 API Key
        return

    # P2-4 修复：速率限制检查
    client_id = api_key or request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

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
    app.include_router(researcher_evaluate_router)
    # Phase C routes
    app.include_router(stock_pool_router, prefix="/api/v1/stock")
    app.include_router(intraday_router, prefix="/api/v1/stock")
    app.include_router(post_market_router, prefix="/api/v1/stock")
    app.include_router(evening_rotation_router, prefix="/api/v1/stock")
    app.include_router(pbo_router, prefix="/api/v1/stock")
    app.include_router(local_sim_router, prefix="/api/v1/stock")
    # CF1' LLM Pipeline
    from .routes.llm import router as llm_router
    app.include_router(llm_router)
    # Decision Web routes
    app.include_router(decision_web_router)
    app.include_router(factor_router, prefix="/api/v1")
    app.include_router(billing_router)

    @app.on_event("startup")
    async def _start_billing_notifier():
        from ..llm.billing_notifier import BillingNotifier
        notifier = BillingNotifier()
        notifier.start()

    @app.on_event("startup")
    async def _start_daily_summary_scheduler():
        """每天固定 3 个收盘后时点发送门控日报邮件（默认 11:35/15:05/23:05, CST）。"""
        import asyncio
        from datetime import datetime, timezone, timedelta
        from ..notifier.daily_summary import get_daily_summary, send_daily_summary

        _TZ_CST = timezone(timedelta(hours=8))
        raw_times = os.environ.get("DECISION_DAILY_SUMMARY_TIMES", "11:35,15:05,23:05")

        trigger_times: list[tuple[int, int]] = []
        for item in raw_times.replace("，", ",").split(","):
            text = item.strip()
            if not text or ":" not in text:
                continue
            hh, mm = text.split(":", 1)
            if hh.isdigit() and mm.isdigit():
                h, m = int(hh), int(mm)
                if 0 <= h <= 23 and 0 <= m <= 59:
                    trigger_times.append((h, m))

        if len(trigger_times) < 3:
            trigger_times = [(11, 35), (15, 5), (23, 5)]

        trigger_times = sorted(set(trigger_times))

        def _next_trigger(now: datetime) -> datetime:
            for h, m in trigger_times:
                candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if now < candidate:
                    return candidate
            first_h, first_m = trigger_times[0]
            return (now + timedelta(days=1)).replace(
                hour=first_h,
                minute=first_m,
                second=0,
                microsecond=0,
            )

        async def _loop():
            while True:
                now = datetime.now(_TZ_CST)
                target = _next_trigger(now)
                wait = (target - now).total_seconds()
                logger.info(
                    "日报定时器: 将在 %s 发送 (%.0f 秒后), 触发时点=%s",
                    target.strftime("%Y-%m-%d %H:%M"),
                    wait,
                    ",".join(f"{h:02d}:{m:02d}" for h, m in trigger_times),
                )
                await asyncio.sleep(wait)
                try:
                    summary = get_daily_summary()
                    send_daily_summary(summary)
                    logger.info("日报邮件已触发: %s", target.strftime("%Y-%m-%d %H:%M"))
                except Exception as exc:
                    logger.error("日报定时器异常: %s", exc)

        asyncio.create_task(_loop())

    return app


app = create_app()
