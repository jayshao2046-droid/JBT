import pytest
from src.failover.handler import FailoverHandler, HandoverPayload


def test_normal_handover_with_orders_and_positions():
    """正常交接：包含订单和持仓"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[
            {"order_id": "o1", "symbol": "rb2505", "direction": "buy", "quantity": 10, "price": 3500.0, "status": "filled"}
        ],
        positions={"rb2505": 10.0, "cu2505": 5.0},
        capital=480000.0,
        source_engine="LocalSimEngine",
        handover_id="h001"
    )
    result = handler.receive_handover(payload)
    assert result.success is True
    assert result.handover_id == "h001"
    assert result.orders_received == 1
    assert result.positions_merged == 2
    assert result.capital_delta == 480000.0
    assert result.errors == []


def test_empty_handover():
    """空数据交接：无订单无持仓"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[],
        positions={},
        capital=500000.0,
        source_engine="LocalSimEngine",
        handover_id="h002"
    )
    result = handler.receive_handover(payload)
    assert result.success is True
    assert result.orders_received == 0
    assert result.positions_merged == 0
    assert result.capital_delta == 500000.0


def test_duplicate_handover_id():
    """重复 handover_id 交接"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[],
        positions={},
        capital=500000.0,
        source_engine="LocalSimEngine",
        handover_id="h003"
    )
    result1 = handler.receive_handover(payload)
    assert result1.success is True

    # 重复提交
    result2 = handler.receive_handover(payload)
    assert result2.success is False
    assert "Duplicate handover_id" in result2.errors


def test_negative_capital_validation():
    """数据校验失败：负资金"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[],
        positions={},
        capital=-1000.0,
        source_engine="LocalSimEngine",
        handover_id="h004"
    )
    result = handler.receive_handover(payload)
    assert result.success is False
    assert "Negative capital" in result.errors


def test_negative_position_validation():
    """数据校验失败：负持仓数量"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[],
        positions={"rb2505": -10.0},
        capital=500000.0,
        source_engine="LocalSimEngine",
        handover_id="h005"
    )
    result = handler.receive_handover(payload)
    assert result.success is False
    assert any("Negative position" in e for e in result.errors)


def test_get_status_initial():
    """get_status 初始状态"""
    handler = FailoverHandler()
    status = handler.get_status()
    assert status.status == "idle"
    assert status.last_handover_id is None
    assert status.last_handover_time is None
    assert status.orders_pending == 0


def test_get_status_after_handover():
    """get_status 交接后状态"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[{"order_id": "o1"}],
        positions={},
        capital=500000.0,
        source_engine="LocalSimEngine",
        handover_id="h006"
    )
    handler.receive_handover(payload)
    status = handler.get_status()
    assert status.status == "completed"
    assert status.last_handover_id == "h006"
    assert status.last_handover_time is not None
    assert status.orders_pending == 1


def test_confirm_normal():
    """confirm 正常确认"""
    handler = FailoverHandler()
    payload = HandoverPayload(
        orders=[{"order_id": "o1"}],
        positions={},
        capital=500000.0,
        source_engine="LocalSimEngine",
        handover_id="h007"
    )
    handler.receive_handover(payload)
    success = handler.confirm_handover("h007")
    assert success is True
    status = handler.get_status()
    assert status.status == "idle"
    assert status.orders_pending == 0


def test_confirm_nonexistent_handover_id():
    """confirm 不存在的 handover_id"""
    handler = FailoverHandler()
    success = handler.confirm_handover("nonexistent")
    assert success is False
