"""测试多进程系统"""
import pytest
import multiprocessing as mp
import time


def test_process_manager_init():
    """测试进程管理器初始化"""
    from researcher.process_manager import ProcessManager

    manager = ProcessManager()
    assert manager is not None
    assert manager.processes == {}


def test_shared_queue():
    """测试共享队列"""
    queue = mp.Queue(maxsize=10)

    # 测试放入和取出
    queue.put({"type": "test", "data": "hello"})
    item = queue.get(timeout=1)

    assert item["type"] == "test"
    assert item["data"] == "hello"


def test_kline_monitor_init():
    """测试 K 线监控器初始化"""
    from researcher.kline_monitor import KlineMonitor

    queue = mp.Queue()
    stop_event = mp.Event()

    monitor = KlineMonitor(queue, stop_event)
    assert monitor is not None
    assert len(monitor.symbols) == 35


def test_news_crawler_init():
    """测试新闻爬虫初始化"""
    from researcher.news_crawler import NewsCrawler

    queue = mp.Queue()
    stop_event = mp.Event()

    crawler = NewsCrawler(queue, stop_event)
    assert crawler is not None
    assert len(crawler.sources) > 0


def test_llm_analyzer_init():
    """测试 LLM 分析器初始化"""
    from researcher.llm_analyzer import LLMAnalyzer

    queue = mp.Queue()
    stop_event = mp.Event()

    analyzer = LLMAnalyzer(queue, stop_event)
    assert analyzer is not None
    assert analyzer.model == "qwen3:14b"


def test_report_generator_init():
    """测试报告生成器初始化"""
    from researcher.report_generator import ReportGenerator

    stop_event = mp.Event()

    generator = ReportGenerator(stop_event)
    assert generator is not None
    assert len(generator.schedules) == 4
