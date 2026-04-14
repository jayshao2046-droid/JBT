"""国际采集源解析器 — 7 个国际期货/宏观资讯源"""

from typing import Dict, Any
from datetime import datetime
from lxml import html as lxml_html


def parse_cme_advisory(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """CME Group 公告解析器"""
    try:
        # 尝试多种选择器
        title_elem = tree.xpath("//div[@class='advisory-list']//h2/text() | //table[@class='advisory-table']//td[1]/text()")
        title = title_elem[0].strip() if title_elem else "CME 公告"

        content_elem = tree.xpath("//div[@class='advisory-content']//text() | //table[@class='advisory-table']//td[2]/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "CME 公告内容", "published_at": None}
    except Exception:
        return {"title": "CME 公告解析失败", "content": "", "published_at": None}


def parse_kitco_gold(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """Kitco 贵金属新闻解析器"""
    try:
        title_elem = tree.xpath("//div[@class='article-list']//h2/a/text() | //article//h2/text()")
        title = title_elem[0].strip() if title_elem else "Kitco 贵金属新闻"

        content_elem = tree.xpath("//div[@class='article-content']//p/text() | //article//p/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "Kitco 新闻内容", "published_at": None}
    except Exception:
        return {"title": "Kitco 解析失败", "content": "", "published_at": None}


def parse_oilprice_com(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """OilPrice 能源资讯解析器"""
    try:
        title_elem = tree.xpath("//div[@class='categoryArticle']//h2/text() | //article//h2/a/text()")
        title = title_elem[0].strip() if title_elem else "OilPrice 能源资讯"

        content_elem = tree.xpath("//div[@class='categoryArticle']//p/text() | //article//p/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "OilPrice 新闻内容", "published_at": None}
    except Exception:
        return {"title": "OilPrice 解析失败", "content": "", "published_at": None}


def parse_mining_com(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """Mining.com 矿业新闻解析器"""
    try:
        title_elem = tree.xpath("//article[@class='post']//h2[@class='entry-title']/a/text() | //article//h2/text()")
        title = title_elem[0].strip() if title_elem else "Mining 矿业新闻"

        content_elem = tree.xpath("//article//div[@class='entry-content']//p/text() | //article//p/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "Mining 新闻内容", "published_at": None}
    except Exception:
        return {"title": "Mining 解析失败", "content": "", "published_at": None}


def parse_investing_commodities(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """Investing.com 大宗商品解析器"""
    try:
        title_elem = tree.xpath("//article[@data-test='article-item']//a/text() | //article//h3/text()")
        title = title_elem[0].strip() if title_elem else "Investing 大宗商品新闻"

        content_elem = tree.xpath("//article[@data-test='article-item']//p/text() | //article//p/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "Investing 新闻内容", "published_at": None}
    except Exception:
        return {"title": "Investing 解析失败", "content": "", "published_at": None}


def parse_fed_releases(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """美联储公告解析器"""
    try:
        title_elem = tree.xpath("//div[@class='row']//a[@class='ng-binding']/text() | //div[@class='row']//a/text()")
        title = title_elem[0].strip() if title_elem else "美联储公告"

        content_elem = tree.xpath("//div[@class='row']//p/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "美联储公告内容", "published_at": None}
    except Exception:
        return {"title": "美联储解析失败", "content": "", "published_at": None}


def parse_reuters_commodities(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """路透社大宗商品解析器（反爬较强，降级处理）"""
    try:
        title_elem = tree.xpath("//article//h3/text() | //h2/a/text()")
        title = title_elem[0].strip() if title_elem else "路透社大宗商品新闻"

        content_elem = tree.xpath("//article//p/text()")
        content = " ".join([c.strip() for c in content_elem if c.strip()])[:500]

        return {"title": title, "content": content or "路透社新闻内容", "published_at": None}
    except Exception:
        return {"title": "路透社解析失败", "content": "", "published_at": None}
