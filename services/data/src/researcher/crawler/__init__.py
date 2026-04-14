"""爬虫子模块 — 双模式引擎 + 采集源注册表 + 解析器"""

from .engine import CodeCrawler, BrowserCrawler, CrawlResult
from .source_registry import SourceRegistry
from .anti_detect import AntiDetect

__all__ = [
    "CodeCrawler",
    "BrowserCrawler",
    "CrawlResult",
    "SourceRegistry",
    "AntiDetect",
]
