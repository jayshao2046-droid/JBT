"""测试去重管理器"""
import pytest
from researcher.deduplication import DeduplicationManager
import tempfile
import os


def test_news_deduplication():
    """测试新闻去重"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_dedup.db")
        manager = DeduplicationManager(db_path)

        url = "https://example.com/news/1"
        title = "测试新闻"
        source = "测试源"

        # 第一次应该返回 False
        assert not manager.is_news_seen(url)

        # 标记为已处理
        manager.mark_news_seen(url, title, source)

        # 第二次应该返回 True
        assert manager.is_news_seen(url)


def test_kline_deduplication():
    """测试 K 线去重"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_dedup.db")
        manager = DeduplicationManager(db_path)

        symbol = "RB"
        timestamp = "2026-04-16T10:00:00"

        # 第一次应该返回 False
        assert not manager.is_kline_analyzed(symbol, timestamp)

        # 标记为已分析
        manager.mark_kline_analyzed(symbol, timestamp)

        # 第二次应该返回 True
        assert manager.is_kline_analyzed(symbol, timestamp)
