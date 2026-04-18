"""Mini API 客户端 - 从 Mini 拉取数据

职责：
1. 拉取 K 线数据
2. 拉取其他市场数据
"""
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MiniClient:
    """Mini API 客户端"""

    def __init__(self, base_url: str = "http://192.168.31.76:8105"):
        self.base_url = base_url
        self.bars_endpoint = f"{base_url}/api/v1/bars"

    def get_bars(self, symbol: str, interval: str = "1m", limit: Optional[int] = None,
                 start: Optional[str] = None, end: Optional[str] = None) -> List[Dict]:
        """获取 K 线数据

        Args:
            symbol: 品种代码（如 SHFE_rb）
            interval: 时间周期（暂未使用，API 固定返回1分钟）
            limit: 限制返回条数
            start: 开始时间（ISO格式或相对时间如 -1h, -7d）
            end: 结束时间（可选，默认当前时间）
        """
        try:
            # 如果未指定 start，默认获取最近1小时数据
            if start is None:
                start = "-1h"

            params = {
                "symbol": symbol,
                "start": start
            }

            if end is not None:
                params["end"] = end

            if limit is not None:
                params["limit"] = limit

            resp = requests.get(self.bars_endpoint, params=params, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                return data.get("bars", [])
            else:
                logger.error(f"Failed to get bars for {symbol}: {resp.status_code} - {resp.text}")
                return []

        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return []

    def get_latest_bar(self, symbol: str, interval: str = "1m") -> Optional[Dict]:
        """获取最新一根 K 线"""
        bars = self.get_bars(symbol, interval, limit=1)
        return bars[0] if bars else None

    def get_multiple_symbols(self, symbols: List[str], interval: str = "1m", limit: int = 1,
                            start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, List[Dict]]:
        """批量获取多个品种的 K 线"""
        result = {}

        for symbol in symbols:
            bars = self.get_bars(symbol, interval, limit, start, end)
            if bars:
                result[symbol] = bars

        return result
