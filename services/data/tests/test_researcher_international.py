"""测试国际采集源解析器"""

import pytest
import sys
import os
from lxml import html as lxml_html

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.crawler.parsers.international import (
    parse_cme_advisory,
    parse_kitco_gold,
    parse_oilprice_com,
    parse_mining_com,
    parse_investing_commodities,
    parse_fed_releases,
    parse_reuters_commodities,
)


def test_parse_cme_advisory():
    """测试 CME Group 公告解析器"""
    # 模拟 HTML
    html = """
    <html>
        <div class="advisory-list">
            <h2>CME Market Advisory</h2>
        </div>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_cme_advisory(tree, "https://www.cmegroup.com/market-data/advisories.html")

    assert "title" in result
    assert "content" in result
    assert "published_at" in result
    assert isinstance(result["title"], str)
    assert len(result["title"]) > 0


def test_parse_kitco_gold():
    """测试 Kitco 贵金属新闻解析器"""
    html = """
    <html>
        <div class="article-list">
            <h2><a>Gold prices rise on Fed signals</a></h2>
        </div>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_kitco_gold(tree, "https://www.kitco.com/news/")

    assert "title" in result
    assert "content" in result
    assert isinstance(result["title"], str)


def test_parse_oilprice_com():
    """测试 OilPrice 能源资讯解析器"""
    html = """
    <html>
        <div class="categoryArticle">
            <h2>Oil prices surge on supply concerns</h2>
        </div>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_oilprice_com(tree, "https://oilprice.com/Latest-Energy-News/World-News")

    assert "title" in result
    assert "content" in result
    assert isinstance(result["title"], str)


def test_parse_mining_com():
    """测试 Mining.com 矿业新闻解析器"""
    html = """
    <html>
        <article class="post">
            <h2 class="entry-title"><a>Copper demand outlook</a></h2>
        </article>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_mining_com(tree, "https://www.mining.com/news/")

    assert "title" in result
    assert "content" in result
    assert isinstance(result["title"], str)


def test_parse_investing_commodities():
    """测试 Investing.com 大宗商品解析器"""
    html = """
    <html>
        <article data-test="article-item">
            <a>Commodities market update</a>
        </article>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_investing_commodities(tree, "https://www.investing.com/news/commodities-news")

    assert "title" in result
    assert "content" in result
    assert isinstance(result["title"], str)


def test_parse_fed_releases():
    """测试美联储公告解析器"""
    html = """
    <html>
        <div class="row">
            <a class="ng-binding">Federal Reserve announces rate decision</a>
        </div>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_fed_releases(tree, "https://www.federalreserve.gov/newsevents/pressreleases.htm")

    assert "title" in result
    assert "content" in result
    assert isinstance(result["title"], str)


def test_parse_reuters_commodities():
    """测试路透社大宗商品解析器"""
    html = """
    <html>
        <article>
            <h3>Commodities trading update</h3>
        </article>
    </html>
    """
    tree = lxml_html.fromstring(html)
    result = parse_reuters_commodities(tree, "https://www.reuters.com/markets/commodities/")

    assert "title" in result
    assert "content" in result
    assert isinstance(result["title"], str)


def test_parsers_handle_empty_html():
    """测试解析器处理空 HTML 不抛异常"""
    empty_html = "<html></html>"
    tree = lxml_html.fromstring(empty_html)

    parsers = [
        parse_cme_advisory,
        parse_kitco_gold,
        parse_oilprice_com,
        parse_mining_com,
        parse_investing_commodities,
        parse_fed_releases,
        parse_reuters_commodities,
    ]

    for parser in parsers:
        result = parser(tree, "http://example.com")
        assert "title" in result
        assert "content" in result
        assert "published_at" in result
        # 解析失败时应返回失败标题，而不是抛异常
        assert "解析失败" in result["title"] or len(result["title"]) > 0


def test_parsers_return_correct_format():
    """测试所有解析器返回正确格式"""
    html = "<html><h2>Test</h2></html>"
    tree = lxml_html.fromstring(html)

    parsers = [
        parse_cme_advisory,
        parse_kitco_gold,
        parse_oilprice_com,
        parse_mining_com,
        parse_investing_commodities,
        parse_fed_releases,
        parse_reuters_commodities,
    ]

    for parser in parsers:
        result = parser(tree, "http://example.com")
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "published_at" in result
        assert isinstance(result["title"], str)
        assert isinstance(result["content"], str)
