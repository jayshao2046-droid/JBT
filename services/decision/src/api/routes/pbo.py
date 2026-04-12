"""PBO 检验 API 路由 — TASK-0075 CA7"""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.research.pbo_validator import PBOValidator


router = APIRouter(prefix="/pbo", tags=["pbo"])


class PBOValidateRequest(BaseModel):
    """PBO 检验请求。"""

    returns: list[float] = Field(..., description="策略收益率序列")
    dates: list[str] = Field(..., description="日期序列（ISO 格式）")
    param_configs: list[dict] = Field(
        ..., description="参数配置列表，每个配置包含 returns 字段"
    )
    n_splits: int = Field(16, description="数据分割数量（必须是偶数）")


class PBOValidateResponse(BaseModel):
    """PBO 检验响应。"""

    pbo: float = Field(..., description="PBO 值（0~1）")
    sharpe_is: float = Field(..., description="样本内最优 Sharpe")
    sharpe_oos: float = Field(..., description="样本外对应 Sharpe")
    rank_correlation: float = Field(..., description="样本内外排名相关性")
    n_configs: int = Field(..., description="参数配置数量")
    n_splits: int = Field(..., description="数据分割数量")
    interpretation: str = Field(..., description="结果解释")


@router.post("/validate", response_model=PBOValidateResponse)
async def validate_pbo(request: PBOValidateRequest):
    """执行 PBO 检验。

    Args:
        request: PBO 检验请求。

    Returns:
        PBO 检验结果。
    """
    try:
        # 构建收益率序列
        returns = pd.Series(request.returns, index=pd.to_datetime(request.dates))

        # 验证参数配置
        for i, config in enumerate(request.param_configs):
            if "returns" not in config:
                raise HTTPException(
                    status_code=400,
                    detail=f"param_configs[{i}] missing 'returns' field",
                )

        # 执行 PBO 检验
        validator = PBOValidator(n_splits=request.n_splits)
        result = validator.validate(returns, request.param_configs)

        # 生成解释
        interpretation = validator.interpret(result)

        return PBOValidateResponse(
            pbo=result["pbo"],
            sharpe_is=result["sharpe_is"],
            sharpe_oos=result["sharpe_oos"],
            rank_correlation=result["rank_correlation"],
            n_configs=result["n_configs"],
            n_splits=result["n_splits"],
            interpretation=interpretation,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PBO validation failed: {e}")


@router.get("/health")
async def health():
    """健康检查。"""
    return {"status": "ok", "module": "pbo_validator"}
