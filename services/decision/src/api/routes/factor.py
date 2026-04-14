"""因子管理 API 路由 — TASK-0116

端点：
  POST /api/v1/factor/mine       从 K 线数据挖掘候选因子
  POST /api/v1/factor/validate   验证候选因子有效性
  GET  /api/v1/factor/list       列出已验证的有效因子（内存缓存）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...research.factor_miner import FactorMiner
from ...research.factor_validator import FactorValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/factor", tags=["factor"])

# 内存缓存：通过验证的有效因子（symbol → factor_name → 最新结果）
_valid_factors: Dict[str, Dict[str, Any]] = {}

_miner = FactorMiner()
_validator = FactorValidator()


# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────

class Bar(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class MineRequest(BaseModel):
    symbol: str
    bars: List[Bar]
    windows: Optional[Dict[str, List[int]]] = None


class MineResponse(BaseModel):
    symbol: str
    factors: List[Dict[str, Any]]
    count: int


class ValidateRequest(BaseModel):
    factor_name: str
    symbol: str
    factor_series: List[float]
    return_series: List[float]


class ValidateResponse(BaseModel):
    factor_name: str
    symbol: str
    ic_mean: float
    ic_ir: float
    p_value: float
    ls_return: float
    passed: bool
    reason: str


class ListResponse(BaseModel):
    total: int
    factors: List[Dict[str, Any]]


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/mine", response_model=MineResponse)
async def mine_factors(req: MineRequest) -> MineResponse:
    """从 K 线数据挖掘候选因子。

    Returns:
        挖掘到的候选因子列表（含标准化值和原始值）
    """
    bars_dict = [b.dict() for b in req.bars]
    try:
        factors = _miner.mine(
            symbol=req.symbol,
            bars=bars_dict,
            windows=req.windows,
        )
    except Exception as exc:
        logger.error("因子挖掘失败: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"因子挖掘失败: {exc}")

    factor_list = [
        {
            "name": f.name,
            "value": f.value,
            "raw_value": f.raw_value,
            "category": f.category,
            "lookback": f.lookback,
            "metadata": f.metadata,
        }
        for f in factors
    ]
    return MineResponse(symbol=req.symbol, factors=factor_list, count=len(factor_list))


@router.post("/validate", response_model=ValidateResponse)
async def validate_factor(req: ValidateRequest) -> ValidateResponse:
    """验证候选因子有效性（IC IR、显著性、多空收益差）。

    通过验证的因子会写入内存缓存，可通过 /list 查询。
    """
    try:
        result = _validator.validate(
            factor_name=req.factor_name,
            symbol=req.symbol,
            factor_series=req.factor_series,
            return_series=req.return_series,
        )
    except Exception as exc:
        logger.error("因子验证失败: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"因子验证失败: {exc}")

    if result.passed:
        if req.symbol not in _valid_factors:
            _valid_factors[req.symbol] = {}
        _valid_factors[req.symbol][req.factor_name] = {
            "factor_name": result.factor_name,
            "symbol": result.symbol,
            "ic_mean": result.ic_mean,
            "ic_ir": result.ic_ir,
            "passed": result.passed,
        }

    return ValidateResponse(
        factor_name=result.factor_name,
        symbol=result.symbol,
        ic_mean=result.ic_mean,
        ic_ir=result.ic_ir,
        p_value=result.p_value,
        ls_return=result.ls_return,
        passed=result.passed,
        reason=result.reason,
    )


@router.get("/list", response_model=ListResponse)
async def list_valid_factors(symbol: Optional[str] = None) -> ListResponse:
    """列出已验证的有效因子。

    Args:
        symbol: 按品种过滤（可选），不传则返回全部
    """
    if symbol:
        factors = list(_valid_factors.get(symbol, {}).values())
    else:
        factors = [
            f
            for sym_factors in _valid_factors.values()
            for f in sym_factors.values()
        ]
    return ListResponse(total=len(factors), factors=factors)
