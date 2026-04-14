"""测试 — 爬虫引擎"""

import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from lxml import html as lxml_html

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.crawler.engine import CodeCrawler, BrowserCrawler, CrawlResult
from researcher.crawler.anti_detect import AntiDetect
from researcher.crawler.source_registry import SourceRegistry
from researcher.models import SourceConfig


class TestAntiDetect:
    """测试反检测工具"""

    def test_get_random_ua(self):
        """测试随机 UA"""
        anti_detect = AntiDetect()
        ua = anti_detect.get_random_ua()
        assert ua in anti_detect.USER_AGENTS
        assert len(anti_detect.USER_AGENTS) >= 20

    def test_get_random_interval(self):
        """测试随机间隔"""
        anti_detect = AntiDetect()
        base = 2.0
        interval = anti_detect.get_random_interval(base)
        assert 1.4 <= interval <= 2.6  # base ± 30%

    def test_handle_rate_limit(self):
        """测试速率限制处理"""
        anti_detect = AntiDetect()

        # 第 1 次尝试
        wait = anti_detect.handle_rate_limit(1)
        assert wait == 2

        # 第 2 次尝试
        wait = anti_detect.handle_rate_limit(2)
        assert wait == 4

        # 第 3 次尝试
        wait = anti_detect.handle_rate_limit(3)
        assert wait == 8

        # 超过最大尝试次数
        wait = anti_detect.handle_rate_limit(4, max_attempts=3)
        assert wait == -1

    def test_playwright_args(self):
        """测试 Playwright 参数"""
        anti_detect = AntiDetect()
        args = anti_detect.get_playwright_args()
        assert "--disable-blink-features=AutomationControlled" in args
        assert "--no-sandbox" in args


class TestCodeCrawler:
    """测试代码模式爬虫"""

    @pytest.mark.asyncio
    async def test_crawl_success(self):
        """测试爬取成功"""
        crawler = CodeCrawler(request_interval=0.1)

        def mock_parser(tree, url):
            return {
                "title": "测试标题",
                "content": "测试内容",
                "published_at": None
            }

        mock_response = MagicMock()
        mock_response.content = b"<html><body>test</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await crawler.crawl(
                url="https://example.com",
                source_id="test_source",
                parser_func=mock_parser,
                timeout=10
            )

            assert result.success is True
            assert result.title == "测试标题"
            assert result.content == "测试内容"
            assert result.source_id == "test_source"

    @pytest.mark.asyncio
    async def test_crawl_failure(self):
        """测试爬取失败"""
        crawler = CodeCrawler(request_interval=0.1)

        def mock_parser(tree, url):
            return {"title": "", "content": "", "published_at": None}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Network error"))

            result = await crawler.crawl(
                url="https://example.com",
                source_id="test_source",
                parser_func=mock_parser,
                timeout=10
            )

            assert result.success is False
            assert result.error == "Network error"

    @pytest.mark.asyncio
    async def test_crawl_batch(self):
        """测试批量爬取"""
        crawler = CodeCrawler(max_concurrent=2, request_interval=0.1)

        def mock_parser(tree, url):
            return {"title": f"Title for {url}", "content": "content", "published_at": None}

        mock_response = MagicMock()
        mock_response.content = b"<html><body>test</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
            results = await crawler.crawl_batch(
                urls=urls,
                source_id="test_source",
                parser_func=mock_parser,
                timeout=10
            )

            assert len(results) == 3
            assert all(r.success for r in results)


class TestSourceRegistry:
    """测试采集源注册表"""

    def test_add_and_get_source(self):
        """测试添加和获取源"""
        registry = SourceRegistry()

        config = SourceConfig(
            source_id="test_source",
            name="测试源",
            url_pattern="https://example.com",
            mode="code",
            parser="article_list",
            schedule=["盘前", "午间"],
            enabled=True,
            priority=8
        )

        registry.add_source(config)

        retrieved = registry.get_source("test_source")
        assert retrieved is not None
        assert retrieved.name == "测试源"
        assert retrieved.priority == 8

    def test_get_active_sources(self):
        """测试获取活跃源"""
        registry = SourceRegistry()

        config1 = SourceConfig(
            source_id="source1",
            name="源1",
            url_pattern="https://example.com/1",
            mode="code",
            parser="article_list",
            schedule=["盘前"],
            enabled=True,
            priority=10
        )

        config2 = SourceConfig(
            source_id="source2",
            name="源2",
            url_pattern="https://example.com/2",
            mode="code",
            parser="article_list",
            schedule=["午间"],
            enabled=True,
            priority=5
        )

        config3 = SourceConfig(
            source_id="source3",
            name="源3（禁用）",
            url_pattern="https://example.com/3",
            mode="code",
            parser="article_list",
            schedule=["盘前"],
            enabled=False,
            priority=8
        )

        registry.add_source(config1)
        registry.add_source(config2)
        registry.add_source(config3)

        # 获取所有活跃源
        active = registry.get_active_sources()
        assert len(active) == 2  # config3 被禁用

        # 按时段过滤
        morning = registry.get_active_sources(segment="盘前")
        assert len(morning) == 1
        assert morning[0].source_id == "source1"

    def test_update_source(self):
        """测试更新源"""
        registry = SourceRegistry()

        config = SourceConfig(
            source_id="test_source",
            name="测试源",
            url_pattern="https://example.com",
            mode="code",
            parser="article_list",
            schedule=["盘前"],
            enabled=True,
            priority=5
        )

        registry.add_source(config)

        # 更新优先级
        registry.update_source("test_source", {"priority": 10})

        updated = registry.get_source("test_source")
        assert updated.priority == 10

    def test_remove_source(self):
        """测试删除源"""
        registry = SourceRegistry()

        config = SourceConfig(
            source_id="test_source",
            name="测试源",
            url_pattern="https://example.com",
            mode="code",
            parser="article_list",
            schedule=["盘前"],
            enabled=True
        )

        registry.add_source(config)
        assert registry.get_source("test_source") is not None

        registry.remove_source("test_source")
        assert registry.get_source("test_source") is None
