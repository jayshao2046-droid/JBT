"""News API collector using public financial news endpoints (httpx async)."""

from __future__ import annotations

import asyncio
import hashlib
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from services.data.src.collectors.base import BaseCollector

_DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}
_TIMEOUT = 15


class NewsAPICollector(BaseCollector):
    """Collect financial news from public API endpoints using httpx async."""

    DEFAULT_SOURCES = ["eastmoney", "cls", "sina_finance", "shmet", "jin10", "stcn"]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="news_api", **kwargs)
        self.use_mock = use_mock

    # --- sync entrypoint (backward compatible) ---
    def collect(self, *, sources: list[str] | None = None, keywords: list[str] | None = None, as_of: str | None = None) -> list[dict[str, Any]]:
        _ = keywords
        source_list = sources or self.DEFAULT_SOURCES
        if self.use_mock:
            return self._mock_records(source_list=source_list, as_of=as_of)
        try:
            return asyncio.get_event_loop().run_until_complete(
                self._async_fetch_all(source_list=source_list, as_of=as_of)
            )
        except RuntimeError:
            # Already inside an event loop — fall back to new loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self._async_fetch_all(source_list=source_list, as_of=as_of)
                )
            finally:
                loop.close()
        except Exception as exc:
            self.logger.warning("news_api async fetch failed: %s, falling back to mock", exc)
            return self._mock_records(source_list=source_list, as_of=as_of)

    # --- async entrypoint ---
    async def async_collect(self, *, sources: list[str] | None = None, as_of: str | None = None) -> list[dict[str, Any]]:
        source_list = sources or self.DEFAULT_SOURCES
        if self.use_mock:
            return self._mock_records(source_list=source_list, as_of=as_of)
        return await self._async_fetch_all(source_list=source_list, as_of=as_of)

    async def _async_fetch_all(self, *, source_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        fetchers = {
            "eastmoney": self._async_fetch_eastmoney,
            "cls": self._async_fetch_cls,
            "sina_finance": self._async_fetch_sina,
            "shmet": self._async_fetch_shmet_news,
            "jin10": self._async_fetch_jin10,
            "stcn": self._async_fetch_stcn,
        }
        records: list[dict[str, Any]] = []
        async with httpx.AsyncClient(headers=_DEFAULT_HEADERS, timeout=_TIMEOUT) as client:
            tasks = []
            task_sources = []
            for src in source_list:
                fn = fetchers.get(src)
                if fn:
                    tasks.append(fn(client))
                    task_sources.append(src)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for src, result in zip(task_sources, results):
                if isinstance(result, Exception):
                    self.logger.warning("news_api async fetch failed for %s: %s", src, result)
                    continue
                for item in result:
                    uid = hashlib.md5(item.get("title", "").encode()).hexdigest()[:12]
                    records.append({
                        "source_type": "news_api",
                        "symbol_or_indicator": src,
                        "timestamp": item.get("time", timestamp),
                        "payload": item | {"source": src, "uid": uid, "mode": "live"},
                    })
                self.logger.info("news_api fetched: %s items=%d", src, len(result))
        if not records:
            raise RuntimeError("all news_api sources failed")
        return records

    @staticmethod
    async def _async_fetch_eastmoney(_client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """东方财富新闻 via AkShare (sync internally)."""
        import akshare as ak
        df = ak.stock_news_em(symbol="000001")
        items = []
        if df is not None and not df.empty:
            for _, row in df.head(50).iterrows():
                items.append({
                    "title": str(row.get("新闻标题", row.get("title", ""))),
                    "time": str(row.get("发布时间", row.get("time", ""))),
                    "url": str(row.get("新闻链接", row.get("url", ""))),
                    "content": str(row.get("新闻内容", row.get("content", "")))[:300],
                })
        return items

    @staticmethod
    async def _async_fetch_cls(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        url = "https://www.cls.cn/nodeapi/updateTelegraphList"
        params = {"app": "CailianpressWeb", "os": "web", "sv": "8.4.6", "rn": 50}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = []
        roll_data = data.get("data", {}).get("roll_data", []) if isinstance(data.get("data"), dict) else []
        for n in roll_data[:50]:
            items.append({"title": n.get("title", "") or n.get("brief", ""), "time": str(n.get("ctime", "")), "content": n.get("content", "")[:300]})
        return items

    @staticmethod
    async def _async_fetch_sina(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {"pageid": 153, "lid": 2516, "k": "", "num": 50, "page": 1}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = []
        result_data = data.get("result", {}).get("data", []) if isinstance(data.get("result"), dict) else []
        for n in result_data:
            items.append({"title": n.get("title", ""), "time": n.get("ctime", ""), "url": n.get("url", ""), "content": n.get("intro", "")[:300]})
        return items

    @staticmethod
    async def _async_fetch_shmet_news(_client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """上海金属网快讯 via AkShare (sync internally)."""
        import akshare as ak
        df = ak.futures_news_shmet(symbol="全部")
        items = []
        if df is not None and not df.empty:
            for _, row in df.head(50).iterrows():
                items.append({
                    "title": str(row.get("title", row.get("标题", ""))),
                    "time": str(row.get("time", row.get("发布时间", ""))),
                    "content": str(row.get("content", row.get("内容", "")))[:300],
                    "url": str(row.get("url", row.get("链接", ""))),
                })
        return items

    @staticmethod
    async def _async_fetch_jin10(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """东方财富财经频道快讯 (替代已封锁的金十 API)."""
        import re
        url = "https://finance.eastmoney.com/a/czqyw.html"
        resp = await client.get(url)
        resp.raise_for_status()
        items = []
        pattern = re.compile(
            r'<a[^>]*href="(https?://finance\.eastmoney\.com/a/\d+\.html)"[^>]*>([^<]+)</a>'
        )
        matches = pattern.findall(resp.text)
        for link, title in matches[:50]:
            title = title.strip()
            if title:
                items.append({"title": title, "url": link, "content": title[:300]})
        return items

    @staticmethod
    async def _async_fetch_stcn(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """证券时报快讯."""
        import re
        url = "https://kuaixun.stcn.com/index.html"
        resp = await client.get(url)
        resp.raise_for_status()
        items = []
        pattern = re.compile(r'<a[^>]*href="(https?://kuaixun\.stcn\.com/[^"]+)"[^>]*>([^<]+)</a>')
        matches = pattern.findall(resp.text)
        for link, title in matches[:50]:
            items.append({"title": title.strip(), "url": link, "content": title.strip()[:300]})
        return items

    def _mock_records(self, *, source_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return [{"source_type": "news_api", "symbol_or_indicator": src, "timestamp": timestamp,
                 "payload": {"title": f"Mock news from {src}", "content": "mock", "source": src, "uid": "mock", "mode": "mock"}}
                for src in source_list]
