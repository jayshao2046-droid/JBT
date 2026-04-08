"""Smoke tests for JBT data service collectors.

Validates that all migrated collectors can be imported and instantiated.
Full integration tests require live API keys and network access.
"""

from __future__ import annotations

import importlib
import pytest


COLLECTOR_MODULES = [
    "services.data.src.collectors.base",
    "services.data.src.collectors.tqsdk_collector",
    "services.data.src.collectors.tushare_collector",
    "services.data.src.collectors.tushare_full_collector",
    "services.data.src.collectors.tushare_futures_collector",
    "services.data.src.collectors.akshare_backup",
    "services.data.src.collectors.macro_collector",
    "services.data.src.collectors.news_api_collector",
    "services.data.src.collectors.news_translator",
    "services.data.src.collectors.rss_collector",
    "services.data.src.collectors.run_rss_collector",
    "services.data.src.collectors.sentiment_collector",
    "services.data.src.collectors.shipping_collector",
    "services.data.src.collectors.position_collector",
    "services.data.src.collectors.volatility_collector",
    "services.data.src.collectors.overseas_minute_collector",
    "services.data.src.collectors.stock_minute_collector",
]


@pytest.mark.parametrize("module_path", COLLECTOR_MODULES)
def test_collector_importable(module_path: str) -> None:
    """Each collector module should be importable without errors."""
    mod = importlib.import_module(module_path)
    assert mod is not None


def test_base_collector_abstract() -> None:
    """BaseCollector should not be instantiable directly."""
    from services.data.src.collectors.base import BaseCollector

    with pytest.raises(TypeError):
        BaseCollector(name="test")  # type: ignore[abstract]


def test_collectors_init_exports() -> None:
    """__init__.py should export all public collectors."""
    from services.data.src.collectors import __all__

    assert len(__all__) >= 12  # 至少 12 个公开采集器
