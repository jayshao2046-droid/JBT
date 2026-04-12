"""Collector implementations for market data sources."""

from src.collectors.akshare_backup import AkshareBackupCollector
from src.collectors.base import BaseCollector
from src.collectors.macro_collector import MacroCollector
from src.collectors.news_api_collector import NewsAPICollector
from src.collectors.overseas_minute_collector import OverseasMinuteCollector
from src.collectors.position_collector import PositionCollector
from src.collectors.rss_collector import RSSCollector
from src.collectors.sentiment_collector import SentimentCollector
from src.collectors.shipping_collector import ShippingCollector
from src.collectors.stock_minute_collector import StockMinuteCollector
from src.collectors.tqsdk_collector import TqSdkCollector
from src.collectors.tushare_collector import TushareDailyCollector
from src.collectors.volatility_collector import VolatilityCollector

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
