"""RSS feed collector using feedparser and trafilatura."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Any

from src.collectors.base import BaseCollector


class RSSCollector(BaseCollector):
    """Collect news from real RSS feeds."""

    # --- 公开直连 RSS 源（不依赖 RSShub，优先使用） ---
    # 注：中文财经 RSS 已普遍失效，中文新闻由 NewsAPICollector 覆盖
    PUBLIC_FEEDS = {
        # 国际财经 & 大宗商品
        "cnbc_world": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "cnbc_commodities": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "reuters_business": "https://feeds.reuters.com/reuters/businessNews",
        "reuters_cn": "https://cn.reuters.com/rssfeed/CNTopGenNews",
        "bloomberg_markets": "https://feeds.bloomberg.com/markets/news.rss",
        "ft_home": "https://www.ft.com/?format=rss",
        "wsj_markets": "https://feeds.a.wsj.com/rss/RSSMarketsMain.xml",
        "investing_commodities": "https://www.investing.com/rss/news_14.rss",
        "investing_forex": "https://www.investing.com/rss/news_1.rss",
        "investing_economy": "https://www.investing.com/rss/news_2.rss",
        "marketwatch_topstories": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "marketwatch_commodities": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
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

    def collect(self, *, feeds: dict[str, str] | None = None, sources: dict[str, str] | None = None, max_items: int = 50, as_of: str | None = None, try_rsshub: bool = True) -> list[dict[str, Any]]:
        """Collect RSS news.

        Strategy:
        1. Fetch from PUBLIC_FEEDS (or custom *feeds* / *sources*).
        2. If PUBLIC_FEEDS yield < *max_items* and *try_rsshub* is True,
           attempt RSSHUB_FEEDS as fallback to supplement results.
        3. If everything fails, return mock records.

        Note: *sources* is accepted as an alias for *feeds* for backward
        compatibility with callers that pass ``sources=...``.
        """
        feed_map = feeds or sources or self.DEFAULT_FEEDS
        if self.use_mock:
            return self._mock_records(feed_map=feed_map, as_of=as_of)
        try:
            # 公开国际源需走代理（CNBC/Reuters/Bloomberg/FT/WSJ/Investing/MarketWatch）
            from src.utils.proxy import overseas_proxy_env
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
            self.logger.warning("all feeds failed, falling back to mock")
            return self._mock_records(feed_map=feed_map, as_of=as_of)
        return records

    _MAX_RETRIES = 3
    _RETRY_BASE_DELAY = 2.0  # seconds, exponential backoff

    def _fetch_live(self, *, feed_map: dict[str, str], max_items: int, as_of: str | None) -> list[dict[str, Any]]:
        import feedparser
        try:
            from trafilatura import fetch_url, extract
            import ssl as _ssl_mod
            # LibreSSL 与 urllib3 v2 不兼容，SSL握手挂起，禁用全文抓取
            _has_trafilatura = "LibreSSL" not in _ssl_mod.OPENSSL_VERSION
        except ImportError:
            _has_trafilatura = False
        records: list[dict[str, Any]] = []
        timestamp = as_of or datetime.utcnow().replace(microsecond=0).isoformat()
        feed_failures: dict[str, int] = {}  # feed_name → consecutive failure count
        for feed_name, url in feed_map.items():
            success = False
            for attempt in range(1, self._MAX_RETRIES + 1):
                try:
                    feed = feedparser.parse(url)
                    time.sleep(0.3)
                    entries = feed.entries[:max_items] if hasattr(feed, "entries") else []
                    if not entries and attempt < self._MAX_RETRIES:
                        delay = self._RETRY_BASE_DELAY * (2 ** (attempt - 1))
                        self.logger.info("rss %s returned 0 entries, retry %d/%d in %.1fs", feed_name, attempt, self._MAX_RETRIES, delay)
                        time.sleep(delay)
                        continue
                    for entry in entries:
                        title = getattr(entry, "title", "")
                        link = getattr(entry, "link", "")
                        published = getattr(entry, "published", timestamp)
                        summary = getattr(entry, "summary", "")[:500]

                        # trafilatura 正文提取：仅在 summary 过短时才抓取全文
                        full_text = ""
                        if _has_trafilatura and link and len(summary) < 100:
                            try:
                                downloaded = fetch_url(link)
                                if downloaded:
                                    extracted = extract(downloaded, include_comments=False, include_tables=False)
                                    full_text = (extracted or "")[:1000]
                            except Exception:
                                pass  # trafilatura 失败不阻塞采集

                        uid = hashlib.md5((link or title).encode()).hexdigest()[:12]
                        records.append({
                            "source_type": "rss_news",
                            "symbol_or_indicator": feed_name,
                            "timestamp": published,
                            "payload": {
                                "title": title,
                                "link": link,
                                "summary": summary,
                                "full_text": full_text,
                                "feed": feed_name,
                                "uid": uid,
                                "mode": "live",
                            },
                        })
                    self.logger.info("rss fetched: %s entries=%d (attempt %d)", feed_name, len(entries), attempt)
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
