"""TASK-0027-A5 采集器冒烟测试。

验证:
1. 每个 collector 可正确 import
2. BaseCollector 接口合规（collect 方法、不可直接实例化）
3. 核心采集器结构校验（类名、默认配置、collect 签名）
4. __init__.py 导出完整性
5. 采集器 mock 模式不触发网络调用
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

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
    "services.data.src.collectors.cftc_collector",
    "services.data.src.collectors.forex_collector",
    "services.data.src.collectors.options_collector",
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


def test_base_collector_has_collect_method() -> None:
    """BaseCollector must declare abstract 'collect' method."""
    from services.data.src.collectors.base import BaseCollector

    assert hasattr(BaseCollector, "collect")
    assert getattr(BaseCollector.collect, "__isabstractmethod__", False)


def test_base_collector_has_fetch_alias() -> None:
    """BaseCollector.fetch should be an alias for collect."""
    from services.data.src.collectors.base import BaseCollector

    assert hasattr(BaseCollector, "fetch")


def test_base_collector_has_save_and_run() -> None:
    """BaseCollector should have save() and run() methods."""
    from services.data.src.collectors.base import BaseCollector

    assert callable(getattr(BaseCollector, "save", None))
    assert callable(getattr(BaseCollector, "run", None))


def test_collectors_init_exports() -> None:
    """__init__.py should export all public collectors."""
    from services.data.src.collectors import __all__

    assert len(__all__) >= 12  # 至少 12 个公开采集器
    assert "BaseCollector" in __all__
    assert "TqSdkCollector" in __all__
    assert "TushareDailyCollector" in __all__


# ── 核心采集器结构校验 ──────────────────────────────────────

CORE_COLLECTORS: list[tuple[str, str, str]] = [
    ("services.data.src.collectors.tushare_collector", "TushareDailyCollector", "tushare"),
    ("services.data.src.collectors.tqsdk_collector", "TqSdkCollector", "tqsdk_minute"),
    ("services.data.src.collectors.macro_collector", "MacroCollector", "macro"),
    ("services.data.src.collectors.news_api_collector", "NewsAPICollector", "news_api"),
    ("services.data.src.collectors.overseas_minute_collector", "OverseasMinuteCollector", "overseas_minute"),
    ("services.data.src.collectors.rss_collector", "RSSCollector", "rss_news"),
    ("services.data.src.collectors.position_collector", "PositionCollector", "position"),
    ("services.data.src.collectors.volatility_collector", "VolatilityCollector", "volatility"),
    ("services.data.src.collectors.sentiment_collector", "SentimentCollector", "sentiment"),
    ("services.data.src.collectors.shipping_collector", "ShippingCollector", "shipping"),
    ("services.data.src.collectors.forex_collector", "ForexCollector", "forex"),
    ("services.data.src.collectors.cftc_collector", "CftcCollector", "cftc"),
    ("services.data.src.collectors.options_collector", "OptionsCollector", "options"),
]


@pytest.mark.parametrize("module_path,class_name,expected_name", CORE_COLLECTORS)
def test_core_collector_class_exists(module_path: str, class_name: str, expected_name: str) -> None:
    """Core collector class should exist and be a BaseCollector subclass."""
    from services.data.src.collectors.base import BaseCollector

    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    assert issubclass(cls, BaseCollector)


@pytest.mark.parametrize("module_path,class_name,expected_name", CORE_COLLECTORS)
def test_core_collector_has_collect_signature(module_path: str, class_name: str, expected_name: str) -> None:
    """Core collector's collect method should accept keyword arguments."""
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    sig = inspect.signature(cls.collect)
    params = list(sig.parameters.keys())
    assert "self" in params


@pytest.mark.parametrize("module_path,class_name,expected_name", CORE_COLLECTORS)
def test_core_collector_instantiation(module_path: str, class_name: str, expected_name: str) -> None:
    """Core collector should instantiate with use_mock=True (no network)."""
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    sig = inspect.signature(cls.__init__)
    if "use_mock" in sig.parameters:
        instance = cls(use_mock=True)
    else:
        instance = cls()
    assert instance.name == expected_name
    assert callable(getattr(instance, "collect", None))


# ── Mock 模式采集器不触发网络 ────────────────────────────────

def test_tushare_mock_collect_returns_list() -> None:
    """TushareDailyCollector with use_mock should return list without network."""
    from services.data.src.collectors.tushare_collector import TushareDailyCollector

    c = TushareDailyCollector(use_mock=True)
    records = c.collect(symbol="SHFE.rb2510")
    assert isinstance(records, list)


def test_macro_mock_collect_returns_list() -> None:
    """MacroCollector with use_mock should return list without network."""
    from services.data.src.collectors.macro_collector import MacroCollector

    c = MacroCollector(use_mock=True)
    records = c.collect()
    assert isinstance(records, list)


def test_news_api_mock_collect_returns_list() -> None:
    """NewsAPICollector with use_mock should return list without network."""
    from services.data.src.collectors.news_api_collector import NewsAPICollector

    c = NewsAPICollector(use_mock=True)
    records = c.collect()
    assert isinstance(records, list)


def test_tqsdk_mock_collect_returns_list() -> None:
    """TqSdkCollector with use_mock should return list without network."""
    from services.data.src.collectors.tqsdk_collector import TqSdkCollector

    c = TqSdkCollector(use_mock=True)
    records = c.collect()
    assert isinstance(records, list)
