"""期货专用解析器 — 东财/金十/新浪/各交易所公告"""

from typing import Dict, Any, Optional
from datetime import datetime
from lxml import html as lxml_html


def parse_eastmoney_futures(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    东方财富期货频道解析器

    Args:
        tree: lxml HTML 树
        url: 原始 URL

    Returns:
        {"title": str, "content": str, "published_at": datetime | None}
    """
    try:
        # 东财期货新闻列表
        title = "".join(tree.xpath("//h1[@class='newsTitle']//text()")).strip()
        if not title:
            title = "".join(tree.xpath("//h1//text()")).strip()

        content_parts = tree.xpath("//div[@class='newsContent']//p//text()")
        content = "\n".join([p.strip() for p in content_parts if p.strip()])

        # 时间提取
        time_str = "".join(tree.xpath("//span[@class='time']//text()")).strip()
        published_at = None
        if time_str:
            try:
                published_at = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        return {
            "title": title or "东财期货新闻",
            "content": content or "无内容",
            "published_at": published_at
        }

    except Exception:
        return {"title": "东财解析失败", "content": "", "published_at": None}


def parse_jin10(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    金十数据快讯解析器

    Args:
        tree: lxml HTML 树
        url: 原始 URL

    Returns:
        {"title": str, "content": str, "published_at": datetime | None}
    """
    try:
        # 金十快讯通常是列表形式
        items = tree.xpath("//div[@class='flash-item']")
        if not items:
            return {"title": "无金十快讯", "content": "", "published_at": None}

        # 取第一条
        item = items[0]
        title = "".join(item.xpath(".//div[@class='flash-title']//text()")).strip()
        content = "".join(item.xpath(".//div[@class='flash-content']//text()")).strip()
        time_str = "".join(item.xpath(".//span[@class='flash-time']//text()")).strip()

        published_at = None
        if time_str:
            try:
                published_at = datetime.strptime(time_str, "%H:%M:%S")
                # 补充日期为今天
                published_at = published_at.replace(
                    year=datetime.now().year,
                    month=datetime.now().month,
                    day=datetime.now().day
                )
            except Exception:
                pass

        return {
            "title": title or "金十快讯",
            "content": content or "无内容",
            "published_at": published_at
        }

    except Exception:
        return {"title": "金十解析失败", "content": "", "published_at": None}


def parse_sina_futures(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    新浪财经期货解析器

    Args:
        tree: lxml HTML 树
        url: 原始 URL

    Returns:
        {"title": str, "content": str, "published_at": datetime | None}
    """
    try:
        title = "".join(tree.xpath("//h1[@id='artibodyTitle']//text()")).strip()
        if not title:
            title = "".join(tree.xpath("//h1//text()")).strip()

        content_parts = tree.xpath("//div[@id='artibody']//p//text()")
        content = "\n".join([p.strip() for p in content_parts if p.strip()])

        time_str = "".join(tree.xpath("//span[@class='time-source']//text()")).strip()
        published_at = None
        if time_str:
            try:
                published_at = datetime.strptime(time_str, "%Y年%m月%d日 %H:%M")
            except Exception:
                pass

        return {
            "title": title or "新浪期货新闻",
            "content": content or "无内容",
            "published_at": published_at
        }

    except Exception:
        return {"title": "新浪解析失败", "content": "", "published_at": None}


def parse_shfe_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """上期所公告解析器"""
    try:
        title = "".join(tree.xpath("//div[@class='title']//text()")).strip()
        content_parts = tree.xpath("//div[@class='content']//text()")
        content = "\n".join([p.strip() for p in content_parts if p.strip()])

        return {
            "title": title or "上期所公告",
            "content": content or "无内容",
            "published_at": None
        }
    except Exception:
        return {"title": "上期所解析失败", "content": "", "published_at": None}


def parse_dce_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """大商所公告解析器"""
    try:
        title = "".join(tree.xpath("//h2//text()")).strip()
        content_parts = tree.xpath("//div[@class='article']//text()")
        content = "\n".join([p.strip() for p in content_parts if p.strip()])

        return {
            "title": title or "大商所公告",
            "content": content or "无内容",
            "published_at": None
        }
    except Exception:
        return {"title": "大商所解析失败", "content": "", "published_at": None}


def parse_czce_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """郑商所公告解析器"""
    try:
        title = "".join(tree.xpath("//div[@class='title']//text()")).strip()
        content_parts = tree.xpath("//div[@class='TRS_Editor']//text()")
        content = "\n".join([p.strip() for p in content_parts if p.strip()])

        return {
            "title": title or "郑商所公告",
            "content": content or "无内容",
            "published_at": None
        }
    except Exception:
        return {"title": "郑商所解析失败", "content": "", "published_at": None}


def parse_cffex_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """中金所公告解析器"""
    try:
        title = "".join(tree.xpath("//h1//text()")).strip()
        content_parts = tree.xpath("//div[@class='content']//text()")
        content = "\n".join([p.strip() for p in content_parts if p.strip()])

        return {
            "title": title or "中金所公告",
            "content": content or "无内容",
            "published_at": None
        }
    except Exception:
        return {"title": "中金所解析失败", "content": "", "published_at": None}
