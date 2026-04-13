"""
test_report_scheduler.py — TASK-0019-B1
pytest 测试：scheduler 注册、generate_daily_report 结构、定时触发、SMTP 未配置不崩溃
"""
import asyncio
from datetime import datetime
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# generate_daily_report 结构
# ---------------------------------------------------------------------------

def test_generate_daily_report_returns_required_keys():
    """generate_daily_report() 返回的 dict 必须包含 6 个规定字段。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    report = ledger.generate_daily_report()

    required_keys = {"date", "total_pnl", "win_rate", "trade_count", "positions", "trades"}
    assert required_keys == set(report.keys())


def test_generate_daily_report_default_values():
    """无实际数据时，generate_daily_report 返回合理默认值。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    report = ledger.generate_daily_report()

    assert isinstance(report["date"], str)
    assert report["total_pnl"] == 0.0
    assert report["win_rate"] == 0.0
    assert report["trade_count"] == 0
    assert isinstance(report["positions"], list)
    assert isinstance(report["trades"], list)


def test_generate_daily_report_date_format():
    """date 字段应为 ISO 格式 (YYYY-MM-DD)。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    report = ledger.generate_daily_report()

    # 确认可被解析为日期
    parsed = datetime.strptime(report["date"], "%Y-%m-%d")
    assert parsed.date() == datetime.now().date()


# ---------------------------------------------------------------------------
# Scheduler 注册
# ---------------------------------------------------------------------------

def test_start_report_scheduler_registered():
    """start_report_scheduler 已注册为 FastAPI startup 事件。"""
    from src.main import app

    startup_handlers = [h.__name__ for h in app.router.on_startup]
    assert "start_report_scheduler" in startup_handlers


# ---------------------------------------------------------------------------
# 定时触发（mock datetime）
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_report_scheduler_triggers_at_target_time(monkeypatch):
    """_report_scheduler 在 sleep 到达后调用 generate_daily_report 并发送邮件。"""
    from src.main import _report_scheduler

    generate_called = False
    send_called = False

    class FakeLedger:
        def generate_daily_report(self):
            nonlocal generate_called
            generate_called = True
            return {
                "date": "2026-04-10",
                "total_pnl": 0,
                "win_rate": 0,
                "trade_count": 0,
                "positions": [],
                "trades": [],
            }

    def fake_send(report_data):
        nonlocal send_called
        send_called = True
        return True

    iteration = 0

    async def fake_sleep(seconds):
        nonlocal iteration
        iteration += 1
        if iteration >= 2:
            raise asyncio.CancelledError()

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    # 在 _report_scheduler 的 try 块中打补丁
    import src.ledger.service
    import src.notifier.email
    monkeypatch.setattr(src.ledger.service, "LedgerService", FakeLedger)
    monkeypatch.setattr(src.notifier.email, "send_daily_report_email", fake_send)

    with pytest.raises(asyncio.CancelledError):
        await _report_scheduler()

    assert generate_called
    assert send_called


# ---------------------------------------------------------------------------
# SMTP 未配置不崩溃
# ---------------------------------------------------------------------------

def test_scheduler_smtp_not_configured_no_crash(monkeypatch):
    """SMTP 未配置时，send_daily_report_email 安全降级，不抛异常。"""
    from src.notifier.email import send_daily_report_email
    from src.ledger.service import LedgerService

    # 清除所有 SMTP 环境变量
    for key in [
        "ALERT_EMAIL_SMTP_HOST", "ALERT_EMAIL_SMTP_USER",
        "ALERT_EMAIL_SMTP_PASSWORD", "ALERT_EMAIL_FROM", "ALERT_EMAIL_TO",
    ]:
        monkeypatch.setenv(key, "")

    ledger = LedgerService()
    report = ledger.generate_daily_report()

    # 不应抛异常
    result = send_daily_report_email(report)
    assert result is False


def test_scheduler_full_pipeline_no_crash(monkeypatch):
    """完整 pipeline（generate → send）即使 SMTP 未配置也不崩溃。"""
    for key in [
        "ALERT_EMAIL_SMTP_HOST", "ALERT_EMAIL_SMTP_USER",
        "ALERT_EMAIL_SMTP_PASSWORD", "ALERT_EMAIL_FROM", "ALERT_EMAIL_TO",
    ]:
        monkeypatch.setenv(key, "")

    from src.ledger.service import LedgerService
    from src.notifier.email import send_daily_report_email

    ledger = LedgerService()
    report = ledger.generate_daily_report()
    result = send_daily_report_email(report)

    assert result is False
    assert set(report.keys()) == {"date", "total_pnl", "win_rate", "trade_count", "positions", "trades"}


# ---------------------------------------------------------------------------
# add_trade 后报表包含实际交易数据
# ---------------------------------------------------------------------------

def test_report_with_actual_trades():
    """add_trade 后 generate_daily_report 包含实际成交数据。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    ledger.add_trade({"instrument_id": "rb2510", "price": 3500.0, "volume": 1, "pnl": 200.0, "trade_id": "T1"})
    ledger.add_trade({"instrument_id": "rb2510", "price": 3520.0, "volume": 1, "pnl": -50.0, "trade_id": "T2"})

    report = ledger.generate_daily_report()
    assert report["trade_count"] == 2
    assert len(report["trades"]) == 2
    assert report["total_pnl"] == 150.0  # 200 + (-50)
    assert report["win_rate"] == 50.0  # 1/2 * 100


def test_report_with_account_data():
    """update_account 后报表包含 CTP 资金数据。"""
    from src.ledger.service import LedgerService

    ledger = LedgerService()
    ledger.update_account({"close_pnl": 800.0, "floating_pnl": -200.0})
    ledger.add_trade({"instrument_id": "rb2510", "price": 3500.0, "volume": 1, "trade_id": "T1"})

    report = ledger.generate_daily_report()
    assert report["total_pnl"] == 600.0  # CTP: close_pnl + floating_pnl
    assert report["trade_count"] == 1


# ---------------------------------------------------------------------------
# 报表 API 端点
# ---------------------------------------------------------------------------

def test_report_daily_endpoint(client):
    """GET /api/v1/report/daily 返回正确的报表结构。"""
    from src.ledger.service import reset_ledger
    reset_ledger()

    resp = client.get("/api/v1/report/daily")
    assert resp.status_code == 200
    data = resp.json()
    required_keys = {"date", "total_pnl", "win_rate", "trade_count", "positions", "trades"}
    assert required_keys == set(data.keys())


def test_report_trades_endpoint(client):
    """GET /api/v1/report/trades 返回当日成交列表。"""
    from src.ledger.service import get_ledger, reset_ledger
    reset_ledger()

    ledger = get_ledger()
    ledger.add_trade({"instrument_id": "rb2510", "price": 3500.0, "volume": 1, "trade_id": "T1"})

    resp = client.get("/api/v1/report/trades")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["trades"]) == 1

    reset_ledger()


def test_report_positions_endpoint(client):
    """GET /api/v1/report/positions 返回当前持仓列表。"""
    from src.ledger.service import get_ledger, reset_ledger
    reset_ledger()

    ledger = get_ledger()
    ledger.update_positions([{"instrument_id": "rb2510", "position": 5}])

    resp = client.get("/api/v1/report/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["positions"]) == 1

    reset_ledger()
