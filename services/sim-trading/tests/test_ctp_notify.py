"""
test_ctp_notify.py — TASK-0014-A2 验证
1. _CTP_AVAILABLE=False 时，import simnow 不报错
2. pause_trading 路由调用后 emit_alert 被触发（mock dispatcher）
3. resume_trading 路由调用后 emit_alert 被触发（mock dispatcher）
"""
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

@pytest.fixture
def client():
    from src.main import app
    return TestClient(app)


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
