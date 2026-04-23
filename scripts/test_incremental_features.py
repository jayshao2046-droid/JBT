#!/usr/bin/env python3
"""测试 SymbolProfiler 增量更新功能"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.decision.src.research.symbol_profiler import SymbolProfiler


async def test_full_calculation():
    """测试全量计算"""
    print("=" * 80)
    print("测试 1: 全量计算（首次计算）")
    print("=" * 80)

    profiler = SymbolProfiler(
        data_service_url="http://192.168.31.156:8105",
        interval=1440,  # 日K线
        enable_cache=True
    )

    symbol = "SHFE.rb0"
    print(f"\n计算品种: {symbol}")

    # 强制全量计算
    features = await profiler.calculate_features(symbol, force_full=True)

    if features:
        print(f"\n✅ 全量计算成功")
        print(f"  波动率: 3M={features.volatility_3m:.4f}, 1Y={features.volatility_1y:.4f}")
        print(f"  趋势强度: 3M={features.trend_strength_3m:.4f}, 1Y={features.trend_strength_1y:.4f}")
        print(f"  置信度: {features.confidence.overall:.2f}")
        print(f"  数据点: 3M={features.metadata.data_points_3m}, 1Y={features.metadata.data_points_1y}")
    else:
        print(f"\n❌ 全量计算失败")

    return features


async def test_incremental_update():
    """测试增量更新"""
    print("\n" + "=" * 80)
    print("测试 2: 增量更新（使用缓存）")
    print("=" * 80)

    profiler = SymbolProfiler(
        data_service_url="http://192.168.31.156:8105",
        interval=1440,
        enable_cache=True
    )

    symbol = "SHFE.rb0"
    print(f"\n计算品种: {symbol}")

    # 使用缓存（增量更新）
    features = await profiler.calculate_features(symbol, force_full=False)

    if features:
        print(f"\n✅ 增量更新成功")
        print(f"  波动率: 3M={features.volatility_3m:.4f}, 1Y={features.volatility_1y:.4f}")
        print(f"  趋势强度: 3M={features.trend_strength_3m:.4f}, 1Y={features.trend_strength_1y:.4f}")
        print(f"  置信度: {features.confidence.overall:.2f}")
        print(f"  数据来源: {features.metadata.data_source}")
    else:
        print(f"\n❌ 增量更新失败")

    return features


async def test_cache_stats():
    """测试缓存统计"""
    print("\n" + "=" * 80)
    print("测试 3: 缓存统计")
    print("=" * 80)

    from services.decision.src.research.feature_cache_manager import FeatureCacheManager

    cache_manager = FeatureCacheManager(cache_dir="runtime/symbol_profiles")
    stats = cache_manager.get_cache_stats()

    print(f"\n缓存目录: {stats['cache_dir']}")
    print(f"总品种数: {stats['total_symbols']}")
    print(f"有效缓存: {stats['valid_caches']}")
    print(f"过期缓存: {stats['expired_caches']}")

    if stats['total_symbols'] > 0:
        symbols = cache_manager.list_all_cached_symbols()
        print(f"\n已缓存品种: {', '.join(symbols[:10])}")
        if len(symbols) > 10:
            print(f"  ... 还有 {len(symbols) - 10} 个品种")


async def test_multiple_symbols():
    """测试多个品种"""
    print("\n" + "=" * 80)
    print("测试 4: 批量计算（3个品种）")
    print("=" * 80)

    profiler = SymbolProfiler(
        data_service_url="http://192.168.31.156:8105",
        interval=1440,
        enable_cache=True
    )

    symbols = ["SHFE.rb0", "DCE.i0", "CZCE.MA0"]

    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] 计算 {symbol}...")
        features = await profiler.calculate_features(symbol, force_full=False)

        if features:
            print(f"  ✅ 波动率={features.volatility_weighted}({features.volatility_1y:.4f}), "
                  f"趋势={features.trend_strength_weighted}({features.trend_strength_1y:.4f})")
        else:
            print(f"  ❌ 计算失败")


async def main():
    print("=" * 80)
    print("SymbolProfiler 增量更新功能测试")
    print("=" * 80)
    print(f"数据源: Mini API (http://192.168.31.156:8105)")
    print(f"K线周期: 日K线 (1440分钟)")
    print(f"缓存目录: runtime/symbol_profiles/")
    print("=" * 80)

    try:
        # 测试 1: 全量计算
        await test_full_calculation()

        # 测试 2: 增量更新
        await test_incremental_update()

        # 测试 3: 缓存统计
        await test_cache_stats()

        # 测试 4: 批量计算
        await test_multiple_symbols()

        print("\n" + "=" * 80)
        print("✅ 所有测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
