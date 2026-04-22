"""RSS feed collector using feedparser and trafilatura."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import re
import time
from datetime import datetime
from html import unescape
from typing import Any

import httpx

from collectors.base import BaseCollector


_FULL_TEXT_WORKERS = 24
_FULL_TEXT_TIMEOUT = 5


class RSSCollector(BaseCollector):
    """Collect news from real RSS feeds."""

    # --- 公开直连 RSS 源（不依赖 RSShub，优先使用） ---
    # 注：中文财经 RSS 已普遍失效，中文新闻由 NewsAPICollector 覆盖
    # 已摘除长期 0 entries 的源：reuters_business / reuters_cn / wsj_markets /
    #     investing_commodities / investing_forex / investing_economy（reuters/wsj/investing 风控/区域屏蔽）
    PUBLIC_FEEDS = {
        # 国际财经主流
        "cnbc_world": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "bloomberg_markets": "https://feeds.bloomberg.com/markets/news.rss",
        "ft_home": "https://www.ft.com/?format=rss",
        "marketwatch_topstories": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "marketwatch_commodities": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
        "bbc_business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "nikkei_asia": "https://asia.nikkei.com/rss/feed/nar",
        # 大宗商品 / 能源 / 金属
        "mining_dot_com": "https://www.mining.com/feed/",
        "oilprice_main": "https://oilprice.com/rss/main",
        # 外汇 / 宏观
        "forexlive": "https://www.forexlive.com/feed/",
        "fxstreet_news": "https://www.fxstreet.com/rss/news",
    }

    # --- RSShub 源（需自部署实例，标记为 optional，Mini 可能无法访问） ---
    RSSHUB_FEEDS = {
        "cls_telegraph": "https://rsshub.app/cls/telegraph",
        "cls_depth": "https://rsshub.app/cls/depth/1000",
        "jin10": "https://rsshub.app/jin10",
        "wallstreetcn": "https://rsshub.app/wallstreetcn/news/global",
        "caixin": "https://rsshub.app/caixin/latest",
        "gelonghui": "https://rsshub.app/gelonghui/live",
        "eastmoney": "https://rsshub.app/eastmoney/report/stock",
        "reuters_commodities": "https://rsshub.app/reuters/category/commodities",
        "reuters_markets": "https://rsshub.app/reuters/category/markets",
        "ft_chinese": "https://rsshub.app/ft/chinese/hotstoryby7day",
        "yicai": "https://rsshub.app/yicai/headline",
        "zhitongcaijing": "https://rsshub.app/zhitongcaijing/recommend",
    }

    # 默认仅使用公开直连源，RSShub 作为可选 fallback
    DEFAULT_FEEDS = {**PUBLIC_FEEDS}

    def __init__(self, *, use_mock: bool = False, **kwargs: Any) -> None:
        kwargs.pop('name', None)
        super().__init__(name="rss_news", **kwargs)
        self.use_mock = use_mock

    def collect(self, *, feeds: dict[str, str] | None = None, sources: dict[str, str] | None = None, max_items: int = 500, as_of: str | None = None, try_rsshub: bool = False) -> list[dict[str, Any]]:
        """Collect RSS news.

        Strategy:
        1. Fetch from PUBLIC_FEEDS (or custom *feeds* / *sources*).
        2. If PUBLIC_FEEDS yield < *max_items* and *try_rsshub* is True,
           attempt RSSHUB_FEEDS as fallback to supplement results.
        3. If everything fails, raise and let scheduler/pipeline handle failure.

        Note: *sources* is accepted as an alias for *feeds* for backward
        compatibility with callers that pass ``sources=...``.
        """
        feed_map = feeds or sources or self.DEFAULT_FEEDS
        if self.use_mock:
            raise RuntimeError("mock data is forbidden for rss collector")
        try:
            # 公开国际源需走代理（CNBC/Reuters/Bloomberg/FT/WSJ/Investing/MarketWatch）
            from utils.proxy import overseas_proxy_env
            with overseas_proxy_env():
                records = self._fetch_live(feed_map=feed_map, max_items=max_items, as_of=as_of)
        except Exception as exc:
            self.logger.warning("rss public feed fetch failed: %s", exc)
            records = []

        # --- RSShub fallback: only try if public feeds insufficient ---
        # RSShub 走国内直连，不需要代理
        if len(records) < max_items and try_rsshub and (feeds is None):
            self.logger.info("public feeds returned %d records (< %d), trying RSShub fallback", len(records), max_items)
            try:
                rsshub_records = self._fetch_live(feed_map=self.RSSHUB_FEEDS, max_items=max_items, as_of=as_of)
                records.extend(rsshub_records)
            except Exception as exc:
                self.logger.warning("rsshub fallback also failed: %s", exc)

        if not records:
            raise RuntimeError("all rss feeds failed")
        return records

    _MAX_RETRIES = 3
    _RETRY_BASE_DELAY = 2.0  # seconds, exponential backoff

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

    @classmethod
    def _normalize_summary(cls, summary: str) -> str:
        text = str(summary or "").strip()
        if not text:
            return ""
        if "<" in text and ">" in text:
            return cls._extract_text_from_html(text)
        return re.sub(r"\s+", " ", unescape(text)).strip()

    @staticmethod
    def _build_uid(*, title: str, link: str, published: str) -> str:
        base = link or f"{title}|{published}"
        return hashlib.md5(base.encode()).hexdigest()[:12]

    def _hydrate_full_texts(self, *, client: httpx.Client, items: list[dict[str, str]]) -> list[str]:
        if not items:
            return []

        def _fetch(item: dict[str, str]) -> str:
            url = item.get("link", "")
            if not url:
                return ""
            return self._download_full_text(client=client, url=url)

        with ThreadPoolExecutor(max_workers=_FULL_TEXT_WORKERS) as executor:
            return list(executor.map(_fetch, items))

    def _download_full_text(self, *, client: httpx.Client, url: str) -> str:
        try:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
        except Exception as exc:
            self.logger.debug("rss article fetch failed for %s: %s", url, exc)
            return ""
        return self._extract_text_from_html(response.text)

    def _fetch_live(self, *, feed_map: dict[str, str], max_items: int, as_of: str | None) -> list[dict[str, Any]]:
        import feedparser
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        feed_failures: dict[str, int] = {}  # feed_name → consecutive failure count
        seen_uids: set[str] = set()
        with httpx.Client(headers={"User-Agent": "Mozilla/5.0"}, timeout=_FULL_TEXT_TIMEOUT) as client:
            for feed_name, url in feed_map.items():
                success = False
                for attempt in range(1, self._MAX_RETRIES + 1):
                    try:
                        feed = feedparser.parse(url)
                        time.sleep(0.3)
                        entries = list(feed.entries) if hasattr(feed, "entries") else []
                        if not entries and attempt < self._MAX_RETRIES:
                            delay = self._RETRY_BASE_DELAY * (2 ** (attempt - 1))
                            self.logger.info("rss %s returned 0 entries, retry %d/%d in %.1fs", feed_name, attempt, self._MAX_RETRIES, delay)
                            time.sleep(delay)
                            continue
                        prepared_items: list[dict[str, str]] = []
                        for entry in entries:
                            title = str(getattr(entry, "title", "") or "").strip()
                            link = str(getattr(entry, "link", "") or "").strip()
                            published = str(getattr(entry, "published", timestamp) or timestamp)
                            summary = self._normalize_summary(str(getattr(entry, "summary", "") or ""))

                            if not title and not link and not summary:
                                continue

                            uid = self._build_uid(title=title, link=link, published=published)
                            if uid in seen_uids:
                                continue
                            seen_uids.add(uid)
                            prepared_items.append({
                                "title": title or summary[:120],
                                "link": link,
                                "published": published,
                                "summary": summary,
                                "uid": uid,
                            })

                        full_texts = self._hydrate_full_texts(client=client, items=prepared_items)
                        for item, full_text in zip(prepared_items, full_texts):
                            content = (full_text or item["summary"]).strip()
                            if not content or content == item["title"].strip():
                                continue
                            records.append({
                                "source_type": "rss_news",
                                "symbol_or_indicator": feed_name,
                                "timestamp": item["published"],
                                "uid": item["uid"],
                                "payload": {
                                    "title": item["title"],
                                    "link": item["link"],
                                    "summary": item["summary"],
                                    "content": content,
                                    "full_text": content,
                                    "feed": feed_name,
                                    "uid": item["uid"],
                                    "mode": "live",
                                },
                            })
                        self.logger.info("rss fetched: %s entries=%d unique=%d (attempt %d)", feed_name, len(entries), len(prepared_items), attempt)
                        success = True
                        break
                    except Exception as exc:
                        if attempt < self._MAX_RETRIES:
                            delay = self._RETRY_BASE_DELAY * (2 ** (attempt - 1))
                            self.logger.warning("rss fetch failed for %s (attempt %d/%d): %s, retrying in %.1fs", feed_name, attempt, self._MAX_RETRIES, exc, delay)
                            time.sleep(delay)
                        else:
                            self.logger.warning("rss fetch failed for %s after %d attempts: %s", feed_name, self._MAX_RETRIES, exc)
                if not success:
                    feed_failures[feed_name] = feed_failures.get(feed_name, 0) + 1
        if feed_failures:
            self.logger.warning("rss feeds with all retries exhausted: %s", list(feed_failures.keys()))
        if not records:
            raise RuntimeError("all RSS feeds failed")
        return records

    def _mock_records(self, *, feed_map: dict[str, str], as_of: str | None) -> list[dict[str, Any]]:
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        return [{"source_type": "rss_news", "symbol_or_indicator": name, "timestamp": timestamp,
                 "payload": {"title": f"Mock article from {name}", "link": "", "summary": "mock", "feed": name, "uid": "mock", "mode": "mock"}}
                for name in feed_map]
