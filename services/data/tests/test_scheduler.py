"""TASK-0027-A5 调度器集成测试。

验证:
1. 模块可导入
2. DataScheduler / APScheduler 初始化 (mock)
3. pipeline 链路调用
4. 调度管道注册逻辑
5. 健康检查集成
6. 交易时段判断
7. _safe_run wrapper
"""

from __future__ import annotations

import importlib
import sys
import types
from typing import Any

import pytest


def test_scheduler_importable() -> None:
    """data_scheduler module should be importable."""
    mod = importlib.import_module("services.data.src.scheduler.data_scheduler")
    assert mod is not None


def test_pipeline_importable() -> None:
    """pipeline module should be importable (skip if polars missing)."""
    try:
        mod = importlib.import_module("services.data.src.scheduler.pipeline")
        assert mod is not None
    except ImportError:
        pytest.skip("pipeline dependencies not installed (polars)")


def test_heartbeat_importable() -> None:
    """heartbeat module should be importable."""
    from services.data.src.health.heartbeat import HeartbeatWriter
    assert HeartbeatWriter is not None


def test_ops_importable() -> None:
    """ops modules should be importable."""
    from services.data.src.ops.backup import backup_data_dir
    from services.data.src.ops.cleanup import cleanup_old_logs
    assert backup_data_dir is not None
    assert cleanup_old_logs is not None


def test_stock_minute_not_present_in_fallback_jobs() -> None:
    from services.data.src.scheduler import data_scheduler

    assert data_scheduler.STOCK_MINUTE_ENABLED is False
    assert "A股分钟K线" not in [name for name, *_ in data_scheduler._FALLBACK_JOBS]


def test_apscheduler_does_not_register_stock_minute(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.data.src.scheduler import data_scheduler

    class FakeScheduler:
        def __init__(self, timezone: str | None = None) -> None:
            self.jobs: list[types.SimpleNamespace] = []

        def add_job(self, func, trigger, args=None, kwargs=None, id=None, name=None, next_run_time=None):
            self.jobs.append(types.SimpleNamespace(id=id, name=name, trigger=trigger))

        def get_jobs(self):
            return list(self.jobs)

        def start(self):
            raise KeyboardInterrupt()

        def shutdown(self, wait: bool = False):
            return None

    fake_scheduler = FakeScheduler()
    monkeypatch.setitem(sys.modules, "apscheduler.schedulers.blocking", types.SimpleNamespace(BlockingScheduler=lambda timezone=None: fake_scheduler))
    monkeypatch.setitem(sys.modules, "apscheduler.triggers.cron", types.SimpleNamespace(CronTrigger=lambda *args, **kwargs: ("cron", args, kwargs)))
    monkeypatch.setitem(sys.modules, "apscheduler.triggers.interval", types.SimpleNamespace(IntervalTrigger=lambda *args, **kwargs: ("interval", args, kwargs)))
    monkeypatch.setattr(data_scheduler, "_get_notifier", lambda config: None)
    monkeypatch.setattr(data_scheduler, "_emit_market_transition_notifications", lambda: None)

    data_scheduler._run_with_apscheduler({})

    assert "stock_minute" not in [job.id for job in fake_scheduler.get_jobs()]


# ── APScheduler 注册完整性 ──────────────────────────────────

def test_apscheduler_registers_core_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """APScheduler should register all core collection jobs."""
    from services.data.src.scheduler import data_scheduler

    class FakeScheduler:
        def __init__(self, timezone: str | None = None) -> None:
            self.jobs: list[types.SimpleNamespace] = []

        def add_job(self, func, trigger, args=None, kwargs=None, id=None, name=None, next_run_time=None):
            self.jobs.append(types.SimpleNamespace(id=id, name=name, trigger=trigger))

        def get_jobs(self):
            return list(self.jobs)

        def start(self):
            raise KeyboardInterrupt()

        def shutdown(self, wait: bool = False):
            return None

    fake_scheduler = FakeScheduler()
    monkeypatch.setitem(sys.modules, "apscheduler.schedulers.blocking", types.SimpleNamespace(BlockingScheduler=lambda timezone=None: fake_scheduler))
    monkeypatch.setitem(sys.modules, "apscheduler.triggers.cron", types.SimpleNamespace(CronTrigger=lambda *args, **kwargs: ("cron", args, kwargs)))
    monkeypatch.setitem(sys.modules, "apscheduler.triggers.interval", types.SimpleNamespace(IntervalTrigger=lambda *args, **kwargs: ("interval", args, kwargs)))
    monkeypatch.setattr(data_scheduler, "_get_notifier", lambda config: None)
    monkeypatch.setattr(data_scheduler, "_emit_market_transition_notifications", lambda: None)

    data_scheduler._run_with_apscheduler({})

    registered_ids = {job.id for job in fake_scheduler.get_jobs()}
    expected_ids = {"minute_kline", "daily_kline", "macro", "position", "news_api", "rss"}
    assert expected_ids.issubset(registered_ids), f"missing: {expected_ids - registered_ids}"


def test_fallback_jobs_cover_all_pipelines() -> None:
    """_FALLBACK_JOBS should contain at least 15 entries."""
    from services.data.src.scheduler import data_scheduler

    assert len(data_scheduler._FALLBACK_JOBS) >= 15


def test_fallback_jobs_have_valid_callables() -> None:
    """Each entry in _FALLBACK_JOBS should have a callable function."""
    from services.data.src.scheduler import data_scheduler

    for name, func, interval_sec, daily_time in data_scheduler._FALLBACK_JOBS:
        assert callable(func), f"{name} func is not callable"
        assert isinstance(name, str) and len(name) > 0


# ── pipeline 链路校验 ──────────────────────────────────────

def test_pipeline_run_minute_exists() -> None:
    """pipeline should export run_minute_pipeline."""
    try:
        from services.data.src.scheduler.pipeline import run_minute_pipeline
        assert callable(run_minute_pipeline)
    except ImportError:
        pytest.skip("pipeline dependencies not installed (polars)")


def test_pipeline_run_daily_exists() -> None:
    """pipeline should export run_daily_pipeline."""
    try:
        from services.data.src.scheduler.pipeline import run_daily_pipeline
        assert callable(run_daily_pipeline)
    except ImportError:
        pytest.skip("pipeline dependencies not installed (polars)")


# ── 交易时段判断 ────────────────────────────────────────────

def test_trading_session_helpers_exist() -> None:
    """Scheduler should expose trading session helper functions."""
    from services.data.src.scheduler import data_scheduler

    assert callable(getattr(data_scheduler, "_is_futures_day_session", None))
    assert callable(getattr(data_scheduler, "_is_futures_night_session", None))
    assert callable(getattr(data_scheduler, "_is_trading_session", None))
    assert callable(getattr(data_scheduler, "_is_overseas_trading_hours", None))


def test_futures_day_session_weekend_returns_false() -> None:
    """Weekend should not be considered a futures day session."""
    from datetime import datetime
    from services.data.src.scheduler.data_scheduler import _is_futures_day_session

    saturday = datetime(2026, 4, 11, 10, 0)  # Saturday
    assert _is_futures_day_session(saturday) is False


def test_futures_night_session_friday_night_returns_false() -> None:
    """Friday night should not have a night session."""
    from datetime import datetime
    from services.data.src.scheduler.data_scheduler import _is_futures_night_session

    friday_night = datetime(2026, 4, 10, 21, 30)  # Friday 21:30
    assert _is_futures_night_session(friday_night) is False


# ── _safe_run 包装器 ────────────────────────────────────────

def test_safe_run_captures_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """_safe_run should not raise on function error."""
    from services.data.src.scheduler import data_scheduler

    monkeypatch.setattr(data_scheduler, "_get_dispatcher", lambda: None)

    def failing_func(**kwargs: Any) -> None:
        raise RuntimeError("test error")

    # Should not raise
    data_scheduler._safe_run("test_collector", failing_func)


def test_safe_run_extracts_record_count() -> None:
    """_extract_record_count should handle various return types."""
    from services.data.src.scheduler.data_scheduler import _extract_record_count

    assert _extract_record_count(42) == 42
    assert _extract_record_count({"a": 10, "b": 20}) == 30
    assert _extract_record_count([1, 2, 3]) == 3
    assert _extract_record_count(None) == 0


# ── 健康检查集成 ────────────────────────────────────────────

def test_health_check_skips_paused_stock_collectors(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.data.src.health import health_check

    monkeypatch.setattr(
        health_check,
        "DATA_RULES",
        {
            "stock_minute": {
                "dir": health_check.DATA_ROOT / "stock_minute",
                "max_age_h": 26,
                "trading_only": False,
                "weekend_skip": True,
                "label": "A股分钟",
                "paused_reason": "已暂停采集",
            },
            "stock_realtime": {
                "dir": health_check.DATA_ROOT / "stock_minute",
                "max_age_h": 2,
                "trading_only": True,
                "weekend_skip": False,
                "label": "A股实时",
                "paused_reason": "已暂停采集",
            },
        },
    )

    results = health_check.get_collector_freshness()

    assert len(results) == 2
    assert all(item["ok"] is True for item in results)
    assert all(item["skipped"] is True for item in results)
    assert all(item["age_str"] == "已暂停采集" for item in results)


def test_health_check_accepts_multiple_news_dirs(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.data.src.health import health_check

    existing_dir = tmp_path / "news_rss"
    existing_dir.mkdir(parents=True)
    (existing_dir / "records.parquet").write_text("ok", encoding="utf-8")

    monkeypatch.setattr(
        health_check,
        "DATA_RULES",
        {
            "news_rss": {
                "dirs": [tmp_path / "missing", existing_dir],
                "max_age_h": 3,
                "trading_only": False,
                "weekend_skip": False,
                "label": "新闻RSS",
            },
        },
    )

    results = health_check.get_collector_freshness()

    assert len(results) == 1
    assert results[0]["name"] == "news_rss"
    assert results[0]["ok"] is True


# ── get_factor_notifier / get_sla_tracker 存根 ──────────────

def test_stub_notifiers_are_safe() -> None:
    """Stub notifiers should not raise and return expected types."""
    from services.data.src.scheduler.data_scheduler import get_factor_notifier, get_sla_tracker

    fn = get_factor_notifier()
    assert fn.send_session_summary("morning") is True

    sla = get_sla_tracker()
    assert sla.send_daily_sla_report() is True
    sla.reset_daily()  # should not raise
