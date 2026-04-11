"""SignalDispatcher 单元测试 — TASK-0059-D

mock httpx 响应，至少 8 个用例覆盖：
  1. 成功分发
  2. 幂等重复
  3. sim-trading 不可用
  4. 重试后成功
  5. 状态查询（已分发）
  6. 状态查询（不存在）
  7. HTTP 500 全部重试失败
  8. limit 订单分发成功
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from shared.contracts.decision.signal_dispatch import (
    SignalDispatchRequest,
    SignalDispatchResponse,
    SignalStatusResponse,
)
from services.decision.src.core.signal_dispatcher import SignalDispatcher


def _make_request(**overrides) -> SignalDispatchRequest:
    defaults = {
        "signal_id": "sig-001",
        "strategy_id": "strat-a",
        "symbol": "000001",
        "direction": "buy",
        "quantity": 100.0,
    }
    defaults.update(overrides)
    return SignalDispatchRequest(**defaults)


def _ok_response(execution_id: str = "exec-abc") -> httpx.Response:
    return httpx.Response(
        status_code=200,
        json={"execution_id": execution_id, "status": "received"},
        request=httpx.Request("POST", "http://localhost:8101/api/v1/signals/receive"),
    )


def _error_response(code: int = 500) -> httpx.Response:
    return httpx.Response(
        status_code=code,
        json={"detail": "internal error"},
        request=httpx.Request("POST", "http://localhost:8101/api/v1/signals/receive"),
    )


# ---------- 1. 成功分发 ----------

@pytest.mark.asyncio
async def test_dispatch_success():
    dispatcher = SignalDispatcher()
    req = _make_request()

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = _ok_response()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await dispatcher.dispatch(req)

    assert resp.status == "dispatched"
    assert resp.signal_id == "sig-001"
    assert resp.execution_id == "exec-abc"


# ---------- 2. 幂等重复 ----------

@pytest.mark.asyncio
async def test_dispatch_duplicate():
    dispatcher = SignalDispatcher()
    req = _make_request()

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = _ok_response()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await dispatcher.dispatch(req)
        resp2 = await dispatcher.dispatch(req)

    assert resp2.status == "duplicate"
    assert resp2.message == "Signal already dispatched"


# ---------- 3. sim-trading 不可用 ----------

@pytest.mark.asyncio
async def test_dispatch_connection_error():
    dispatcher = SignalDispatcher()
    req = _make_request(signal_id="sig-conn-err")

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError(
            "Connection refused",
            request=httpx.Request("POST", "http://localhost:8101/api/v1/signals/receive"),
        )
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("services.decision.src.core.signal_dispatcher.asyncio.sleep", new_callable=AsyncMock):
            resp = await dispatcher.dispatch(req)

    assert resp.status == "failed"
    assert len(resp.errors) == 3
    assert "Connection refused" in resp.errors[0]


# ---------- 4. 重试后成功 ----------

@pytest.mark.asyncio
async def test_dispatch_retry_then_success():
    dispatcher = SignalDispatcher()
    req = _make_request(signal_id="sig-retry-ok")

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.ConnectError(
                "Connection refused",
                request=httpx.Request("POST", "http://localhost:8101/api/v1/signals/receive"),
            )
        return _ok_response("exec-retry")

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = side_effect
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("services.decision.src.core.signal_dispatcher.asyncio.sleep", new_callable=AsyncMock):
            resp = await dispatcher.dispatch(req)

    assert resp.status == "dispatched"
    assert resp.execution_id == "exec-retry"


# ---------- 5. 状态查询（已分发）----------

@pytest.mark.asyncio
async def test_get_status_dispatched():
    dispatcher = SignalDispatcher()
    req = _make_request(signal_id="sig-status-ok")

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = _ok_response("exec-st")
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await dispatcher.dispatch(req)

    status = dispatcher.get_status("sig-status-ok")
    assert status is not None
    assert status.status == "dispatched"
    assert status.execution_id == "exec-st"


# ---------- 6. 状态查询（不存在）----------

def test_get_status_not_found():
    dispatcher = SignalDispatcher()
    result = dispatcher.get_status("no-such-signal")
    assert result is None


# ---------- 7. HTTP 500 全部重试失败 ----------

@pytest.mark.asyncio
async def test_dispatch_all_retries_exhausted():
    dispatcher = SignalDispatcher()
    req = _make_request(signal_id="sig-500")

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = _error_response(500)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("services.decision.src.core.signal_dispatcher.asyncio.sleep", new_callable=AsyncMock):
            resp = await dispatcher.dispatch(req)

    assert resp.status == "failed"
    assert len(resp.errors) == 3
    assert "500" in resp.errors[0]


# ---------- 8. limit 订单分发成功 ----------

@pytest.mark.asyncio
async def test_dispatch_limit_order():
    dispatcher = SignalDispatcher()
    req = _make_request(
        signal_id="sig-limit",
        order_type="limit",
        price=10.5,
        direction="sell",
    )

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = _ok_response("exec-limit")
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await dispatcher.dispatch(req)

    assert resp.status == "dispatched"
    assert resp.execution_id == "exec-limit"


# ---------- 9. 分发失败后状态查询返回 failed ----------

@pytest.mark.asyncio
async def test_get_status_after_failure():
    dispatcher = SignalDispatcher()
    req = _make_request(signal_id="sig-fail-status")

    with patch("services.decision.src.core.signal_dispatcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError(
            "refused",
            request=httpx.Request("POST", "http://localhost:8101/api/v1/signals/receive"),
        )
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("services.decision.src.core.signal_dispatcher.asyncio.sleep", new_callable=AsyncMock):
            await dispatcher.dispatch(req)

    status = dispatcher.get_status("sig-fail-status")
    assert status is not None
    assert status.status == "failed"
    assert status.error is not None
