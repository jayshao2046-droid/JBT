"""Strategy queue API routes."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

if __package__:
    from ...backtest.strategy_queue import StrategyQueue
else:
    from backtest.strategy_queue import StrategyQueue

router = APIRouter(prefix="/api/v1/strategy-queue", tags=["strategy-queue"])

# Shared singleton – lives for the process lifetime.
_queue = StrategyQueue()


def get_queue() -> StrategyQueue:
    """Return the module-level queue singleton (useful for testing)."""
    return _queue


# ── Request / Response models ────────────────────────────────────────

class EnqueueRequest(BaseModel):
    strategy_id: str = Field(..., min_length=1, max_length=128)
    strategy_content: str = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0)
    callback_url: Optional[str] = None


class EnqueueResponse(BaseModel):
    queue_id: str
    strategy_id: str
    status: str
    message: str
    queued_at: str


class QueueStatusResponse(BaseModel):
    total_count: int
    queued_count: int
    running_count: int
    completed_count: int
    failed_count: int
    items: list[dict[str, Any]]


class ClearResponse(BaseModel):
    message: str
    cleared_count: int


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/enqueue", response_model=EnqueueResponse, status_code=status.HTTP_201_CREATED)
def enqueue_strategy(body: EnqueueRequest) -> EnqueueResponse:
    q = get_queue()
    try:
        queue_id = q.enqueue(
            strategy_id=body.strategy_id,
            strategy_content=body.strategy_content,
            priority=body.priority,
            callback_url=body.callback_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except OverflowError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Queue is full (max 100 items)",
        )

    item = q.get_item(queue_id)
    assert item is not None
    return EnqueueResponse(
        queue_id=item.queue_id,
        strategy_id=item.strategy_id,
        status=item.status,
        message="Strategy enqueued successfully",
        queued_at=item.queued_at,
    )


@router.get("/status", response_model=QueueStatusResponse)
def queue_status(
    status_filter: Optional[str] = Query(None, alias="status"),
) -> QueueStatusResponse:
    q = get_queue()
    all_items = q.get_all_items()
    filtered = q.get_all_items(status_filter=status_filter) if status_filter else all_items

    counts: dict[str, int] = {"queued": 0, "running": 0, "completed": 0, "failed": 0}
    for it in all_items:
        if it.status in counts:
            counts[it.status] += 1

    return QueueStatusResponse(
        total_count=len(all_items),
        queued_count=counts["queued"],
        running_count=counts["running"],
        completed_count=counts["completed"],
        failed_count=counts["failed"],
        items=[it.to_dict() for it in filtered],
    )


@router.delete("/clear", response_model=ClearResponse)
def clear_queue() -> ClearResponse:
    q = get_queue()
    cleared = q.clear_queue()
    return ClearResponse(message="Queue cleared", cleared_count=cleared)
