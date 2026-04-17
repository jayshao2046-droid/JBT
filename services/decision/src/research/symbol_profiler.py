"""品种统计特征画像器 — TASK-U0-20260417-004

计算品种的统计特征，用于指导参数映射和策略设计。

核心功能:
- 滚动窗口特征计算（3个月/1年/5年）
- 加权分级（短期 60% + 中期 30% + 长期 10%）
- 特征分类（Low/Medium/High）

特征维度:
- 波动率（Volatility）
- 趋势强度（Trend Strength）
- 自相关性（Autocorrelation）
- 偏度（Skewness）
- 峰度（Kurtosis）
- 流动性（Liquidity）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SymbolFeatures:
    """品种特征"""
    symbol: str

    # 波动率
    volatility_3m: float
    volatility_1y: float
    volatility_5y: float
    volatility_weighted: str  # Low/Medium/High

    # 趋势强度
    trend_strength_3m: float
    trend_strength_1y: float
    trend_strength_weighted: str  # Weak/Strong

    # 自相关性
    autocorr_3m: float
    autocorr_1y: float

    # 偏度和峰度
    skewness: float
    kurtosis: float

    # 流动性
    liquidity: str  # Low/High


class SymbolProfiler:
    """品种统计特征画像器

    使用滚动窗口计算品种特征，避免"用5年前的市场特征指导今天的交易"。
    """

    # 分级阈值
    VOLATILITY_THRESHOLDS = {
        "low": 0.01,    # ATR/Close < 1%
        "high": 0.02,   # ATR/Close > 2%
    }

    TREND_THRESHOLDS = {
        "weak": 0.3,    # ADX < 30
        "strong": 0.5,  # ADX > 50
    }

    def __init__(self, data_service_url: str = "http://192.168.31.76:8105"):
        self.data_service_url = data_service_url.rstrip("/")

    async def calculate_features(self, symbol: str) -> Optional[SymbolFeatures]:
        """计算品种特征

        Args:
            symbol: 品种代码（如 DCE.p0）

        Returns:
            SymbolFeatures 或 None（数据不足时）
        """
        logger.info(f"📊 计算品种特征: {symbol}")

        try:
            # 获取不同时间窗口的数据
            bars_3m = await self._fetch_bars(symbol, days=90)
            bars_1y = await self._fetch_bars(symbol, days=252)
            bars_5y = await self._fetch_bars(symbol, days=1260)

            if not bars_3m or not bars_1y:
                logger.warning(f"品种 {symbol} 数据不足")
                return None

            # 计算波动率
            vol_3m = self._calculate_volatility(bars_3m)
            vol_1y = self._calculate_volatility(bars_1y)
            vol_5y = self._calculate_volatility(bars_5y) if bars_5y else vol_1y

            # 加权波动率（短期 60% + 中期 30% + 长期 10%）
            vol_weighted_value = vol_3m * 0.6 + vol_1y * 0.3 + vol_5y * 0.1
            vol_weighted_level = self._classify_volatility(vol_weighted_value)

            # 计算趋势强度
            trend_3m = self._calculate_trend_strength(bars_3m)
            trend_1y = self._calculate_trend_strength(bars_1y)

            # 加权趋势强度
            trend_weighted_value = trend_3m * 0.6 + trend_1y * 0.4
            trend_weighted_level = self._classify_trend(trend_weighted_value)

            # 计算自相关性
            autocorr_3m = self._calculate_autocorr(bars_3m)
            autocorr_1y = self._calculate_autocorr(bars_1y)

            # 计算偏度和峰度
            skewness = self._calculate_skewness(bars_1y)
            kurtosis = self._calculate_kurtosis(bars_1y)

            # 计算流动性
            liquidity = self._classify_liquidity(bars_3m)

            features = SymbolFeatures(
                symbol=symbol,
                volatility_3m=vol_3m,
                volatility_1y=vol_1y,
                volatility_5y=vol_5y,
                volatility_weighted=vol_weighted_level,
                trend_strength_3m=trend_3m,
                trend_strength_1y=trend_1y,
                trend_strength_weighted=trend_weighted_level,
                autocorr_3m=autocorr_3m,
                autocorr_1y=autocorr_1y,
                skewness=skewness,
                kurtosis=kurtosis,
                liquidity=liquidity,
            )

            logger.info(
                f"✅ {symbol} 特征: "
                f"波动率={vol_weighted_level}, "
                f"趋势={trend_weighted_level}, "
                f"流动性={liquidity}"
            )

            return features

        except Exception as e:
            logger.error(f"计算品种特征失败 {symbol}: {e}", exc_info=True)
            return None

    async def _fetch_bars(self, symbol: str, days: int) -> list[dict]:
        """获取 K 线数据"""
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        url = f"{self.data_service_url}/api/v1/bars"
        params = {
            "symbol": symbol,
            "start": start_date,
            "end": end_date,
            "interval": 60,  # 60分钟
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()

            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("bars", data.get("data", []))

        except Exception as e:
            logger.error(f"获取数据失败 {symbol}: {e}")
            return []

    def _calculate_volatility(self, bars: list[dict]) -> float:
        """计算波动率（ATR / Close）"""
        if len(bars) < 20:
            return 0.0

        closes = [float(b.get("close", 0)) for b in bars]
        highs = [float(b.get("high", 0)) for b in bars]
        lows = [float(b.get("low", 0)) for b in bars]

        # 简化版 ATR
        tr_sum = 0.0
        for i in range(1, len(bars)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            tr_sum += tr

        atr = tr_sum / (len(bars) - 1)
        avg_close = sum(closes) / len(closes)

        return atr / avg_close if avg_close > 0 else 0.0

    def _calculate_trend_strength(self, bars: list[dict]) -> float:
        """计算趋势强度（简化版 ADX）"""
        if len(bars) < 20:
            return 0.0

        closes = [float(b.get("close", 0)) for b in bars]

        # 简化版: 使用线性回归斜率的绝对值
        n = len(closes)
        x_mean = (n - 1) / 2
        y_mean = sum(closes) / n

        numerator = sum((i - x_mean) * (closes[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        trend_strength = abs(slope) / y_mean if y_mean > 0 else 0.0

        return min(trend_strength * 100, 1.0)  # 归一化到 [0, 1]

    def _calculate_autocorr(self, bars: list[dict]) -> float:
        """计算自相关性（lag=1）"""
        if len(bars) < 20:
            return 0.0

        closes = [float(b.get("close", 0)) for b in bars]
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]

        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)

        # 计算 lag=1 自相关
        numerator = sum(
            (returns[i] - mean_return) * (returns[i - 1] - mean_return)
            for i in range(1, len(returns))
        )
        denominator = sum((r - mean_return) ** 2 for r in returns)

        return numerator / denominator if denominator > 0 else 0.0

    def _calculate_skewness(self, bars: list[dict]) -> float:
        """计算偏度"""
        if len(bars) < 20:
            return 0.0

        closes = [float(b.get("close", 0)) for b in bars]
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]

        if len(returns) < 3:
            return 0.0

        n = len(returns)
        mean_return = sum(returns) / n
        std_return = (sum((r - mean_return) ** 2 for r in returns) / n) ** 0.5

        if std_return == 0:
            return 0.0

        skewness = (
            sum((r - mean_return) ** 3 for r in returns) / n
        ) / (std_return ** 3)

        return skewness

    def _calculate_kurtosis(self, bars: list[dict]) -> float:
        """计算峰度"""
        if len(bars) < 20:
            return 0.0

        closes = [float(b.get("close", 0)) for b in bars]
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]

        if len(returns) < 4:
            return 0.0

        n = len(returns)
        mean_return = sum(returns) / n
        std_return = (sum((r - mean_return) ** 2 for r in returns) / n) ** 0.5

        if std_return == 0:
            return 0.0

        kurtosis = (
            sum((r - mean_return) ** 4 for r in returns) / n
        ) / (std_return ** 4)

        return kurtosis - 3  # 超额峰度

    def _classify_volatility(self, vol: float) -> str:
        """分类波动率"""
        if vol < self.VOLATILITY_THRESHOLDS["low"]:
            return "Low"
        elif vol > self.VOLATILITY_THRESHOLDS["high"]:
            return "High"
        else:
            return "Medium"

    def _classify_trend(self, trend: float) -> str:
        """分类趋势强度"""
        if trend < self.TREND_THRESHOLDS["weak"]:
            return "Weak"
        else:
            return "Strong"

    def _classify_liquidity(self, bars: list[dict]) -> str:
        """分类流动性（基于成交量）"""
        if len(bars) < 20:
            return "Low"

        volumes = [float(b.get("volume", 0)) for b in bars]
        avg_volume = sum(volumes) / len(volumes)

        # 简化版: 平均成交量 > 10000 为高流动性
        return "High" if avg_volume > 10000 else "Low"
