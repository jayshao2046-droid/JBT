"""期货专用解析器（多文章提取版） — 东财/金十/新浪/三大交易所 + 和讯/卓创/99期货

每个解析器返回 Dict 格式：
{
    "title": "源名称",
    "content": "",
    "published_at": None,
    "articles": [{"title": ..., "content": ..., "url": ..., "published_at": ...}, ...]
}
向后兼容：engine.py 可直接读取 title/content，新调度器额外读取 articles 列表
"""

import re
from typing import Dict, Any
from datetime import datetime
from lxml import html as lxml_html

# 金十快讯 UI 噪音模式："分享收藏详情复制HH:MM:SS" 前缀
_JIN10_UI_PREFIX = re.compile(r'^[\u5206\u4eab\u6536\u85cf\u8be6\u60c5\u590d\u5236\s]{2,}\d{2}:\d{2}:\d{2}\s*')


def parse_eastmoney_futures(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """东方财富期货频道 — 提取文章列表（从首页 /a/ 链接提取）"""
    articles = []
    try:
        items = tree.xpath("//a[contains(@href,'/a/')]")
        seen = set()
        for item in items:
            title = item.text_content().strip()
            href = item.get("href", "")
            if not title or len(title) < 8 or title in seen:
                continue
            seen.add(title)
            if href and not href.startswith("http"):
                href = "https://futures.eastmoney.com" + href
            articles.append({
                "title": title[:120], "content": title,
                "url": href or url, "published_at": None
            })
            if len(articles) >= 20:
                break
    except Exception:
        pass
    return {"title": "东方财富期货", "content": "", "published_at": None, "articles": articles}


def parse_jin10(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """金十数据快讯 — 提取多条快讯"""
    articles = []
    try:
        items = tree.xpath(
            "//div[contains(@class,'flash-item')] | "
            "//div[contains(@class,'jin-flash-item')] | "
            "//div[contains(@class,'news-item')]"
        )
        for item in items[:20]:
            raw = item.text_content().strip()
            # 清洗 "分享收藏详情复制HH:MM:SS" UI 噪音前缀
            title = _JIN10_UI_PREFIX.sub('', raw).strip()[:200]
            time_el = item.xpath(".//span[contains(@class,'time')]//text()")
            pub_at = None
            if time_el:
                try:
                    t = datetime.strptime(time_el[0].strip(), "%H:%M:%S")
                    now = datetime.now()
                    pub_at = t.replace(year=now.year, month=now.month, day=now.day)
                except Exception:
                    pass
            if title and len(title) > 5:
                articles.append({
                    "title": title[:120], "content": title,
                    "url": url, "published_at": pub_at
                })
        if not articles:
            # 不再创建占位文章，让质量门槛自然过滤
            pass
    except Exception:
        pass
    return {"title": "金十数据", "content": "", "published_at": None, "articles": articles}


def parse_sina_futures(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """新浪财经期货 — 提取新闻列表"""
    articles = []
    try:
        items = tree.xpath(
            "//div[@class='feed-card-item'] | "
            "//ul[contains(@class,'list')]//li[.//a] | "
            "//div[@class='main-content']//a"
        )
        for item in items[:15]:
            if item.tag == 'a':
                title = item.text_content().strip()
                href = item.get("href", "")
            else:
                a_tags = item.xpath(".//a")
                if not a_tags:
                    continue
                title = a_tags[0].text_content().strip()
                href = a_tags[0].get("href", "")
            if not title or len(title) < 5:
                continue
            articles.append({
                "title": title[:120], "content": title,
                "url": href or url, "published_at": None
            })
        if not articles:
            title = "".join(tree.xpath("//h1//text()")).strip()
            content = " ".join(tree.xpath("//div[@id='artibody']//p//text()"))[:500]
            if title and len(title) >= 5:
                articles.append({"title": title, "content": content or title, "url": url, "published_at": None})
    except Exception:
        pass
    return {"title": "新浪期货", "content": "", "published_at": None, "articles": articles}


def parse_shfe_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """上期所交易所公告"""
    articles = []
    try:
        items = tree.xpath("//ul[contains(@class,'list')]//li//a | //div[contains(@class,'notice')]//a")
        for item in items[:10]:
            title = item.text_content().strip()
            href = item.get("href", "")
            if title and len(title) > 3:
                if href and not href.startswith("http"):
                    href = "https://www.shfe.com.cn" + href
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
    except Exception:
        pass
    return {"title": "上期所公告", "content": "", "published_at": None, "articles": articles}


def parse_dce_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """大商所交易所公告"""
    articles = []
    try:
        items = tree.xpath("//ul[contains(@class,'list')]//li//a | //div[contains(@class,'article')]//a")
        for item in items[:10]:
            title = item.text_content().strip()
            href = item.get("href", "")
            if title and len(title) > 3:
                if href and not href.startswith("http"):
                    href = "http://www.dce.com.cn" + href
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
    except Exception:
        pass
    return {"title": "大商所公告", "content": "", "published_at": None, "articles": articles}


def parse_czce_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """郑商所交易所公告"""
    articles = []
    try:
        items = tree.xpath("//ul[contains(@class,'list')]//li//a | //div[contains(@class,'TRS_Editor')]//a")
        for item in items[:10]:
            title = item.text_content().strip()
            href = item.get("href", "")
            if title and len(title) > 3:
                if href and not href.startswith("http"):
                    href = "http://www.czce.com.cn" + href
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
    except Exception:
        pass
    return {"title": "郑商所公告", "content": "", "published_at": None, "articles": articles}


def parse_cffex_notice(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """中金所交易所公告"""
    articles = []
    try:
        items = tree.xpath("//div[contains(@class,'content')]//a | //ul//li//a")
        for item in items[:10]:
            title = item.text_content().strip()
            href = item.get("href", "")
            if title and len(title) > 3:
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
    except Exception:
        pass
    return {"title": "中金所公告", "content": "", "published_at": None, "articles": articles}


# ── 新增数据源解析器 ──────────────────────────────────────────────────────

def parse_hexun_futures(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """和讯期货"""
    articles = []
    try:
        items = tree.xpath("//div[contains(@class,'news')]//li//a | //ul[contains(@class,'list')]//a")
        for item in items[:15]:
            title = item.text_content().strip()
            href = item.get("href", "")
            if title and len(title) > 5:
                articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
    except Exception:
        pass
    return {"title": "和讯期货", "content": "", "published_at": None, "articles": articles}


def parse_mysteel(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """我的钢铁网 — 从首页提取新闻链接"""
    articles = []
    try:
        items = tree.xpath("//a[contains(@href,'mysteel.com')]")
        seen = set()
        for item in items:
            title = item.text_content().strip()
            href = item.get("href", "")
            if not title or len(title) < 6 or title in seen:
                continue
            seen.add(title)
            if href and not href.startswith("http"):
                href = "https://www.mysteel.com" + href
            articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
            if len(articles) >= 15:
                break
    except Exception:
        pass
    return {"title": "我的钢铁网", "content": "", "published_at": None, "articles": articles}


def parse_sci99(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """卓创资讯 — 从首页提取新闻链接"""
    articles = []
    try:
        items = tree.xpath("//a[contains(@href,'sci99.com')]")
        seen = set()
        for item in items:
            title = item.text_content().strip()
            href = item.get("href", "")
            if not title or len(title) < 6 or title in seen:
                continue
            seen.add(title)
            articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
            if len(articles) >= 15:
                break
    except Exception:
        pass
    return {"title": "卓创资讯", "content": "", "published_at": None, "articles": articles}


def parse_99futures(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]:
    """99期货 — 从首页提取新闻链接"""
    articles = []
    try:
        items = tree.xpath("//a[contains(@href,'99qh.com')]")
        seen = set()
        for item in items:
            title = item.text_content().strip()
            href = item.get("href", "")
            if not title or len(title) < 6 or title in seen:
                continue
            seen.add(title)
            articles.append({"title": title[:120], "content": title, "url": href or url, "published_at": None})
            if len(articles) >= 15:
                break
    except Exception:
        pass
    return {"title": "99期货", "content": "", "published_at": None, "articles": articles}
