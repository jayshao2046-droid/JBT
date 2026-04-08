"""Collector implementations for market data sources."""

from services.data.src.collectors.akshare_backup import AkshareBackupCollector
from services.data.src.collectors.base import BaseCollector
from services.data.src.collectors.macro_collector import MacroCollector
from services.data.src.collectors.news_api_collector import NewsAPICollector
from services.data.src.collectors.overseas_minute_collector import OverseasMinuteCollector
from services.data.src.collectors.position_collector import PositionCollector
from services.data.src.collectors.rss_collector import RSSCollector
from services.data.src.collectors.sentiment_collector import SentimentCollector
from services.data.src.collectors.shipping_collector import ShippingCollector
from services.data.src.collectors.stock_minute_collector import StockMinuteCollector
from services.data.src.collectors.tqsdk_collector import TqSdkCollector
from services.data.src.collectors.tushare_collector import TushareDailyCollector
from services.data.src.collectors.volatility_collector import VolatilityCollector

__all__ = [
    "BaseCollector",
    "TqSdkCollector",
    "TushareDailyCollector",
    "AkshareBackupCollector",
    "MacroCollector",
    "PositionCollector",
    "VolatilityCollector",
    "NewsAPICollector",
    "OverseasMinuteCollector",
    "RSSCollector",
    "SentimentCollector",
    "ShippingCollector",
    "StockMinuteCollector",
]
