"""信号分发器 — 将决策信号异步转发到 sim-trading 服务。

TASK-0059-D / Token: tok-3185c6c9
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

from shared.contracts.decision.signal_dispatch import (
    SignalDispatchRequest,
    SignalDispatchResponse,
    SignalStatusResponse,
)

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_BACKOFF = 0.5  # seconds


class SignalDispatcher:
    """将 SignalDispatchRequest 转发到 sim-trading 的 /api/v1/signals/receive。"""

    def __init__(self, sim_trading_url: str = "http://localhost:8101") -> None:
        self.sim_trading_url = sim_trading_url.rstrip("/")
        self._dispatched: dict[str, dict] = {}  # signal_id -> status record
        self.max_history = 10000

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def dispatch(self, request: SignalDispatchRequest) -> SignalDispatchResponse:
        now = datetime.now(timezone.utc).isoformat()

        # 0. FIFO 淘汰逻辑（防止内存泄漏）
        if len(self._dispatched) > self.max_history:
            oldest_keys = sorted(
                self._dispatched.keys(),
                key=lambda k: self._dispatched[k].get("dispatched_at", ""),
            )[: len(self._dispatched) - self.max_history]
            for key in oldest_keys:
                del self._dispatched[key]

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
        errors: list[str] = []

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, json=payload)
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
