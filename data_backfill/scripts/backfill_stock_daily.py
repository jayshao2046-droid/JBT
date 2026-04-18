#!/usr/bin/env python3
"""
A股全量日线回补脚本 — 按交易日批量拉取，高效落盘。
10年约2430个交易日 × 5500只 ≈ 1300万行。

按 trade_date 拉取（一次API=一天全市场），远快于按个股逐只拉。
数据按月分文件存储: data/stock_daily/YYYYMM.parquet

用法:
  cd /Users/jaybot/jbt
  source .venv/bin/activate
  python3 data_backfill/scripts/backfill_stock_daily.py --start 20160101
  python3 data_backfill/scripts/backfill_stock_daily.py --start 20160101 --end 20260419
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ── 日志 ──
LOG_DIR = Path("/Users/jaybot/jbt/data_backfill/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "stock_daily_backfill.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── 常量 ──
TUSHARE_TOKEN = os.environ.get(
    "TUSHARE_TOKEN",
    "e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba",
)
TARGET_DIR = Path("/Users/jaybot/jbt/data/stock_daily")


def get_trade_cal(pro, start: str, end: str) -> list[str]:
    """获取交易日历"""
    cal = pro.trade_cal(exchange="SSE", start_date=start, end_date=end, is_open="1")
    if cal is None or cal.empty:
        return []
    return sorted(cal["cal_date"].tolist())


def backfill_stock_daily(start_date: str, end_date: str):
    """按交易日批量拉取全市场日线"""
    import tushare as ts

    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("A股全量日线回补: %s ~ %s", start_date, end_date)
    logger.info("目标目录: %s", TARGET_DIR)
    logger.info("=" * 60)

    # 获取交易日历
    trade_dates = get_trade_cal(pro, start_date, end_date)
    logger.info("交易日数: %d", len(trade_dates))

    if not trade_dates:
        logger.error("无交易日，退出")
        return

    # 检查已有进度（跳过已下载的月份最后日期之前的数据）
    existing_files = sorted(TARGET_DIR.glob("*.parquet"))
    skip_before = None
    if existing_files:
        last_file = existing_files[-1]
        try:
            last_df = pd.read_parquet(last_file)
            if not last_df.empty and "trade_date" in last_df.columns:
                skip_before = last_df["trade_date"].max()
                logger.info("发现已有数据到 %s，从下一天继续", skip_before)
        except Exception:
            pass

    if skip_before:
        trade_dates = [d for d in trade_dates if d > skip_before]
        logger.info("跳过已完成日期后，剩余 %d 个交易日", len(trade_dates))

    # 按月分组
    monthly_dates: dict[str, list[str]] = {}
    for d in trade_dates:
        month_key = d[:6]  # YYYYMM
        monthly_dates.setdefault(month_key, []).append(d)

    total_rows = 0
    total_days = 0
    failed_dates: list[str] = []

    for month_key in sorted(monthly_dates.keys()):
        dates = monthly_dates[month_key]
        month_frames: list[pd.DataFrame] = []

        for td in dates:
            retries = 3
            for attempt in range(retries):
                try:
                    df = pro.daily(trade_date=td)
                    if df is not None and not df.empty:
                        month_frames.append(df)
                        total_days += 1
                    time.sleep(0.25)  # Tushare 限频: ~4 req/s
                    break
                except Exception as e:
                    if attempt < retries - 1:
                        logger.warning("  %s attempt %d failed: %s, retrying...", td, attempt + 1, e)
                        time.sleep(2 ** (attempt + 1))
                    else:
                        logger.error("  ❌ %s 失败: %s", td, e)
                        failed_dates.append(td)

        if month_frames:
            merged = pd.concat(month_frames, ignore_index=True)
            merged = merged.sort_values(["ts_code", "trade_date"]).drop_duplicates(
                subset=["ts_code", "trade_date"], keep="last"
            )

            # 合并已有月份数据
            month_file = TARGET_DIR / f"{month_key}.parquet"
            if month_file.exists():
                old = pd.read_parquet(month_file)
                merged = pd.concat([old, merged], ignore_index=True)
                merged = merged.sort_values(["ts_code", "trade_date"]).drop_duplicates(
                    subset=["ts_code", "trade_date"], keep="last"
                )

            merged.to_parquet(month_file, index=False, engine="pyarrow")
            total_rows += len(merged)
            logger.info("✅ %s: %d天, %d行, 文件 %s",
                        month_key, len(dates), len(merged), month_file.name)
        else:
            logger.warning("⚠️ %s: 无数据", month_key)

    # 同时回补指数日线
    logger.info("开始回补主要指数日线...")
    INDEX_CODES = [
        "000001.SH",  # 上证指数
        "399001.SZ",  # 深证成指
        "399006.SZ",  # 创业板指
        "000300.SH",  # 沪深300
        "000905.SH",  # 中证500
        "000852.SH",  # 中证1000
    ]

    index_dir = TARGET_DIR / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    for idx_code in INDEX_CODES:
        try:
            df = pro.index_daily(ts_code=idx_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                fname = idx_code.replace(".", "_")
                out_file = index_dir / f"{fname}.parquet"

                if out_file.exists():
                    old = pd.read_parquet(out_file)
                    df = pd.concat([old, df], ignore_index=True)
                    df = df.sort_values("trade_date").drop_duplicates(
                        subset=["trade_date"], keep="last"
                    )

                df.to_parquet(out_file, index=False, engine="pyarrow")
                logger.info("✅ 指数 %s: %d rows", idx_code, len(df))
            time.sleep(0.5)
        except Exception as e:
            logger.error("❌ 指数 %s: %s", idx_code, e)

    logger.info("=" * 60)
    logger.info("A股日线回补完成: %d天, %d行, %d失败",
                total_days, total_rows, len(failed_dates))
    if failed_dates:
        logger.warning("失败日期: %s", ", ".join(failed_dates[:20]))
    logger.info("数据目录: %s", TARGET_DIR)
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="A股全量日线回补")
    parser.add_argument("--start", default="20160101",
                        help="起始日期 (默认 20160101, 即10年)")
    parser.add_argument("--end", default=None,
                        help="结束日期 (默认今天)")
    args = parser.parse_args()

    end_date = args.end or datetime.now().strftime("%Y%m%d")
    backfill_stock_daily(args.start, end_date)


if __name__ == "__main__":
    main()
