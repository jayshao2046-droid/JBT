#!/usr/bin/env python3
"""
验证回补数据并导入到正式目录
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/jaybot/JBT/data_backfill/logs/verify.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def verify_data(backfill_dir: Path, start_date: str, end_date: str) -> dict[str, bool]:
    """验证回补数据的完整性和正确性

    Args:
        backfill_dir: 回补数据目录
        start_date: 期望的开始日期
        end_date: 期望的结束日期

    Returns:
        dict: {symbol: is_valid}
    """
    results = {}
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    for symbol_dir in sorted(backfill_dir.iterdir()):
        if not symbol_dir.is_dir():
            continue

        symbol = symbol_dir.name
        logger.info(f"验证 {symbol}...")

        try:
            # 读取所有 parquet 文件
            parquet_files = list(symbol_dir.glob("*.parquet"))
            if not parquet_files:
                logger.warning(f"  ❌ {symbol}: 没有找到数据文件")
                results[symbol] = False
                continue

            dfs = [pd.read_parquet(f) for f in parquet_files]
            df = pd.concat(dfs, ignore_index=True)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").drop_duplicates(subset=["datetime"])

            # 检查数据范围
            data_start = df["datetime"].min()
            data_end = df["datetime"].max()

            logger.info(f"  数据范围: {data_start} ~ {data_end}")
            logger.info(f"  记录数: {len(df)}")

            # 检查是否覆盖目标时间段
            if data_start > start_dt or data_end < end_dt:
                logger.warning(f"  ⚠️  {symbol}: 数据范围不完整")
                results[symbol] = False
            else:
                logger.info(f"  ✅ {symbol}: 验证通过")
                results[symbol] = True

        except Exception as e:
            logger.error(f"  ❌ {symbol}: 验证失败 - {e}")
            results[symbol] = False

    return results


def merge_and_import(
    backfill_dir: Path,
    target_dir: Path,
    symbol: str,
    dry_run: bool = False,
) -> bool:
    """合并回补数据到正式目录

    Args:
        backfill_dir: 回补数据目录
        target_dir: 目标目录 (futures_minute/1m/)
        symbol: 品种名称
        dry_run: 是否仅模拟运行

    Returns:
        bool: 是否成功
    """
    try:
        source_dir = backfill_dir / symbol
        target_symbol_dir = target_dir / symbol

        if not source_dir.exists():
            logger.error(f"源目录不存在: {source_dir}")
            return False

        # 读取回补数据
        backfill_files = list(source_dir.glob("*.parquet"))
        if not backfill_files:
            logger.warning(f"{symbol}: 没有回补数据")
            return False

        logger.info(f"导入 {symbol}...")

        for backfill_file in backfill_files:
            month = backfill_file.stem  # 例如 202604
            target_file = target_symbol_dir / backfill_file.name

            # 读取回补数据
            df_new = pd.read_parquet(backfill_file)
            df_new["datetime"] = pd.to_datetime(df_new["datetime"])

            # 如果目标文件存在，合并数据
            if target_file.exists():
                df_old = pd.read_parquet(target_file)
                df_old["datetime"] = pd.to_datetime(df_old["datetime"])

                # 合并并去重
                df_merged = pd.concat([df_old, df_new], ignore_index=True)
                df_merged = df_merged.sort_values("datetime").drop_duplicates(
                    subset=["datetime"], keep="last"
                )

                logger.info(f"  {month}: 合并 {len(df_old)} + {len(df_new)} = {len(df_merged)} 条记录")
            else:
                df_merged = df_new
                logger.info(f"  {month}: 新增 {len(df_merged)} 条记录")

            # 保存
            if not dry_run:
                target_symbol_dir.mkdir(parents=True, exist_ok=True)
                df_merged.to_parquet(target_file, index=False, engine="pyarrow")
                logger.info(f"  ✅ 已保存: {target_file}")
            else:
                logger.info(f"  [DRY RUN] 将保存到: {target_file}")

        return True

    except Exception as e:
        logger.error(f"❌ {symbol} 导入失败: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="验证并导入回补数据")
    parser.add_argument("--verify", action="store_true", help="验证回补数据")
    parser.add_argument("--import", dest="do_import", action="store_true", help="导入数据到正式目录")
    parser.add_argument("--start", help="期望的开始日期，格式: 2026-04-10")
    parser.add_argument("--end", help="期望的结束日期，格式: 2026-04-17")
    parser.add_argument("--backfill-dir", default="/Users/jaybot/JBT/data_backfill/output", help="回补数据目录")
    parser.add_argument("--target-dir", default="/Users/jaybot/JBT/data/futures_minute/1m", help="目标数据目录")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟运行，不实际写入")
    parser.add_argument("--clean", action="store_true", help="导入成功后清除回补数据")

    args = parser.parse_args()

    backfill_dir = Path(args.backfill_dir)
    target_dir = Path(args.target_dir)

    if args.verify:
        if not args.start or not args.end:
            logger.error("验证模式需要指定 --start 和 --end")
            sys.exit(1)

        logger.info("=" * 60)
        logger.info("开始验证回补数据")
        logger.info("=" * 60)

        results = verify_data(backfill_dir, args.start, args.end)

        valid_count = sum(results.values())
        logger.info("=" * 60)
        logger.info(f"验证完成: {valid_count}/{len(results)} 个品种通过验证")

        if valid_count < len(results):
            logger.warning("部分品种验证失败，请检查日志")
            sys.exit(1)

    if args.do_import:
        logger.info("=" * 60)
        logger.info("开始导入数据到正式目录")
        if args.dry_run:
            logger.info("[DRY RUN 模式]")
        logger.info("=" * 60)

        success_count = 0
        for symbol_dir in sorted(backfill_dir.iterdir()):
            if not symbol_dir.is_dir():
                continue

            symbol = symbol_dir.name
            if merge_and_import(backfill_dir, target_dir, symbol, args.dry_run):
                success_count += 1

        logger.info("=" * 60)
        logger.info(f"导入完成: {success_count} 个品种")

        if args.clean and not args.dry_run:
            logger.info("清除回补数据...")
            for symbol_dir in backfill_dir.iterdir():
                if symbol_dir.is_dir():
                    shutil.rmtree(symbol_dir)
                    logger.info(f"  已删除: {symbol_dir}")


if __name__ == "__main__":
    main()
