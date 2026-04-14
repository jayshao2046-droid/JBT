"""
test_ctp_notify.py — TASK-0014-A2 验证
1. _CTP_AVAILABLE=False 时，import simnow 不报错
2. pause_trading 路由调用后 emit_alert 被触发（mock dispatcher）
3. resume_trading 路由调用后 emit_alert 被触发（mock dispatcher）
"""
import sys
import asyncio
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.notifier.dispatcher import clear_dispatcher


@pytest.fixture(autouse=True)
def _reset_dispatcher():
    clear_dispatcher()
    yield
    clear_dispatcher()


# ---------------------------------------------------------------------------
# 1. simnow 安全 import（_CTP_AVAILABLE=False）
# ---------------------------------------------------------------------------

def test_simnow_import_without_ctp():
    """openctp-ctp 不可用时，import simnow 不应抛异常，_CTP_AVAILABLE 字段必须存在。"""
    from src.gateway import simnow as simnow_mod
    assert hasattr(simnow_mod, "_CTP_AVAILABLE")


# ---------------------------------------------------------------------------
# 2. pause_trading 路由触发 emit_alert
# ---------------------------------------------------------------------------

# 使用 conftest.py 中的 client fixture


def test_pause_triggers_emit_alert(client):
    """POST /api/v1/system/pause → emit_alert 被调用一次，level=P1，event_code=TRADING_PAUSED。"""
    with patch("src.risk.guards.emit_alert") as mock_emit:
        resp = client.post("/api/v1/system/pause", json={"reason": "测试暂停"})
    assert resp.status_code == 200
    mock_emit.assert_called_once()
    call_args = mock_emit.call_args
    assert call_args.args[0] == "P1"
    ctx = call_args.args[2]
    assert ctx["event_code"] == "TRADING_PAUSED"


# ---------------------------------------------------------------------------
# 3. resume_trading 路由触发 emit_alert
# ---------------------------------------------------------------------------

def test_resume_triggers_emit_alert(client):
    """POST /api/v1/system/resume → emit_alert 被调用一次，level=P2，event_code=TRADING_RESUMED。"""
    with patch("src.risk.guards.emit_alert") as mock_emit:
        resp = client.post("/api/v1/system/resume")
    assert resp.status_code == 200
    mock_emit.assert_called_once()
    call_args = mock_emit.call_args
    assert call_args.args[0] == "P2"
    ctx = call_args.args[2]
    assert ctx["event_code"] == "TRADING_RESUMED"


# ---------------------------------------------------------------------------
# 4. OnFrontConnected 事件码验证（通过 emit_alert 集成测试）
# ---------------------------------------------------------------------------

def test_front_connected_event_dispatches_correctly():
    """emit_alert with CTP_FRONT_CONNECTED produces correct RiskEvent via dispatcher."""
    from src.notifier.dispatcher import NotifierDispatcher, register_dispatcher

    feishu = MagicMock()
    feishu.send.return_value = True
    email = MagicMock()
    email.send.return_value = True
    register_dispatcher(NotifierDispatcher(feishu, email))

    from src.risk.guards import emit_alert
    emit_alert("P2", "CTP 行情前置已连接", {"event_code": "CTP_FRONT_CONNECTED", "source": "simnow_md"})

    event = feishu.send.call_args.args[0]
    assert event.event_code == "CTP_FRONT_CONNECTED"
    assert event.risk_level == "P2"
    assert event.source == "simnow_md"


# ---------------------------------------------------------------------------
# 5. OnFrontDisconnected 事件码验证
# ---------------------------------------------------------------------------

def test_front_disconnected_event_dispatches_p1():
    """emit_alert with CTP_FRONT_DISCONNECTED produces P1 RiskEvent."""
    from src.notifier.dispatcher import NotifierDispatcher, register_dispatcher

    feishu = MagicMock()
    feishu.send.return_value = True
    email = MagicMock()
    email.send.return_value = True
    register_dispatcher(NotifierDispatcher(feishu, email))

    from src.risk.guards import emit_alert
    emit_alert("P1", "CTP 交易前置断开 reason=4097", {"event_code": "CTP_FRONT_DISCONNECTED", "source": "simnow_td"})

    event = feishu.send.call_args.args[0]
    assert event.event_code == "CTP_FRONT_DISCONNECTED"
    assert event.risk_level == "P1"


def test_is_trading_session_filters_non_session_noise():
    """交易时段精确匹配：9:00-11:30 / 13:00-15:00 / 21:00-23:00，其余全部 False。"""
    from src.gateway.simnow import is_trading_session

    # 工作日交易时段 → True
    assert is_trading_session(datetime(2026, 4, 14, 9, 0)) is True     # Tue 09:00 开盘
    assert is_trading_session(datetime(2026, 4, 14, 9, 30)) is True    # Tue 09:30
    assert is_trading_session(datetime(2026, 4, 14, 11, 29)) is True   # Tue 11:29 即将收盘
    assert is_trading_session(datetime(2026, 4, 14, 13, 0)) is True    # Tue 13:00 午盘开
    assert is_trading_session(datetime(2026, 4, 14, 14, 59)) is True   # Tue 14:59
    assert is_trading_session(datetime(2026, 4, 14, 21, 0)) is True    # Tue 21:00 夜盘开
    assert is_trading_session(datetime(2026, 4, 14, 22, 59)) is True   # Tue 22:59

    # 工作日非交易时段 → False
    assert is_trading_session(datetime(2026, 4, 14, 8, 55)) is False   # Tue 08:55 盘前
    assert is_trading_session(datetime(2026, 4, 14, 11, 30)) is False  # Tue 11:30 收盘
    assert is_trading_session(datetime(2026, 4, 14, 12, 0)) is False   # Tue 12:00 午休
    assert is_trading_session(datetime(2026, 4, 14, 15, 0)) is False   # Tue 15:00 收盘
    assert is_trading_session(datetime(2026, 4, 14, 16, 0)) is False   # Tue 16:00
    assert is_trading_session(datetime(2026, 4, 14, 20, 55)) is False  # Tue 20:55 盘前
    assert is_trading_session(datetime(2026, 4, 14, 23, 0)) is False   # Tue 23:00 收盘
    assert is_trading_session(datetime(2026, 4, 14, 6, 0)) is False    # Tue 06:00
    assert is_trading_session(datetime(2026, 4, 15, 1, 0)) is False    # Wed 01:00 无凌晨盘

    # 周末完全静默 → False
    assert is_trading_session(datetime(2026, 4, 18, 9, 30)) is False   # Sat 09:30
    assert is_trading_session(datetime(2026, 4, 18, 21, 30)) is False  # Sat 21:30
    assert is_trading_session(datetime(2026, 4, 19, 10, 0)) is False   # Sun 10:00


def test_risk_alerts_sse_returns_keepalive():
    """风控告警 SSE 不应再伪造固定 P1 告警。"""
    from src.api.router import get_risk_alerts

    async def _read_first_chunk():
        resp = await get_risk_alerts()
        first = await resp.body_iterator.__anext__()
        return resp, first

    resp, first_chunk = asyncio.run(_read_first_chunk())
    if isinstance(first_chunk, bytes):
        first_chunk = first_chunk.decode()

    assert resp.media_type == "text/event-stream"
    assert ": keepalive" in first_chunk
    assert "保证金率超过 70%" not in first_chunk


# ---------------------------------------------------------------------------
# 6. 恢复流程通知验证
# ---------------------------------------------------------------------------

def test_recovery_notification_after_disconnect():
    """After CTP_FRONT_DISCONNECTED dispatched, emit_recovery sends RECOVERED event."""
    import time as _time
    from src.notifier.dispatcher import NotifierDispatcher, register_dispatcher

    feishu = MagicMock()
    feishu.send.return_value = True
    email = MagicMock()
    email.send.return_value = True
    dp = NotifierDispatcher(feishu, email, dedup_window_s=0.01)
    register_dispatcher(dp)

    from src.risk.guards import emit_alert
    emit_alert("P1", "CTP 前置断开", {"event_code": "CTP_FRONT_DISCONNECTED"})

    _time.sleep(0.02)  # wait for dedup window to expire

    result = dp.emit_recovery("CTP_FRONT_DISCONNECTED")
    assert result is not None

    last_event = feishu.send.call_args.args[0]
    assert last_event.event_code == "CTP_FRONT_DISCONNECTED_RECOVERED"
    assert last_event.risk_level == "P2"


# ---------------------------------------------------------------------------
# 7. CTP 成交回报数据流入 ledger
# ---------------------------------------------------------------------------

def test_trade_data_flows_to_ledger():
    """add_trade() 后 ledger 成交列表包含该记录。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    trade = {
        "instrument_id": "rb2510",
        "price": 3500.0,
        "volume": 1,
        "trade_id": "T001",
        "direction": "0",
        "offset": "0",
        "trade_time": "10:30:00",
        "exchange_id": "SHFE",
    }
    ledger.add_trade(trade)
    trades = ledger.get_trades()
    assert len(trades) == 1
    assert trades[0]["instrument_id"] == "rb2510"
    assert trades[0]["price"] == 3500.0


# ---------------------------------------------------------------------------
# 8. CTP 账户数据更新 ledger
# ---------------------------------------------------------------------------

def test_account_data_updates_ledger():
    """update_account() 后 get_account_summary 包含资金数据。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    account = {
        "balance": 500000.0,
        "available": 490000.0,
        "margin": 10000.0,
        "floating_pnl": 200.0,
        "close_pnl": 300.0,
        "commission": 50.0,
    }
    ledger.update_account(account)
    # add_trade needed to make get_account_summary return non-empty
    ledger.add_trade({"instrument_id": "rb2510", "price": 3500.0, "volume": 1, "trade_id": "T1"})
    summary = ledger.get_account_summary()
    assert summary["total_pnl"] == 500.0  # close_pnl + floating_pnl


# ---------------------------------------------------------------------------
# 9. CTP 持仓数据更新 ledger
# ---------------------------------------------------------------------------

def test_position_data_updates_ledger():
    """update_positions() 后 get_positions 返回正确持仓。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    positions = [
        {"instrument_id": "rb2510", "direction": "2", "position": 5, "floating_pnl": 100.0},
        {"instrument_id": "cu2510", "direction": "3", "position": 2, "floating_pnl": -50.0},
    ]
    ledger.update_positions(positions)
    result = ledger.get_positions()
    assert len(result) == 2
    assert result[0]["instrument_id"] == "rb2510"
