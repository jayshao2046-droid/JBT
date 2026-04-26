"""信号分发器 — 将决策信号异步转发到 sim-trading 服务。

TASK-0059-D / Token: tok-3185c6c9
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from .settings import get_settings

try:
    from shared.contracts.decision.signal_dispatch import (
        SignalDispatchRequest,
        SignalDispatchResponse,
        SignalStatusResponse,
    )
except ModuleNotFoundError:
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
        status: str
        signal_id: str
        execution_id: Optional[str] = None
        message: str
        timestamp: str
        errors: list[str] = Field(default_factory=list)


    class SignalStatusResponse(BaseModel):
        signal_id: str
        status: str
        dispatched_at: Optional[str] = None
        executed_at: Optional[str] = None
        execution_id: Optional[str] = None
        error: Optional[str] = None

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_BACKOFF = 0.5  # seconds


class SignalDispatcher:
    """将 SignalDispatchRequest 转发到 sim-trading 的 /api/v1/signals/receive。"""

    def __init__(
        self,
        sim_trading_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        settings = get_settings()
        resolved_api_key = settings.sim_trading_api_key if api_key is None else api_key

        self.sim_trading_url = (sim_trading_url or settings.sim_trading_url).rstrip("/")
        self._api_key = (resolved_api_key or "").strip()
        self._timeout = timeout
        # 安全修复：P1-1 - 使用 OrderedDict 替代普通 dict，自动维护插入顺序
        self._dispatched: OrderedDict[str, dict] = OrderedDict()
        self.max_history = 10000

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def dispatch(self, request: SignalDispatchRequest) -> SignalDispatchResponse:
        now = datetime.now(timezone.utc).isoformat()

        # 0. FIFO 淘汰逻辑（防止内存泄漏）- 安全修复：P1-1
        # OrderedDict 自动维护插入顺序，直接删除最旧的记录，O(1) 复杂度
        if len(self._dispatched) >= self.max_history:
            num_to_remove = len(self._dispatched) - self.max_history + 1
            for _ in range(num_to_remove):
                self._dispatched.popitem(last=False)  # FIFO: 删除最早插入的项

        # 1. 幂等检查
        if request.signal_id in self._dispatched:
            rec = self._dispatched[request.signal_id]
            return SignalDispatchResponse(
                status="duplicate",
                signal_id=request.signal_id,
                execution_id=rec.get("execution_id"),
                message="Signal already dispatched",
                timestamp=now,
            )

        # 2. 记录 pending
        self._dispatched[request.signal_id] = {
            "status": "pending",
            "dispatched_at": now,
            "execution_id": None,
            "error": None,
        }

        # 3. 发送到 sim-trading（带重试）
        url = f"{self.sim_trading_url}/api/v1/signals/receive"
        payload = request.model_dump(mode="json")
        headers = {"X-API-Key": self._api_key} if self._api_key else None
        errors: list[str] = []

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                body = resp.json()
                execution_id = body.get("execution_id") or f"exec-{uuid.uuid4().hex[:12]}"

                # 成功
                self._dispatched[request.signal_id].update(
                    status="dispatched",
                    execution_id=execution_id,
                )
                return SignalDispatchResponse(
                    status="dispatched",
                    signal_id=request.signal_id,
                    execution_id=execution_id,
                    message="Signal dispatched to sim-trading",
                    timestamp=now,
                )
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                err_msg = f"attempt {attempt}/{_MAX_RETRIES}: {exc}"
                logger.warning("signal dispatch failed: %s", err_msg)
                errors.append(err_msg)
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_BASE_BACKOFF * (2 ** (attempt - 1)))

        # 所有重试耗尽
        self._dispatched[request.signal_id].update(
            status="failed",
            error=errors[-1] if errors else "unknown",
        )
        return SignalDispatchResponse(
            status="failed",
            signal_id=request.signal_id,
            message="All retry attempts exhausted",
            timestamp=now,
            errors=errors,
        )

    def get_status(self, signal_id: str) -> Optional[SignalStatusResponse]:
        rec = self._dispatched.get(signal_id)
        if rec is None:
            return None
        return SignalStatusResponse(
            signal_id=signal_id,
            status=rec["status"],
            dispatched_at=rec.get("dispatched_at"),
            executed_at=rec.get("executed_at"),
            execution_id=rec.get("execution_id"),
            error=rec.get("error"),
        )
