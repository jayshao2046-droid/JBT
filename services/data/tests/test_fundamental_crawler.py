"""测试基本面爬虫"""
import pytest
from researcher.fundamental_crawler import FundamentalCrawler
import multiprocessing as mp


def test_fundamental_crawler_sources():
    """测试基本面数据源配置"""
    queue = mp.Queue()
    stop_event = mp.Event()

    crawler = FundamentalCrawler(queue, stop_event)

    # 验证数据源数量
    assert len(crawler.sources) >= 3

    # 验证数据源结构
    for source in crawler.sources:
        assert "name" in source
        assert "url" in source
        assert "interval" in source
        assert "type" in source
