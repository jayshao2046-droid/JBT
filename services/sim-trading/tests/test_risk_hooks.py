import pytest
from unittest.mock import MagicMock

from src.notifier.dispatcher import (
    NotifierDispatcher,
    SystemRiskState,
    clear_dispatcher,
    register_dispatcher,
)
from src.notifier.email import EmailNotifier
from src.notifier.feishu import FeishuNotifier
from src.risk.guards import RiskGuards, emit_alert


@pytest.fixture(autouse=True)
def _reset_dispatcher():
    clear_dispatcher()
    yield
    clear_dispatcher()


def test_risk_guards_instantiation():
    """RiskGuards 类可以被实例化，不触发 NotImplementedError。"""
    guards = RiskGuards()
    assert guards is not None


def test_risk_guards_has_reduce_only():
    """RiskGuards 存在 check_reduce_only 方法。"""
    guards = RiskGuards()
    assert hasattr(guards, "check_reduce_only")


def test_risk_guards_has_disaster_stop():
    """RiskGuards 存在 check_disaster_stop 方法。"""
    guards = RiskGuards()
    assert hasattr(guards, "check_disaster_stop")


def test_risk_guards_has_emit_alert():
    """RiskGuards 存在 emit_alert 方法。"""
    guards = RiskGuards()
    assert hasattr(guards, "emit_alert")


def test_emit_alert_without_dispatcher_returns_none(monkeypatch):
    """未 bootstrap dispatcher 时，emit_alert 应安全跳过，不抛异常。"""
    monkeypatch.setenv("STAGE", "sim")

    guards = RiskGuards()
    state = guards.emit_alert("P1", "dispatcher missing")

    assert state is None


def test_emit_alert_dispatches_minimal_risk_event(monkeypatch):
    """emit_alert 应将 level/message/context 映射为最小 RiskEvent 并经双通道发送。"""
    monkeypatch.setenv("STAGE", "live")

    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = True
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True
    register_dispatcher(NotifierDispatcher(feishu, email))

    state = emit_alert(
        "p2",
        "margin threshold reached",
        {
            "account_id": "ACC-001",
            "symbol": "IF2406",
            "trace_id": "TRACE-001",
        },
    )

    assert state == SystemRiskState.NORMAL

    event = feishu.send.call_args.args[0]
    assert event.task_id == "TASK-0014"
    assert event.stage_preset == "live"
    assert event.risk_level == "P2"
    assert event.account_id == "ACC-001"
    assert event.strategy_id == ""
    assert event.symbol == "IF2406"
    assert event.signal_id == ""
    assert event.trace_id == "TRACE-001"
    assert event.event_code == "RISK_ALERT"
    assert event.reason == "margin threshold reached"

    email_event = email.send.call_args.args[0]
    assert email_event == event


# TODO: 断网/断数据源下本地缓存行为验证
# 验收点（TASK-0013/TASK-0017 补充预审冻结）：
#   1. 断网时读取最近一次本地快照进行安全降级判断
#   2. 或安全拒绝开仓进入 Fail-Safe
#   3. 不得 crash，不得产出错误信号
#   4. 缓存路径：CACHE_SNAPSHOT_PATH（来自 .env.example）
#   5. 缓存过期判断：CACHE_STALE_SECONDS（来自 .env.example）
def test_offline_cache_behavior_placeholder():
    """断网/断数据源下缓存行为验证占位测试（当前 skip，等待 C 完整实现）。"""
    pytest.skip("offline cache behavior validation — pending TASK-0017 deployment pre-validation")
