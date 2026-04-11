"""
沙箱回测路由 — TASK-0056 CA2'
POST /sandbox/backtest → 执行沙箱回测
POST /sandbox/validate → 校验策略配置
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...core.settings import get_settings
from ...research.sandbox_engine import SandboxEngine

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


class BacktestRequest(BaseModel):
    strategy_id: Optional[str] = None
    strategy_config: Dict[str, Any]
    start_time: str
    end_time: str
    asset_type: str = "futures"
    initial_capital: float = 1_000_000
    symbols: Optional[List[str]] = None
    price_limit: float = 0.10
    allow_short: bool = False


class ValidateRequest(BaseModel):
    strategy_config: Dict[str, Any]


class ValidateResponse(BaseModel):
    valid: bool
    errors: List[str]


def _get_engine() -> SandboxEngine:
    settings = get_settings()
    return SandboxEngine(data_service_url=settings.data_service_url)


@router.post("/backtest")
async def run_sandbox_backtest(req: BacktestRequest) -> dict:
    engine = _get_engine()
    # Merge stock-specific params into strategy_config
    config = {**req.strategy_config}
    if req.asset_type == "stock":
        config.setdefault("price_limit", req.price_limit)
        config.setdefault("allow_short", req.allow_short)
    result = await engine.run_backtest(
        strategy_config=config,
        start_time=req.start_time,
        end_time=req.end_time,
        asset_type=req.asset_type,
        initial_capital=req.initial_capital,
        symbols=req.symbols,
    )
    return result.to_dict()


@router.post("/validate")
async def validate_strategy_config(req: ValidateRequest) -> ValidateResponse:
    errors: list[str] = []
    cfg = req.strategy_config

    if "short_window" in cfg:
        sw = cfg["short_window"]
        if not isinstance(sw, int) or sw < 1:
            errors.append("short_window must be a positive integer")

    if "long_window" in cfg:
        lw = cfg["long_window"]
        if not isinstance(lw, int) or lw < 1:
            errors.append("long_window must be a positive integer")

    if "short_window" in cfg and "long_window" in cfg:
        if isinstance(cfg["short_window"], int) and isinstance(cfg["long_window"], int):
            if cfg["short_window"] >= cfg["long_window"]:
                errors.append("short_window must be less than long_window")

    if "position_size" in cfg:
        ps = cfg["position_size"]
        if not isinstance(ps, (int, float)) or ps <= 0 or ps > 1:
            errors.append("position_size must be between 0 (exclusive) and 1 (inclusive)")

    return ValidateResponse(valid=len(errors) == 0, errors=errors)
