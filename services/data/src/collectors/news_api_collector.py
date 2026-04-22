"""News API collector using public financial news endpoints (httpx async)."""

from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

import httpx

from collectors.base import BaseCollector

_DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}
_TIMEOUT = 15
_FULL_TEXT_CONCURRENCY = 8


class NewsAPICollector(BaseCollector):
    """Collect financial news from public API endpoints using httpx async."""

    DEFAULT_SOURCES = [
        "eastmoney",
        "cls",
        "sina_finance",
        "shmet",
        "stcn",
        "wallstreetcn",
    ]

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="news_api", **kwargs)
        self.use_mock = use_mock

    # --- sync entrypoint (backward compatible) ---
    def collect(self, *, sources: list[str] | None = None, keywords: list[str] | None = None, as_of: str | None = None) -> list[dict[str, Any]]:
        _ = keywords
        source_list = sources or self.DEFAULT_SOURCES
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for news_api collector")
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
            self.logger.error("news_api async fetch failed: %s", exc)
            raise

    # --- async entrypoint ---
    async def async_collect(self, *, sources: list[str] | None = None, as_of: str | None = None) -> list[dict[str, Any]]:
        source_list = sources or self.DEFAULT_SOURCES
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for news_api collector")
        return await self._async_fetch_all(source_list=source_list, as_of=as_of)

    async def _async_fetch_all(self, *, source_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        fetchers = {
            "eastmoney": self._async_fetch_eastmoney,
            "cls": self._async_fetch_cls,
            "sina_finance": self._async_fetch_sina,
            "shmet": self._async_fetch_shmet_news,
            "stcn": self._async_fetch_stcn,
            "wallstreetcn": self._async_fetch_wallstreetcn,
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
                enriched_items = await self._hydrate_full_content(client=client, items=result)
                for item in enriched_items:
                    uid = hashlib.md5(item.get("title", "").encode()).hexdigest()[:12]
                    records.append({
                        "source_type": "news_api",
                        "symbol_or_indicator": src,
                        "timestamp": item.get("time", timestamp),
                        "uid": uid,
                        "payload": item | {"source": src, "uid": uid, "mode": "live"},
                    })
                self.logger.info("news_api fetched: %s items=%d", src, len(result))
        if not records:
            raise RuntimeError("all news_api sources failed")
        return records

    async def _hydrate_full_content(self, *, client: httpx.AsyncClient, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(_FULL_TEXT_CONCURRENCY)

        async def _enrich(item: dict[str, Any]) -> dict[str, Any]:
            enriched = dict(item)
            summary = str(enriched.get("summary") or enriched.get("content") or "")
            content = str(enriched.get("content") or summary)
            url = str(enriched.get("url") or "").strip()

            if url:
                async with semaphore:
                    full_text = await self._download_full_text(client=client, url=url)
                if full_text:
                    enriched["content"] = full_text
                    enriched["full_text"] = full_text
                else:
                    enriched["content"] = content
            else:
                enriched["content"] = content

            enriched["summary"] = summary
            return enriched

        return list(await asyncio.gather(*(_enrich(item) for item in items)))

    async def _download_full_text(self, *, client: httpx.AsyncClient, url: str) -> str:
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
        except Exception as exc:
            self.logger.debug("news_api full-text fetch failed for %s: %s", url, exc)
            return ""
        return await asyncio.to_thread(self._extract_text_from_html, response.text)

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        try:
            from trafilatura import extract

            extracted = extract(
                html,
                include_comments=False,
                include_tables=False,
                favor_recall=True,
                deduplicate=False,
            )
            if extracted:
                return extracted.strip()
        except Exception:
            pass

        cleaned = re.sub(r"<script.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    async def _async_fetch_eastmoney(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """东方财富财经导读（直连 np-listapi，避免 akshare 内部 regex 错误）."""
        url = " 7×24 财经快讯（直连 newsapi.eastmoney.com，避免 akshare 内部 regex 错误）."""
        url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://kuaixun.eastmoney.com/",
        }
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        text = resp.text
        # JSONP 形式：var ajaxResult={...}
        import json as _json
        prefix = "var ajaxResult="
        if text.startswith(prefix):
            text = text[len(prefix):].rstrip("; \n\r\t")
        try:
            data = _json.loads(text)
        except Exception:
            return []
        items = []
        rows = data.get("LivesList") or []
        for n in rows:
            sort = str(n.get("sort", ""))
            time_str = ""
            if sort and len(sort) >= 13:
                # sort like 1776869648080559（毫秒+序号），取前13位毫秒
                try:
                    ms = int(sort[:13])
                    time_str = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
                except Exception:
                    time_str = sort
            items.append({
                "title": n.get("title", "") or n.get("simtitle", ""),
                "time": time_str,
                "url": n.get("url_w", "") or n.get("url_unique", ""),
                "summary": n.get("digest", "") or n.get("simdigest", ""),
                "content": n.get("digest", "") or n.get("simdigest", ""),
            })
        return items

    @staticmethod
    async def _async_fetch_wallstreetcn(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """华尔街见闻全球快讯."""
        url = "https://api-one-wscn.awtmt.com/apiv1/content/lives"
        params = {"channel": "global-channel", "limit": 100}
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://wallstreetcn.com",
            "Referer": "https://wallstreetcn.com/",
        }
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        items = []
        rows = (data.get("data") or {}).get("items") or []
        for n in rows:
            ts = n.get("display_time") or n.get("created_at") or 0
            try:
                ts_iso = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else ""
            except Exception:
                ts_iso = str(ts)
            items.append({
                "title": n.get("title", "") or (n.get("content_text", "")[:80]),
                "time": ts_iso,
                "url": n.get("uri", "") or f"https://wallstreetcn.com/livenews/{n.get('id','')}",
                "summary": n.get("content_text", "") or "",
                "content": n.get("content_text", "") or n.get("content", ""),
            })
        return items

    @staticmethod
    async def _async_fetch_cls(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        url = "https://www.cls.cn/nodeapi/updateTelegraphList"
        params = {"app": "CailianpressWeb", "os": "web", "sv": "8.4.6", "rn": 200}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = []
        roll_data = data.get("data", {}).get("roll_data", []) if isinstance(data.get("data"), dict) else []
        for n in roll_data:
            article_id = n.get("id", "")
            items.append({
                "title": n.get("title", "") or n.get("brief", ""),
                "time": str(n.get("ctime", "")),
                "url": f"https://www.cls.cn/detail/{article_id}" if article_id else "",
                "content": n.get("content", ""),
                "summary": n.get("brief", "") or n.get("title", ""),
            })
        return items

    @staticmethod
    async def _async_fetch_sina(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {"pageid": 153, "lid": 2516, "k": "", "num": 100, "page": 1}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = []
        result_data = data.get("result", {}).get("data", []) if isinstance(data.get("result"), dict) else []
        for n in result_data:
            items.append({
                "title": n.get("title", ""),
                "time": n.get("ctime", ""),
                "url": n.get("url", ""),
                "content": n.get("intro", ""),
                "summary": n.get("intro", ""),
            })
        return items

    @staticmethod
    async def _async_fetch_shmet_news(_client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """上海金属网快讯 via AkShare (sync internally)."""
        import akshare as ak
        df = ak.futures_news_shmet(symbol="全部")
        items = []
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                items.append({
                    "title": str(row.get("title", row.get("标题", ""))),
                    "time": str(row.get("time", row.get("发布时间", ""))),
                    "content": str(row.get("content", row.get("内容", ""))),
                    "url": str(row.get("url", row.get("链接", ""))),
                })
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
        for link, title in matches:
            items.append({"title": title.strip(), "url": link, "summary": title.strip(), "content": title.strip()})
        return items

    def _mock_records(self, *, source_list: list[str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return [{"source_type": "news_api", "symbol_or_indicator": src, "timestamp": timestamp,
                 "payload": {"title": f"Mock news from {src}", "content": "mock", "source": src, "uid": "mock", "mode": "mock"}}
                for src in source_list]
