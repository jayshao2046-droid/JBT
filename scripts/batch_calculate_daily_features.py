#!/usr/bin/env python3
"""批量计算35个期货品种的日K线特征"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.decision.src.research.symbol_profiler import SymbolProfiler

# 35个期货品种（主力连续合约）
SYMBOLS = [
    # 上期所 (SHFE)
    "SHFE.cu0", "SHFE.al0", "SHFE.zn0", "SHFE.pb0", "SHFE.ni0", "SHFE.sn0", "SHFE.au0",
    "SHFE.ag0", "SHFE.rb0", "SHFE.wr0", "SHFE.hc0", "SHFE.ss0", "SHFE.fu0", "SHFE.bu0",
    "SHFE.ru0", "SHFE.sp0", "SHFE.sc0",

    # 大商所 (DCE)
    "DCE.c0", "DCE.cs0", "DCE.a0", "DCE.b0", "DCE.m0", "DCE.y0", "DCE.p0", "DCE.l0",
    "DCE.v0", "DCE.pp0", "DCE.j0", "DCE.jm0", "DCE.i0", "DCE.eg0", "DCE.eb0", "DCE.pg0",

    # 郑商所 (CZCE)
    "CZCE.SR0", "CZCE.CF0",
]


async def main():
    print("=" * 80)
    print("批量计算35个期货品种的日K线特征")
    print("=" * 80)
    print(f"数据源: Mini API (http://192.168.31.156:8105)")
    print(f"K线周期: 日K线 (1440分钟)")
    print(f"品种数量: {len(SYMBOLS)}")
    print("=" * 80)
    print()

    # 使用日K线（1440分钟）
    profiler = SymbolProfiler(
        data_service_url="http://192.168.31.156:8105",
        interval=1440  # 日K线
    )

    results = []
    failed = []

    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"[{i}/{len(SYMBOLS)}] 处理 {symbol}...")

        try:
            features = await profiler.calculate_features(symbol)

            if features:
                results.append(features)

                # 检查特征稳定性
                vol_diff = abs(features.volatility_3m - features.volatility_1y)
                vol_ratio = vol_diff / features.volatility_1y if features.volatility_1y > 0 else 0

                stability_flag = "⚠️ 不稳定" if vol_ratio > 0.3 else "✅ 稳定"

                print(f"  波动率: 3M={features.volatility_3m:.4f}, 1Y={features.volatility_1y:.4f}, "
                      f"差异={vol_ratio:.1%} {stability_flag}")
                print(f"  趋势强度: 3M={features.trend_strength_3m:.4f}, 1Y={features.trend_strength_1y:.4f}")
                print(f"  置信度: {features.confidence.overall:.2f}")
                print()
            else:
                failed.append(symbol)
                print(f"  ❌ 数据不足或计算失败")
                print()

        except Exception as e:
            failed.append(symbol)
            print(f"  ❌ 异常: {e}")
            print()

    # 汇总报告
    print("=" * 80)
    print("汇总报告")
    print("=" * 80)
    print(f"成功: {len(results)}/{len(SYMBOLS)}")
    print(f"失败: {len(failed)}/{len(SYMBOLS)}")

    if failed:
        print(f"\n失败品种: {', '.join(failed)}")

    # 统计特征不稳定的品种
    unstable = []
    for f in results:
        vol_diff = abs(f.volatility_3m - f.volatility_1y)
        vol_ratio = vol_diff / f.volatility_1y if f.volatility_1y > 0 else 0
        if vol_ratio > 0.3:
            unstable.append((f.symbol, vol_ratio))

    if unstable:
        print(f"\n特征不稳定品种 ({len(unstable)}):")
        for symbol, ratio in sorted(unstable, key=lambda x: x[1], reverse=True):
            print(f"  {symbol}: 波动率差异 {ratio:.1%}")

    # 按波动率分类统计
    low_vol = [f for f in results if f.volatility_weighted == "Low"]
    med_vol = [f for f in results if f.volatility_weighted == "Medium"]
    high_vol = [f for f in results if f.volatility_weighted == "High"]

    print(f"\n波动率分布:")
    print(f"  Low: {len(low_vol)} 品种")
    print(f"  Medium: {len(med_vol)} 品种")
    print(f"  High: {len(high_vol)} 品种")

    print("\n✅ 批量计算完成")


if __name__ == "__main__":
    asyncio.run(main())
