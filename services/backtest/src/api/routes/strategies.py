"""
Strategies routes — 供前端 /api/strategies 与 /api/strategy/import 调用。
当前阶段为内存存储（Phase 1 skeleton）。
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["strategies"])

# ---------------------------------------------------------------------------
# In-memory store（Phase 1，后续替换为数据库）
# ---------------------------------------------------------------------------
_STRATEGY_STORE: Dict[str, Dict[str, Any]] = {}


class StrategyImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class StrategyResponse(BaseModel):
    id: str
    name: str
    content: str
    status: str = "idle"
    created_at: float
    updated_at: float
    size: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/strategies", response_model=List[StrategyResponse])
def list_strategies() -> List[StrategyResponse]:
    return [StrategyResponse(**s) for s in _STRATEGY_STORE.values()]


@router.post("/strategy/import", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def import_strategy(payload: StrategyImport) -> StrategyResponse:
    now = time.time()
    sid = payload.name.replace(" ", "_").lower()
    if sid in _STRATEGY_STORE:
        # 更新已有策略
        _STRATEGY_STORE[sid]["content"] = payload.content
        _STRATEGY_STORE[sid]["updated_at"] = now
        _STRATEGY_STORE[sid]["size"] = len(payload.content.encode())
        return StrategyResponse(**_STRATEGY_STORE[sid])

    record: Dict[str, Any] = {
        "id": sid,
        "name": payload.name,
        "content": payload.content,
        "status": "idle",
        "created_at": now,
        "updated_at": now,
        "size": len(payload.content.encode()),
    }
    _STRATEGY_STORE[sid] = record
    return StrategyResponse(**record)


@router.delete("/strategy/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(strategy_id: str) -> None:
    if strategy_id not in _STRATEGY_STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    del _STRATEGY_STORE[strategy_id]
