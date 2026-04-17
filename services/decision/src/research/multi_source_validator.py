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
from typing import Optional

from .symbol_profiler import SymbolProfiler, SymbolFeatures

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
        """从 Tushare 获取特征（简化版）

        注意：这里需要实现 Tushare 数据获取逻辑。
        当前返回 None，表示暂不支持。
        """
        # TODO: 实现 Tushare 数据获取
        logger.warning("Tushare 数据源暂未实现")
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
