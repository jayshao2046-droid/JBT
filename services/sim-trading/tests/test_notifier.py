"""
test_notifier.py — TASK-0014 P1
pytest 测试：飞书通道 / 邮件通道 / Dispatcher 双通道失败阻单 / 字段完整性
"""
import dataclasses
from unittest.mock import MagicMock

import pytest

from src.main import app, bootstrap_notifier_dispatcher
from src.notifier.dispatcher import NotifierDispatcher, RiskEvent, SystemRiskState
from src.notifier.dispatcher import bootstrap_dispatcher, clear_dispatcher, get_dispatcher
from src.notifier.feishu import FeishuNotifier
from src.notifier.email import EmailNotifier


@pytest.fixture(autouse=True)
def _reset_dispatcher():
    clear_dispatcher()
    yield
    clear_dispatcher()


# ---------------------------------------------------------------------------
# 辅助工厂
# ---------------------------------------------------------------------------

def _make_event(**kwargs) -> RiskEvent:
    defaults = dict(
        task_id="TASK-0014",
        stage_preset="sim",
        risk_level="P1",
        account_id="ACC-001",
        strategy_id="STR-001",
        symbol="IF2406",
        signal_id="SIG-001",
        trace_id="TRACE-001",
        event_code="RISK_REDUCE_ONLY",
        reason="drawdown exceeded threshold",
    )
    defaults.update(kwargs)
    return RiskEvent(**defaults)


# ---------------------------------------------------------------------------
# FeishuNotifier
# ---------------------------------------------------------------------------

def test_feishu_send_disabled_returns_true(monkeypatch):
    """NOTIFY_FEISHU_ENABLED=false 时 send() 应立即返回 True（跳过即通过）。"""
    monkeypatch.setenv("NOTIFY_FEISHU_ENABLED", "false")
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "")
    notifier = FeishuNotifier()
    assert notifier.send(_make_event()) is True


# ---------------------------------------------------------------------------
# EmailNotifier
# ---------------------------------------------------------------------------

def test_email_send_disabled_returns_true(monkeypatch):
    """NOTIFY_EMAIL_ENABLED=false 时 send() 应立即返回 True（跳过即通过）。"""
    monkeypatch.setenv("NOTIFY_EMAIL_ENABLED", "false")
    notifier = EmailNotifier()
    assert notifier.send(_make_event()) is True


# ---------------------------------------------------------------------------
# NotifierDispatcher
# ---------------------------------------------------------------------------

def test_dispatcher_both_fail_blocks_orders():
    """双通道均返回 False → state == ORDERS_BLOCKED，is_orders_blocked() == True。"""
    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = False
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = False

    dispatcher = NotifierDispatcher(feishu, email)
    state = dispatcher.dispatch(_make_event())

    assert state == SystemRiskState.ORDERS_BLOCKED
    assert dispatcher.is_orders_blocked() is True


def test_dispatcher_one_fail_not_blocked():
    """飞书失败 / 邮件成功 → state == FEISHU_FAILED，is_orders_blocked() == False。"""
    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = False
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True

    dispatcher = NotifierDispatcher(feishu, email)
    state = dispatcher.dispatch(_make_event())

    assert state == SystemRiskState.FEISHU_FAILED
    assert dispatcher.is_orders_blocked() is False


def test_bootstrap_dispatcher_returns_singleton(monkeypatch):
    """bootstrap_dispatcher 应返回可复用的进程内单例。"""
    monkeypatch.setenv("NOTIFY_FEISHU_ENABLED", "false")
    monkeypatch.setenv("NOTIFY_EMAIL_ENABLED", "false")

    first = bootstrap_dispatcher()
    second = bootstrap_dispatcher()

    assert first is second
    assert get_dispatcher() is first


def test_main_bootstrap_registers_dispatcher_on_app_state(monkeypatch):
    """main.py bootstrap 应把 dispatcher 同时注册到全局单例和 app.state。"""
    monkeypatch.setenv("NOTIFY_FEISHU_ENABLED", "false")
    monkeypatch.setenv("NOTIFY_EMAIL_ENABLED", "false")

    dispatcher = bootstrap_notifier_dispatcher(force=True)

    assert get_dispatcher() is dispatcher
    assert app.state.notifier_dispatcher is dispatcher


# ---------------------------------------------------------------------------
# RiskEvent 字段完整性
# ---------------------------------------------------------------------------

def test_risk_event_has_required_fields():
    """RiskEvent dataclass 必须包含 10 个规定字段。"""
    required_fields = {
        "task_id",
        "stage_preset",
        "risk_level",
        "account_id",
        "strategy_id",
        "symbol",
        "signal_id",
        "trace_id",
        "event_code",
        "reason",
    }
    actual_fields = {f.name for f in dataclasses.fields(RiskEvent)}
    assert required_fields == actual_fields
