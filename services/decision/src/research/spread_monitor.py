"""产业链价差监控模块 — TASK-0117 模块 1

监控期货产业链内的价差 Z-score，超阈值时自动生成套利策略意图。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import os

import httpx
import pandas as pd

logger = logging.getLogger(__name__)


class SpreadMonitor:
    """监控期货产业链内的价差 Z-score。

    Z-score > 2σ → qwen3 自动生成套利策略意图 → pipeline.full_pipeline()
    """

    CHAINS = {
        "黑色链": ["rb", "hc", "i", "j", "jm"],   # 螺纹钢-热轧-铁矿-焦炭-焦煤
        "有色链": ["cu", "al", "zn"],               # 铜-铝-锌
        "油脂链": ["p", "y", "a"],                  # 棕榈-豆油-豆粕
    }

    ZSCORE_WINDOW = 60  # 滚动窗口：60 个交易日
    THRESHOLD = 2.0     # 触发阈值：绝对值 > 2.0

    def __init__(self, data_api_url: Optional[str] = None):
        """初始化价差监控器。

        Args:
            data_api_url: 数据服务 API 地址，默认从环境变量读取
        """
        self.data_api_url = data_api_url or os.getenv(
            "DATA_SERVICE_URL", "http://192.168.31.74:8105"
        )
        self._triggered_today: Dict[Tuple[str, str], bool] = {}  # 防止重复触发

    async def monitor_all(self) -> List[Dict[str, Any]]:
        """拉取各链所有品种日K线，计算跨品种价差，返回超阈值触发列表。

        Returns:
            触发列表，每项包含 chain_name, pair, zscore, triggered
        """
        results = []

        for chain_name, symbols in self.CHAINS.items():
            logger.info(f"监控 {chain_name}，品种: {symbols}")

            # 拉取所有品种的日K线
            bars_data = await self._fetch_chain_bars(symbols)

            # 计算所有品种对的价差 Z-score
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i + 1:]:
                    pair = (symbol1, symbol2)

                    # 检查今日是否已触发
                    if self._triggered_today.get(pair, False):
                        logger.debug(f"{pair} 今日已触发，跳过")
                        continue

                    # 计算价差 Z-score
                    zscore = self._calc_pair_zscore(
                        bars_data.get(symbol1),
                        bars_data.get(symbol2)
                    )

                    if zscore is None:
                        continue

                    # 判断是否超阈值
                    triggered = abs(zscore) > self.THRESHOLD

                    result = {
                        "chain_name": chain_name,
                        "pair": pair,
                        "zscore": zscore,
                        "triggered": triggered,
                    }
                    results.append(result)

                    # 超阈值时触发 pipeline
                    if triggered:
                        logger.warning(
                            f"{chain_name} {pair} 价差偏离 {zscore:.2f}σ，触发套利意图生成"
                        )
                        await self._trigger_pipeline(chain_name, pair, zscore)
                        self._triggered_today[pair] = True

        return results

    async def _fetch_chain_bars(
        self, symbols: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """拉取产业链所有品种的日K线数据。

        Args:
            symbols: 品种列表

        Returns:
            {symbol: DataFrame} 字典，DataFrame 包含 close 列
        """
        bars_data = {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            for symbol in symbols:
                try:
                    url = f"{self.data_api_url}/api/v1/bars"
                    params = {
                        "symbol": symbol,
                        "interval": "1d",
                        "count": self.ZSCORE_WINDOW + 10,  # 多拉一些防止缺失
                    }

                    resp = await client.get(url, params=params)
                    resp.raise_for_status()

                    data = resp.json()
                    if not data or "bars" not in data:
                        logger.warning(f"{symbol} 返回数据为空")
                        continue

                    bars = data["bars"]
                    if len(bars) < self.ZSCORE_WINDOW:
                        logger.warning(
                            f"{symbol} K线数量不足: {len(bars)} < {self.ZSCORE_WINDOW}"
                        )
                        continue

                    # 转为 DataFrame
                    df = pd.DataFrame(bars)
                    if "close" not in df.columns:
                        logger.warning(f"{symbol} 缺少 close 列")
                        continue

                    bars_data[symbol] = df
                    logger.debug(f"{symbol} 拉取 {len(df)} 根K线")

                except Exception as e:
                    logger.warning(f"{symbol} 拉取K线失败: {e}", exc_info=True)
                    continue

        return bars_data

    def _calc_pair_zscore(
        self,
        bars1: Optional[pd.DataFrame],
        bars2: Optional[pd.DataFrame],
    ) -> Optional[float]:
        """计算两个品种的价差 Z-score。

        使用收盘价比值（非价差绝对值）处理不同单位问题。

        Args:
            bars1: 品种1的K线数据
            bars2: 品种2的K线数据

        Returns:
            Z-score 值，数据不足时返回 None
        """
        if bars1 is None or bars2 is None:
            return None

        if len(bars1) < self.ZSCORE_WINDOW or len(bars2) < self.ZSCORE_WINDOW:
            return None

        # 取最近 ZSCORE_WINDOW 根K线
        close1 = bars1["close"].iloc[-self.ZSCORE_WINDOW:].values
        close2 = bars2["close"].iloc[-self.ZSCORE_WINDOW:].values

        # 计算价差序列（收盘价比值）
        spread_series = close1 / close2

        # 计算 Z-score
        zscore = self._calc_zscore(pd.Series(spread_series), self.ZSCORE_WINDOW)

        return zscore

    def _calc_zscore(self, spread_series: pd.Series, window: int) -> float:
        """滚动窗口计算 Z-score。

        Args:
            spread_series: 价差序列
            window: 滚动窗口大小

        Returns:
            当前 Z-score 值
        """
        if len(spread_series) == 0:
            return 0.0

        mean = spread_series.mean()
        std = spread_series.std()

        if std == 0 or pd.isna(std):
            return 0.0

        current_value = spread_series.iloc[-1]
        zscore = (current_value - mean) / std

        return float(zscore)

    async def _trigger_pipeline(
        self, chain_name: str, pair: Tuple[str, str], zscore: float
    ) -> None:
        """构造套利意图并调用 pipeline.full_pipeline()。

        Args:
            chain_name: 产业链名称
            pair: 品种对
            zscore: Z-score 值
        """
        from ..llm.pipeline import LLMPipeline
        from ..notifier.feishu import DecisionFeishuNotifier

        intent = (
            f"监测到 {chain_name} {pair[0]}-{pair[1]} 价差偏离 {zscore:.1f}σ，"
            f"请生成套利策略"
        )

        try:
            # 调用 pipeline
            pipeline = LLMPipeline()
            result = await pipeline.full_pipeline(
                symbol=f"{pair[0]}-{pair[1]}",
                context={"intent": intent, "chain": chain_name, "zscore": zscore}
            )

            # 飞书推送结果摘要
            notifier = DecisionFeishuNotifier()
            await notifier.send(
                title=f"产业链套利机会 — {chain_name}",
                content=(
                    f"品种对: {pair[0]}-{pair[1]}\n"
                    f"价差偏离: {zscore:.2f}σ\n"
                    f"策略生成: {'成功' if result.get('approved') else '未通过'}"
                ),
                level="info",
                template="blue",
            )

            logger.info(f"套利意图已触发 pipeline: {intent}")

        except Exception as e:
            # pipeline 调用失败时只记录 WARNING，不重试，不影响其他监控
            logger.warning(
                f"触发 pipeline 失败 ({chain_name} {pair}): {e}",
                exc_info=True
            )

    def reset_daily_triggers(self) -> None:
        """重置每日触发记录（每日收盘后调用）。"""
        self._triggered_today.clear()
        logger.info("已重置每日触发记录")
