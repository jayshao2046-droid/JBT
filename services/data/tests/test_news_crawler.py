"""测试新闻爬虫"""
import pytest
from researcher.news_crawler import NewsCrawler
import multiprocessing as mp


def test_news_crawler_sources():
    """测试新闻源配置"""
    queue = mp.Queue()
    stop_event = mp.Event()

    crawler = NewsCrawler(queue, stop_event)

    # 验证新闻源数量
    assert len(crawler.sources) >= 3

    # 验证新闻源结构
    for source in crawler.sources:
        assert "name" in source
        assert "url" in source
        assert "interval" in source


def test_is_futures_related():
    """测试期货相关判断"""
    queue = mp.Queue()
    stop_event = mp.Event()

    crawler = NewsCrawler(queue, stop_event)

    # 测试正面案例
    assert crawler._is_futures_related("螺纹钢期货大涨")
    assert crawler._is_futures_related("铜价上涨")
    assert crawler._is_futures_related("股指期货IF")

    # 测试负面案例
    assert not crawler._is_futures_related("今天天气不错")
