"""情绪采集解析器 — 东财股吧 / 雪球 / 财联社"""

import json
import re
from typing import Dict, Any
from datetime import datetime
from lxml import html as lxml_html


def parse_eastmoney_guba(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    东方财富股吧 JSON API 解析器

    URL: https://guba.eastmoney.com/interface/GetList.aspx?t=1&f=1&gpdm=ZS000001&action=0&pageindex=1&pagesize=20
    返回 JSONP 格式: __GetList({...})
    """
    try:
        raw_text = tree.text_content().strip()
        # 去掉 JSONP callback 包装
        if "(" in raw_text and raw_text.rstrip().endswith(")"):
            raw_text = raw_text[raw_text.index("(") + 1 : raw_text.rindex(")")]
        data = json.loads(raw_text)
        items = data.get("re", [])

        titles = []
        for item in items[:15]:
            title = item.get("BSTITLE", "").strip()
            if title:
                titles.append(title)

        return {
            "title": f"东财股吧 {len(titles)} 条讨论",
            "content": "\n".join(titles),
            "published_at": datetime.now(),
        }
    except Exception as e:
        return {"title": "东财股吧解析失败", "content": str(e)[:100], "published_at": None}


def parse_xueqiu_sentiment(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    雪球热帖解析器（Browser 模式，Playwright 渲染）

    URL: https://xueqiu.com/hq#exchange=qihuo
    优先尝试 JSON API 响应，降级到 HTML xpath
    """
    try:
        raw_text = tree.text_content().strip()

        # 先尝试 JSON API 响应
        if raw_text.lstrip().startswith("{"):
            data = json.loads(raw_text)
            statuses = data.get("list", data.get("statuses", []))
            titles = []
            for s in statuses[:15]:
                text = s.get("text", s.get("title", s.get("description", ""))).strip()
                if text:
                    text = re.sub(r"<[^>]+>", "", text).strip()[:120]
                    if text:
                        titles.append(text)
            return {
                "title": f"雪球 {len(titles)} 条热帖",
                "content": "\n".join(titles),
                "published_at": datetime.now(),
            }

        # 浏览器渲染 HTML 模式
        posts = tree.xpath(
            "//ul[contains(@class,'timeline')]//div[contains(@class,'status-content')]//text() | "
            "//div[contains(@class,'item__text')]//text() | "
            "//div[@class='stock-detail']//text()"
        )
        content = "\n".join([p.strip() for p in posts if len(p.strip()) > 10][:20])
        return {
            "title": "雪球期货板块情绪",
            "content": content or "无内容",
            "published_at": datetime.now(),
        }
    except Exception as e:
        return {"title": "雪球解析失败", "content": str(e)[:100], "published_at": None}


def parse_cls_telegraph(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """
    财联社电报解析器（Browser 模式）

    URL: https://www.cls.cn/telegraph
    """
    try:
        # 电报列表条目
        items = tree.xpath(
            "//div[contains(@class,'telegraph-content-item')]//text() | "
            "//div[contains(@class,'tele-content')]//text() | "
            "//ul[contains(@class,'telegraph-list')]//li//span//text()"
        )
        texts = [t.strip() for t in items if len(t.strip()) > 10][:20]

        if not texts:
            # 备用：尝试内嵌 JSON
            raw = tree.text_content().strip()
            idx = raw.find("{")
            if idx >= 0:
                data = json.loads(raw[idx:])
                roll_data = data.get("data", {}).get("roll_data", [])
                texts = [d.get("content", "") for d in roll_data[:15] if d.get("content")]

        return {
            "title": f"财联社电报 {len(texts)} 条",
            "content": "\n".join(texts),
            "published_at": datetime.now(),
        }
    except Exception as e:
        return {"title": "财联社解析失败", "content": str(e)[:100], "published_at": None}
