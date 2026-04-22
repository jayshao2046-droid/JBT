#!/usr/bin/env python3
"""
期货分钟K线数据回补工具
优先使用 TqSdk DataDownloader 按时间段下载历史数据，权限不足时回退到回测累积方案。
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
from tqsdk import TqApi, TqAuth, TqBacktest, BacktestFinished

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/jaybot/JBT/data_backfill/logs/backfill.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# 35个连续合约品种列表
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


def symbol_to_filename(symbol: str) -> str:
    """将 TqSdk 格式的合约代码转换为文件名格式
    例如: KQ.m@SHFE.rb -> KQ_m_SHFE_rb
    """
    return symbol.replace(".", "_").replace("@", "_")


def _normalize_minute_frame(
    df: pd.DataFrame,
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame | None:
    """统一清洗分钟线结果，兼容 CSV 与回测返回格式。"""
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


def _download_with_data_downloader(
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    tq_account: str,
    tq_password: str,
) -> pd.DataFrame | None:
    """优先走官方历史下载器，失败时返回 None 交给回测方案兜底。"""
    try:
        from tqsdk.tools import DataDownloader
    except Exception as exc:
        logger.info("  %s DataDownloader 不可用，回退回测: %s", symbol, exc)
        return None

    api: TqApi | None = None
    csv_path: Path | None = None

    try:
        api = TqApi(auth=TqAuth(tq_account, tq_password), web_gui=False)
        fd, temp_name = tempfile.mkstemp(prefix=f"{symbol_to_filename(symbol)}_", suffix=".csv")
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


def _download_with_backtest(
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    tq_account: str,
    tq_password: str,
) -> pd.DataFrame | None:
    """回测模式兜底，解决无历史下载权限时的分钟线回补。"""
    api: TqApi | None = None

    try:
        api = TqApi(
            auth=TqAuth(tq_account, tq_password),
            backtest=TqBacktest(start_dt=start_dt, end_dt=end_dt),
            web_gui=False,
        )

        klines = api.get_kline_serial(symbol, duration_seconds=60, data_length=200000)

        logger.info("  %s 正在通过回测累积下载K线数据...", symbol)
        collected_frames: list[pd.DataFrame] = []
        last_id = -1
        deadline = time.time() + 900

        while True:
            try:
                api.wait_update(deadline=deadline)
            except BacktestFinished:
                break

            frame = klines.copy()
            frame = frame[frame["datetime"] != 0]
            if frame.empty:
                if time.time() > deadline:
                    logger.warning("  %s 回测下载超时且无有效数据", symbol)
                    break
                continue

            if time.time() > deadline:
                logger.warning("  %s 回测下载超时，使用已累计数据", symbol)
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

        frame = _normalize_minute_frame(pd.concat(collected_frames, ignore_index=True), start_dt, end_dt)
        if frame is not None:
            logger.info("  %s 使用回测累积下载 %d bars", symbol, len(frame))
        return frame

    except Exception as exc:
        logger.error("  %s 回测下载失败: %s", symbol, exc)
        return None
    finally:
        if api is not None:
            try:
                api.close()
            except Exception:
                pass


def backfill_single_contract(
    symbol: str,
    start_date: str,
    end_date: str,
    output_dir: Path,
    tq_account: str,
    tq_password: str,
) -> bool:
    """回补单个合约的分钟K线数据

    Args:
        symbol: TqSdk 合约代码，如 "KQ.m@SHFE.rb"
        start_date: 开始日期，格式 "2026-04-10"
        end_date: 结束日期，格式 "2026-04-17"
        output_dir: 输出目录
        tq_account: 天勤账号
        tq_password: 天勤密码

    Returns:
        bool: 是否成功
    """
    try:
        logger.info(f"开始回补 {symbol}: {start_date} ~ {end_date}")

        # 转换日期格式为 datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 包含结束日期

        df = _download_with_data_downloader(symbol, start_dt, end_dt, tq_account, tq_password)
        if df is None:
            df = _download_with_backtest(symbol, start_dt, end_dt, tq_account, tq_password)

        if df is None or df.empty:
            logger.warning(f"  {symbol} 没有可保存的数据")
            return False

        # 按月份分组保存
        filename = symbol_to_filename(symbol)
        for year_month, group in df.groupby(df["datetime"].dt.to_period("M")):
            month_str = year_month.strftime("%Y%m")
            output_file = output_dir / filename / f"{month_str}.parquet"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存为 Parquet
            group.to_parquet(output_file, index=False, engine="pyarrow")
            logger.info(f"  已保存: {output_file} ({len(group)} 条记录)")

        logger.info(f"✅ {symbol} 回补完成，共 {len(df)} 条记录")
        return True

    except Exception as e:
        logger.error(f"❌ {symbol} 回补失败: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="期货分钟K线数据回补工具")
    parser.add_argument("--start", required=True, help="开始日期，格式: 2026-04-10")
    parser.add_argument("--end", required=True, help="结束日期，格式: 2026-04-17")
    parser.add_argument("--symbols", nargs="+", help="指定回补的合约列表（不指定则回补全部35个）")
    parser.add_argument("--account", required=True, help="天勤账号")
    parser.add_argument("--password", required=True, help="天勤密码")
    parser.add_argument("--output", default="/Users/jaybot/JBT/data_backfill/output", help="输出目录")

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 确定要回补的合约列表
    symbols = args.symbols if args.symbols else CONTINUOUS_CONTRACTS

    logger.info(f"开始回补任务: {args.start} ~ {args.end}")
    logger.info(f"回补品种数量: {len(symbols)}")

    success_count = 0
    failed_symbols = []

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] 处理 {symbol}")
        success = backfill_single_contract(
            symbol=symbol,
            start_date=args.start,
            end_date=args.end,
            output_dir=output_dir,
            tq_account=args.account,
            tq_password=args.password,
        )
        if success:
            success_count += 1
        else:
            failed_symbols.append(symbol)

    logger.info("=" * 60)
    logger.info(f"回补任务完成: 成功 {success_count}/{len(symbols)}")
    if failed_symbols:
        logger.warning(f"失败的合约: {', '.join(failed_symbols)}")


if __name__ == "__main__":
    main()
