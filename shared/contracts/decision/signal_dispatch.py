"""跨服务信号分发契约 — 纯 Pydantic model，无业务逻辑。

登记时间: 2026-04-12
来源: TASK-0059-C (CA6 信号闭环)
Token: tok-9e1369d9
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SignalDispatchRequest(BaseModel):
    signal_id: str = Field(..., min_length=1)
    strategy_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    direction: str = Field(..., pattern=r"^(buy|sell|long|short)$")
    quantity: float = Field(..., gt=0)
    price: Optional[float] = None
    order_type: str = Field(default="market", pattern=r"^(market|limit)$")
    timestamp: Optional[str] = None
    valid_until: Optional[str] = None
    account_id: Optional[str] = None
    risk_level: str = Field(default="normal", pattern=r"^(low|normal|high|critical)$")
    meta_data: Optional[dict] = None


class SignalDispatchResponse(BaseModel):
    status: str  # dispatched / failed / duplicate
    signal_id: str
    execution_id: Optional[str] = None
    message: str
    timestamp: str
    errors: list[str] = Field(default_factory=list)


class SignalStatusResponse(BaseModel):
    signal_id: str
    status: str  # pending / dispatched / executed / failed
    dispatched_at: Optional[str] = None
    executed_at: Optional[str] = None
    execution_id: Optional[str] = None
    error: Optional[str] = None
