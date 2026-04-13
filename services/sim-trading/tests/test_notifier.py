"""
test_notifier.py — TASK-0014 P1
pytest 测试：飞书通道 / 邮件通道 / Dispatcher 双通道失败阻单 / 字段完整性
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dataclasses
from unittest.mock import MagicMock

import pytest

from src.main import bootstrap_notifier_dispatcher
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


def test_feishu_send_api_error_code_returns_false(monkeypatch):
    """飞书 API 返回 code!=0（如 19024）时 send() 应返回 False。"""
    import io
    import json
    import urllib.request

    monkeypatch.setenv("NOTIFY_FEISHU_ENABLED", "true")
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://fake.example/hook")

    class _FakeResp:
        def read(self):
            return json.dumps({"code": 19024, "msg": "Key Words Not Found"}).encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: _FakeResp())
    notifier = FeishuNotifier()
    assert notifier.send(_make_event()) is False


def test_feishu_send_api_success_code_returns_true(monkeypatch):
    """飞书 API 返回 code=0 时 send() 应返回 True。"""
    import json
    import urllib.request

    monkeypatch.setenv("NOTIFY_FEISHU_ENABLED", "true")
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://fake.example/hook")

    class _FakeResp:
        def read(self):
            return json.dumps({"code": 0, "msg": "success"}).encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: _FakeResp())
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

    # 在测试函数内部导入 app，避免模块级别导入被其他测试的 reload 影响
    from src.main import app

    assert get_dispatcher() is dispatcher
    assert app.state.notifier_dispatcher is dispatcher


# ---------------------------------------------------------------------------
# RiskEvent 字段完整性
# ---------------------------------------------------------------------------

def test_risk_event_has_required_fields():
    """RiskEvent dataclass 必须包含 15 个规定字段（含 A3 新增）。"""
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
        # A3 additions
        "source",
        "message",
        "timestamp",
        "extra",
        "category",
    }
    actual_fields = {f.name for f in dataclasses.fields(RiskEvent)}
    assert required_fields == actual_fields


# ---------------------------------------------------------------------------
# A3: Dedup / Suppression
# ---------------------------------------------------------------------------

def test_dedup_window_suppresses_duplicate():
    """同一 event_code 在去重窗口内只触发一次实际发送。"""
    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = True
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True

    dispatcher = NotifierDispatcher(feishu, email, dedup_window_s=60)

    event1 = _make_event(event_code="CTP_CONN_LOST")
    event2 = _make_event(event_code="CTP_CONN_LOST")

    dispatcher.dispatch(event1)
    dispatcher.dispatch(event2)

    assert feishu.send.call_count == 1
    assert email.send.call_count == 1
    assert dispatcher.get_suppressed_count("CTP_CONN_LOST") == 1


def test_dedup_window_allows_different_codes():
    """不同 event_code 不受去重影响，各自独立发送。"""
    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = True
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True

    dispatcher = NotifierDispatcher(feishu, email, dedup_window_s=60)

    dispatcher.dispatch(_make_event(event_code="CTP_CONN_LOST"))
    dispatcher.dispatch(_make_event(event_code="CTP_AUTH_FAIL"))

    assert feishu.send.call_count == 2
    assert email.send.call_count == 2


# ---------------------------------------------------------------------------
# A3: Escalation
# ---------------------------------------------------------------------------

def test_escalation_p1_to_p0():
    """连续触发超阈值后 P1 自动升级为 P0。"""
    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = True
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True

    dispatcher = NotifierDispatcher(
        feishu, email,
        dedup_window_s=0,  # disable dedup for this test
        escalation_threshold=3,
        escalation_window_s=300,
    )

    events = [_make_event(event_code="CTP_AUTH_FAIL", risk_level="P1") for _ in range(3)]
    for e in events:
        dispatcher.dispatch(e)

    # The 3rd event should have been escalated to P0
    assert events[-1].risk_level == "P0"
    # First two should remain P1
    assert events[0].risk_level == "P1"
    assert events[1].risk_level == "P1"


# ---------------------------------------------------------------------------
# A3: RiskEvent Category Inference
# ---------------------------------------------------------------------------

def test_category_inference():
    """event_code 前缀正确映射到 RiskEventCategory。"""
    from src.risk.guards import infer_category, RiskEventCategory

    assert infer_category("CTP_CONN_LOST") == RiskEventCategory.CTP_CONNECTION
    assert infer_category("CTP_AUTH_FAIL") == RiskEventCategory.CTP_AUTH
    assert infer_category("CTP_TRADE_REJECT") == RiskEventCategory.CTP_TRADING
    assert infer_category("CTP_ORDER_CANCEL") == RiskEventCategory.CTP_TRADING
    assert infer_category("RISK_REDUCE_ONLY") == RiskEventCategory.RISK_LIMIT
    assert infer_category("SYS_RESTART") == RiskEventCategory.SYSTEM
    assert infer_category("UNKNOWN_EVENT") == RiskEventCategory.SYSTEM


# ---------------------------------------------------------------------------
# A3: Feishu Card Color Mapping
# ---------------------------------------------------------------------------

def test_feishu_card_color_mapping():
    """飞书卡片颜色映射符合 JBT 统一标准。"""
    from src.notifier.feishu import _LEVEL_COLOR

    assert _LEVEL_COLOR["P0"] == "red"
    assert _LEVEL_COLOR["P1"] == "orange"
    assert _LEVEL_COLOR["P2"] == "yellow"


# ---------------------------------------------------------------------------
# A3: Email Safe Degradation
# ---------------------------------------------------------------------------

def test_email_missing_smtp_returns_false(monkeypatch):
    """启用邮件但缺少 SMTP 配置时应安全降级 → 返回 False。"""
    monkeypatch.setenv("NOTIFY_EMAIL_ENABLED", "true")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_HOST", "")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_USER", "")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_PASSWORD", "")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "")
    monkeypatch.setenv("ALERT_EMAIL_TO", "")

    notifier = EmailNotifier()
    assert notifier.send(_make_event()) is False


def test_send_risk_email_convenience(monkeypatch):
    """send_risk_email 便捷函数在未配置时安全降级。"""
    from src.notifier.email import send_risk_email

    monkeypatch.setenv("NOTIFY_EMAIL_ENABLED", "false")
    assert send_risk_email(_make_event()) is True


# ---------------------------------------------------------------------------
# Daily Report Email (TASK-0019-B1)
# ---------------------------------------------------------------------------

def test_send_daily_report_email_signature():
    """send_daily_report_email 接受 dict 参数并返回 bool。"""
    from src.notifier.email import send_daily_report_email
    import inspect

    sig = inspect.signature(send_daily_report_email)
    params = list(sig.parameters.keys())
    assert params == ["report_data"]


def test_send_daily_report_email_missing_smtp_returns_false(monkeypatch):
    """SMTP 未配置时 send_daily_report_email 安全降级返回 False。"""
    from src.notifier.email import send_daily_report_email

    monkeypatch.setenv("ALERT_EMAIL_SMTP_HOST", "")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_USER", "")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_PASSWORD", "")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "")
    monkeypatch.setenv("ALERT_EMAIL_TO", "")

    result = send_daily_report_email({
        "date": "2026-04-10",
        "total_pnl": 0,
        "win_rate": 0,
        "trade_count": 0,
        "positions": [],
        "trades": [],
    })
    assert result is False


def test_send_daily_report_email_template_fields(monkeypatch):
    """send_daily_report_email 生成的邮件包含关键模板字段。"""
    from src.notifier.email import send_daily_report_email
    import smtplib

    sent_messages = []

    class FakeSMTP:
        def __init__(self, *a, **kw):
            pass
        def ehlo(self):
            pass
        def starttls(self):
            pass
        def login(self, user, password):
            pass
        def sendmail(self, from_addr, to_addrs, msg):
            sent_messages.append(msg)
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("ALERT_EMAIL_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_PORT", "587")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_USER", "user@test.com")
    monkeypatch.setenv("ALERT_EMAIL_SMTP_PASSWORD", "secret")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "from@test.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "to@test.com")

    result = send_daily_report_email({
        "date": "2026-04-10",
        "total_pnl": 1234.56,
        "win_rate": 66.7,
        "trade_count": 12,
        "positions": [{"symbol": "IF2406", "direction": "long", "volume": 2, "pnl": 500}],
        "trades": [],
    })
    assert result is True
    assert len(sent_messages) == 1

    # 解码 MIME 消息
    import email as email_mod
    parsed = email_mod.message_from_string(sent_messages[0])
    # 获取 HTML payload
    for part in parsed.walk():
        if part.get_content_type() == "text/html":
            body = part.get_payload(decode=True).decode("utf-8")
            break
    else:
        body = parsed.get_payload(decode=True).decode("utf-8")

    assert "SIM-DAILY" in body
    assert "2026-04-10" in body
    assert "#2980b9" in body
    assert "1234.56" in body
    assert "66.7" in body
    assert "IF2406" in body
