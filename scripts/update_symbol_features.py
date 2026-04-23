#!/usr/bin/env python3
"""每日更新品种特征（增量更新）

在每天 17:30（日K线采集完成后）自动运行，更新 data API 当前支持的连续合约特征。
"""
import asyncio
import json
import logging
import re
import sys
from urllib import request as urllib_request
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

DEFAULT_SYMBOLS = [
    # 上期所 (SHFE)
    "SHFE.cu0", "SHFE.al0", "SHFE.zn0", "SHFE.ru0", "SHFE.ss0", "SHFE.sp0", "SHFE.au0",
    "SHFE.ag0", "SHFE.rb0", "SHFE.hc0",

    # 大商所 (DCE)
    "DCE.i0", "DCE.m0", "DCE.pp0", "DCE.v0", "DCE.l0", "DCE.c0", "DCE.jd0", "DCE.y0",
    "DCE.p0", "DCE.a0", "DCE.jm0", "DCE.j0", "DCE.eb0", "DCE.pg0", "DCE.lh0",

    # 郑商所 (CZCE)
    "CZCE.TA0", "CZCE.MA0", "CZCE.CF0", "CZCE.SR0", "CZCE.OI0",
    "CZCE.RM0", "CZCE.FG0", "CZCE.SA0", "CZCE.PF0", "CZCE.UR0",
]

SUPPORTED_CONTINUOUS_PATTERN = re.compile(r"^KQ_m_([A-Za-z]+)_([A-Za-z]+)$")


def load_supported_symbols(api_base_url: str) -> list[str]:
    """从 data API 动态读取当前支持的连续合约，避免脚本清单与采集配置漂移。"""
    url = f"{api_base_url.rstrip('/')}/api/v1/symbols"

    try:
        with urllib_request.urlopen(url, timeout=10) as response:
            payload = json.load(response)
    except Exception as exc:
        logger.warning("读取 data API symbols 失败，回退默认清单: %s", exc)
        return DEFAULT_SYMBOLS

    raw_symbols = payload.get("symbols", []) if isinstance(payload, dict) else payload
    resolved: list[str] = []
    for raw_symbol in raw_symbols:
        match = SUPPORTED_CONTINUOUS_PATTERN.match(str(raw_symbol))
        if not match:
            continue
        exchange, code = match.groups()
        resolved.append(f"{exchange}.{code}0")

    symbols = sorted(dict.fromkeys(resolved))
    if not symbols:
        logger.warning("data API 未返回可用连续合约，回退默认清单")
        return DEFAULT_SYMBOLS

    return symbols


async def update_all_symbols():
    """更新所有品种的特征"""
    data_service_url = "http://192.168.31.156:8105"
    symbols = load_supported_symbols(data_service_url)

    logger.info("=" * 80)
    logger.info("开始更新品种特征（增量更新）")
    logger.info("=" * 80)
    logger.info(f"品种数量: {len(symbols)}")
    logger.info(f"数据源: Mini API ({data_service_url})")
    logger.info(f"K线周期: 日K线 (1440分钟)")
    logger.info("=" * 80)

    profiler = SymbolProfiler(
        data_service_url=data_service_url,
        interval=1440,  # 日K线
        enable_cache=True
    )

    success_count = 0
    failed_symbols = []

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] 更新 {symbol}...")

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
    logger.info(f"成功: {success_count}/{len(symbols)}")
    logger.info(f"失败: {len(failed_symbols)}/{len(symbols)}")

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
