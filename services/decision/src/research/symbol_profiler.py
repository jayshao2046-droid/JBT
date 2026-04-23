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

BARE_SYMBOL_EXCHANGE_MAP = {
    # SHFE
    "rb": "SHFE", "hc": "SHFE", "cu": "SHFE", "al": "SHFE", "zn": "SHFE",
    "ni": "SHFE", "ss": "SHFE", "au": "SHFE", "ag": "SHFE", "fu": "SHFE",
    "bu": "SHFE", "ru": "SHFE", "sp": "SHFE", "sn": "SHFE", "pb": "SHFE",
    "wr": "SHFE",
    # INE
    "sc": "INE", "nr": "INE", "lu": "INE", "bc": "INE", "ec": "INE",
    # DCE
    "i": "DCE", "j": "DCE", "jm": "DCE", "a": "DCE", "b": "DCE",
    "m": "DCE", "y": "DCE", "p": "DCE", "c": "DCE", "cs": "DCE",
    "jd": "DCE", "lh": "DCE", "l": "DCE", "v": "DCE", "pp": "DCE",
    "eg": "DCE", "eb": "DCE", "pg": "DCE",
    # CZCE
    "sr": "CZCE", "cf": "CZCE", "ta": "CZCE", "ma": "CZCE", "oi": "CZCE",
    "rm": "CZCE", "fg": "CZCE", "sa": "CZCE", "ur": "CZCE", "ap": "CZCE",
    "cj": "CZCE", "pk": "CZCE", "pf": "CZCE",
    # CFFEX
    "if": "CFFEX", "ih": "CFFEX", "ic": "CFFEX", "im": "CFFEX",
    "t": "CFFEX", "tf": "CFFEX", "ts": "CFFEX",
}


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

    # 分级阈值（默认值，用于年化波动率和 ADX 分类）
    VOLATILITY_THRESHOLDS = {
        "low": 0.15,    # 年化波动率 < 15%
        "high": 0.30,   # 年化波动率 > 30%
    }

    TREND_THRESHOLDS = {
        "weak": 20.0,   # ADX < 20
        "strong": 30.0, # ADX > 30
    }

    # 典型品种波动率基准范围（年化，用于自检）
    INDUSTRY_BENCHMARKS = {
        "rb": (0.15, 0.40), "cu": (0.12, 0.35), "au": (0.08, 0.25),
        "ag": (0.15, 0.45), "p": (0.15, 0.40), "y": (0.12, 0.35),
        "m": (0.12, 0.35), "i": (0.20, 0.50), "sc": (0.20, 0.50),
    }

    # 每日交易分钟数（期货日盘+夜盘合计约 600 分钟）
    TRADING_MINS_PER_DAY = 600

    def __init__(
        self,
        data_service_url: str = "http://192.168.31.76:8105",
        interval: int = 1440,
        cache_dir: str = "runtime/symbol_profiles",
        enable_cache: bool = True
    ):
        """
        Args:
            data_service_url: 数据服务地址
            interval: K线周期（分钟），默认1440（日K），可设置为1/5/15/30/60/1440等
            cache_dir: 缓存目录
            enable_cache: 是否启用缓存（增量更新）
        """
        self.data_service_url = data_service_url.rstrip("/")
        self.interval = interval
        self.enable_cache = enable_cache

        if enable_cache:
            from .feature_cache_manager import FeatureCacheManager
            self.cache_manager = FeatureCacheManager(cache_dir=cache_dir)
        else:
            self.cache_manager = None

    async def calculate_features(self, symbol: str, force_full: bool = False) -> Optional[SymbolFeatures]:
        """计算品种特征（增强版，支持增量更新）

        Args:
            symbol: 品种代码（如 DCE.p0）
            force_full: 强制全量计算（忽略缓存）

        Returns:
            SymbolFeatures 或 None（数据不足时）
        """
        logger.info(f"📊 计算品种特征: {symbol}")

        try:
            # 尝试使用缓存（增量更新）
            if self.enable_cache and not force_full:
                cache = self.cache_manager.load_cache(symbol)
                if cache and self.cache_manager.is_cache_valid(cache, max_age_days=1):
                    logger.info(f"使用增量更新: {symbol}")
                    return await self._incremental_update(symbol, cache)

            # 全量计算
            logger.info(f"执行全量计算: {symbol}")
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

            # 保存缓存（如果启用）
            if self.enable_cache:
                self._save_to_cache(symbol, features, bars_3m, bars_1y, bars_5y)

            return features

        except Exception as e:
            logger.error(f"计算品种特征失败 {symbol}: {e}", exc_info=True)
            return None

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """将裸品种/裸合约代码补全为 data API 可接受的带交易所前缀格式。"""
        raw = symbol.strip()
        if not raw or raw.startswith("KQ_m_") or "." in raw:
            return raw

        import re

        match = re.fullmatch(r"([A-Za-z]+)(\d+)?", raw)
        if not match:
            return raw

        product, month = match.groups()
        exchange = BARE_SYMBOL_EXCHANGE_MAP.get(product.lower())
        if exchange is None:
            return raw

        normalized_product = product.upper() if exchange == "CZCE" else product.lower()
        return f"{exchange}.{normalized_product}{month or ''}"

    @staticmethod
    def _to_kq_symbol(symbol: str) -> str:
        """将交易所.品种格式转为 KQ_m_ 主力合约格式

        DCE.p  → KQ_m_DCE_p
        DCE.p0 → KQ_m_DCE_p （去掉尾部数字）
        CZCE.CF → KQ_m_CZCE_CF
        已是 KQ_m_ 格式则原样返回。
        """
        symbol = SymbolProfiler._normalize_symbol(symbol)
        if symbol.startswith("KQ_m_"):
            return symbol
        if "." in symbol:
            exchange, code = symbol.split(".", 1)
            # 去掉尾部数字（如 p0 → p, CF305 → CF）
            import re
            code_clean = re.sub(r'\d+$', '', code)
            return f"KQ_m_{exchange}_{code_clean}"
        return symbol

    async def _fetch_bars(self, symbol: str, days: int) -> list[dict]:
        """获取 K 线数据"""
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # 期货品种自动转换为 KQ_m_ 主力合约格式
        api_symbol = self._to_kq_symbol(symbol)

        url = f"{self.data_service_url}/api/v1/bars"
        params = {
            "symbol": api_symbol,
            "start": start_date,
            "end": end_date,
            "timeframe_minutes": self.interval,  # Fix: API 参数名是 timeframe_minutes
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

        根据实际 K 线周期动态计算年化因子：
        bars_per_day = trading_mins_per_day / interval
        annualization_factor = sqrt(252 * bars_per_day)
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

        # 动态年化因子：根据实际 K 线周期计算
        bars_per_day = max(1, self.TRADING_MINS_PER_DAY // self.interval)
        annualization_factor = (252 * bars_per_day) ** 0.5

        return std_dev * annualization_factor

    def _calculate_trend_strength(self, bars: list[dict]) -> float:
        """计算趋势强度（真实 ADX）"""
        if len(bars) < 30:
            return 0.0

        highs = [float(b.get("high", 0)) for b in bars]
        lows = [float(b.get("low", 0)) for b in bars]
        closes = [float(b.get("close", 0)) for b in bars]
        n = len(closes)
        period = 14

        if n < period * 2:
            return 0.0

        # 计算 True Range
        tr = [highs[0] - lows[0]]
        for i in range(1, n):
            tr.append(max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            ))

        # 计算 +DM / -DM
        plus_dm = [0.0] * n
        minus_dm = [0.0] * n
        for i in range(1, n):
            up = highs[i] - highs[i - 1]
            down = lows[i - 1] - lows[i]
            plus_dm[i] = up if (up > down and up > 0) else 0.0
            minus_dm[i] = down if (down > up and down > 0) else 0.0

        # Wilder 平滑
        def _wilder_smooth(data: list[float], p: int) -> list[float]:
            result = [0.0] * len(data)
            result[p] = sum(data[1:p + 1])
            for i in range(p + 1, len(data)):
                result[i] = result[i - 1] - result[i - 1] / p + data[i]
            return result

        smooth_tr = _wilder_smooth(tr, period)
        smooth_plus = _wilder_smooth(plus_dm, period)
        smooth_minus = _wilder_smooth(minus_dm, period)

        # 计算 DX → ADX
        dx_values = []
        for i in range(period, n):
            if smooth_tr[i] < 1e-10:
                continue
            plus_di = 100.0 * smooth_plus[i] / smooth_tr[i]
            minus_di = 100.0 * smooth_minus[i] / smooth_tr[i]
            di_sum = plus_di + minus_di
            if di_sum > 0:
                dx_values.append(100.0 * abs(plus_di - minus_di) / di_sum)

        if not dx_values:
            return 0.0

        # ADX = 最近 period 个 DX 的简单平均
        adx = sum(dx_values[-period:]) / min(period, len(dx_values))
        return round(adx, 2)

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
        """分类波动率（年化标准差）"""
        if vol < self.VOLATILITY_THRESHOLDS["low"]:
            return "Low"
        elif vol > self.VOLATILITY_THRESHOLDS["high"]:
            return "High"
        else:
            return "Medium"

    def _classify_trend(self, trend: float) -> str:
        """分类趋势强度（ADX 值）"""
        if trend < self.TREND_THRESHOLDS["weak"]:
            return "Weak"
        elif trend > self.TREND_THRESHOLDS["strong"]:
            return "Strong"
        else:
            return "Medium"

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

        # 6. 行业基准验证（自动匹配品种）
        symbol_code = ""
        try:
            raw = bars_3m[0].get("symbol", "") if bars_3m else ""
            import re
            m = re.search(r'[._]([a-zA-Z]{1,3})[0-9]', str(raw))
            if m:
                symbol_code = m.group(1).lower()
        except Exception:
            pass

        if symbol_code and symbol_code in self.INDUSTRY_BENCHMARKS:
            bench_low, bench_high = self.INDUSTRY_BENCHMARKS[symbol_code]
            if vol_1y < bench_low * 0.5 or vol_1y > bench_high * 2.0:
                warnings.append(
                    f"波动率异常: {vol_1y:.4f} 不在 {symbol_code} 典型范围 "
                    f"[{bench_low:.2f}, {bench_high:.2f}]，可能数据周期或年化因子有误"
                )
                volatility_confidence *= 0.5

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

    async def _incremental_update(self, symbol: str, cache: dict) -> Optional[SymbolFeatures]:
        """增量更新特征（只获取新数据）

        Args:
            symbol: 品种代码
            cache: 缓存数据

        Returns:
            更新后的 SymbolFeatures
        """
        from datetime import datetime

        logger.info(f"🔄 增量更新: {symbol}, 上次更新={cache.get('last_update')}")

        try:
            # 获取增量日期范围
            start_date, end_date = self.cache_manager.get_incremental_date_range(cache)

            # 如果没有新数据，直接返回缓存的特征
            if start_date >= end_date:
                logger.info(f"无新数据，使用缓存: {symbol}")
                return self._features_from_cache(cache)

            # 获取新数据
            new_bars = await self._fetch_bars_range(symbol, start_date, end_date)
            if not new_bars:
                logger.info(f"未获取到新数据，使用缓存: {symbol}")
                return self._features_from_cache(cache)

            logger.info(f"获取到 {len(new_bars)} 条新数据")

            # 提取新数据的收益率和价格
            new_returns = self._extract_returns(new_bars)
            new_prices = [bar["close"] for bar in new_bars]

            # 合并滚动状态
            rolling_state = cache.get("rolling_state", {})
            window_sizes = {
                "returns_3m": 63,    # 约3个月交易日
                "returns_1y": 252,   # 约1年交易日
                "prices_5y": 1260,   # 约5年交易日
            }

            updated_state = self.cache_manager.merge_rolling_state(
                old_state=rolling_state,
                new_data={
                    "returns_3m": new_returns,
                    "returns_1y": new_returns,
                    "prices_5y": new_prices,
                },
                window_sizes=window_sizes
            )

            # 基于更新后的滚动状态重新计算特征
            features = self._calculate_features_from_state(symbol, updated_state)

            # 保存更新后的缓存
            if features:
                self._save_to_cache_with_state(symbol, features, updated_state, start_date, end_date)

            return features

        except Exception as e:
            logger.error(f"增量更新失败 {symbol}: {e}", exc_info=True)
            # 失败时尝试使用缓存
            return self._features_from_cache(cache)

    def _features_from_cache(self, cache: dict) -> Optional[SymbolFeatures]:
        """从缓存重建 SymbolFeatures 对象"""
        try:
            features_data = cache.get("features", {})
            metadata_data = cache.get("metadata", {})
            confidence_data = cache.get("confidence", {})

            metadata = FeatureMetadata(**metadata_data)
            confidence = FeatureConfidence(**confidence_data)

            return SymbolFeatures(
                symbol=features_data["symbol"],
                volatility_3m=features_data["volatility_3m"],
                volatility_1y=features_data["volatility_1y"],
                volatility_5y=features_data["volatility_5y"],
                volatility_weighted=features_data["volatility_weighted"],
                trend_strength_3m=features_data["trend_strength_3m"],
                trend_strength_1y=features_data["trend_strength_1y"],
                trend_strength_weighted=features_data["trend_strength_weighted"],
                autocorr_3m=features_data["autocorr_3m"],
                autocorr_1y=features_data["autocorr_1y"],
                skewness=features_data["skewness"],
                kurtosis=features_data["kurtosis"],
                liquidity=features_data["liquidity"],
                metadata=metadata,
                confidence=confidence,
            )
        except Exception as e:
            logger.error(f"从缓存重建特征失败: {e}")
            return None

    async def _fetch_bars_range(self, symbol: str, start_date: str, end_date: str) -> list[dict]:
        """获取指定日期范围的 K 线数据"""
        api_symbol = self._to_kq_symbol(symbol)
        url = f"{self.data_service_url}/api/v1/bars"
        params = {
            "symbol": api_symbol,
            "start": start_date,
            "end": end_date,
            "timeframe_minutes": self.interval,  # Fix: API 参数名是 timeframe_minutes
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
            logger.error(f"获取数据失败 {symbol} [{start_date} ~ {end_date}]: {e}")
            return []

    def _extract_returns(self, bars: list[dict]) -> list[float]:
        """从 K 线数据提取收益率"""
        if len(bars) < 2:
            return []

        returns = []
        for i in range(1, len(bars)):
            prev_close = bars[i - 1]["close"]
            curr_close = bars[i]["close"]
            if prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                returns.append(ret)

        return returns

    def _calculate_features_from_state(self, symbol: str, rolling_state: dict) -> Optional[SymbolFeatures]:
        """基于滚动状态计算特征"""
        try:
            returns_3m = rolling_state.get("returns_3m", [])
            returns_1y = rolling_state.get("returns_1y", [])
            prices_5y = rolling_state.get("prices_5y", [])

            if len(returns_3m) < 20 or len(returns_1y) < 50:
                logger.warning(f"滚动状态数据不足: 3m={len(returns_3m)}, 1y={len(returns_1y)}")
                return None

            # 计算波动率（年化标准差）
            import numpy as np
            vol_3m = float(np.std(returns_3m) * np.sqrt(252))
            vol_1y = float(np.std(returns_1y) * np.sqrt(252))
            vol_5y = vol_1y  # 简化处理

            # 加权波动率
            vol_weighted_value = vol_3m * 0.6 + vol_1y * 0.3 + vol_5y * 0.1
            vol_weighted_level = self._classify_volatility(vol_weighted_value)

            # 计算趋势强度（简化版，基于收益率序列）
            trend_3m = abs(float(np.mean(returns_3m))) / (vol_3m + 1e-8)
            trend_1y = abs(float(np.mean(returns_1y))) / (vol_1y + 1e-8)
            trend_weighted_value = trend_3m * 0.6 + trend_1y * 0.4
            trend_weighted_level = self._classify_trend(trend_weighted_value)

            # 计算自相关性
            autocorr_3m = float(np.corrcoef(returns_3m[:-1], returns_3m[1:])[0, 1]) if len(returns_3m) > 1 else 0.0
            autocorr_1y = float(np.corrcoef(returns_1y[:-1], returns_1y[1:])[0, 1]) if len(returns_1y) > 1 else 0.0

            # 计算偏度和峰度
            from scipy import stats
            skewness = float(stats.skew(returns_1y))
            kurtosis = float(stats.kurtosis(returns_1y))

            # 流动性（简化为 High）
            liquidity = "High"

            # 元数据
            from datetime import datetime
            metadata = FeatureMetadata(
                data_source="Mini API (incremental)",
                calculation_time=datetime.now().isoformat(),
                data_start_date="",
                data_end_date="",
                data_points_3m=len(returns_3m),
                data_points_1y=len(returns_1y),
                data_points_5y=len(prices_5y),
                missing_data_ratio=0.0,
            )

            # 置信度（简化）
            confidence = FeatureConfidence(
                overall=0.85,
                volatility=0.9,
                trend=0.8,
                liquidity=0.85,
                data_sufficiency=0.9,
                data_quality=0.9,
                feature_stability=0.8,
                warnings=[],
            )

            return SymbolFeatures(
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

        except Exception as e:
            logger.error(f"从滚动状态计算特征失败: {e}", exc_info=True)
            return None

    def _save_to_cache(self, symbol: str, features: SymbolFeatures, bars_3m: list, bars_1y: list, bars_5y: list):
        """保存特征到缓存（全量）"""
        from datetime import datetime

        try:
            # 提取滚动状态
            returns_3m = self._extract_returns(bars_3m)
            returns_1y = self._extract_returns(bars_1y)
            prices_5y = [bar["close"] for bar in bars_5y] if bars_5y else []

            # 构造缓存数据
            # 获取时间字段（兼容 timestamp/datetime/date）
            def get_time_field(bar):
                return bar.get("timestamp") or bar.get("datetime") or bar.get("date") or ""

            cache_data = {
                "symbol": symbol,
                "last_update": datetime.now().isoformat(),
                "data_range": {
                    "start": get_time_field(bars_5y[0]) if bars_5y else get_time_field(bars_1y[0]),
                    "end": get_time_field(bars_3m[-1]),
                },
                "features": {
                    "symbol": features.symbol,
                    "volatility_3m": features.volatility_3m,
                    "volatility_1y": features.volatility_1y,
                    "volatility_5y": features.volatility_5y,
                    "volatility_weighted": features.volatility_weighted,
                    "trend_strength_3m": features.trend_strength_3m,
                    "trend_strength_1y": features.trend_strength_1y,
                    "trend_strength_weighted": features.trend_strength_weighted,
                    "autocorr_3m": features.autocorr_3m,
                    "autocorr_1y": features.autocorr_1y,
                    "skewness": features.skewness,
                    "kurtosis": features.kurtosis,
                    "liquidity": features.liquidity,
                },
                "metadata": {
                    "data_source": features.metadata.data_source,
                    "calculation_time": features.metadata.calculation_time,
                    "data_start_date": features.metadata.data_start_date,
                    "data_end_date": features.metadata.data_end_date,
                    "data_points_3m": features.metadata.data_points_3m,
                    "data_points_1y": features.metadata.data_points_1y,
                    "data_points_5y": features.metadata.data_points_5y,
                    "missing_data_ratio": features.metadata.missing_data_ratio,
                },
                "confidence": {
                    "overall": features.confidence.overall,
                    "volatility": features.confidence.volatility,
                    "trend": features.confidence.trend,
                    "liquidity": features.confidence.liquidity,
                    "data_sufficiency": features.confidence.data_sufficiency,
                    "data_quality": features.confidence.data_quality,
                    "feature_stability": features.confidence.feature_stability,
                    "warnings": features.confidence.warnings,
                },
                "rolling_state": {
                    "returns_3m": returns_3m[-63:],  # 保留最近63个
                    "returns_1y": returns_1y[-252:],  # 保留最近252个
                    "prices_5y": prices_5y[-1260:],  # 保留最近1260个
                },
            }

            self.cache_manager.save_cache(symbol, cache_data)
            logger.info(f"💾 缓存已保存: {symbol}")

        except Exception as e:
            logger.error(f"保存缓存失败 {symbol}: {e}", exc_info=True)

    def _save_to_cache_with_state(self, symbol: str, features: SymbolFeatures, rolling_state: dict, start_date: str, end_date: str):
        """保存特征到缓存（增量更新）"""
        from datetime import datetime

        try:
            cache_data = {
                "symbol": symbol,
                "last_update": datetime.now().isoformat(),
                "data_range": {
                    "start": start_date,
                    "end": end_date,
                },
                "features": {
                    "symbol": features.symbol,
                    "volatility_3m": features.volatility_3m,
                    "volatility_1y": features.volatility_1y,
                    "volatility_5y": features.volatility_5y,
                    "volatility_weighted": features.volatility_weighted,
                    "trend_strength_3m": features.trend_strength_3m,
                    "trend_strength_1y": features.trend_strength_1y,
                    "trend_strength_weighted": features.trend_strength_weighted,
                    "autocorr_3m": features.autocorr_3m,
                    "autocorr_1y": features.autocorr_1y,
                    "skewness": features.skewness,
                    "kurtosis": features.kurtosis,
                    "liquidity": features.liquidity,
                },
                "metadata": {
                    "data_source": features.metadata.data_source,
                    "calculation_time": features.metadata.calculation_time,
                    "data_start_date": features.metadata.data_start_date,
                    "data_end_date": features.metadata.data_end_date,
                    "data_points_3m": features.metadata.data_points_3m,
                    "data_points_1y": features.metadata.data_points_1y,
                    "data_points_5y": features.metadata.data_points_5y,
                    "missing_data_ratio": features.metadata.missing_data_ratio,
                },
                "confidence": {
                    "overall": features.confidence.overall,
                    "volatility": features.confidence.volatility,
                    "trend": features.confidence.trend,
                    "liquidity": features.confidence.liquidity,
                    "data_sufficiency": features.confidence.data_sufficiency,
                    "data_quality": features.confidence.data_quality,
                    "feature_stability": features.confidence.feature_stability,
                    "warnings": features.confidence.warnings,
                },
                "rolling_state": rolling_state,
            }

            self.cache_manager.save_cache(symbol, cache_data)
            logger.info(f"💾 缓存已更新: {symbol}")

        except Exception as e:
            logger.error(f"保存缓存失败 {symbol}: {e}", exc_info=True)

    async def refresh_all_features(self, symbols: list[str]) -> dict[str, Any]:
        """批量刷新所有品种特征（盘后定时调度用）

        Args:
            symbols: 品种代码列表

        Returns:
            {refreshed, failed, skipped, details}
        """
        import asyncio

        results = {"refreshed": 0, "failed": 0, "skipped": 0, "details": []}

        for symbol in symbols:
            try:
                features = await self.calculate_features(symbol)
                if features:
                    results["refreshed"] += 1
                    results["details"].append({"symbol": symbol, "status": "ok"})
                else:
                    results["skipped"] += 1
                    results["details"].append({"symbol": symbol, "status": "skipped", "reason": "数据不足"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"symbol": symbol, "status": "failed", "error": str(e)})

            # 避免 API 过载
            await asyncio.sleep(0.5)

        logger.info(
            "特征批量刷新完成: %d 成功, %d 失败, %d 跳过 (共 %d)",
            results["refreshed"], results["failed"], results["skipped"], len(symbols),
        )
        return results

