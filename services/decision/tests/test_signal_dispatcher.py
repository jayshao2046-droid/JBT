"""TASK-0119 批次 B — decision 服务信号分发器测试。

验证 P1-1: 内存泄漏修复（FIFO 淘汰机制）。
"""

from __future__ import annotations

import pytest

from services.decision.src.core.signal_dispatcher import SignalDispatcher
from shared.contracts.decision.signal_dispatch import SignalDispatchRequest


@pytest.mark.asyncio
async def test_signal_dispatcher_fifo_eviction():
    """P1-1: 验证 FIFO 淘汰机制防止内存泄漏。"""
    dispatcher = SignalDispatcher()
    dispatcher.max_history = 10  # 设置小容量便于测试

    # 发送 15 个信号（超过容量）
    for i in range(15):
        request = SignalDispatchRequest(
            signal_id=f"signal-{i:03d}",
            strategy_id="test-strategy",
            symbol="TEST",
            direction="buy",
            quantity=100,
            price=1000.0,
            timestamp="2026-04-15T10:00:00Z",
        )
        # 由于没有真实的 sim-trading 服务，会失败，但会记录到 _dispatched
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass  # 忽略网络错误

    # 验证只保留最新的 10 个
    assert len(dispatcher._dispatched) == 10

    # 验证最早的 5 个被淘汰（signal-000 到 signal-004）
    for i in range(5):
        assert f"signal-{i:03d}" not in dispatcher._dispatched

    # 验证最新的 10 个保留（signal-005 到 signal-014）
    for i in range(5, 15):
        assert f"signal-{i:03d}" in dispatcher._dispatched


@pytest.mark.asyncio
async def test_signal_dispatcher_fifo_order():
    """P1-1: 验证 FIFO 淘汰顺序正确（先进先出）。"""
    dispatcher = SignalDispatcher()
    dispatcher.max_history = 5

    # 发送 8 个信号
    signal_ids = [f"sig-{i}" for i in range(8)]
    for signal_id in signal_ids:
        request = SignalDispatchRequest(
            signal_id=signal_id,
            strategy_id="test",
            symbol="TEST",
            action="BUY",
            quantity=100,
            price=1000.0,
            timestamp="2026-04-15T10:00:00Z",
        )
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass

    # 验证保留最新的 5 个（sig-3 到 sig-7）
    assert len(dispatcher._dispatched) == 5
    assert "sig-0" not in dispatcher._dispatched
    assert "sig-1" not in dispatcher._dispatched
    assert "sig-2" not in dispatcher._dispatched
    assert "sig-3" in dispatcher._dispatched
    assert "sig-7" in dispatcher._dispatched


@pytest.mark.asyncio
async def test_signal_dispatcher_no_eviction_under_limit():
    """P1-1: 验证未超过容量时不淘汰。"""
    dispatcher = SignalDispatcher()
    dispatcher.max_history = 100

    # 发送 50 个信号（未超过容量）
    for i in range(50):
        request = SignalDispatchRequest(
            signal_id=f"signal-{i}",
            strategy_id="test",
            symbol="TEST",
            action="BUY",
            quantity=100,
            price=1000.0,
            timestamp="2026-04-15T10:00:00Z",
        )
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass

    # 验证所有信号都保留
    assert len(dispatcher._dispatched) == 50
    for i in range(50):
        assert f"signal-{i}" in dispatcher._dispatched


@pytest.mark.asyncio
async def test_signal_dispatcher_duplicate_handling():
    """P1-1: 验证重复信号不增加内存占用。"""
    dispatcher = SignalDispatcher()
    dispatcher.max_history = 10

    request = SignalDispatchRequest(
        signal_id="duplicate-signal",
        strategy_id="test",
        symbol="TEST",
        action="BUY",
        quantity=100,
        price=1000.0,
        timestamp="2026-04-15T10:00:00Z",
    )

    # 发送同一个信号 5 次
    for _ in range(5):
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass

    # 验证只记录一次
    assert len(dispatcher._dispatched) == 1
    assert "duplicate-signal" in dispatcher._dispatched


@pytest.mark.asyncio
async def test_signal_dispatcher_memory_bounded():
    """P1-1: 验证内存占用有上界。"""
    dispatcher = SignalDispatcher()
    dispatcher.max_history = 1000

    # 发送大量信号
    for i in range(5000):
        request = SignalDispatchRequest(
            signal_id=f"signal-{i}",
            strategy_id="test",
            symbol="TEST",
            action="BUY",
            quantity=100,
            price=1000.0,
            timestamp="2026-04-15T10:00:00Z",
        )
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass

    # 验证内存占用不超过上限
    assert len(dispatcher._dispatched) == 1000

    # 验证保留最新的 1000 个
    for i in range(4000, 5000):
        assert f"signal-{i}" in dispatcher._dispatched

    # 验证最早的被淘汰
    for i in range(0, 4000):
        assert f"signal-{i}" not in dispatcher._dispatched


@pytest.mark.asyncio
async def test_signal_dispatcher_get_status_after_eviction():
    """P1-1: 验证淘汰后的信号状态查询返回 None。"""
    dispatcher = SignalDispatcher()
    dispatcher.max_history = 5

    # 发送 10 个信号
    for i in range(10):
        request = SignalDispatchRequest(
            signal_id=f"signal-{i}",
            strategy_id="test",
            symbol="TEST",
            action="BUY",
            quantity=100,
            price=1000.0,
            timestamp="2026-04-15T10:00:00Z",
        )
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass

    # 验证被淘汰的信号状态为 None
    for i in range(5):
        status = dispatcher.get_status(f"signal-{i}")
        assert status is None

    # 验证保留的信号状态可查询
    for i in range(5, 10):
        status = dispatcher.get_status(f"signal-{i}")
        assert status is not None
        assert status.signal_id == f"signal-{i}"


@pytest.mark.asyncio
async def test_signal_dispatcher_eviction_performance():
    """P1-1: 验证 FIFO 淘汰性能（O(1) 复杂度）。"""
    import time

    dispatcher = SignalDispatcher()
    dispatcher.max_history = 10000

    # 发送 20000 个信号，测量时间
    start = time.time()
    for i in range(20000):
        request = SignalDispatchRequest(
            signal_id=f"signal-{i}",
            strategy_id="test",
            symbol="TEST",
            action="BUY",
            quantity=100,
            price=1000.0,
            timestamp="2026-04-15T10:00:00Z",
        )
        try:
            await dispatcher.dispatch(request)
        except Exception:
            pass
    elapsed = time.time() - start

    # 验证性能合理（应在几秒内完成）
    assert elapsed < 10.0  # 20000 次操作应在 10 秒内完成

    # 验证内存占用正确
    assert len(dispatcher._dispatched) == 10000
