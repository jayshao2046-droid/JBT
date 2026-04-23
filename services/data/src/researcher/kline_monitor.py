"""
K线监控器 - 实时监控期货分钟K线

职责：
1. 从 Mini API 拉取最新 K 线数据
2. 检测异常波动（涨跌幅 > 2%）
3. 推送异常事件到共享队列
"""
import logging
import time
from datetime import datetime
from typing import Optional
import requests
import multiprocessing as mp

logger = logging.getLogger(__name__)


class KlineMonitor:
    """K线监控器"""

    def __init__(self, queue: mp.Queue, stop_event: mp.Event):
        self.queue = queue
        self.stop_event = stop_event
        self.mini_api = "http://192.168.31.156:8105/api/v1/bars"

        # 35 个期货品种
        self.symbols = [
            "IF", "IC", "IH", "IM", "TS", "TF", "T",  # 金融期货
            "CU", "AL", "ZN", "PB", "NI", "SN", "AU", "AG",  # 有色金属
            "RB", "HC", "SS", "FU", "BU", "RU", "SP", "LU",  # 黑色化工
            "C", "CS", "A", "M", "Y", "P", "OI", "RM", "SR", "CF", "TA", "MA", "FG", "PK"  # 农产品
        ]

        self.last_prices = {}  # 记录上一次价格

    def run(self):
        """主循环"""
        logger.info("KlineMonitor started")

        while not self.stop_event.is_set():
            try:
                self._check_all_symbols()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"KlineMonitor error: {e}", exc_info=True)
                time.sleep(10)

        logger.info("KlineMonitor stopped")

    def _check_all_symbols(self):
        """检查所有品种"""
        for symbol in self.symbols:
            if self.stop_event.is_set():
                break

            try:
                self._check_symbol(symbol)
            except Exception as e:
                logger.error(f"Error checking {symbol}: {e}")

    def _check_symbol(self, symbol: str):
        """检查单个品种"""
        try:
            # 拉取最新 1 根 K 线
            resp = requests.get(
                self.mini_api,
                params={
                    "symbol": symbol,
                    "interval": "1m",
                    "limit": 2  # 拉 2 根，计算涨跌幅
                },
                timeout=5
            )

            if resp.status_code != 200:
                return

            data = resp.json()
            if not data or len(data) < 2:
                return

            # 计算涨跌幅
            prev_close = data[1]["close"]
            curr_close = data[0]["close"]
            change_pct = (curr_close - prev_close) / prev_close * 100

            # 检测异常波动（> 2%）
            if abs(change_pct) > 2.0:
                event = {
                    "type": "kline_alert",
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "prev_close": prev_close,
                    "curr_close": curr_close,
                    "change_pct": change_pct,
                    "volume": data[0]["volume"]
                }

                # 推送到队列
                # 安全修复：P0-6 - 明确捕获预期异常类型
                try:
                    self.queue.put_nowait(event)
                    logger.info(f"Alert: {symbol} {change_pct:+.2f}%")
                except Exception as e:
                    logger.warning(f"Queue full, dropping kline alert for {symbol}")

        except Exception as e:
            logger.debug(f"Error checking {symbol}: {e}")
