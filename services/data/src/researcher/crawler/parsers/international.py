"""国际采集源解析器（多文章提取版） — CME/Kitco/OilPrice/Mining/Investing/Fed/Reuters

每个解析器返回 Dict 格式：
{
    "title": "源名称",
    "content": "",
    "published_at": None,
    "articles": [{"title": ..., "content": ..., "url": ..., "published_at": ...}, ...]
}
"""

from typing import Dict, Any
from datetime import datetime
from lxml import html as lxml_html
import logging

logger = logging.getLogger(__name__)


def parse_cme_advisory(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """CME Group 公告 — 多公告提取"""
    articles = []
    try:
        # 表格型公告列表
        rows = tree.xpath(
            "//table[contains(@class,'advisory')]//tr | "
            "//div[@class='advisory-list']//div[contains(@class,'item')]"
        )
        for row in rows[:10]:
            title = row.text_content().strip()[:200]
            href_el = row.xpath(".//a/@href")
            href = href_el[0] if href_el else ""
            if href and not href.startswith("http"):
                href = "https://www.cmegroup.com" + href
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
        if not articles:
            title_elem = tree.xpath("//h1//text() | //h2//text()")
            title = title_elem[0].strip() if title_elem else "CME 公告"
            content = " ".join(tree.xpath("//div[contains(@class,'content')]//p//text()"))[:500]
            articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception as exc:
        logger.debug("parse_cme_advisory 解析异常: %s", exc)
    return {"title": "CME Group", "content": "", "published_at": None, "articles": articles}


def parse_kitco_gold(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """Kitco 贵金属新闻 — 多文章提取"""
    articles = []
    try:
        # 优先匹配 /news/article/ 路径（最精准）
        items = tree.xpath("//a[contains(@href,'/news/article/')]")
        # 备用：匹配任何含实质内容的 /news/ 链接
        if not items:
            items = tree.xpath("//a[contains(@href,'/news/') and string-length(normalize-space(.)) > 15]")
        seen = set()
        for item in items:
            title = item.text_content().strip()
            href = item.get("href", "")
            if not title or len(title) < 10 or title in seen:
                continue
            seen.add(title)
            if href and not href.startswith("http"):
                href = "https://www.kitco.com" + href
            articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
            if len(articles) >= 15:
                break
    except Exception as exc:
        logger.debug("parse_kitco_gold 解析异常: %s", exc)
    return {"title": "Kitco Gold", "content": "", "published_at": None, "articles": articles}


def parse_oilprice_com(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """OilPrice 能源资讯 — 多文章提取"""
    articles = []
    try:
        items = tree.xpath(
            "//div[contains(@class,'categoryArticle')] | "
            "//article | "
            "//div[contains(@class,'article-item')]"
        )
        for item in items[:15]:
            a_tags = item.xpath(".//h2//a | .//h3//a | .//a[.//h2 or .//h3]")
            if not a_tags:
                a_tags = item.xpath(".//a")
            if not a_tags:
                continue
            title = a_tags[0].text_content().strip()
            href = a_tags[0].get("href", "")
            if href and not href.startswith("http"):
                href = "https://oilprice.com" + href
            snippet = " ".join(item.xpath(".//p//text()"))[:300]
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": snippet or title, "url": href or url, "published_at": None})
        if not articles:
            title = "".join(tree.xpath("//h1//text()")).strip() or "OilPrice"
            content = " ".join(tree.xpath("//p//text()"))[:500]
            articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception as exc:
        logger.debug("parse_oilprice_com 解析异常: %s", exc)
    return {"title": "OilPrice", "content": "", "published_at": None, "articles": articles}


def parse_mining_com(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """Mining.com 矿业新闻 — 多文章提取"""
    articles = []
    try:
        items = tree.xpath("//article | //div[contains(@class,'post')]")
        for item in items[:15]:
            a_tags = item.xpath(".//h2//a | .//h3//a")
            if not a_tags:
                continue
            title = a_tags[0].text_content().strip()
            href = a_tags[0].get("href", "")
            snippet = " ".join(item.xpath(".//p//text()"))[:300]
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": snippet or title, "url": href or url, "published_at": None})
        if not articles:
            title = "".join(tree.xpath("//h1//text()")).strip() or "Mining.com"
            content = " ".join(tree.xpath("//p//text()"))[:500]
            articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception as exc:
        logger.debug("parse_mining_com 解析异常: %s", exc)
    return {"title": "Mining.com", "content": "", "published_at": None, "articles": articles}


def parse_investing_commodities(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """Investing.com 大宗商品 — 多文章提取"""
    articles = []
    try:
        items = tree.xpath(
            "//article[@data-test='article-item'] | "
            "//article | "
            "//div[contains(@class,'articleItem')]"
        )
        for item in items[:15]:
            a_tags = item.xpath(".//a[.//h3 or .//h2 or contains(@class,'title')]")
            if not a_tags:
                a_tags = item.xpath(".//a")
            if not a_tags:
                continue
            title = a_tags[0].text_content().strip()
            href = a_tags[0].get("href", "")
            if href and not href.startswith("http"):
                href = "https://www.investing.com" + href
            snippet = " ".join(item.xpath(".//p//text()"))[:300]
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": snippet or title, "url": href or url, "published_at": None})
        if not articles:
            title = "".join(tree.xpath("//h1//text()")).strip() or "Investing Commodities"
            content = " ".join(tree.xpath("//p//text()"))[:500]
            articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception as exc:
        logger.debug("parse_investing_commodities 解析异常: %s", exc)
    return {"title": "Investing Commodities", "content": "", "published_at": None, "articles": articles}


def parse_fed_releases(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """美联储公告 — 多公告提取"""
    articles = []
    try:
        items = tree.xpath(
            "//div[@class='row']//a[@class='ng-binding'] | "
            "//div[contains(@class,'row')]//a | "
            "//div[contains(@class,'fomc')]//a"
        )
        for item in items[:10]:
            title = item.text_content().strip()
            href = item.get("href", "")
            if href and not href.startswith("http"):
                href = "https://www.federalreserve.gov" + href
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
        if not articles:
            title = "".join(tree.xpath("//h1//text()")).strip() or "Fed Release"
            content = " ".join(tree.xpath("//p//text()"))[:500]
            articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception as exc:
        logger.debug("parse_fed_releases 解析异常: %s", exc)
    return {"title": "Fed Releases", "content": "", "published_at": None, "articles": articles}


def parse_reuters_commodities(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """路透社大宗商品 — 多文章提取"""
    articles = []
    try:
        items = tree.xpath("//article | //div[contains(@class,'story-card')]")
        for item in items[:15]:
            a_tags = item.xpath(".//h3//a | .//h2//a | .//a[.//h3]")
            if not a_tags:
                a_tags = item.xpath(".//a")
            if not a_tags:
                continue
            title = a_tags[0].text_content().strip()
            href = a_tags[0].get("href", "")
            if href and not href.startswith("http"):
                href = "https://www.reuters.com" + href
            snippet = " ".join(item.xpath(".//p//text()"))[:300]
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": snippet or title, "url": href or url, "published_at": None})
        if not articles:
            title = "".join(tree.xpath("//h1//text()")).strip() or "Reuters Commodities"
            content = " ".join(tree.xpath("//p//text()"))[:500]
            articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception as exc:
        logger.debug("parse_reuters_commodities 解析异常: %s", exc)
    return {"title": "Reuters Commodities", "content": "", "published_at": None, "articles": articles}
