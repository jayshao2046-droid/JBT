"""解析器注册 — 通用解析器 + 期货专用解析器 + 国际解析器"""

from .generic import (
    parse_article_list,
    parse_rss,
    parse_json_api
)

from .futures import (
    parse_eastmoney_futures,
    parse_jin10,
    parse_sina_futures,
    parse_shfe_notice,
    parse_dce_notice,
    parse_czce_notice,
    parse_cffex_notice
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

# 解析器注册表
PARSER_REGISTRY = {
    # 通用解析器
    "article_list": parse_article_list,
    "rss": parse_rss,
    "json_api": parse_json_api,

    # 期货专用解析器
    "eastmoney_futures": parse_eastmoney_futures,
    "jin10": parse_jin10,
    "sina_futures": parse_sina_futures,
    "shfe_notice": parse_shfe_notice,
    "dce_notice": parse_dce_notice,
    "czce_notice": parse_czce_notice,
    "cffex_notice": parse_cffex_notice,

    # 国际解析器（7 个）
    "cme_advisory": parse_cme_advisory,
    "kitco_gold": parse_kitco_gold,
    "oilprice_com": parse_oilprice_com,
    "mining_com": parse_mining_com,
    "investing_commodities": parse_investing_commodities,
    "fed_releases": parse_fed_releases,
    "reuters_commodities": parse_reuters_commodities,
}


def get_parser(parser_name: str):
    """获取解析器函数"""
    return PARSER_REGISTRY.get(parser_name)

