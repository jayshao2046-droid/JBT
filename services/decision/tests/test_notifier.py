"""
test_notifier.py — TASK-0021 F batch
单元测试：决策服务通知模块
"""
import os
import json
import smtplib
import unittest.mock as mock
import urllib.request

import pytest

from src.notifier.dispatcher import DecisionEvent, NotifyLevel, NotifierDispatcher, DispatchState
from src.notifier.feishu import DecisionFeishuNotifier
from src.notifier.email import DecisionEmailNotifier


# ── Feishu 测试 ──────────────────────────────────────────────────────────────

def test_feishu_disabled_returns_true():
    """NOTIFY_FEISHU_ENABLED=false 时，直接返回 True 不发送。"""
    os.environ["NOTIFY_FEISHU_ENABLED"] = "false"
    notifier = DecisionFeishuNotifier()
    event = DecisionEvent(
        event_type="SYSTEM",
        notify_level=NotifyLevel.NOTIFY,
        event_code="TEST-001",
        title="Test",
        body="test body",
    )
    assert notifier.send(event) is True


def test_feishu_enabled_no_url_returns_false():
    """NOTIFY_FEISHU_ENABLED=true 但无 webhook URL，返回 False。"""
    os.environ["NOTIFY_FEISHU_ENABLED"] = "true"
    os.environ.pop("FEISHU_WEBHOOK_URL", None)
    notifier = DecisionFeishuNotifier()
    event = DecisionEvent(
        event_type="SYSTEM",
        notify_level=NotifyLevel.P1,
        event_code="TEST-002",
        title="Alert",
        body="alert body",
    )
    assert notifier.send(event) is False


def test_feishu_sends_interactive_card(monkeypatch):
    """启用后发送飞书 interactive card。"""
    os.environ["NOTIFY_FEISHU_ENABLED"] = "true"
    os.environ["FEISHU_WEBHOOK_URL"] = "http://fake-feishu.example.com/hook"

    captured_payload = {}

    class FakeResponse:
        def read(self): return json.dumps({"code": 0}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout=10):
        captured_payload["data"] = json.loads(req.data.decode())
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    notifier = DecisionFeishuNotifier()
    event = DecisionEvent(
        event_type="RESEARCH",
        notify_level=NotifyLevel.RESEARCH,
        event_code="RES-001",
        title="研究完成",
        body="**Sharpe:** 1.23",
        strategy_id="S001",
        model_id="XGBoost",
        session_id="sess-abc",
    )
    assert notifier.send(event) is True
    card = captured_payload["data"]
    assert card["msg_type"] == "interactive"
    assert "RES-001" in json.dumps(card)
    assert card["card"]["header"]["template"] == "blue"


def test_feishu_level_colors():
    """各 notify_level 映射正确颜色。"""
    from src.notifier.feishu import _LEVEL_COLOR
    assert _LEVEL_COLOR["P0"] == "red"
    assert _LEVEL_COLOR["P1"] == "orange"
    assert _LEVEL_COLOR["P2"] == "yellow"
    assert _LEVEL_COLOR["SIGNAL"] == "grey"
    assert _LEVEL_COLOR["RESEARCH"] == "blue"
    assert _LEVEL_COLOR["NOTIFY"] == "turquoise"


# ── Email 测试 ──────────────────────────────────────────────────────────────

def test_email_disabled_returns_true():
    os.environ["NOTIFY_EMAIL_ENABLED"] = "false"
    notifier = DecisionEmailNotifier()
    event = DecisionEvent(
        event_type="DAILY",
        notify_level=NotifyLevel.NOTIFY,
        event_code="DAILY-001",
        title="日报",
        body="日报正文",
    )
    assert notifier.send(event) is True


def test_email_missing_env_returns_false():
    os.environ["NOTIFY_EMAIL_ENABLED"] = "true"
    for k in ["ALERT_EMAIL_SMTP_HOST", "ALERT_EMAIL_SMTP_USER", "ALERT_EMAIL_SMTP_PASSWORD",
              "ALERT_EMAIL_FROM", "ALERT_EMAIL_TO"]:
        os.environ.pop(k, None)
    notifier = DecisionEmailNotifier()
    event = DecisionEvent(
        event_type="SYSTEM",
        notify_level=NotifyLevel.P1,
        event_code="SYS-001",
        title="系统告警",
        body="body",
    )
    assert notifier.send(event) is False


def test_email_sends_html(monkeypatch):
    """启用且 SMTP 配置完整时，构建并发送 HTML 邮件。"""
    os.environ["NOTIFY_EMAIL_ENABLED"] = "true"
    os.environ["ALERT_EMAIL_SMTP_HOST"] = "smtp.example.com"
    os.environ["ALERT_EMAIL_SMTP_PORT"] = "587"
    os.environ["ALERT_EMAIL_SMTP_USER"] = "user@example.com"
    os.environ["ALERT_EMAIL_SMTP_PASSWORD"] = "pass"
    os.environ["ALERT_EMAIL_FROM"] = "from@example.com"
    os.environ["ALERT_EMAIL_TO"] = "to@example.com"

    sent_msgs = []

    class FakeSMTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def starttls(self): pass
        def login(self, *a): pass
        def sendmail(self, frm, to, msg): sent_msgs.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    notifier = DecisionEmailNotifier()
    event = DecisionEvent(
        event_type="RESEARCH",
        notify_level=NotifyLevel.RESEARCH,
        event_code="RES-HTML-001",
        title="研究摘要",
        body="摘要正文",
        model_id="XGBoost",
    )
    assert notifier.send(event) is True
    assert len(sent_msgs) == 1
    # HTML body is base64-encoded in MIME; decode and verify
    import base64, re
    b64_parts = re.findall(r"(?:[A-Za-z0-9+/]{4})+(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?", sent_msgs[0])
    decoded_all = ""
    for part in b64_parts:
        try:
            decoded_all += base64.b64decode(part).decode("utf-8", errors="ignore")
        except Exception:
            pass
    assert "RES-HTML-001" in decoded_all


# ── Dispatcher 测试 ──────────────────────────────────────────────────────────

def _make_event() -> DecisionEvent:
    return DecisionEvent(
        event_type="SYSTEM",
        notify_level=NotifyLevel.NOTIFY,
        event_code="DISP-001",
        title="dispatch test",
        body="body",
    )


def test_dispatcher_both_ok():
    feishu = mock.MagicMock(spec=DecisionFeishuNotifier)
    email = mock.MagicMock(spec=DecisionEmailNotifier)
    feishu.send.return_value = True
    email.send.return_value = True
    disp = NotifierDispatcher(feishu, email)
    state = disp.dispatch(_make_event())
    assert state == DispatchState.NORMAL


def test_dispatcher_feishu_fail():
    feishu = mock.MagicMock(spec=DecisionFeishuNotifier)
    email = mock.MagicMock(spec=DecisionEmailNotifier)
    feishu.send.return_value = False
    email.send.return_value = True
    disp = NotifierDispatcher(feishu, email)
    state = disp.dispatch(_make_event())
    assert state == DispatchState.FEISHU_FAILED


def test_dispatcher_email_fail():
    feishu = mock.MagicMock(spec=DecisionFeishuNotifier)
    email = mock.MagicMock(spec=DecisionEmailNotifier)
    feishu.send.return_value = True
    email.send.return_value = False
    disp = NotifierDispatcher(feishu, email)
    state = disp.dispatch(_make_event())
    assert state == DispatchState.EMAIL_FAILED


def test_dispatcher_both_fail():
    feishu = mock.MagicMock(spec=DecisionFeishuNotifier)
    email = mock.MagicMock(spec=DecisionEmailNotifier)
    feishu.send.return_value = False
    email.send.return_value = False
    disp = NotifierDispatcher(feishu, email)
    state = disp.dispatch(_make_event())
    assert state == DispatchState.BOTH_FAILED
