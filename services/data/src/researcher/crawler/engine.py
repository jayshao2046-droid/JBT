"""双模式爬虫引擎 — 代码模式(httpx) + 浏览器模式(Playwright)"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import httpx
from lxml import html as lxml_html

from .anti_detect import AntiDetect


@dataclass
class CrawlResult:
    """爬取结果"""
    url: str
    title: str
    content: str
    published_at: Optional[datetime]
    source_id: str
    success: bool = True
    error: Optional[str] = None


class CodeCrawler:
    """代码模式爬虫 — httpx + lxml"""

    def __init__(self, max_concurrent: int = 5, request_interval: float = 2.0):
        self.max_concurrent = max_concurrent
        self.request_interval = request_interval
        self.anti_detect = AntiDetect()

    async def crawl(self, url: str, source_id: str, parser_func, timeout: int = 30) -> CrawlResult:
        """
        爬取单个 URL

        Args:
            url: 目标 URL
            source_id: 采集源 ID
            parser_func: 解析函数
            timeout: 超时秒数

        Returns:
            CrawlResult
        """
        try:
            # 反检测：UA 轮换 + 请求间隔
            headers = {"User-Agent": self.anti_detect.get_random_ua()}
            await asyncio.sleep(self.anti_detect.get_random_interval(self.request_interval))

            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                resp.raise_for_status()

                # 解析内容
                tree = lxml_html.fromstring(resp.content)
                parsed = parser_func(tree, url)

                return CrawlResult(
                    url=url,
                    title=parsed.get("title", ""),
                    content=parsed.get("content", ""),
                    published_at=parsed.get("published_at"),
                    source_id=source_id,
                    success=True
                )

        except Exception as e:
            return CrawlResult(
                url=url,
                title="",
                content="",
                published_at=None,
                source_id=source_id,
                success=False,
                error=str(e)
            )

    async def crawl_batch(
        self,
        urls: List[str],
        source_id: str,
        parser_func,
        timeout: int = 30
    ) -> List[CrawlResult]:
        """批量爬取（并发控制）"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self.crawl(url, source_id, parser_func, timeout)

        tasks = [crawl_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)


class BrowserCrawler:
    """浏览器模式爬虫 — Playwright headless Chromium"""

    def __init__(self, max_concurrent: int = 2, request_interval: float = 5.0):
        self.max_concurrent = max_concurrent
        self.request_interval = request_interval
        self.anti_detect = AntiDetect()
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=self.anti_detect.get_playwright_args()
                )
            except ImportError:
                raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

    async def crawl(self, url: str, source_id: str, parser_func, timeout: int = 30) -> CrawlResult:
        """
        爬取单个 URL（浏览器模式）

        Args:
            url: 目标 URL
            source_id: 采集源 ID
            parser_func: 解析函数（接收 page 对象）
            timeout: 超时秒数

        Returns:
            CrawlResult
        """
        try:
            await self._ensure_browser()

            # 反检测：请求间隔
            await asyncio.sleep(self.anti_detect.get_random_interval(self.request_interval))

            page = await self._browser.new_page(
                user_agent=self.anti_detect.get_random_ua()
            )

            try:
                await page.goto(url, timeout=timeout * 1000, wait_until="networkidle")

                # 解析内容
                parsed = await parser_func(page, url)

                return CrawlResult(
                    url=url,
                    title=parsed.get("title", ""),
                    content=parsed.get("content", ""),
                    published_at=parsed.get("published_at"),
                    source_id=source_id,
                    success=True
                )

            finally:
                await page.close()

        except Exception as e:
            return CrawlResult(
                url=url,
                title="",
                content="",
                published_at=None,
                source_id=source_id,
                success=False,
                error=str(e)
            )

    async def crawl_batch(
        self,
        urls: List[str],
        source_id: str,
        parser_func,
        timeout: int = 30
    ) -> List[CrawlResult]:
        """批量爬取（并发控制）"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self.crawl(url, source_id, parser_func, timeout)

        tasks = [crawl_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def close(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
