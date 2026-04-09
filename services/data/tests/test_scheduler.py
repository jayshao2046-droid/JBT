"""Smoke tests for JBT data service scheduler.

Validates scheduler module imports and basic structure.
"""

from __future__ import annotations

import importlib
import sys
import types
import pytest


def test_scheduler_importable() -> None:
    """data_scheduler module should be importable."""
    mod = importlib.import_module("services.data.src.scheduler.data_scheduler")
    assert mod is not None


def test_pipeline_importable() -> None:
    """pipeline module should be importable."""
    mod = importlib.import_module("services.data.src.scheduler.pipeline")
    assert mod is not None


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
