#!/usr/bin/env python3
"""批量计算 42 个品种的特征画像（支持多周期）

支持的周期：15 / 30 / 60 / 120 / 240 分钟
每个周期独立输出到 runtime/symbol_profiles/{interval}m/

用法：
  python scripts/batch_calculate_symbol_features.py               # 默认只跑 60m
  python scripts/batch_calculate_symbol_features.py --intervals 15 30 60 120 240
  python scripts/batch_calculate_symbol_features.py --intervals 60

说明：
  - 策略用哪个周期，就应该用对应周期的特征（波动率/自相关在不同 interval 有显著差异）
  - 5min 暂不支持（API 数据量过大，约 3年×480根=5万条，可能触发限速）

输出：
  - runtime/symbol_profiles/{interval}m/{EXCHANGE.PRODUCT}.json
  - runtime/symbol_profiles/{interval}m/summary.csv
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.symbol_profiler import SymbolProfiler


# 42 个品种列表（与 generate_42_factor_expansion_strategies.py 保持一致）
# 使用裸品种格式，SymbolProfiler 内部自动转为 KQ_m_ 连续合约格式
SYMBOLS = [
    # CZCE 农产品/化工（大写商品码）
    "CZCE.AP",  # 苹果
    "CZCE.CF",  # 棉花
    "CZCE.FG",  # 玻璃
    "CZCE.MA",  # 甲醇
    "CZCE.OI",  # 菜油
    "CZCE.PF",  # 短纤
    "CZCE.RM",  # 菜粕
    "CZCE.SA",  # 纯碱
    "CZCE.SR",  # 白糖
    "CZCE.TA",  # PTA
    "CZCE.UR",  # 尿素

    # DCE 黑色系/农产品/化工（小写）
    "DCE.a",    # 豆一
    "DCE.c",    # 玉米
    "DCE.cs",   # 玉米淀粉
    "DCE.eb",   # 苯乙烯
    "DCE.eg",   # 乙二醇
    "DCE.i",    # 铁矿石
    "DCE.j",    # 焦炭
    "DCE.jd",   # 鸡蛋
    "DCE.jm",   # 焦煤
    "DCE.l",    # 塑料
    "DCE.lh",   # 生猪
    "DCE.m",    # 豆粕
    "DCE.p",    # 棕榈油
    "DCE.pg",   # 液化石油气
    "DCE.pp",   # 聚丙烯
    "DCE.v",    # PVC
    "DCE.y",    # 豆油

    # INE
    "INE.sc",   # 原油

    # SHFE 金属/能源（小写）
    "SHFE.ag",  # 白银
    "SHFE.al",  # 铝
    "SHFE.au",  # 黄金
    "SHFE.bu",  # 沥青
    "SHFE.cu",  # 铜
    "SHFE.fu",  # 燃料油
    "SHFE.hc",  # 热轧卷板
    "SHFE.ni",  # 镍
    "SHFE.rb",  # 螺纹钢
    "SHFE.ru",  # 橡胶
    "SHFE.sp",  # 纸浆
    "SHFE.ss",  # 不锈钢
    "SHFE.zn",  # 锌
]


async def run_for_interval(interval: int) -> None:
    """对所有品种跑指定 interval 的特征计算，输出到 runtime/symbol_profiles/{interval}m/"""
    profiler = SymbolProfiler(
        data_service_url="http://192.168.31.74:8105",
        interval=interval,
    )

    # 创建输出目录（按周期分目录）
    output_dir = Path(f"runtime/symbol_profiles/{interval}m")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"批量计算 {len(SYMBOLS)} 个品种特征画像  [interval={interval}min]")
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
            features = await profiler.calculate_features(symbol, force_full=True)

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

        # 每个 symbol 后等待 3s，避免 Mini API 连接池耗尽
        if i < len(SYMBOLS):
            await asyncio.sleep(3)

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

    print(f"\n总计: {len(SYMBOLS)} 个品种  [interval={interval}min]")
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
    print(f"  - CSV: {output_dir}/summary.csv")

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


async def main():
    parser = argparse.ArgumentParser(description="批量计算品种特征画像（多周期支持）")
    parser.add_argument(
        "--intervals",
        nargs="+",
        type=int,
        default=[60],
        choices=[5, 15, 30, 60, 120, 240],
        help="要计算的 K 线周期（分钟），可多选，默认 60。示例: --intervals 15 30 60",
    )
    args = parser.parse_args()

    intervals = args.intervals
    print(f"\n将依次计算以下周期的特征: {intervals}\n")

    for interval in intervals:
        await run_for_interval(interval)
        if len(intervals) > 1:
            print(f"\n{'▶' * 40}")
            print(f"  {interval}min 完成，稍作等待后继续下一个周期...")
            print(f"{'▶' * 40}\n")
            await asyncio.sleep(2)  # 避免连续请求过猛


if __name__ == "__main__":
    asyncio.run(main())
