"""多源交叉验证器 — TASK-U0-20260417-006 P1

对品种特征进行多源交叉验证，确保数据可信度。

验证流程:
1. 从多个数据源计算相同特征
2. 比较不同数据源的结果
3. 如果差异过大，降低置信度或拒绝使用
4. 输出交叉验证报告

数据源:
- Mini API (主要)
- Tushare (交叉验证)
- TQSDK (可选)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from .symbol_profiler import SymbolProfiler, SymbolFeatures, FeatureMetadata, FeatureConfidence

logger = logging.getLogger(__name__)


@dataclass
class CrossValidationReport:
    """交叉验证报告"""
    symbol: str
    primary_source: str  # 主数据源
    validation_sources: list[str]  # 验证数据源

    # 特征一致性
    volatility_consistency: float  # 波动率一致性 [0-1]
    trend_consistency: float  # 趋势一致性 [0-1]
    overall_consistency: float  # 总体一致性 [0-1]

    # 差异详情
    volatility_diff: dict[str, float]  # 各数据源波动率差异
    trend_diff: dict[str, float]  # 各数据源趋势差异

    # 验证结果
    is_valid: bool  # 是否通过验证
    warnings: list[str]  # 警告信息
    recommendation: str  # 建议


class MultiSourceValidator:
    """多源交叉验证器

    从多个数据源计算品种特征，交叉验证确保数据可信度。
    """

    # 一致性阈值
    VOLATILITY_TOLERANCE = 0.005  # 波动率容差：0.5%
    TREND_TOLERANCE = 0.1  # 趋势强度容差：0.1
    CONSISTENCY_THRESHOLD = 0.7  # 一致性阈值：70%

    def __init__(
        self,
        mini_api_url: str = "http://192.168.31.76:8105",
        tushare_token: Optional[str] = None,
    ):
        self.mini_profiler = SymbolProfiler(data_service_url=mini_api_url)
        self.tushare_token = tushare_token

    async def validate_features(
        self,
        symbol: str,
        enable_tushare: bool = True,
    ) -> tuple[Optional[SymbolFeatures], CrossValidationReport]:
        """交叉验证品种特征

        Args:
            symbol: 品种代码
            enable_tushare: 是否启用 Tushare 验证

        Returns:
            (最终特征, 交叉验证报告)
        """
        logger.info(f"🔍 开始多源交叉验证: {symbol}")

        # 1. 从主数据源（Mini API）获取特征
        primary_features = await self.mini_profiler.calculate_features(symbol)

        if not primary_features:
            logger.error(f"主数据源获取失败: {symbol}")
            return None, self._create_failed_report(symbol, "主数据源获取失败")

        # 2. 从验证数据源获取特征
        validation_sources = []
        validation_features = {}

        if enable_tushare and self.tushare_token:
            tushare_features = await self._get_tushare_features(symbol)
            if tushare_features:
                validation_sources.append("Tushare")
                validation_features["Tushare"] = tushare_features

        # 如果没有验证数据源，直接返回主数据源结果
        if not validation_sources:
            logger.warning(f"⚠️ 无验证数据源，仅使用主数据源: {symbol}")
            return primary_features, self._create_single_source_report(symbol, primary_features)

        # 3. 交叉验证
        report = self._cross_validate(
            symbol,
            primary_features,
            validation_features
        )

        # 4. 根据验证结果调整置信度
        if report.is_valid:
            # 验证通过，提升置信度
            primary_features.confidence.overall = min(
                1.0,
                primary_features.confidence.overall * (1.0 + report.overall_consistency * 0.1)
            )
            logger.info(f"✅ 交叉验证通过，置信度提升至 {primary_features.confidence.overall:.2f}")
        else:
            # 验证失败，降低置信度
            primary_features.confidence.overall *= 0.7
            primary_features.confidence.warnings.extend(report.warnings)
            logger.warning(f"⚠️ 交叉验证失败，置信度降低至 {primary_features.confidence.overall:.2f}")

        return primary_features, report

    async def _get_tushare_features(self, symbol: str) -> Optional[SymbolFeatures]:
        """从 Tushare 获取期货日线并计算品种特征。

        仅获取主力合约日线数据，计算波动率/趋势/流动性等指标，
        与 Mini API 主数据源做交叉验证。
        """
        try:
            import tushare as ts
        except ImportError:
            logger.warning("tushare 未安装，跳过交叉验证")
            return None

        try:
            pro = ts.pro_api(self.tushare_token)

            # 期货主力合约代码映射：JBT symbol -> Tushare ts_code
            ts_code = f"{symbol.upper()}.ZCE"  # 默认郑商所
            exchange_map = {
                "au": "SHFE", "ag": "SHFE", "cu": "SHFE", "al": "SHFE",
                "zn": "SHFE", "pb": "SHFE", "ni": "SHFE", "sn": "SHFE",
                "rb": "SHFE", "hc": "SHFE", "ss": "SHFE", "bu": "SHFE",
                "ru": "SHFE", "fu": "SHFE", "sp": "SHFE", "nr": "SHFE",
                "sc": "INE", "lu": "INE", "bc": "INE", "ec": "INE",
                "i": "DCE", "j": "DCE", "jm": "DCE", "a": "DCE",
                "b": "DCE", "m": "DCE", "y": "DCE", "p": "DCE",
                "c": "DCE", "cs": "DCE", "jd": "DCE", "lh": "DCE",
                "l": "DCE", "v": "DCE", "pp": "DCE", "eg": "DCE",
                "eb": "DCE", "pg": "DCE",
                "sr": "ZCE", "cf": "ZCE", "ta": "ZCE", "ma": "ZCE",
                "oi": "ZCE", "rm": "ZCE", "fg": "ZCE", "sa": "ZCE",
                "ur": "ZCE", "ap": "ZCE", "cj": "ZCE", "pk": "ZCE",
                "if": "CFFEX", "ih": "CFFEX", "ic": "CFFEX", "im": "CFFEX",
                "t": "CFFEX", "tf": "CFFEX", "ts": "CFFEX",
            }
            sym_lower = symbol.lower()
            exchange = exchange_map.get(sym_lower, "ZCE")
            ts_code = f"{symbol.upper()}.{exchange}"

            # 拉取最近 5 年日线
            end_dt = datetime.now()
            start_5y = (end_dt - timedelta(days=365 * 5)).strftime("%Y%m%d")
            end_str = end_dt.strftime("%Y%m%d")

            df = pro.fut_daily(ts_code=ts_code, start_date=start_5y, end_date=end_str)
            if df is None or df.empty:
                # 尝试主力连续合约
                df = pro.fut_daily(ts_code=f"{symbol.upper()}99.{exchange}",
                                   start_date=start_5y, end_date=end_str)
            if df is None or df.empty:
                logger.warning("Tushare 未获取到 %s 日线数据", symbol)
                return None

            df = df.sort_values("trade_date").reset_index(drop=True)
            close = df["close"].values.astype(float)
            vol = df["vol"].values.astype(float) if "vol" in df.columns else np.zeros(len(close))

            if len(close) < 60:
                logger.warning("Tushare %s 数据量不足（%d 条），跳过", symbol, len(close))
                return None

            # 收益率
            returns = np.diff(np.log(close))

            # 各期间切片
            n_3m = min(63, len(returns))
            n_1y = min(252, len(returns))

            ret_3m = returns[-n_3m:]
            ret_1y = returns[-n_1y:]
            ret_all = returns

            # 波动率（年化）
            vol_3m = float(np.std(ret_3m) * np.sqrt(252))
            vol_1y = float(np.std(ret_1y) * np.sqrt(252))
            vol_5y = float(np.std(ret_all) * np.sqrt(252))

            # 趋势强度（线性回归 R²）
            def _trend_r2(r: np.ndarray) -> float:
                if len(r) < 5:
                    return 0.0
                x = np.arange(len(r), dtype=float)
                cum = np.cumsum(r)
                ss_tot = np.sum((cum - cum.mean()) ** 2)
                if ss_tot < 1e-12:
                    return 0.0
                slope, intercept = np.polyfit(x, cum, 1)
                fitted = slope * x + intercept
                ss_res = np.sum((cum - fitted) ** 2)
                return float(max(0.0, 1.0 - ss_res / ss_tot))

            trend_3m = _trend_r2(ret_3m)
            trend_1y = _trend_r2(ret_1y)

            # 自相关
            def _autocorr(r: np.ndarray, lag: int = 1) -> float:
                if len(r) < lag + 2:
                    return 0.0
                c = np.corrcoef(r[lag:], r[:-lag])
                return float(c[0, 1]) if not np.isnan(c[0, 1]) else 0.0

            autocorr_3m = _autocorr(ret_3m)
            autocorr_1y = _autocorr(ret_1y)

            # 偏度 & 峰度
            skewness = float(np.mean((ret_1y - ret_1y.mean()) ** 3) / (np.std(ret_1y) ** 3 + 1e-12))
            kurtosis = float(np.mean((ret_1y - ret_1y.mean()) ** 4) / (np.std(ret_1y) ** 4 + 1e-12))

            # 流动性（用成交量均值判断）
            avg_vol = float(np.mean(vol[-n_1y:])) if np.any(vol > 0) else 0.0
            liquidity = "High" if avg_vol > 50000 else "Low"

            # 波动率分类
            if vol_1y > 0.3:
                vol_weighted = "High"
            elif vol_1y > 0.15:
                vol_weighted = "Medium"
            else:
                vol_weighted = "Low"

            # 趋势分类
            trend_weighted = "Strong" if trend_1y > 0.3 else "Weak"

            now_str = datetime.now().isoformat()
            metadata = FeatureMetadata(
                data_source="Tushare",
                calculation_time=now_str,
                data_start_date=df["trade_date"].iloc[0],
                data_end_date=df["trade_date"].iloc[-1],
                data_points_3m=n_3m,
                data_points_1y=n_1y,
                data_points_5y=len(returns),
                missing_data_ratio=0.0,
            )
            confidence = FeatureConfidence(
                overall=0.7,
                volatility=0.8 if n_1y >= 200 else 0.5,
                trend=0.7 if n_1y >= 200 else 0.4,
                liquidity=0.6,
                data_sufficiency=min(1.0, len(returns) / 252),
                data_quality=0.7,
                feature_stability=0.6,
                warnings=["Tushare 交叉验证源"],
            )

            return SymbolFeatures(
                symbol=symbol,
                volatility_3m=vol_3m,
                volatility_1y=vol_1y,
                volatility_5y=vol_5y,
                volatility_weighted=vol_weighted,
                trend_strength_3m=trend_3m,
                trend_strength_1y=trend_1y,
                trend_strength_weighted=trend_weighted,
                autocorr_3m=autocorr_3m,
                autocorr_1y=autocorr_1y,
                skewness=skewness,
                kurtosis=kurtosis,
                liquidity=liquidity,
                metadata=metadata,
                confidence=confidence,
            )

        except Exception as exc:
            logger.warning("Tushare 特征计算异常 (%s): %s", symbol, exc)
            return None

    def _cross_validate(
        self,
        symbol: str,
        primary: SymbolFeatures,
        validation: dict[str, SymbolFeatures]
    ) -> CrossValidationReport:
        """执行交叉验证"""
        warnings = []

        # 计算波动率差异
        volatility_diff = {}
        volatility_diffs = []

        for source, features in validation.items():
            diff = abs(primary.volatility_1y - features.volatility_1y)
            volatility_diff[source] = diff
            volatility_diffs.append(diff)

            if diff > self.VOLATILITY_TOLERANCE:
                warnings.append(
                    f"波动率差异过大: Mini={primary.volatility_1y:.4f} vs "
                    f"{source}={features.volatility_1y:.4f} (差异={diff:.4f})"
                )

        # 计算趋势差异
        trend_diff = {}
        trend_diffs = []

        for source, features in validation.items():
            diff = abs(primary.trend_strength_1y - features.trend_strength_1y)
            trend_diff[source] = diff
            trend_diffs.append(diff)

            if diff > self.TREND_TOLERANCE:
                warnings.append(
                    f"趋势强度差异过大: Mini={primary.trend_strength_1y:.4f} vs "
                    f"{source}={features.trend_strength_1y:.4f} (差异={diff:.4f})"
                )

        # 计算一致性
        volatility_consistency = 1.0 - min(1.0, sum(volatility_diffs) / len(volatility_diffs) / self.VOLATILITY_TOLERANCE)
        trend_consistency = 1.0 - min(1.0, sum(trend_diffs) / len(trend_diffs) / self.TREND_TOLERANCE)
        overall_consistency = (volatility_consistency + trend_consistency) / 2

        # 判断是否通过验证
        is_valid = overall_consistency >= self.CONSISTENCY_THRESHOLD

        # 生成建议
        if is_valid:
            recommendation = "数据源一致性良好，特征可信"
        elif overall_consistency >= 0.5:
            recommendation = "数据源存在差异，建议谨慎使用"
        else:
            recommendation = "数据源差异过大，不建议使用"

        return CrossValidationReport(
            symbol=symbol,
            primary_source="Mini API",
            validation_sources=list(validation.keys()),
            volatility_consistency=volatility_consistency,
            trend_consistency=trend_consistency,
            overall_consistency=overall_consistency,
            volatility_diff=volatility_diff,
            trend_diff=trend_diff,
            is_valid=is_valid,
            warnings=warnings,
            recommendation=recommendation
        )

    def _create_failed_report(self, symbol: str, reason: str) -> CrossValidationReport:
        """创建失败报告"""
        return CrossValidationReport(
            symbol=symbol,
            primary_source="Mini API",
            validation_sources=[],
            volatility_consistency=0.0,
            trend_consistency=0.0,
            overall_consistency=0.0,
            volatility_diff={},
            trend_diff={},
            is_valid=False,
            warnings=[reason],
            recommendation="数据获取失败，无法验证"
        )

    def _create_single_source_report(
        self,
        symbol: str,
        features: SymbolFeatures
    ) -> CrossValidationReport:
        """创建单数据源报告"""
        return CrossValidationReport(
            symbol=symbol,
            primary_source="Mini API",
            validation_sources=[],
            volatility_consistency=1.0,
            trend_consistency=1.0,
            overall_consistency=1.0,
            volatility_diff={},
            trend_diff={},
            is_valid=True,
            warnings=["仅使用单一数据源，未进行交叉验证"],
            recommendation="建议启用多数据源交叉验证以提升可信度"
        )
