#!/usr/bin/env python3
"""每日更新品种特征（增量更新）

在每天 17:30（日K线采集完成后）自动运行，更新35个期货品种的特征。
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.decision.src.research.symbol_profiler import SymbolProfiler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

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


async def update_all_symbols():
    """更新所有品种的特征"""
    logger.info("=" * 80)
    logger.info("开始更新品种特征（增量更新）")
    logger.info("=" * 80)
    logger.info(f"品种数量: {len(SYMBOLS)}")
    logger.info(f"数据源: Mini API (http://192.168.31.76:8105)")
    logger.info(f"K线周期: 日K线 (1440分钟)")
    logger.info("=" * 80)

    profiler = SymbolProfiler(
        data_service_url="http://192.168.31.76:8105",
        interval=1440,  # 日K线
        enable_cache=True
    )

    success_count = 0
    failed_symbols = []

    for i, symbol in enumerate(SYMBOLS, 1):
        logger.info(f"[{i}/{len(SYMBOLS)}] 更新 {symbol}...")

        try:
            # 使用增量更新（如果缓存有效）
            features = await profiler.calculate_features(symbol, force_full=False)

            if features:
                success_count += 1
                logger.info(
                    f"  ✅ 波动率={features.volatility_weighted}({features.volatility_1y:.4f}), "
                    f"趋势={features.trend_strength_weighted}({features.trend_strength_1y:.4f}), "
                    f"置信度={features.confidence.overall:.2f}"
                )
            else:
                failed_symbols.append(symbol)
                logger.warning(f"  ❌ 更新失败（数据不足）")

        except Exception as e:
            failed_symbols.append(symbol)
            logger.error(f"  ❌ 更新失败: {e}")

    # 汇总报告
    logger.info("=" * 80)
    logger.info("更新完成")
    logger.info("=" * 80)
    logger.info(f"成功: {success_count}/{len(SYMBOLS)}")
    logger.info(f"失败: {len(failed_symbols)}/{len(SYMBOLS)}")

    if failed_symbols:
        logger.warning(f"失败品种: {', '.join(failed_symbols)}")

    # 缓存统计
    from services.decision.src.research.feature_cache_manager import FeatureCacheManager
    cache_manager = FeatureCacheManager(cache_dir="runtime/symbol_profiles")
    stats = cache_manager.get_cache_stats()

    logger.info(f"\n缓存统计:")
    logger.info(f"  总品种数: {stats['total_symbols']}")
    logger.info(f"  有效缓存: {stats['valid_caches']}")
    logger.info(f"  过期缓存: {stats['expired_caches']}")

    return success_count, failed_symbols


async def main():
    try:
        success_count, failed_symbols = await update_all_symbols()

        if len(failed_symbols) == 0:
            logger.info("\n✅ 所有品种更新成功")
            sys.exit(0)
        elif success_count > 0:
            logger.warning(f"\n⚠️ 部分品种更新失败 ({len(failed_symbols)} 个)")
            sys.exit(1)
        else:
            logger.error("\n❌ 所有品种更新失败")
            sys.exit(2)

    except Exception as e:
        logger.error(f"\n❌ 更新任务失败: {e}", exc_info=True)
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
