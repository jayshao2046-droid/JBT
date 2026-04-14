"""通用解析器 — article_list / rss / json_api"""

from typing import Dict, Any, Optional
from datetime import datetime
from lxml import html as lxml_html, etree
import json


def parse_article_list(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    通用文章列表解析器

    适用于标准的新闻列表页面，提取第一篇文章的标题和内容。

    Args:
        tree: lxml HTML 树
        url: 原始 URL

    Returns:
        {"title": str, "content": str, "published_at": datetime | None}
    """
    try:
        # 尝试提取标题（常见选择器）
        title_candidates = [
            tree.xpath("//h1[@class='title']//text()"),
            tree.xpath("//h1[@class='article-title']//text()"),
            tree.xpath("//h1//text()"),
            tree.xpath("//title//text()"),
        ]

        title = ""
        for candidate in title_candidates:
            if candidate:
                title = "".join(candidate).strip()
                break

        # 尝试提取内容（常见选择器）
        content_candidates = [
            tree.xpath("//div[@class='content']//text()"),
            tree.xpath("//div[@class='article-content']//text()"),
            tree.xpath("//article//text()"),
            tree.xpath("//div[@id='content']//text()"),
        ]

        content = ""
        for candidate in content_candidates:
            if candidate:
                content = "\n".join([t.strip() for t in candidate if t.strip()])
                break

        return {
            "title": title or "无标题",
            "content": content or "无内容",
            "published_at": None  # 通用解析器不提取时间
        }

    except Exception:
        return {"title": "解析失败", "content": "", "published_at": None}


def parse_rss(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    RSS 解析器

    Args:
        tree: lxml HTML 树（实际是 XML）
        url: 原始 URL

    Returns:
        {"title": str, "content": str, "published_at": datetime | None}
    """
    try:
        # RSS 通常是 XML 格式
        items = tree.xpath("//item")
        if not items:
            return {"title": "无 RSS 条目", "content": "", "published_at": None}

        # 取第一条
        item = items[0]
        title = "".join(item.xpath(".//title//text()")).strip()
        description = "".join(item.xpath(".//description//text()")).strip()
        pub_date_str = "".join(item.xpath(".//pubDate//text()")).strip()

        # 尝试解析时间
        published_at = None
        if pub_date_str:
            try:
                from email.utils import parsedate_to_datetime
                published_at = parsedate_to_datetime(pub_date_str)
            except Exception:
                pass

        return {
            "title": title or "无标题",
            "content": description or "无内容",
            "published_at": published_at
        }

    except Exception:
        return {"title": "RSS 解析失败", "content": "", "published_at": None}


def parse_json_api(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    JSON API 解析器

    适用于返回 JSON 格式的 API。

    Args:
        tree: lxml HTML 树（实际是 JSON 字符串）
        url: 原始 URL

    Returns:
        {"title": str, "content": str, "published_at": datetime | None}
    """
    try:
        # tree 实际是 JSON 字符串
        text = etree.tostring(tree, encoding="unicode", method="text")
        data = json.loads(text)

        # 假设 JSON 格式为 {"data": [{"title": ..., "content": ..., "time": ...}]}
        items = data.get("data", [])
        if not items:
            return {"title": "无数据", "content": "", "published_at": None}

        item = items[0]
        title = item.get("title", "无标题")
        content = item.get("content", "无内容")
        time_str = item.get("time", "")

        # 尝试解析时间
        published_at = None
        if time_str:
            try:
                published_at = datetime.fromisoformat(time_str)
            except Exception:
                pass

        return {
            "title": title,
            "content": content,
            "published_at": published_at
        }

    except Exception:
        return {"title": "JSON 解析失败", "content": "", "published_at": None}
