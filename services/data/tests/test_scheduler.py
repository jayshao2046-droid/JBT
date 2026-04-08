"""Smoke tests for JBT data service scheduler.

Validates scheduler module imports and basic structure.
"""

from __future__ import annotations

import importlib
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
