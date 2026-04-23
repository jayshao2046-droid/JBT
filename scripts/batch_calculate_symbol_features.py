#!/usr/bin/env python3
"""批量计算 35 个品种的特征画像

输出：
1. 每个品种的特征 JSON 文件
2. 汇总报告（CSV 格式）
3. 置信度低于 0.7 的品种列表
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.symbol_profiler import SymbolProfiler


# 35 个品种列表
SYMBOLS = [
    # 黑色系
    "SHFE.rb2505",  # 螺纹钢
    "DCE.i2505",    # 铁矿石
    "DCE.j2505",    # 焦炭
    "DCE.jm2505",   # 焦煤
    "SHFE.hc2505",  # 热轧卷板

    # 有色金属
    "SHFE.cu2505",  # 铜
    "SHFE.al2505",  # 铝
    "SHFE.zn2505",  # 锌
    "SHFE.pb2505",  # 铅
    "SHFE.ni2505",  # 镍
    "SHFE.sn2505",  # 锡

    # 贵金属
    "SHFE.au2506",  # 黄金
    "SHFE.ag2506",  # 白银

    # 能源化工
    "SHFE.fu2505",  # 燃料油
    "SHFE.bu2506",  # 沥青
    "SHFE.ru2505",  # 橡胶
    "DCE.l2505",    # 塑料
    "DCE.v2505",    # PVC
    "DCE.pp2505",   # 聚丙烯
    "DCE.eg2505",   # 乙二醇
    "DCE.eb2505",   # 苯乙烯
    "DCE.pg2505",   # 液化石油气

    # 农产品
    "DCE.m2505",    # 豆粕
    "DCE.y2505",    # 豆油
    "DCE.a2505",    # 豆一
    "DCE.b2505",    # 豆二
    "DCE.p2505",    # 棕榈油
    "DCE.c2505",    # 玉米
    "DCE.cs2505",   # 玉米淀粉
    "CZCE.SR505",   # 白糖
    "CZCE.CF505",   # 棉花
    "CZCE.TA505",   # PTA
    "CZCE.MA505",   # 甲醇
    "CZCE.RM505",   # 菜粕
    "CZCE.OI505",   # 菜油
]


async def main():
    profiler = SymbolProfiler(data_service_url="http://192.168.31.74:8105")

    # 创建输出目录
    output_dir = Path("runtime/symbol_profiles")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"批量计算 {len(SYMBOLS)} 个品种的特征画像")
    print("=" * 80)
    print(f"数据源: Mini API (http://192.168.31.74:8105)")
    print(f"输出目录: {output_dir}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = []
    low_confidence_symbols = []
    failed_symbols = []

    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{i}/{len(SYMBOLS)}] 处理 {symbol}...")

        try:
            features = await profiler.calculate_features(symbol)

            if not features:
                print(f"  ❌ 失败：数据不足")
                failed_symbols.append(symbol)
                continue

            # 保存 JSON
            output_file = output_dir / f"{symbol.replace('.', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
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
                    }
                }, f, indent=2, ensure_ascii=False)

            # 记录结果
            results.append({
                "symbol": symbol,
                "volatility": features.volatility_weighted,
                "volatility_1y": features.volatility_1y,
                "trend": features.trend_strength_weighted,
                "liquidity": features.liquidity,
                "confidence": features.confidence.overall,
                "warnings": len(features.confidence.warnings),
            })

            # 检查置信度
            if features.confidence.overall < 0.7:
                low_confidence_symbols.append((symbol, features.confidence.overall))
                print(f"  ⚠️ 置信度低: {features.confidence.overall:.2f}")
            else:
                print(f"  ✅ 成功: 置信度 {features.confidence.overall:.2f}")

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            failed_symbols.append(symbol)

    # 生成汇总报告
    print(f"\n{'=' * 80}")
    print("汇总报告")
    print("=" * 80)

    # 保存 CSV
    csv_file = output_dir / "summary.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("品种,波动率分级,波动率1Y,趋势强度,流动性,置信度,警告数\n")
        for r in results:
            f.write(f"{r['symbol']},{r['volatility']},{r['volatility_1y']:.4f},"
                   f"{r['trend']},{r['liquidity']},{r['confidence']:.2f},{r['warnings']}\n")

    print(f"\n总计: {len(SYMBOLS)} 个品种")
    print(f"  ✅ 成功: {len(results)} 个")
    print(f"  ❌ 失败: {len(failed_symbols)} 个")
    print(f"  ⚠️ 低置信度 (<0.7): {len(low_confidence_symbols)} 个")

    if low_confidence_symbols:
        print(f"\n低置信度品种:")
        for symbol, conf in low_confidence_symbols:
            print(f"  - {symbol}: {conf:.2f}")

    if failed_symbols:
        print(f"\n失败品种:")
        for symbol in failed_symbols:
            print(f"  - {symbol}")

    print(f"\n输出文件:")
    print(f"  - JSON: {output_dir}/*.json")
    print(f"  - CSV: {csv_file}")

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
