"""
Backtest routes — 供前端调用的简化回测 API。
/api/backtest/run      → 发起回测任务（桥接到 /api/v1/jobs）
/api/backtest/results  → 查看回测结果列表
/api/backtest/summary  → 汇总统计
/api/backtest/progress/{task_id} → 任务进度
/api/backtest/cancel/{task_id}   → 取消任务
/api/backtest/adjust             → 调整参数后重新运行
/api/backtest/history/{strategy_id} → 策略历史回测
/api/backtest/results/{task_id}  → 单个结果详情
/api/backtest/results/{task_id}/equity  → 权益曲线
/api/backtest/results/{task_id}/trades  → 成交记录
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# ---------------------------------------------------------------------------
# In-memory store（Phase 1 skeleton）
# ---------------------------------------------------------------------------
_TASK_STORE: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class BacktestRunRequest(BaseModel):
    strategy_id: Optional[str] = None
    strategy_name: Optional[str] = None
    symbol: str = Field(default="rb2501")
    start_date: str = Field(default="2025-01-01")
    end_date: str = Field(default="2025-12-31")
    initial_capital: float = Field(default=1_000_000.0, gt=0)
    preset: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class BacktestAdjustRequest(BaseModel):
    task_id: str
    params: Dict[str, Any] = Field(default_factory=dict)


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    strategy_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: float
    updated_at: float
    result_id: Optional[str] = None


class BacktestResult(BaseModel):
    task_id: str
    strategy_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: float


class BacktestSummary(BaseModel):
    total: int
    running: int
    completed: int
    failed: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/run", response_model=TaskStatus, status_code=status.HTTP_201_CREATED)
def run_backtest(payload: BacktestRunRequest) -> TaskStatus:
    task_id = str(uuid4())
    now = time.time()
    task: Dict[str, Any] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "strategy_id": payload.strategy_id or payload.strategy_name,
        "symbol": payload.symbol,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "created_at": now,
        "updated_at": now,
        "result_id": None,
        "params": payload.params or {},
        "initial_capital": payload.initial_capital,
    }
    _TASK_STORE[task_id] = task
    return TaskStatus(**task)


@router.get("/summary", response_model=BacktestSummary)
def get_summary() -> BacktestSummary:
    tasks = list(_TASK_STORE.values())
    return BacktestSummary(
        total=len(tasks),
        running=sum(1 for t in tasks if t["status"] == "running"),
        completed=sum(1 for t in tasks if t["status"] == "completed"),
        failed=sum(1 for t in tasks if t["status"] == "failed"),
    )


@router.get("/results", response_model=List[BacktestResult])
def list_results() -> List[BacktestResult]:
    return [
        BacktestResult(
            task_id=t["task_id"],
            strategy_id=t.get("strategy_id"),
            symbol=t.get("symbol"),
            start_date=t.get("start_date"),
            end_date=t.get("end_date"),
            status=t["status"],
            metrics=t.get("metrics", {}),
            created_at=t["created_at"],
        )
        for t in _TASK_STORE.values()
    ]


@router.get("/results/{task_id}", response_model=BacktestResult)
def get_result(task_id: str) -> BacktestResult:
    task = _TASK_STORE.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return BacktestResult(
        task_id=task["task_id"],
        strategy_id=task.get("strategy_id"),
        symbol=task.get("symbol"),
        start_date=task.get("start_date"),
        end_date=task.get("end_date"),
        status=task["status"],
        metrics=task.get("metrics", {}),
        created_at=task["created_at"],
    )


@router.get("/results/{task_id}/equity")
def get_equity(task_id: str) -> Dict[str, Any]:
    if task_id not in _TASK_STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"task_id": task_id, "equity": []}


@router.get("/results/{task_id}/trades")
def get_trades(task_id: str) -> Dict[str, Any]:
    if task_id not in _TASK_STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"task_id": task_id, "trades": []}


@router.get("/progress/{task_id}")
def get_progress(task_id: str) -> Dict[str, Any]:
    task = _TASK_STORE.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"task_id": task_id, "status": task["status"], "progress": task["progress"]}


@router.post("/cancel/{task_id}")
def cancel_backtest(task_id: str) -> Dict[str, Any]:
    task = _TASK_STORE.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task["status"] not in ("pending", "running"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not cancellable")
    task["status"] = "cancelled"
    task["updated_at"] = time.time()
    return {"task_id": task_id, "status": "cancelled"}


@router.post("/adjust", response_model=TaskStatus, status_code=status.HTTP_201_CREATED)
def adjust_backtest(payload: BacktestAdjustRequest) -> TaskStatus:
    original = _TASK_STORE.get(payload.task_id)
    if original is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original task not found")
    task_id = str(uuid4())
    now = time.time()
    task: Dict[str, Any] = {
        **original,
        "task_id": task_id,
        "status": "pending",
        "progress": 0.0,
        "params": {**original.get("params", {}), **payload.params},
        "created_at": now,
        "updated_at": now,
        "result_id": None,
    }
    _TASK_STORE[task_id] = task
    return TaskStatus(**task)


@router.get("/history/{strategy_id}", response_model=List[BacktestResult])
def get_history(strategy_id: str) -> List[BacktestResult]:
    return [
        BacktestResult(
            task_id=t["task_id"],
            strategy_id=t.get("strategy_id"),
            symbol=t.get("symbol"),
            start_date=t.get("start_date"),
            end_date=t.get("end_date"),
            status=t["status"],
            metrics=t.get("metrics", {}),
            created_at=t["created_at"],
        )
        for t in _TASK_STORE.values()
        if t.get("strategy_id") == strategy_id
    ]
