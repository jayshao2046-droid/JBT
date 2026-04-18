"""解析器注册表 — 映射 source_id → parser 函数

每个 parser 函数签名：(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]
返回值必须包含 articles 列表（多文章提取版）
"""

from .futures import (
    parse_eastmoney_futures,
    parse_jin10,
    parse_sina_futures,
    parse_shfe_notice,
    parse_dce_notice,
    parse_czce_notice,
    parse_cffex_notice,
    parse_hexun_futures,
    parse_mysteel,
    parse_sci99,
    parse_99futures,
)
from .international import (
    parse_cme_advisory,
    parse_kitco_gold,
    parse_oilprice_com,
    parse_mining_com,
    parse_investing_commodities,
    parse_fed_releases,
    parse_reuters_commodities,
)

PARSER_REGISTRY = {
    # 国内期货 (11)
    "eastmoney_futures": parse_eastmoney_futures,
    "jin10": parse_jin10,
    "sina_futures": parse_sina_futures,
    "shfe_notice": parse_shfe_notice,
    "dce_notice": parse_dce_notice,
    "czce_notice": parse_czce_notice,
    "cffex_notice": parse_cffex_notice,
    "hexun_futures": parse_hexun_futures,
    "mysteel": parse_mysteel,
    "sci99": parse_sci99,
    "99futures": parse_99futures,
    # 国际 (7)
    "cme_advisory": parse_cme_advisory,
    "kitco_gold": parse_kitco_gold,
    "oilprice_com": parse_oilprice_com,
    "mining_com": parse_mining_com,
    "investing_commodities": parse_investing_commodities,
    "fed_releases": parse_fed_releases,
    "reuters_commodities": parse_reuters_commodities,
}


def get_parser(name: str):
    """获取解析器函数"""
    return PARSER_REGISTRY.get(name)
