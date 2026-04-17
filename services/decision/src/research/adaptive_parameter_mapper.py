"""参数自适应映射器 — TASK-U0-20260417-006 P2

根据品种特征动态生成参数搜索空间。

核心理念:
- 拒绝硬编码参数范围
- 根据品种特征（波动率、趋势强度、流动性）动态调整参数空间
- 避免"棕榈油跑出螺纹钢参数"的荒谬情况

映射规则:
1. 高波动品种 → ATR止损系数放大，入场阈值放宽
2. 低波动品种 → ATR止损系数缩小，入场阈值收紧
3. 强趋势品种 → 启用趋势跟踪，关闭均值回归
4. 弱趋势品种 → 启用均值回归，关闭突破过滤
5. 高流动性品种 → 允许更高频交易
6. 低流动性品种 → 限制交易频率，放宽持仓时间
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .symbol_profiler import SymbolFeatures

logger = logging.getLogger(__name__)


@dataclass
class ParameterSpace:
    """参数搜索空间"""
    # ATR 相关
    atr_entry_min: float  # ATR 入场阈值最小值
    atr_entry_max: float  # ATR 入场阈值最大值
    atr_stop_multiplier_min: float  # ATR 止损系数最小值
    atr_stop_multiplier_max: float  # ATR 止损系数最大值

    # 趋势相关
    adx_threshold_min: float  # ADX 阈值最小值
    adx_threshold_max: float  # ADX 阈值最大值
    enable_trend_following: bool  # 是否启用趋势跟踪
    enable_mean_reversion: bool  # 是否启用均值回归

    # 成交量相关
    volume_ratio_min: float  # 成交量比率最小值
    volume_ratio_max: float  # 成交量比率最大值

    # RSI 相关
    rsi_oversold_min: int  # RSI 超卖阈值最小值
    rsi_oversold_max: int  # RSI 超卖阈值最大值
    rsi_overbought_min: int  # RSI 超买阈值最小值
    rsi_overbought_max: int  # RSI 超买阈值最大值

    # 持仓时间
    min_holding_bars: int  # 最小持仓K线数
    max_holding_bars: int  # 最大持仓K线数

    # 风险管理
    position_fraction_min: float  # 仓位比例最小值
    position_fraction_max: float  # 仓位比例最大值
    stop_loss_yuan_min: int  # 止损金额最小值
    stop_loss_yuan_max: int  # 止损金额最大值

    # 市场过滤
    market_filter_atr_min: float  # 市场过滤 ATR 最小值
    market_filter_adx_min: float  # 市场过滤 ADX 最小值
    market_filter_volume_ratio_min: float  # 市场过滤成交量比率最小值

    # 元信息
    reasoning: str  # 参数空间生成理由


class AdaptiveParameterMapper:
    """参数自适应映射器

    根据品种特征动态生成参数搜索空间。
    """

    def __init__(self):
        logger.info("🎯 参数自适应映射器已启动")

    def generate_parameter_space(
        self,
        features: SymbolFeatures
    ) -> ParameterSpace:
        """根据品种特征生成参数搜索空间

        Args:
            features: 品种特征

        Returns:
            参数搜索空间
        """
        logger.info(f"🎯 为 {features.symbol} 生成参数空间...")

        # 解析特征
        volatility = features.volatility_weighted  # Low/Medium/High
        trend = features.trend_strength_weighted  # Weak/Strong
        liquidity = features.liquidity  # Low/High

        reasoning_parts = []

        # 1. 根据波动率调整 ATR 参数
        if volatility == "High":
            atr_entry_min, atr_entry_max = 0.008, 0.020
            atr_stop_multiplier_min, atr_stop_multiplier_max = 2.0, 3.5
            stop_loss_yuan_min, stop_loss_yuan_max = 1500, 3000
            reasoning_parts.append("高波动品种：ATR阈值放宽(0.008-0.020)，止损系数放大(2.0-3.5)")
        elif volatility == "Medium":
            atr_entry_min, atr_entry_max = 0.003, 0.010
            atr_stop_multiplier_min, atr_stop_multiplier_max = 1.5, 2.5
            stop_loss_yuan_min, stop_loss_yuan_max = 1000, 2000
            reasoning_parts.append("中波动品种：ATR阈值适中(0.003-0.010)，止损系数适中(1.5-2.5)")
        else:  # Low
            atr_entry_min, atr_entry_max = 0.001, 0.005
            atr_stop_multiplier_min, atr_stop_multiplier_max = 1.0, 2.0
            stop_loss_yuan_min, stop_loss_yuan_max = 500, 1500
            reasoning_parts.append("低波动品种：ATR阈值收紧(0.001-0.005)，止损系数缩小(1.0-2.0)")

        # 2. 根据趋势强度调整策略类型
        if trend == "Strong":
            adx_threshold_min, adx_threshold_max = 25, 35
            enable_trend_following = True
            enable_mean_reversion = False
            reasoning_parts.append("强趋势品种：启用趋势跟踪，ADX阈值(25-35)，关闭均值回归")
        else:  # Weak
            adx_threshold_min, adx_threshold_max = 15, 25
            enable_trend_following = False
            enable_mean_reversion = True
            reasoning_parts.append("弱趋势品种：启用均值回归，ADX阈值(15-25)，关闭趋势跟踪")

        # 3. 根据流动性调整成交量和持仓时间
        if liquidity == "High":
            volume_ratio_min, volume_ratio_max = 1.2, 2.0
            min_holding_bars, max_holding_bars = 2, 20
            position_fraction_min, position_fraction_max = 0.1, 0.3
            reasoning_parts.append("高流动性品种：成交量比率(1.2-2.0)，持仓时间短(2-20K线)，仓位可放大(0.1-0.3)")
        else:  # Low
            volume_ratio_min, volume_ratio_max = 0.8, 1.5
            min_holding_bars, max_holding_bars = 5, 50
            position_fraction_min, position_fraction_max = 0.05, 0.15
            reasoning_parts.append("低流动性品种：成交量比率放宽(0.8-1.5)，持仓时间长(5-50K线)，仓位保守(0.05-0.15)")

        # 4. RSI 参数（根据趋势调整）
        if trend == "Strong":
            rsi_oversold_min, rsi_oversold_max = 40, 50
            rsi_overbought_min, rsi_overbought_max = 50, 60
            reasoning_parts.append("强趋势品种：RSI阈值中性(40-60)，避免逆势交易")
        else:  # Weak
            rsi_oversold_min, rsi_oversold_max = 20, 35
            rsi_overbought_min, rsi_overbought_max = 65, 80
            reasoning_parts.append("弱趋势品种：RSI阈值极端(20-35/65-80)，捕捉超买超卖")

        # 5. 市场过滤（必须比入场条件更宽松）
        market_filter_atr_min = atr_entry_min * 0.3  # 市场过滤 ATR 是入场的 30%
        market_filter_adx_min = adx_threshold_min * 0.6  # 市场过滤 ADX 是入场的 60%
        market_filter_volume_ratio_min = volume_ratio_min * 0.7  # 市场过滤成交量是入场的 70%
        reasoning_parts.append(
            f"市场过滤条件比入场条件更宽松：ATR={market_filter_atr_min:.4f}, "
            f"ADX={market_filter_adx_min:.1f}, VolumeRatio={market_filter_volume_ratio_min:.2f}"
        )

        reasoning = " | ".join(reasoning_parts)

        parameter_space = ParameterSpace(
            atr_entry_min=atr_entry_min,
            atr_entry_max=atr_entry_max,
            atr_stop_multiplier_min=atr_stop_multiplier_min,
            atr_stop_multiplier_max=atr_stop_multiplier_max,
            adx_threshold_min=adx_threshold_min,
            adx_threshold_max=adx_threshold_max,
            enable_trend_following=enable_trend_following,
            enable_mean_reversion=enable_mean_reversion,
            volume_ratio_min=volume_ratio_min,
            volume_ratio_max=volume_ratio_max,
            rsi_oversold_min=rsi_oversold_min,
            rsi_oversold_max=rsi_oversold_max,
            rsi_overbought_min=rsi_overbought_min,
            rsi_overbought_max=rsi_overbought_max,
            min_holding_bars=min_holding_bars,
            max_holding_bars=max_holding_bars,
            position_fraction_min=position_fraction_min,
            position_fraction_max=position_fraction_max,
            stop_loss_yuan_min=stop_loss_yuan_min,
            stop_loss_yuan_max=stop_loss_yuan_max,
            market_filter_atr_min=market_filter_atr_min,
            market_filter_adx_min=market_filter_adx_min,
            market_filter_volume_ratio_min=market_filter_volume_ratio_min,
            reasoning=reasoning
        )

        logger.info(f"✅ 参数空间已生成: {features.symbol}")
        logger.info(f"   理由: {reasoning}")

        return parameter_space

    def validate_parameters(
        self,
        parameters: dict,
        space: ParameterSpace
    ) -> tuple[bool, list[str]]:
        """验证参数是否在搜索空间内

        Args:
            parameters: 待验证的参数
            space: 参数搜索空间

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        # 验证 ATR 参数
        if "atr_entry_threshold" in parameters:
            val = parameters["atr_entry_threshold"]
            if not (space.atr_entry_min <= val <= space.atr_entry_max):
                errors.append(
                    f"ATR入场阈值 {val} 超出范围 [{space.atr_entry_min}, {space.atr_entry_max}]"
                )

        # 验证 ADX 参数
        if "adx_threshold" in parameters:
            val = parameters["adx_threshold"]
            if not (space.adx_threshold_min <= val <= space.adx_threshold_max):
                errors.append(
                    f"ADX阈值 {val} 超出范围 [{space.adx_threshold_min}, {space.adx_threshold_max}]"
                )

        # 验证成交量比率
        if "volume_ratio" in parameters:
            val = parameters["volume_ratio"]
            if not (space.volume_ratio_min <= val <= space.volume_ratio_max):
                errors.append(
                    f"成交量比率 {val} 超出范围 [{space.volume_ratio_min}, {space.volume_ratio_max}]"
                )

        # 验证仓位比例
        if "position_fraction" in parameters:
            val = parameters["position_fraction"]
            if not (space.position_fraction_min <= val <= space.position_fraction_max):
                errors.append(
                    f"仓位比例 {val} 超出范围 [{space.position_fraction_min}, {space.position_fraction_max}]"
                )

        return len(errors) == 0, errors
