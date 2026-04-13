import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

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


def test_reduce_only_blocks_open_order(monkeypatch):
    """只减仓模式：offset='0'（开仓）应被拒绝。"""
    monkeypatch.setattr("src.risk.guards.get_dispatcher", lambda: None)
    guards = RiskGuards()
    order = {"instrument_id": "rb2510", "offset": "0", "direction": "0"}
    assert guards.check_reduce_only(order, []) is False


def test_reduce_only_allows_close_order(monkeypatch):
    """只减仓模式：offset='1'（平仓）应允许通过。"""
    monkeypatch.setattr("src.risk.guards.get_dispatcher", lambda: None)
    guards = RiskGuards()
    order = {"instrument_id": "rb2510", "offset": "1", "direction": "1"}
    assert guards.check_reduce_only(order, []) is True


def test_reduce_only_allows_close_today(monkeypatch):
    """只减仓模式：offset='3'（平今）应允许通过。"""
    monkeypatch.setattr("src.risk.guards.get_dispatcher", lambda: None)
    guards = RiskGuards()
    order = {"instrument_id": "rb2510", "offset": "3", "direction": "1"}
    assert guards.check_reduce_only(order, []) is True


def test_disaster_stop_triggers_on_large_drawdown(monkeypatch):
    """灾难止损：回撤超阈值时返回 False。"""
    monkeypatch.setenv("RISK_NAV_DRAWDOWN_HALT", "0.10")
    monkeypatch.setattr("src.risk.guards.get_dispatcher", lambda: None)
    guards = RiskGuards()
    acct = {"balance": 400000, "pre_balance": 500000}  # 20% 回撤
    assert guards.check_disaster_stop(acct) is False


def test_disaster_stop_ok_within_threshold(monkeypatch):
    """灾难止损：回撤未超阈值时返回 True。"""
    monkeypatch.setenv("RISK_NAV_DRAWDOWN_HALT", "0.10")
    monkeypatch.setattr("src.risk.guards.get_dispatcher", lambda: None)
    guards = RiskGuards()
    acct = {"balance": 480000, "pre_balance": 500000}  # 4% 回撤
    assert guards.check_disaster_stop(acct) is True


def test_disaster_stop_safe_on_zero_pre_balance(monkeypatch):
    """灾难止损：pre_balance 为 0 时安全放行。"""
    monkeypatch.setenv("RISK_NAV_DRAWDOWN_HALT", "0.10")
    monkeypatch.setattr("src.risk.guards.get_dispatcher", lambda: None)
    guards = RiskGuards()
    acct = {"balance": 500000, "pre_balance": 0}
    assert guards.check_disaster_stop(acct) is True


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


# ---------------------------------------------------------------------------
# A4: RiskEventCategory 推断 — 运行时事件
# ---------------------------------------------------------------------------

def test_infer_category_ctp_front_events():
    """CTP_FRONT_CONNECTED/DISCONNECTED 前缀未命中 CTP_CONN，回退到 SYSTEM。"""
    from src.risk.guards import infer_category, RiskEventCategory
    assert infer_category("CTP_FRONT_CONNECTED") == RiskEventCategory.SYSTEM
    assert infer_category("CTP_FRONT_DISCONNECTED") == RiskEventCategory.SYSTEM


def test_infer_category_system_shutdown():
    """SYSTEM_SHUTDOWN 命中 SYS 前缀，映射为 SYSTEM。"""
    from src.risk.guards import infer_category, RiskEventCategory
    assert infer_category("SYSTEM_SHUTDOWN") == RiskEventCategory.SYSTEM


def test_infer_category_ctp_rsp_error():
    """CTP_RSP_ERROR 前缀未命中已有映射，回退到 SYSTEM。"""
    from src.risk.guards import infer_category, RiskEventCategory
    assert infer_category("CTP_RSP_ERROR") == RiskEventCategory.SYSTEM


# ---------------------------------------------------------------------------
# A4: 升级机制 — 连续断线场景
# ---------------------------------------------------------------------------

def test_escalation_consecutive_disconnects():
    """连续 CTP_FRONT_DISCONNECTED 在 escalation_window 内达到阈值时 P1 升级为 P0。"""
    import time as _time

    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = True
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True
    dp = NotifierDispatcher(feishu, email, dedup_window_s=0.01, escalation_threshold=3, escalation_window_s=300.0)
    register_dispatcher(dp)

    for i in range(3):
        emit_alert("P1", f"CTP 断开 #{i}", {"event_code": "CTP_FRONT_DISCONNECTED"})
        _time.sleep(0.02)  # ensure dedup window expires

    last_event = feishu.send.call_args.args[0]
    assert last_event.risk_level == "P0"


def test_escalation_does_not_affect_p2():
    """P2 事件不受升级机制影响，即使频率超阈值。"""
    import time as _time

    feishu = MagicMock(spec=FeishuNotifier)
    feishu.send.return_value = True
    email = MagicMock(spec=EmailNotifier)
    email.send.return_value = True
    dp = NotifierDispatcher(feishu, email, dedup_window_s=0.01, escalation_threshold=3, escalation_window_s=300.0)
    register_dispatcher(dp)

    for i in range(5):
        emit_alert("P2", f"CTP 前置已连接 #{i}", {"event_code": "CTP_FRONT_CONNECTED"})
        _time.sleep(0.02)

    last_event = feishu.send.call_args.args[0]
    assert last_event.risk_level == "P2"


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
