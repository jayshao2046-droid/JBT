#!/usr/bin/env python3
"""测试增强版 SymbolProfiler

验证：
1. 数据溯源记录
2. 置信度评分
3. 特征稳定性检查
4. 行业基准验证
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.symbol_profiler import SymbolProfiler


async def main():
    profiler = SymbolProfiler(data_service_url="http://192.168.31.76:8105")

    # 测试品种列表
    test_symbols = [
        "SHFE.rb2505",  # 螺纹钢
        "DCE.p2505",    # 棕榈油
        "SHFE.au2506",  # 黄金
    ]

    print("=" * 80)
    print("增强版 SymbolProfiler 测试")
    print("=" * 80)

    for symbol in test_symbols:
        print(f"\n{'=' * 80}")
        print(f"品种: {symbol}")
        print("=" * 80)

        features = await profiler.calculate_features(symbol)

        if not features:
            print(f"❌ {symbol} 特征计算失败")
            continue

        # 输出特征
        print(f"\n【特征画像】")
        print(f"  波动率: {features.volatility_weighted} (3M={features.volatility_3m:.4f}, 1Y={features.volatility_1y:.4f}, 5Y={features.volatility_5y:.4f})")
        print(f"  趋势强度: {features.trend_strength_weighted} (3M={features.trend_strength_3m:.4f}, 1Y={features.trend_strength_1y:.4f})")
        print(f"  流动性: {features.liquidity}")
        print(f"  自相关性: 3M={features.autocorr_3m:.4f}, 1Y={features.autocorr_1y:.4f}")
        print(f"  偏度: {features.skewness:.4f}")
        print(f"  峰度: {features.kurtosis:.4f}")

        # 输出元数据
        print(f"\n【数据溯源】")
        print(f"  数据源: {features.metadata.data_source}")
        print(f"  计算时间: {features.metadata.calculation_time}")
        print(f"  数据范围: {features.metadata.data_start_date} ~ {features.metadata.data_end_date}")
        print(f"  数据点数: 3M={features.metadata.data_points_3m}, 1Y={features.metadata.data_points_1y}, 5Y={features.metadata.data_points_5y}")
        print(f"  缺失率: {features.metadata.missing_data_ratio:.2%}")

        # 输出置信度
        print(f"\n【置信度评分】")
        print(f"  总体置信度: {features.confidence.overall:.2f}")
        print(f"  波动率置信度: {features.confidence.volatility:.2f}")
        print(f"  趋势置信度: {features.confidence.trend:.2f}")
        print(f"  流动性置信度: {features.confidence.liquidity:.2f}")
        print(f"\n  影响因素:")
        print(f"    数据充足性: {features.confidence.data_sufficiency:.2f}")
        print(f"    数据质量: {features.confidence.data_quality:.2f}")
        print(f"    特征稳定性: {features.confidence.feature_stability:.2f}")

        # 输出警告
        if features.confidence.warnings:
            print(f"\n【警告信息】")
            for warning in features.confidence.warnings:
                print(f"  ⚠️ {warning}")
        else:
            print(f"\n✅ 无警告，特征可信")

        # 判断是否可用
        if features.confidence.overall >= 0.7:
            print(f"\n✅ 特征置信度 {features.confidence.overall:.2f} >= 0.7，可用于策略生成")
        else:
            print(f"\n❌ 特征置信度 {features.confidence.overall:.2f} < 0.7，不建议用于策略生成")

    print(f"\n{'=' * 80}")
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
