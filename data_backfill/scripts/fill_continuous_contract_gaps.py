#!/usr/bin/env python3
"""检查并补全连续合约分钟线缺口。

基于 Mini 当前 futures_minute/1m 基线，仅针对连续合约目录 KQ_m_* 做月文件完整性检查，
并使用 TqBacktest 空转方式回补内部缺月与尾部缺月。

默认策略：
- 只把“首个已存在月份之后”的缺月视为需要补全的目标，上市前自然空窗不计入缺口。
- 将连续缺月按窗口分组（默认单窗口最多 6 个月），每个窗口执行一次空转回测。
- 回测返回数据后按月份落盘，并与现有月文件去重合并。
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


LOG_DIR = Path("/Users/jaybot/JBT/data_backfill/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
    handlers=[
        logging.FileHandler(LOG_DIR / "fill_continuous_contract_gaps.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

TARGET_DIR = Path("/Users/jaybot/JBT/data/futures_minute/1m")

CONTINUOUS_CONTRACTS = [
    "KQ.m@CZCE.CF", "KQ.m@CZCE.FG", "KQ.m@CZCE.MA", "KQ.m@CZCE.OI", "KQ.m@CZCE.PF",
    "KQ.m@CZCE.RM", "KQ.m@CZCE.SA", "KQ.m@CZCE.SR", "KQ.m@CZCE.TA", "KQ.m@CZCE.UR",
    "KQ.m@DCE.a", "KQ.m@DCE.c", "KQ.m@DCE.eb", "KQ.m@DCE.i", "KQ.m@DCE.j",
    "KQ.m@DCE.jd", "KQ.m@DCE.jm", "KQ.m@DCE.l", "KQ.m@DCE.lh", "KQ.m@DCE.m",
    "KQ.m@DCE.p", "KQ.m@DCE.pg", "KQ.m@DCE.pp", "KQ.m@DCE.v", "KQ.m@DCE.y",
    "KQ.m@SHFE.ag", "KQ.m@SHFE.al", "KQ.m@SHFE.au", "KQ.m@SHFE.cu", "KQ.m@SHFE.hc",
    "KQ.m@SHFE.rb", "KQ.m@SHFE.ru", "KQ.m@SHFE.sp", "KQ.m@SHFE.ss", "KQ.m@SHFE.zn",
]


@dataclass(frozen=True)
class GapWindow:
    start_month: str
    end_month: str
    missing_months: tuple[str, ...]


def symbol_to_dirname(symbol: str) -> str:
    return symbol.replace(".", "_").replace("@", "_")


def month_range(start_month: str, end_month: str) -> list[str]:
    months: list[str] = []
    year = int(start_month[:4])
    month = int(start_month[4:])
    end_year = int(end_month[:4])
    end_month_num = int(end_month[4:])

    while (year, month) <= (end_year, end_month_num):
        months.append(f"{year}{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1

    return months


def next_month(month_str: str) -> str:
    year = int(month_str[:4])
    month = int(month_str[4:]) + 1
    if month == 13:
        return f"{year + 1}01"
    return f"{year}{month:02d}"


def split_into_windows(missing_months: list[str], max_months_per_window: int) -> list[GapWindow]:
    if not missing_months:
        return []

    windows: list[GapWindow] = []
    chunk: list[str] = [missing_months[0]]

    for month in missing_months[1:]:
        is_consecutive = month == next_month(chunk[-1])
        if is_consecutive and len(chunk) < max_months_per_window:
            chunk.append(month)
            continue

        windows.append(GapWindow(chunk[0], chunk[-1], tuple(chunk)))
        chunk = [month]

    windows.append(GapWindow(chunk[0], chunk[-1], tuple(chunk)))
    return windows


def month_bounds(month_str: str) -> tuple[datetime, datetime]:
    start_dt = datetime.strptime(month_str + "01", "%Y%m%d")
    end_dt = datetime.strptime(next_month(month_str) + "01", "%Y%m%d")
    return start_dt, end_dt


def normalize_minute_frame(df: pd.DataFrame, start_dt: datetime, end_dt: datetime) -> pd.DataFrame | None:
    if df is None or df.empty or "datetime" not in df.columns:
        return None

    frame = df.copy()
    parsed = pd.to_datetime(frame["datetime"], errors="coerce")
    if parsed.isna().all():
        numeric = pd.to_numeric(frame["datetime"], errors="coerce")
        parsed = pd.to_datetime(numeric, unit="ns", utc=True, errors="coerce")
        parsed = parsed.dt.tz_convert("Asia/Shanghai").dt.tz_localize(None)
    elif getattr(parsed.dt, "tz", None) is not None:
        parsed = parsed.dt.tz_convert("Asia/Shanghai").dt.tz_localize(None)

    frame["datetime"] = parsed
    frame = frame.dropna(subset=["datetime"])
    frame = frame[(frame["datetime"] >= pd.Timestamp(start_dt)) & (frame["datetime"] < pd.Timestamp(end_dt))]
    if frame.empty:
        return None

    return frame.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")


def list_existing_months(symbol: str, target_dir: Path) -> list[str]:
    symbol_dir = target_dir / symbol_to_dirname(symbol)
    if not symbol_dir.exists():
        return []
    return sorted(
        path.stem
        for path in symbol_dir.glob("*.parquet")
        if path.stem.isdigit() and len(path.stem) == 6
    )


def detect_missing_months(symbol: str, start_month: str, end_month: str, target_dir: Path) -> tuple[list[str], list[str]]:
    existing_months = list_existing_months(symbol, target_dir)
    if not existing_months:
        return [], []

    anchor_start = max(start_month, existing_months[0])
    expected_months = month_range(anchor_start, end_month)
    missing_months = [month for month in expected_months if month not in existing_months]
    return existing_months, missing_months


def build_gap_windows(
    existing_months: list[str],
    missing_months: list[str],
    *,
    start_month: str,
    end_month: str,
    max_months_per_window: int,
    full_range_backtest: bool,
) -> list[GapWindow]:
    if not missing_months:
        return []

    if full_range_backtest:
        anchor_start = max(start_month, existing_months[0])
        return [GapWindow(anchor_start, end_month, tuple(missing_months))]

    return split_into_windows(missing_months, max_months_per_window)


def download_gap_window_with_idle_backtest(
    symbol: str,
    window: GapWindow,
    *,
    tq_account: str,
    tq_password: str,
    data_length: int,
    timeout_seconds: int,
) -> pd.DataFrame | None:
    from tqsdk import BacktestFinished, TqApi, TqAuth, TqBacktest

    start_dt, _ = month_bounds(window.start_month)
    _, end_dt = month_bounds(window.end_month)

    api = None
    collected_frames: list[pd.DataFrame] = []
    last_id = -1

    try:
        api = TqApi(
            auth=TqAuth(tq_account, tq_password),
            backtest=TqBacktest(start_dt=start_dt, end_dt=end_dt),
            web_gui=False,
        )
        klines = api.get_kline_serial(symbol, duration_seconds=60, data_length=data_length)
        logger.info(
            "空转回测 %s: %s~%s (%d months, data_length=%d)",
            symbol,
            window.start_month,
            window.end_month,
            len(window.missing_months),
            data_length,
        )

        deadline = time.time() + timeout_seconds
        while True:
            try:
                api.wait_update(deadline=deadline)
            except BacktestFinished:
                break

            frame = klines.copy()
            frame = frame[frame["datetime"] != 0]
            if frame.empty:
                if time.time() > deadline:
                    logger.warning("%s %s~%s 超时且无有效数据", symbol, window.start_month, window.end_month)
                    break
                continue

            new_rows = frame[frame["id"] > last_id] if last_id >= 0 else frame
            if new_rows.empty:
                if time.time() > deadline:
                    logger.warning("%s %s~%s 超时，使用已累计数据", symbol, window.start_month, window.end_month)
                    break
                continue

            collected_frames.append(new_rows.copy())
            last_id = int(new_rows["id"].max())

        if not collected_frames:
            return None

        merged = pd.concat(collected_frames, ignore_index=True)
        normalized = normalize_minute_frame(merged, start_dt, end_dt)
        if normalized is not None:
            logger.info(
                "%s %s~%s 回测完成: %d bars",
                symbol,
                window.start_month,
                window.end_month,
                len(normalized),
            )
        return normalized
    finally:
        if api is not None:
            try:
                api.close()
            except Exception:
                pass


def save_frame_by_month(symbol: str, frame: pd.DataFrame, target_dir: Path) -> int:
    symbol_dir = target_dir / symbol_to_dirname(symbol)
    symbol_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    for period, group in frame.groupby(frame["datetime"].dt.to_period("M")):
        month_str = period.strftime("%Y%m")
        file_path = symbol_dir / f"{month_str}.parquet"
        group = group.sort_values("datetime")

        if file_path.exists():
            old = pd.read_parquet(file_path)
            old["datetime"] = pd.to_datetime(old["datetime"], errors="coerce")
            group = pd.concat([old, group], ignore_index=True)
            group = group.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")

        group.to_parquet(file_path, index=False, engine="pyarrow")
        total_rows += len(group)
        logger.info("已写入 %s (%d rows)", file_path, len(group))

    return total_rows


def summarize_gaps(symbols: Iterable[str], start_month: str, end_month: str, target_dir: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for symbol in symbols:
        _, missing_months = detect_missing_months(symbol, start_month, end_month, target_dir)
        if missing_months:
            result[symbol] = missing_months
    return result


def run_gap_fill(
    symbols: list[str],
    *,
    start_month: str,
    end_month: str,
    target_dir: Path,
    tq_account: str,
    tq_password: str,
    data_length: int,
    timeout_seconds: int,
    max_months_per_window: int,
    full_range_backtest: bool,
    check_only: bool,
) -> int:
    gap_map = summarize_gaps(symbols, start_month, end_month, target_dir)
    logger.info("基线扫描完成: %d/%d 个品种存在缺口", len(gap_map), len(symbols))

    for symbol, missing_months in gap_map.items():
        existing_months, _ = detect_missing_months(symbol, start_month, end_month, target_dir)
        windows = build_gap_windows(
            existing_months,
            missing_months,
            start_month=start_month,
            end_month=end_month,
            max_months_per_window=max_months_per_window,
            full_range_backtest=full_range_backtest,
        )
        logger.info(
            "%s 缺口月份=%d, 窗口=%d, 示例=%s",
            symbol,
            len(missing_months),
            len(windows),
            ",".join(missing_months[:12]),
        )

    if check_only or not gap_map:
        remaining = summarize_gaps(symbols, start_month, end_month, target_dir)
        logger.info("检查结束: remaining_symbols=%d", len(remaining))
        return 0 if not remaining else 1

    filled_windows = 0
    failed_windows: list[str] = []

    for symbol, missing_months in gap_map.items():
        existing_months, _ = detect_missing_months(symbol, start_month, end_month, target_dir)
        windows = build_gap_windows(
            existing_months,
            missing_months,
            start_month=start_month,
            end_month=end_month,
            max_months_per_window=max_months_per_window,
            full_range_backtest=full_range_backtest,
        )
        for window in windows:
            frame = download_gap_window_with_idle_backtest(
                symbol,
                window,
                tq_account=tq_account,
                tq_password=tq_password,
                data_length=data_length,
                timeout_seconds=timeout_seconds,
            )
            if frame is None or frame.empty:
                failed_windows.append(f"{symbol}:{window.start_month}-{window.end_month}")
                logger.warning("%s %s~%s 未返回可保存数据", symbol, window.start_month, window.end_month)
                continue
            save_frame_by_month(symbol, frame, target_dir)
            filled_windows += 1

    remaining = summarize_gaps(symbols, start_month, end_month, target_dir)
    logger.info("回补结束: success_windows=%d, failed_windows=%d, remaining_symbols=%d",
                filled_windows, len(failed_windows), len(remaining))
    if failed_windows:
        logger.warning("失败窗口: %s", ", ".join(failed_windows))
    if remaining:
        for symbol, missing_months in remaining.items():
            logger.warning("剩余缺口 %s: %s", symbol, ",".join(missing_months[:20]))
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查并补全连续合约分钟线缺口")
    parser.add_argument("--symbols", nargs="+", help="指定连续合约列表，默认全部 35 个")
    parser.add_argument("--start-month", default="201801", help="检查起始月份 YYYYMM，默认 201801")
    parser.add_argument("--end-month", default=datetime.now().strftime("%Y%m"), help="检查结束月份 YYYYMM，默认当前月")
    parser.add_argument("--target-dir", default=str(TARGET_DIR), help="连续合约分钟线目录")
    parser.add_argument("--data-length", type=int, default=5000, help="get_kline_serial data_length，默认 5000")
    parser.add_argument("--timeout-seconds", type=int, default=900, help="单窗口回测超时秒数，默认 900")
    parser.add_argument("--max-months-per-window", type=int, default=6, help="连续缺月单窗口最多合并几个月，默认 6")
    parser.add_argument("--full-range-backtest", action="store_true", help="对存在缺口的品种直接从锚点月回测到结束月")
    parser.add_argument("--check-only", action="store_true", help="只检查缺口，不执行回补")
    parser.add_argument("--account", default=os.environ.get("TQSDK_PHONE", ""), help="天勤账号")
    parser.add_argument("--password", default=os.environ.get("TQSDK_PASSWORD", ""), help="天勤密码")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    symbols = args.symbols if args.symbols else CONTINUOUS_CONTRACTS

    if not args.check_only and (not args.account or not args.password):
        logger.error("缺少 TQSDK_PHONE / TQSDK_PASSWORD")
        return 2

    if len(args.start_month) != 6 or len(args.end_month) != 6:
        logger.error("start-month / end-month 必须是 YYYYMM")
        return 2

    return run_gap_fill(
        symbols=symbols,
        start_month=args.start_month,
        end_month=args.end_month,
        target_dir=Path(args.target_dir),
        tq_account=args.account,
        tq_password=args.password,
        data_length=args.data_length,
        timeout_seconds=args.timeout_seconds,
        max_months_per_window=args.max_months_per_window,
        full_range_backtest=args.full_range_backtest,
        check_only=args.check_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())