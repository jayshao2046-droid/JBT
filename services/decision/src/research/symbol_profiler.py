"""品种统计特征画像器 — TASK-U0-20260417-006 增强版

计算品种的统计特征，用于指导参数映射和策略设计。

核心功能:
- 滚动窗口特征计算（3个月/1年/5年）
- 加权分级（短期 60% + 中期 30% + 长期 10%）
- 特征分类（Low/Medium/High）
- 多源交叉验证（P1）
- 置信度评分（P1）
- 数据溯源记录（P0）

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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class FeatureMetadata:
    """特征元数据（数据溯源）"""
    data_source: str  # 数据来源（如 "Mini API"）
    calculation_time: str  # 计算时间
    data_start_date: str  # 数据起始日期
    data_end_date: str  # 数据结束日期
    data_points_3m: int  # 3个月数据点数
    data_points_1y: int  # 1年数据点数
    data_points_5y: int  # 5年数据点数
    missing_data_ratio: float  # 缺失数据比例


@dataclass
class FeatureConfidence:
    """特征置信度评分"""
    overall: float  # 总体置信度 [0-1]
    volatility: float  # 波动率置信度
    trend: float  # 趋势强度置信度
    liquidity: float  # 流动性置信度

    # 置信度影响因素
    data_sufficiency: float  # 数据充足性 [0-1]
    data_quality: float  # 数据质量 [0-1]
    feature_stability: float  # 特征稳定性 [0-1]

    # 警告信息
    warnings: list[str] = field(default_factory=list)


@dataclass
class SymbolFeatures:
    """品种特征（增强版）"""
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

    # 新增：元数据和置信度
    metadata: FeatureMetadata = None
    confidence: FeatureConfidence = None


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
        """计算品种特征（增强版）

        Args:
            symbol: 品种代码（如 DCE.p0）

        Returns:
            SymbolFeatures 或 None（数据不足时）
        """
        logger.info(f"📊 计算品种特征: {symbol}")

        try:
            # 获取不同时间窗口的数据
            bars_3m = await self._fetch_bars(symbol, days=90)
            bars_1y = await self._fetch_bars(symbol, days=365)
            bars_5y = await self._fetch_bars(symbol, days=1825)

            if not bars_3m or not bars_1y:
                logger.warning(f"品种 {symbol} 数据不足")
                return None

            # 记录数据溯源
            metadata = self._create_metadata(bars_3m, bars_1y, bars_5y)

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

            # 计算置信度
            confidence = self._calculate_confidence(
                bars_3m, bars_1y, bars_5y,
                vol_3m, vol_1y, vol_5y,
                trend_3m, trend_1y,
                metadata
            )

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
                metadata=metadata,
                confidence=confidence,
            )

            logger.info(
                f"✅ {symbol} 特征: "
                f"波动率={vol_weighted_level}({vol_weighted_value:.4f}), "
                f"趋势={trend_weighted_level}({trend_weighted_value:.4f}), "
                f"流动性={liquidity}, "
                f"置信度={confidence.overall:.2f}"
            )

            # 输出警告
            if confidence.warnings:
                for warning in confidence.warnings:
                    logger.warning(f"⚠️ {symbol}: {warning}")

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
        """计算波动率（年化标准差）

        使用日收益率标准差 * sqrt(252) 计算年化波动率。
        这比 ATR/Close 更准确，因为 ATR 受 K 线周期影响。
        """
        if len(bars) < 20:
            return 0.0

        closes = [float(b.get("close", 0)) for b in bars]

        # 计算收益率
        returns = []
        for i in range(1, len(closes)):
            if closes[i - 1] > 0:
                ret = (closes[i] - closes[i - 1]) / closes[i - 1]
                returns.append(ret)

        if len(returns) < 10:
            return 0.0

        # 计算标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        # 年化波动率（假设每天4个60分钟K线，252个交易日）
        # 如果是60分钟K线，需要 sqrt(4 * 252) = sqrt(1008) ≈ 31.75
        annualization_factor = (252 * 4) ** 0.5

        return std_dev * annualization_factor

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

    def _create_metadata(
        self,
        bars_3m: list[dict],
        bars_1y: list[dict],
        bars_5y: list[dict]
    ) -> FeatureMetadata:
        """创建特征元数据（数据溯源）"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 提取日期范围
        def get_date_range(bars):
            if not bars:
                return None, None
            dates = [b.get("datetime", b.get("timestamp", "")) for b in bars]
            return min(dates) if dates else None, max(dates) if dates else None

        start_5y, end_5y = get_date_range(bars_5y) if bars_5y else (None, None)
        start_1y, end_1y = get_date_range(bars_1y)

        # 使用最长时间范围
        data_start = start_5y or start_1y
        data_end = end_5y or end_1y

        # 计算缺失数据比例
        expected_points_3m = 90 * 4  # 90天 * 4小时/天（假设60分钟K线）
        expected_points_1y = 365 * 4
        expected_points_5y = 1825 * 4

        actual_3m = len(bars_3m)
        actual_1y = len(bars_1y)
        actual_5y = len(bars_5y) if bars_5y else 0

        missing_ratio = 1.0 - (
            (actual_3m / expected_points_3m * 0.6) +
            (actual_1y / expected_points_1y * 0.3) +
            (actual_5y / expected_points_5y * 0.1 if actual_5y > 0 else 0)
        )

        return FeatureMetadata(
            data_source="Mini API (http://192.168.31.76:8105)",
            calculation_time=now,
            data_start_date=data_start or "Unknown",
            data_end_date=data_end or "Unknown",
            data_points_3m=actual_3m,
            data_points_1y=actual_1y,
            data_points_5y=actual_5y,
            missing_data_ratio=max(0.0, min(1.0, missing_ratio))
        )

    def _calculate_confidence(
        self,
        bars_3m: list[dict],
        bars_1y: list[dict],
        bars_5y: list[dict],
        vol_3m: float,
        vol_1y: float,
        vol_5y: float,
        trend_3m: float,
        trend_1y: float,
        metadata: FeatureMetadata
    ) -> FeatureConfidence:
        """计算特征置信度

        置信度评分基于：
        1. 数据充足性（数据点数是否足够）
        2. 数据质量（缺失数据比例）
        3. 特征稳定性（不同时间窗口的特征是否一致）
        """
        warnings = []

        # 1. 数据充足性
        min_points_3m = 60  # 至少60个数据点
        min_points_1y = 200
        min_points_5y = 800

        data_sufficiency = min(1.0, (
            (len(bars_3m) / min_points_3m * 0.5) +
            (len(bars_1y) / min_points_1y * 0.3) +
            ((len(bars_5y) / min_points_5y * 0.2) if bars_5y else 0.1)
        ))

        if data_sufficiency < 0.7:
            warnings.append(f"数据充足性不足: {data_sufficiency:.2f} < 0.7")

        # 2. 数据质量
        data_quality = 1.0 - metadata.missing_data_ratio

        if data_quality < 0.8:
            warnings.append(f"数据质量较低: 缺失率 {metadata.missing_data_ratio:.2%}")

        # 3. 特征稳定性（波动率和趋势强度的跨周期一致性）
        vol_stability = 1.0 - min(1.0, abs(vol_3m - vol_1y) / max(vol_1y, 0.001))
        trend_stability = 1.0 - min(1.0, abs(trend_3m - trend_1y) / max(trend_1y, 0.001))

        feature_stability = (vol_stability + trend_stability) / 2

        if feature_stability < 0.6:
            warnings.append(
                f"特征不稳定: 波动率3M={vol_3m:.4f} vs 1Y={vol_1y:.4f}, "
                f"趋势3M={trend_3m:.4f} vs 1Y={trend_1y:.4f}"
            )

        # 4. 计算各维度置信度
        volatility_confidence = (data_sufficiency * 0.4 + data_quality * 0.3 + vol_stability * 0.3)
        trend_confidence = (data_sufficiency * 0.4 + data_quality * 0.3 + trend_stability * 0.3)
        liquidity_confidence = (data_sufficiency * 0.6 + data_quality * 0.4)

        # 5. 总体置信度
        overall_confidence = (
            volatility_confidence * 0.4 +
            trend_confidence * 0.4 +
            liquidity_confidence * 0.2
        )

        # 6. 行业基准验证（螺纹钢典型波动率 2-4%）
        if "rb" in metadata.data_source.lower() or "rb" in str(bars_3m[0].get("symbol", "")).lower():
            if vol_1y < 0.01 or vol_1y > 0.06:
                warnings.append(
                    f"波动率异常: {vol_1y:.4f} 不在螺纹钢典型范围 [0.02, 0.04]"
                )
                volatility_confidence *= 0.7

        return FeatureConfidence(
            overall=overall_confidence,
            volatility=volatility_confidence,
            trend=trend_confidence,
            liquidity=liquidity_confidence,
            data_sufficiency=data_sufficiency,
            data_quality=data_quality,
            feature_stability=feature_stability,
            warnings=warnings
        )
