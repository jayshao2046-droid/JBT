#!/usr/bin/env python3
"""测试参数自适应映射器

验证：
1. 根据品种特征生成参数空间
2. 不同特征品种的参数差异
3. 参数验证逻辑
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.symbol_profiler import SymbolProfiler
from services.decision.src.research.adaptive_parameter_mapper import AdaptiveParameterMapper


async def main():
    profiler = SymbolProfiler(data_service_url="http://192.168.31.156:8105")
    mapper = AdaptiveParameterMapper()

    # 测试品种列表
    test_symbols = [
        "SHFE.rb2505",  # 螺纹钢 - Medium波动 + Weak趋势
        "DCE.p2505",    # 棕榈油 - High波动 + Weak趋势
        "SHFE.au2506",  # 黄金 - High波动 + Weak趋势
    ]

    print("=" * 80)
    print("参数自适应映射器测试")
    print("=" * 80)

    for symbol in test_symbols:
        print(f"\n{'=' * 80}")
        print(f"品种: {symbol}")
        print("=" * 80)

        # 1. 获取品种特征
        features = await profiler.calculate_features(symbol)

        if not features:
            print(f"❌ {symbol} 特征获取失败")
            continue

        print(f"\n【品种特征】")
        print(f"  波动率: {features.volatility_weighted} ({features.volatility_1y:.4f})")
        print(f"  趋势强度: {features.trend_strength_weighted} ({features.trend_strength_1y:.4f})")
        print(f"  流动性: {features.liquidity}")

        # 2. 生成参数空间
        space = mapper.generate_parameter_space(features)

        print(f"\n【参数搜索空间】")
        print(f"  ATR 入场阈值: [{space.atr_entry_min:.4f}, {space.atr_entry_max:.4f}]")
        print(f"  ATR 止损系数: [{space.atr_stop_multiplier_min:.1f}, {space.atr_stop_multiplier_max:.1f}]")
        print(f"  ADX 阈值: [{space.adx_threshold_min:.0f}, {space.adx_threshold_max:.0f}]")
        print(f"  成交量比率: [{space.volume_ratio_min:.2f}, {space.volume_ratio_max:.2f}]")
        print(f"  RSI 超卖: [{space.rsi_oversold_min}, {space.rsi_oversold_max}]")
        print(f"  RSI 超买: [{space.rsi_overbought_min}, {space.rsi_overbought_max}]")
        print(f"  持仓时间: [{space.min_holding_bars}, {space.max_holding_bars}] K线")
        print(f"  仓位比例: [{space.position_fraction_min:.2f}, {space.position_fraction_max:.2f}]")
        print(f"  止损金额: [{space.stop_loss_yuan_min}, {space.stop_loss_yuan_max}] 元")

        print(f"\n【策略类型】")
        print(f"  趋势跟踪: {'✅ 启用' if space.enable_trend_following else '❌ 关闭'}")
        print(f"  均值回归: {'✅ 启用' if space.enable_mean_reversion else '❌ 关闭'}")

        print(f"\n【市场过滤】")
        print(f"  ATR 最小值: {space.market_filter_atr_min:.4f}")
        print(f"  ADX 最小值: {space.market_filter_adx_min:.1f}")
        print(f"  成交量比率最小值: {space.market_filter_volume_ratio_min:.2f}")

        print(f"\n【生成理由】")
        print(f"  {space.reasoning}")

        # 3. 测试参数验证
        print(f"\n【参数验证测试】")

        # 测试合法参数
        valid_params = {
            "atr_entry_threshold": (space.atr_entry_min + space.atr_entry_max) / 2,
            "adx_threshold": (space.adx_threshold_min + space.adx_threshold_max) / 2,
            "volume_ratio": (space.volume_ratio_min + space.volume_ratio_max) / 2,
            "position_fraction": (space.position_fraction_min + space.position_fraction_max) / 2,
        }

        is_valid, errors = mapper.validate_parameters(valid_params, space)
        print(f"  合法参数: {valid_params}")
        print(f"  验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")

        # 测试非法参数
        invalid_params = {
            "atr_entry_threshold": space.atr_entry_max + 0.01,  # 超出范围
            "adx_threshold": space.adx_threshold_min - 5,  # 超出范围
        }

        is_valid, errors = mapper.validate_parameters(invalid_params, space)
        print(f"\n  非法参数: {invalid_params}")
        print(f"  验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        if errors:
            for error in errors:
                print(f"    ⚠️ {error}")

    print(f"\n{'=' * 80}")
    print("测试完成")
    print("=" * 80)
    print("\n【对比分析】")
    print("不同品种的参数空间应该有明显差异：")
    print("- 高波动品种（棕榈油、黄金）：ATR阈值更高，止损更大")
    print("- 中波动品种（螺纹钢）：ATR阈值适中")
    print("- 强趋势品种：启用趋势跟踪，ADX阈值更高")
    print("- 弱趋势品种：启用均值回归，ADX阈值更低")


if __name__ == "__main__":
    asyncio.run(main())
