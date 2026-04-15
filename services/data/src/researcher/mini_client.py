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

    def get_bars(self, symbol: str, interval: str = "1m", limit: Optional[int] = None) -> List[Dict]:
        """获取 K 线数据"""
        try:
            params = {
                "symbol": symbol,
                "interval": interval
            }

            if limit is not None:
                params["limit"] = limit

            resp = requests.get(self.bars_endpoint, params=params, timeout=10)

            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"Failed to get bars for {symbol}: {resp.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
            return []

    def get_latest_bar(self, symbol: str, interval: str = "1m") -> Optional[Dict]:
        """获取最新一根 K 线"""
        bars = self.get_bars(symbol, interval, limit=1)
        return bars[0] if bars else None

    def get_multiple_symbols(self, symbols: List[str], interval: str = "1m", limit: int = 1) -> Dict[str, List[Dict]]:
        """批量获取多个品种的 K 线"""
        result = {}

        for symbol in symbols:
            bars = self.get_bars(symbol, interval, limit)
            if bars:
                result[symbol] = bars

        return result
