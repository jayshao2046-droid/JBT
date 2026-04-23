"""合约解析器 — TASK-0127

解析期货合约代码，查询主力合约月份。

功能：
1. 解析合约代码（DCE.p0 → {exchange: DCE, commodity: p, contract: 0}）
2. 查询主力合约月份（通过 Mini data API）
3. 转换为具体月份合约（DCE.p0 → DCE.p2505）
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ContractResolver:
    """合约解析器"""

    # 品种→交易所映射表
    COMMODITY_EXCHANGE_MAP = {
        # DCE 大商所
        "rb": "SHFE", "hc": "SHFE", "i": "DCE", "j": "DCE", "jm": "DCE",
        "cu": "SHFE", "al": "SHFE", "zn": "SHFE", "ni": "SHFE", "ss": "SHFE",
        "au": "SHFE", "ag": "SHFE", "sc": "INE", "fu": "SHFE", "bu": "SHFE",
        "ru": "SHFE", "sp": "SHFE", "eb": "DCE", "pg": "DCE", "p": "DCE",
        "y": "DCE", "m": "DCE", "a": "DCE", "c": "DCE", "cs": "DCE",
        "l": "DCE", "v": "DCE", "pp": "DCE", "lh": "DCE",
        # CZCE 郑商所
        "ap": "CZCE", "cf": "CZCE", "sr": "CZCE", "ma": "CZCE",
        "ta": "CZCE", "eg": "CZCE",
    }

    # 主力合约月份映射表（降级方案）
    # 格式：{commodity: month_offset}
    # month_offset: 0=当月, 1=下月, 5=5个月后
    MAIN_CONTRACT_FALLBACK = {
        # 黑色系
        "rb": 5,  # 螺纹钢，通常 5 个月后
        "hc": 5,  # 热轧卷板
        "i": 5,   # 铁矿石
        "j": 5,   # 焦炭
        "jm": 5,  # 焦煤
        # 有色金属
        "cu": 3,  # 铜
        "al": 3,  # 铝
        "zn": 3,  # 锌
        "ni": 3,  # 镍
        "ss": 3,  # 不锈钢
        # 贵金属
        "au": 2,  # 黄金
        "ag": 2,  # 白银
        # 能化
        "sc": 3,  # 原油
        "fu": 3,  # 燃料油
        "bu": 3,  # 沥青
        "ru": 5,  # 橡胶
        "sp": 3,  # 纸浆
        "eb": 3,  # 苯乙烯
        "pg": 3,  # 液化石油气
        # 农产品
        "p": 5,   # 棕榈油
        "y": 5,   # 豆油
        "m": 5,   # 豆粕
        "a": 5,   # 豆一
        "c": 5,   # 玉米
        "cs": 5,  # 玉米淀粉
        "l": 5,   # 塑料
        "v": 5,   # PVC
        "pp": 5,  # 聚丙烯
        "lh": 3,  # 生猪
        "ap": 5,  # 苹果
        "cf": 5,  # 棉花
        "sr": 5,  # 白糖
        "ma": 5,  # 甲醇
        "ta": 5,  # PTA
        "eg": 5,  # 乙二醇
    }

    def __init__(self, data_url: str = "http://192.168.31.74:8105"):
        """初始化合约解析器

        Args:
            data_url: Mini data API 地址
        """
        self.data_url = data_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=10.0)

    def parse_symbol(self, symbol: str) -> dict[str, str]:
        """解析品种代码

        Args:
            symbol: 合约代码（如 DCE.p0, SHFE.rb2505）

        Returns:
            {exchange: 交易所, commodity: 品种, contract: 合约月份}
        """
        # 匹配格式：EXCHANGE.COMMODITY[CONTRACT]
        # 例如：DCE.p0, SHFE.rb2505, CZCE.CF605
        pattern = r"^([A-Z]+)\.([a-zA-Z]+)(\d*)$"
        match = re.match(pattern, symbol)

        if not match:
            raise ValueError(f"无法解析合约代码: {symbol}")

        exchange, commodity, contract = match.groups()

        return {
            "exchange": exchange,
            "commodity": commodity.lower(),
            "contract": contract or "0",
        }

    async def get_main_contract(self, symbol: str) -> str:
        """获取主力合约代码

        Args:
            symbol: 品种代码（如 DCE.p0, DCE.p）

        Returns:
            主力合约代码（如 DCE.p2505）
        """
        # 如果没有交易所前缀，根据品种查找正确的交易所
        if "." not in symbol:
            commodity = symbol.lower()
            exchange = self.COMMODITY_EXCHANGE_MAP.get(commodity, "DCE")
            symbol = f"{exchange}.{symbol}"

        parsed = self.parse_symbol(symbol)
        exchange = parsed["exchange"]
        commodity = parsed["commodity"]
        contract = parsed["contract"]

        # 如果已经是具体月份合约，直接返回
        if contract and contract != "0" and len(contract) >= 4:
            return symbol

        # 尝试从 Mini data API 查询主力合约
        try:
            main_contract = await self._query_main_contract_from_api(exchange, commodity)
            if main_contract:
                logger.info(f"✅ 查询到主力合约: {symbol} → {main_contract}")
                return main_contract
        except Exception as e:
            logger.warning(f"查询主力合约失败 ({symbol}): {e}，使用降级方案")

        # 降级方案：使用固定月份映射表
        main_contract = self._get_main_contract_fallback(exchange, commodity)
        logger.info(f"⚠️ 使用降级主力合约: {symbol} → {main_contract}")
        return main_contract

    async def _query_main_contract_from_api(
        self,
        exchange: str,
        commodity: str,
    ) -> Optional[str]:
        """从 Mini data API 查询主力合约

        Args:
            exchange: 交易所代码
            commodity: 品种代码

        Returns:
            主力合约代码，查询失败返回 None
        """
        # TODO: 实现真实的 Mini data API 查询
        # 当前 Mini data API 可能没有主力合约查询接口
        # 这里预留接口，后续可接入
        return None

    def _get_main_contract_fallback(self, exchange: str, commodity: str) -> str:
        """降级方案：根据固定规则生成主力合约代码

        Args:
            exchange: 交易所代码
            commodity: 品种代码

        Returns:
            主力合约代码
        """
        # 获取当前年月
        now = datetime.now()
        year = now.year % 100  # 取后两位
        month = now.month

        # 获取月份偏移
        month_offset = self.MAIN_CONTRACT_FALLBACK.get(commodity, 5)

        # 计算主力合约月份
        target_month = month + month_offset
        target_year = year

        if target_month > 12:
            target_month -= 12
            target_year += 1

        # 格式化合约代码
        # DCE/SHFE: 4位（yymm），如 2505
        # CZCE: 3位（ymm），如 505
        if exchange == "CZCE":
            contract = f"{target_year % 10}{target_month:02d}"
        else:
            contract = f"{target_year:02d}{target_month:02d}"

        return f"{exchange}.{commodity}{contract}"

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
