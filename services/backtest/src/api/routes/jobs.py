from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Literal, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

if __package__:
    from ...core.settings import get_settings
else:
    from core.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["jobs"])

JobStatus = Literal["pending", "running", "completed", "failed"]


class BacktestJobCreateRequest(BaseModel):
    asset_type: Literal["futures"] = Field(
        default="futures",
        description="第一阶段只支持期货回测，股票适配器仅预留不启用。",
    )
    strategy_template_id: str = Field(
        ...,
        min_length=1,
        description="固定策略模板 ID，由服务端预置。",
    )
    strategy_yaml_filename: str = Field(
        ...,
        min_length=1,
        description="用户上传的一体化 YAML 文件名，包含策略参数与风控参数。",
    )
    symbol: str = Field(..., min_length=1, description="期货合约代码。")
    start_date: date
    end_date: date
    initial_capital: float = Field(default=1000000.0, gt=0)
    notes: Optional[str] = None


class BacktestJobResponse(BaseModel):
    job_id: UUID
    asset_type: Literal["futures"]
    strategy_template_id: str
    strategy_yaml_filename: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    status: JobStatus
    strategy_mode: Literal["fixed_template_with_uploaded_yaml"]
    risk_config_source: Literal["yaml"]
    execution_stage: Literal["batch_a_skeleton"]
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BacktestJobListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[BacktestJobResponse]


_JOB_STORE: Dict[UUID, BacktestJobResponse] = {}


def _current_time() -> datetime:
    return datetime.now().astimezone()


def _get_job_or_404(job_id: UUID) -> BacktestJobResponse:
    job = _JOB_STORE.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/jobs", response_model=BacktestJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: BacktestJobCreateRequest) -> BacktestJobResponse:
    settings = get_settings()

    if payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be greater than or equal to start_date",
        )
    if not payload.strategy_yaml_filename.endswith((".yaml", ".yml")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="strategy_yaml_filename must be a .yaml or .yml file",
        )

    now = _current_time()
    job = BacktestJobResponse(
        job_id=uuid4(),
        asset_type=payload.asset_type,
        strategy_template_id=payload.strategy_template_id,
        strategy_yaml_filename=payload.strategy_yaml_filename,
        symbol=payload.symbol,
        start_date=payload.start_date,
        end_date=payload.end_date,
        initial_capital=payload.initial_capital,
        status="pending",
        strategy_mode="fixed_template_with_uploaded_yaml",
        risk_config_source="yaml",
        execution_stage="batch_a_skeleton",
        notes=payload.notes
        or "Batch A only registers the job; runtime execution will be wired in batch B.",
        created_at=now,
        updated_at=now,
    )
    _JOB_STORE[job.job_id] = job

    if len(_JOB_STORE) > settings.backtest_max_concurrent:
        _JOB_STORE.pop(job.job_id, None)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Concurrent backtest skeleton queue limit reached",
        )

    return job


@router.get("/jobs", response_model=BacktestJobListResponse)
def list_jobs(
    strategy_template_id: Optional[str] = Query(default=None),
    symbol: Optional[str] = Query(default=None),
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> BacktestJobListResponse:
    items = list(_JOB_STORE.values())

    if strategy_template_id:
        items = [job for job in items if job.strategy_template_id == strategy_template_id]
    if symbol:
        items = [job for job in items if job.symbol == symbol]
    if status_filter:
        items = [job for job in items if job.status == status_filter]

    total = len(items)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    return BacktestJobListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items[start_index:end_index],
    )


@router.get("/jobs/{job_id}", response_model=BacktestJobResponse)
def get_job(job_id: UUID) -> BacktestJobResponse:
    return _get_job_or_404(job_id)