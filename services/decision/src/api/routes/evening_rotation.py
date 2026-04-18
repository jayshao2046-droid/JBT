"""
晚间轮换 API 路由 (CB8)
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ...research.evening_rotation import EveningRotator

router = APIRouter(prefix="/rotation", tags=["rotation"])

# 全局单例
_rotator = EveningRotator()


class RotateRequest(BaseModel):
    universe: list[str]
    lookback_days: int = 20


@router.post("/run")
async def run_rotation(req: RotateRequest):
    """运行晚间轮换"""
    selected = _rotator.rotate(req.universe, req.lookback_days)
    return _rotator.get_rotation_plan()


@router.get("/plan")
async def get_plan():
    """获取最近一次轮换计划"""
    return _rotator.get_rotation_plan()
