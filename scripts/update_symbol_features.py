#!/usr/bin/env python3
"""每日更新品种特征（增量更新）

在每天 17:30（日K线采集完成后）自动运行，更新 data API 当前支持的连续合约特征。

默认覆盖 5/15/30/60/120/240 分钟线和 1440 日线。
"""
import argparse
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

DEFAULT_INTERVALS = (5, 15, 30, 60, 120, 240, 1440)
DEFAULT_SYMBOL_DELAY_SECONDS = 3.0
LEGACY_DAILY_CACHE_DIR = "runtime/symbol_profiles"

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


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="更新品种特征（默认覆盖 6 个分钟周期 + 日线）")
    parser.add_argument(
        "--intervals",
        nargs="+",
        type=int,
        default=list(DEFAULT_INTERVALS),
        help="要更新的 K 线周期，单位分钟。默认: 5 15 30 60 120 240 1440",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="仅更新指定品种，例如 SHFE.rb0 DCE.i0；默认从 data API 自动读取全部 continuous symbols",
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="忽略缓存，强制对指定周期做全量重算",
    )
    parser.add_argument(
        "--symbol-delay-seconds",
        type=float,
        default=DEFAULT_SYMBOL_DELAY_SECONDS,
        help="相邻品种之间的等待秒数，默认 3 秒，用于减轻 Mini data API 压力",
    )
    return parser


def normalize_intervals(intervals: list[int]) -> list[int]:
    normalized: list[int] = []
    seen: set[int] = set()
    for interval in intervals:
        if interval <= 0:
            raise ValueError(f"interval must be positive, got {interval}")
        if interval in seen:
            continue
        seen.add(interval)
        normalized.append(interval)
    return normalized


def resolve_cache_dir(interval: int) -> str:
    if interval == 1440:
        return LEGACY_DAILY_CACHE_DIR
    return f"runtime/symbol_profiles/{interval}m"


async def update_symbols_for_interval(
    *,
    data_service_url: str,
    symbols: list[str],
    interval: int,
    force_full: bool,
    symbol_delay_seconds: float,
) -> dict[str, object]:
    cache_dir = resolve_cache_dir(interval)
    interval_label = "日K线" if interval == 1440 else f"{interval}分钟K线"

    logger.info("=" * 80)
    logger.info("开始更新品种特征 [%s]", interval_label)
    logger.info("=" * 80)
    logger.info("品种数量: %s", len(symbols))
    logger.info("数据源: Mini API (%s)", data_service_url)
    logger.info("缓存目录: %s", cache_dir)
    logger.info("更新模式: %s", "全量重算" if force_full else "增量更新")
    logger.info("=" * 80)

    profiler = SymbolProfiler(
        data_service_url=data_service_url,
        interval=interval,
        enable_cache=True,
        cache_dir=cache_dir,
    )

    success_count = 0
    failed_symbols: list[str] = []

    for index, symbol in enumerate(symbols, 1):
        logger.info("[%s/%s][%s] 更新 %s...", index, len(symbols), interval_label, symbol)

        try:
            features = await profiler.calculate_features(symbol, force_full=force_full)

            if features:
                success_count += 1
                logger.info(
                    "  ✅ 波动率=%s(%.4f), 趋势=%s(%.4f), 置信度=%.2f",
                    features.volatility_weighted,
                    features.volatility_1y,
                    features.trend_strength_weighted,
                    features.trend_strength_1y,
                    features.confidence.overall,
                )
            else:
                failed_symbols.append(symbol)
                logger.warning("  ❌ 更新失败（数据不足）")

        except Exception as exc:
            failed_symbols.append(symbol)
            logger.error("  ❌ 更新失败: %s", exc)

        if symbol_delay_seconds > 0 and index < len(symbols):
            await asyncio.sleep(symbol_delay_seconds)

    from services.decision.src.research.feature_cache_manager import FeatureCacheManager

    stats = FeatureCacheManager(cache_dir=cache_dir).get_cache_stats()

    logger.info("=" * 80)
    logger.info("[%s] 更新完成", interval_label)
    logger.info("=" * 80)
    logger.info("成功: %s/%s", success_count, len(symbols))
    logger.info("失败: %s/%s", len(failed_symbols), len(symbols))
    if failed_symbols:
        logger.warning("失败品种: %s", ", ".join(failed_symbols))

    logger.info("缓存统计:")
    logger.info("  总品种数: %s", stats["total_symbols"])
    logger.info("  有效缓存: %s", stats["valid_caches"])
    logger.info("  过期缓存: %s", stats["expired_caches"])

    return {
        "interval": interval,
        "cache_dir": cache_dir,
        "success_count": success_count,
        "failed_symbols": failed_symbols,
        "total_symbols": len(symbols),
    }


async def update_all_symbols(args: argparse.Namespace) -> list[dict[str, object]]:
    """按指定周期更新所有品种特征。"""
    data_service_url = "http://192.168.31.74:8105"
    symbols = args.symbols or load_supported_symbols(data_service_url)
    intervals = normalize_intervals(args.intervals)

    logger.info("=" * 80)
    logger.info("开始更新品种特征（默认 6 个分钟周期 + 日线）")
    logger.info("=" * 80)
    logger.info("品种数量: %s", len(symbols))
    logger.info("数据源: Mini API (%s)", data_service_url)
    logger.info("周期列表: %s", ", ".join(str(interval) for interval in intervals))
    logger.info("品种间延迟: %.1fs", args.symbol_delay_seconds)
    logger.info("=" * 80)

    results: list[dict[str, object]] = []
    for interval in intervals:
        result = await update_symbols_for_interval(
            data_service_url=data_service_url,
            symbols=symbols,
            interval=interval,
            force_full=args.force_full,
            symbol_delay_seconds=args.symbol_delay_seconds,
        )
        results.append(result)

    return results


async def main():
    args = build_argument_parser().parse_args()

    try:
        results = await update_all_symbols(args)

        total_success = sum(int(result["success_count"]) for result in results)
        total_failed = sum(len(result["failed_symbols"]) for result in results)
        total_targets = sum(int(result["total_symbols"]) for result in results)

        logger.info("=" * 80)
        logger.info("全周期汇总")
        logger.info("=" * 80)
        for result in results:
            interval = int(result["interval"])
            interval_label = "日K线" if interval == 1440 else f"{interval}分钟K线"
            logger.info(
                "%s: 成功 %s/%s, 失败 %s, 缓存目录=%s",
                interval_label,
                result["success_count"],
                result["total_symbols"],
                len(result["failed_symbols"]),
                result["cache_dir"],
            )

        if total_failed == 0:
            logger.info("\n✅ 所有周期更新成功 (%s/%s)", total_success, total_targets)
            sys.exit(0)
        elif total_success > 0:
            logger.warning("\n⚠️ 部分周期存在失败 (%s 个)", total_failed)
            sys.exit(1)
        else:
            logger.error("\n❌ 所有品种更新失败")
            sys.exit(2)

    except Exception as exc:
        logger.error("\n❌ 更新任务失败: %s", exc, exc_info=True)
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
