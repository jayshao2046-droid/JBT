"""Collector implementations for market data sources."""

from collectors.akshare_backup import AkshareBackupCollector
from collectors.base import BaseCollector
from collectors.macro_collector import MacroCollector
from collectors.news_api_collector import NewsAPICollector
from collectors.overseas_minute_collector import OverseasMinuteCollector
from collectors.position_collector import PositionCollector
from collectors.rss_collector import RSSCollector
from collectors.sentiment_collector import SentimentCollector
from collectors.shipping_collector import ShippingCollector
from collectors.stock_minute_collector import StockMinuteCollector
from collectors.tqsdk_collector import TqSdkCollector
from collectors.tushare_collector import TushareDailyCollector
from collectors.volatility_collector import VolatilityCollector

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
