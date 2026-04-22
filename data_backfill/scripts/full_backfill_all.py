#!/usr/bin/env python3
"""
全量数据回补脚本 — 35个期货品种分钟K线 + Tushare日K线
分年度批次执行，避免 TqSdk data_length 溢出。

用法:
    cd /Users/jaybot/JBT/data_backfill/scripts
    source /Users/jaybot/JBT/.venv/bin/activate
  python3 full_backfill_all.py --mode minute   # 仅分钟回补
  python3 full_backfill_all.py --mode daily    # 仅日K回补
  python3 full_backfill_all.py --mode all      # 全量回补
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ── 日志 ──────────────────────────────────────────────────
LOG_DIR = Path("/Users/jaybot/JBT/data_backfill/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "full_backfill.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── 常量 ──────────────────────────────────────────────────
OUTPUT_DIR = Path("/Users/jaybot/JBT/data_backfill/output")
TARGET_DIR = Path("/Users/jaybot/JBT/data/futures_minute/1m")
DAILY_TARGET_DIR = Path("/Users/jaybot/JBT/data/futures_daily")

TQ_ACCOUNT = os.environ.get("TQSDK_PHONE", "17621181300")
TQ_PASSWORD = os.environ.get("TQSDK_PASSWORD", "Jay.486858")
TUSHARE_TOKEN = os.environ.get(
    "TUSHARE_TOKEN",
    "e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba",
)

# 35 个连续合约
CONTINUOUS_CONTRACTS = [
    # 郑商所 (CZCE)
    "KQ.m@CZCE.CF", "KQ.m@CZCE.FG", "KQ.m@CZCE.MA", "KQ.m@CZCE.OI", "KQ.m@CZCE.PF",
    "KQ.m@CZCE.RM", "KQ.m@CZCE.SA", "KQ.m@CZCE.SR", "KQ.m@CZCE.TA", "KQ.m@CZCE.UR",
    # 大商所 (DCE)
    "KQ.m@DCE.a", "KQ.m@DCE.c", "KQ.m@DCE.eb", "KQ.m@DCE.i", "KQ.m@DCE.j",
    "KQ.m@DCE.jd", "KQ.m@DCE.jm", "KQ.m@DCE.l", "KQ.m@DCE.lh", "KQ.m@DCE.m",
    "KQ.m@DCE.p", "KQ.m@DCE.pg", "KQ.m@DCE.pp", "KQ.m@DCE.v", "KQ.m@DCE.y",
    # 上期所 (SHFE)
    "KQ.m@SHFE.ag", "KQ.m@SHFE.al", "KQ.m@SHFE.au", "KQ.m@SHFE.cu", "KQ.m@SHFE.hc",
    "KQ.m@SHFE.rb", "KQ.m@SHFE.ru", "KQ.m@SHFE.sp", "KQ.m@SHFE.ss", "KQ.m@SHFE.zn",
]

# 品种到交易所映射（Tushare 用）
SYMBOL_EXCHANGE_MAP = {
    # CZCE
    "CF": "CZCE", "FG": "CZCE", "MA": "CZCE", "OI": "CZCE", "PF": "CZCE",
    "RM": "CZCE", "SA": "CZCE", "SR": "CZCE", "TA": "CZCE", "UR": "CZCE",
    # DCE
    "A": "DCE", "C": "DCE", "EB": "DCE", "I": "DCE", "J": "DCE",
    "JD": "DCE", "JM": "DCE", "L": "DCE", "LH": "DCE", "M": "DCE",
    "P": "DCE", "PG": "DCE", "PP": "DCE", "V": "DCE", "Y": "DCE",
    # SHFE
    "AG": "SHFE", "AL": "SHFE", "AU": "SHFE", "CU": "SHFE", "HC": "SHFE",
    "RB": "SHFE", "RU": "SHFE", "SP": "SHFE", "SS": "SHFE", "ZN": "SHFE",
}


def symbol_to_dirname(symbol: str) -> str:
    """KQ.m@SHFE.rb -> KQ_m_SHFE_rb"""
    return symbol.replace(".", "_").replace("@", "_")


def _normalize_minute_frame(
    df: pd.DataFrame,
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame | None:
    """统一清洗分钟线结果，兼容 CSV 下载与回测累积返回格式。"""
    if df is None or df.empty or "datetime" not in df.columns:
        return None

    frame = df.copy()
    parsed = pd.to_datetime(frame["datetime"], errors="coerce")
    if parsed.isna().all():
        numeric = pd.to_numeric(frame["datetime"], errors="coerce")
        parsed = pd.to_datetime(numeric, unit="ns", errors="coerce")

    frame["datetime"] = parsed
    frame = frame.dropna(subset=["datetime"])
    frame = frame[(frame["datetime"] >= pd.Timestamp(start_dt)) & (frame["datetime"] < pd.Timestamp(end_dt))]
    if frame.empty:
        return None

    return frame.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")


def _download_minute_chunk_with_data_downloader(
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame | None:
    """优先使用官方历史下载器；若权限不足则返回 None 交给回测路径。"""
    try:
        from tqsdk import TqApi, TqAuth
        from tqsdk.tools import DataDownloader
    except Exception as exc:
        logger.info("  %s DataDownloader 不可用，回退回测: %s", symbol, exc)
        return None

    api: TqApi | None = None
    csv_path: Path | None = None

    try:
        api = TqApi(auth=TqAuth(TQ_ACCOUNT, TQ_PASSWORD), web_gui=False)
        fd, temp_name = tempfile.mkstemp(prefix=f"{symbol_to_dirname(symbol)}_", suffix=".csv")
        os.close(fd)
        csv_path = Path(temp_name)

        downloader = DataDownloader(
            api,
            symbol_list=symbol,
            dur_sec=60,
            start_dt=start_dt,
            end_dt=end_dt,
            csv_file_name=str(csv_path),
        )
        while not downloader.is_finished():
            api.wait_update()

        if not csv_path.exists():
            logger.warning("  %s DataDownloader 未产出文件，回退回测", symbol)
            return None

        frame = _normalize_minute_frame(pd.read_csv(csv_path), start_dt, end_dt)
        if frame is None:
            logger.warning("  %s DataDownloader 返回空数据，回退回测", symbol)
            return None

        logger.info("  %s 使用 DataDownloader 下载 %d bars", symbol, len(frame))
        return frame

    except Exception as exc:
        logger.warning("  %s DataDownloader 不可用，回退回测: %s", symbol, exc)
        return None
    finally:
        if api is not None:
            try:
                api.close()
            except Exception:
                pass
        if csv_path is not None and csv_path.exists():
            csv_path.unlink()


def _download_minute_chunk_with_backtest(
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame | None:
    """无历史下载权限时，退回回测模式持续累积分钟线。"""
    from tqsdk import TqApi, TqAuth, TqBacktest, BacktestFinished

    api: TqApi | None = None

    try:
        api = TqApi(
            auth=TqAuth(TQ_ACCOUNT, TQ_PASSWORD),
            backtest=TqBacktest(start_dt=start_dt, end_dt=end_dt),
            web_gui=False,
        )
        klines = api.get_kline_serial(symbol, duration_seconds=60, data_length=200000)

        collected_frames: list[pd.DataFrame] = []
        last_id = -1
        deadline = time.time() + 900  # 15 分钟超时，覆盖长年度回测

        while True:
            try:
                api.wait_update(deadline=deadline)
            except BacktestFinished:
                break

            frame = klines.copy()
            frame = frame[frame["datetime"] != 0]
            if frame.empty:
                if time.time() > deadline:
                    logger.warning("  %s chunk %s~%s 超时且无有效数据", symbol, start_dt.date(), end_dt.date())
                    break
                continue

            if time.time() > deadline:
                logger.warning("  %s chunk %s~%s 超时，使用已累计数据", symbol, start_dt.date(), end_dt.date())
                new_rows = frame[frame["id"] > last_id] if last_id >= 0 else frame
                if not new_rows.empty:
                    collected_frames.append(new_rows.copy())
                break

            new_rows = frame[frame["id"] > last_id] if last_id >= 0 else frame
            if new_rows.empty:
                continue

            collected_frames.append(new_rows.copy())
            last_id = int(new_rows["id"].max())

        if not collected_frames:
            return None

        return _normalize_minute_frame(pd.concat(collected_frames, ignore_index=True), start_dt, end_dt)

    except Exception as exc:
        logger.error("  %s chunk %s~%s 回测失败: %s", symbol, start_dt.date(), end_dt.date(), exc)
        return None
    finally:
        if api is not None:
            try:
                api.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════
# Part 1: 分钟 K 线回补（Downloader 优先，回测兜底）
# ═══════════════════════════════════════════════════════════

def backfill_minute_chunk(
    symbol: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame | None:
    """回补单个品种某时间段的分钟K线，返回 DataFrame"""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    df = _download_minute_chunk_with_data_downloader(symbol, start_dt, end_dt)
    if df is not None:
        return df

    return _download_minute_chunk_with_backtest(symbol, start_dt, end_dt)


def save_minute_to_parquet(df: pd.DataFrame, symbol: str) -> int:
    """将分钟数据按月份保存到 TARGET_DIR"""
    dirname = symbol_to_dirname(symbol)
    target = TARGET_DIR / dirname
    target.mkdir(parents=True, exist_ok=True)

    total = 0
    for period, group in df.groupby(df["datetime"].dt.to_period("M")):
        month_str = period.strftime("%Y%m")
        filepath = target / f"{month_str}.parquet"

        # 如果已有数据则合并
        if filepath.exists():
            old = pd.read_parquet(filepath)
            old["datetime"] = pd.to_datetime(old["datetime"])
            combined = pd.concat([old, group], ignore_index=True)
            combined = combined.sort_values("datetime").drop_duplicates(
                subset=["datetime"], keep="last"
            )
        else:
            combined = group.sort_values("datetime")

        combined.to_parquet(filepath, index=False, engine="pyarrow")
        total += len(combined)

    return total


def run_minute_backfill(start_year: int = 2021, end_date: str | None = None):
    """分年度批次回补所有 35 个品种的分钟 K 线"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    end_year = int(end_date[:4])

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=" * 60)
    logger.info("开始分钟K线全量回补: %d ~ %s", start_year, end_date)
    logger.info("品种数: %d, 目标: %s", len(CONTINUOUS_CONTRACTS), TARGET_DIR)
    logger.info("=" * 60)

    # 构建年度区间
    chunks: list[tuple[str, str]] = []
    for y in range(start_year, end_year + 1):
        cs = f"{y}-01-01"
        ce = f"{y}-12-31" if y < end_year else end_date
        chunks.append((cs, ce))

    success = 0
    failed: list[str] = []

    for idx, symbol in enumerate(CONTINUOUS_CONTRACTS, 1):
        logger.info("[%d/%d] %s", idx, len(CONTINUOUS_CONTRACTS), symbol)
        all_frames: list[pd.DataFrame] = []

        for cs, ce in chunks:
            logger.info("  chunk %s ~ %s", cs, ce)
            df = backfill_minute_chunk(symbol, cs, ce)
            if df is not None and not df.empty:
                all_frames.append(df)
                logger.info("  → %d bars", len(df))
            time.sleep(1)  # API 限流

        if all_frames:
            merged = pd.concat(all_frames, ignore_index=True)
            merged = merged.sort_values("datetime").drop_duplicates(
                subset=["datetime"], keep="last"
            )
            total = save_minute_to_parquet(merged, symbol)
            logger.info("✅ %s 完成: %d bars, %s ~ %s",
                        symbol, total,
                        merged["datetime"].min().strftime("%Y-%m-%d"),
                        merged["datetime"].max().strftime("%Y-%m-%d"))
            success += 1
        else:
            logger.warning("❌ %s 无数据", symbol)
            failed.append(symbol)

        time.sleep(2)

    logger.info("=" * 60)
    logger.info("分钟K线回补完成: 成功 %d/%d", success, len(CONTINUOUS_CONTRACTS))
    if failed:
        logger.warning("失败品种: %s", ", ".join(failed))
    logger.info("数据目录: %s", TARGET_DIR)
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════
# Part 2: 日 K 线回补（Tushare）
# ═══════════════════════════════════════════════════════════

def run_daily_backfill(start_date: str = "20100101"):
    """通过 Tushare 回补期货日K线"""
    import tushare as ts

    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    DAILY_TARGET_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("开始期货日K线回补 (Tushare): from %s", start_date)
    logger.info("目标目录: %s", DAILY_TARGET_DIR)
    logger.info("=" * 60)

    today = datetime.now().strftime("%Y%m%d")
    success = 0
    failed: list[str] = []

    for product, exchange in SYMBOL_EXCHANGE_MAP.items():
        logger.info("回补 %s.%s 日K线...", exchange, product)
        try:
            # Tushare fut_daily 需要 ts_code (如 RB.SHF) 或 trade_date
            # 用 fut_mapping 获取主力合约映射
            mapping_df = pro.fut_mapping(symbol=product)
            if mapping_df is None or mapping_df.empty:
                logger.warning("  %s 无主力映射", product)
                failed.append(product)
                continue

            # 获取所有主力合约的日K
            ts_codes = mapping_df["ts_code"].unique().tolist()
            all_daily: list[pd.DataFrame] = []

            for ts_code in ts_codes[:50]:  # 限制合约数量
                try:
                    df = pro.fut_daily(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=today,
                    )
                    if df is not None and not df.empty:
                        all_daily.append(df)
                    time.sleep(0.3)  # Tushare 限频
                except Exception as e:
                    logger.debug("  %s: %s", ts_code, e)

            if all_daily:
                merged = pd.concat(all_daily, ignore_index=True)
                merged = merged.sort_values("trade_date").drop_duplicates(
                    subset=["ts_code", "trade_date"], keep="last"
                )

                # 保存
                out_dir = DAILY_TARGET_DIR / f"{exchange}_{product}"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / "daily.parquet"
                merged.to_parquet(out_file, index=False, engine="pyarrow")
                logger.info("✅ %s.%s: %d rows, %s ~ %s",
                            exchange, product, len(merged),
                            merged["trade_date"].min(),
                            merged["trade_date"].max())
                success += 1
            else:
                logger.warning("❌ %s 无日K数据", product)
                failed.append(product)

            time.sleep(1)  # 品种间限频

        except Exception as e:
            logger.error("❌ %s 失败: %s", product, e)
            failed.append(product)

    logger.info("=" * 60)
    logger.info("期货日K回补完成: 成功 %d/%d", success, len(SYMBOL_EXCHANGE_MAP))
    if failed:
        logger.warning("失败品种: %s", ", ".join(failed))
    logger.info("=" * 60)


def run_stock_daily_backfill(start_date: str = "20100101"):
    """通过 Tushare 回补A股主要指数的日K线"""
    import tushare as ts

    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    STOCK_DAILY_DIR = Path("/Users/jaybot/JBT/data/stock_daily")
    STOCK_DAILY_DIR.mkdir(parents=True, exist_ok=True)

    # 主要指数和ETF
    STOCK_CODES = [
        "000001.SH",  # 上证指数
        "399001.SZ",  # 深证成指
        "399006.SZ",  # 创业板指
        "000300.SH",  # 沪深300
        "000905.SH",  # 中证500
        "000852.SH",  # 中证1000
        "510050.SH",  # 50ETF
        "510300.SH",  # 300ETF
        "159919.SZ",  # 300ETF(深)
        "510500.SH",  # 500ETF
    ]

    logger.info("=" * 60)
    logger.info("开始A股指数日K回补 (Tushare): from %s", start_date)
    logger.info("=" * 60)

    today = datetime.now().strftime("%Y%m%d")
    success = 0

    for code in STOCK_CODES:
        try:
            if code.endswith(".SH") or code.endswith(".SZ"):
                # 指数用 index_daily，ETF用 fund_daily 或 daily
                if code.startswith("0") or code.startswith("3"):
                    df = pro.index_daily(ts_code=code, start_date=start_date, end_date=today)
                else:
                    df = pro.daily(ts_code=code, start_date=start_date, end_date=today)

            if df is not None and not df.empty:
                out_dir = STOCK_DAILY_DIR / code.replace(".", "_")
                out_dir.mkdir(parents=True, exist_ok=True)
                df.to_parquet(out_dir / "daily.parquet", index=False, engine="pyarrow")
                logger.info("✅ %s: %d rows", code, len(df))
                success += 1

            time.sleep(0.5)
        except Exception as e:
            logger.error("❌ %s: %s", code, e)

    logger.info("A股指数日K回补完成: 成功 %d/%d", success, len(STOCK_CODES))


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="全量数据回补")
    parser.add_argument("--mode", choices=["minute", "daily", "stock", "all"],
                        default="all", help="回补模式")
    parser.add_argument("--start-year", type=int, default=2021,
                        help="分钟回补起始年份 (默认 2021)")
    parser.add_argument("--daily-start", default="20100101",
                        help="日K回补起始日期 (默认 20100101)")
    args = parser.parse_args()

    logger.info("全量数据回补启动: mode=%s", args.mode)

    if args.mode in ("minute", "all"):
        run_minute_backfill(start_year=args.start_year)

    if args.mode in ("daily", "all"):
        run_daily_backfill(start_date=args.daily_start)

    if args.mode in ("stock", "all"):
        run_stock_daily_backfill(start_date=args.daily_start)

    logger.info("全量回补任务结束")


if __name__ == "__main__":
    main()
