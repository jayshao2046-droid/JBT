"""研究员模块 - 24/7 持续运行的数据研究员

主要组件：
- ProcessManager: 多进程管理器
- KlineMonitor: K线监控器
- NewsCrawler: 新闻爬虫
- FundamentalCrawler: 基本面爬虫
- LLMAnalyzer: LLM分析器
- ReportGenerator: 报告生成器
"""

from .process_manager import ProcessManager
from .kline_monitor import KlineMonitor
from .news_crawler import NewsCrawler
from .fundamental_crawler import FundamentalCrawler
from .llm_analyzer import LLMAnalyzer
from .report_generator import ReportGenerator

__all__ = [
    "ProcessManager",
    "KlineMonitor",
    "NewsCrawler",
    "FundamentalCrawler",
    "LLMAnalyzer",
    "ReportGenerator"
]
