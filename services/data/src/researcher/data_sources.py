"""
数据源配置 - 定义所有数据源

职责：
1. 定义期货品种列表
2. 定义新闻源配置
3. 定义基本面数据源配置
"""
from typing import List, Dict


# 35 个期货品种
FUTURES_SYMBOLS = [
    # 金融期货 (7)
    "IF", "IC", "IH", "IM",  # 股指期货
    "TS", "TF", "T",  # 国债期货

    # 有色金属 (8)
    "CU", "AL", "ZN", "PB", "NI", "SN", "AU", "AG",

    # 黑色化工 (8)
    "RB", "HC", "SS",  # 黑色
    "FU", "BU", "RU", "SP", "LU",  # 化工

    # 农产品 (12)
    "C", "CS", "A", "M", "Y", "P",  # 油脂油料
    "OI", "RM", "SR", "CF", "TA", "MA", "FG", "PK"  # 软商品
]


# 新闻源配置
NEWS_SOURCES = [
    {
        "name": "新浪财经-期货",
        "url": "https://finance.sina.com.cn/futuremarket/",
        "interval": 300,  # 5分钟
        "priority": "P0"
    },
    {
        "name": "东方财富-期货",
        "url": "https://futures.eastmoney.com/news/",
        "interval": 300,
        "priority": "P0"
    },
    {
        "name": "金十数据",
        "url": "https://www.jin10.com/",
        "interval": 180,  # 3分钟
        "priority": "P0"
    },
    {
        "name": "和讯期货",
        "url": "http://futures.hexun.com/",
        "interval": 600,
        "priority": "P1"
    },
    {
        "name": "期货日报",
        "url": "http://www.qhrb.com.cn/",
        "interval": 3600,
        "priority": "P1"
    }
]


# 基本面数据源配置
FUNDAMENTAL_SOURCES = [
    {
        "name": "我的钢铁网-库存",
        "url": "https://www.mysteel.com/",
        "interval": 3600,
        "type": "inventory",
        "priority": "P0"
    },
    {
        "name": "卓创资讯-产量",
        "url": "https://www.sci99.com/",
        "interval": 3600,
        "type": "production",
        "priority": "P1"
    },
    {
        "name": "统计局-宏观",
        "url": "http://www.stats.gov.cn/",
        "interval": 86400,
        "type": "macro",
        "priority": "P1"
    },
    {
        "name": "SMM-有色金属",
        "url": "https://www.smm.cn/",
        "interval": 3600,
        "type": "metal",
        "priority": "P0"
    }
]


# 报告时段配置
REPORT_SCHEDULES = [
    {"hour": 8, "minute": 45, "segment": "盘前", "type": "segment"},
    {"hour": 11, "minute": 45, "segment": "午间", "type": "segment"},
    {"hour": 15, "minute": 15, "segment": "盘后", "type": "segment"},
    {"hour": 23, "minute": 15, "segment": "夜盘收盘", "type": "segment"},
    {"hour": 23, "minute": 30, "segment": "每日深度", "type": "daily"}
]


# Mini API 配置
MINI_API_CONFIG = {
    "base_url": "http://192.168.31.156:8105",
    "bars_endpoint": "/api/v1/bars",
    "reports_endpoint": "/api/v1/researcher/reports",
    "timeout": 10
}


# Ollama 配置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "qwen3:14b",
    "timeout": 30
}
