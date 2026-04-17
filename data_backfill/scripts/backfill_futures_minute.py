#!/usr/bin/env python3
"""
期货分钟K线数据回补工具
使用 TqSdk 回测机制补全缺失的历史数据
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest

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

        # 初始化 TqApi（回测模式）
        api = TqApi(
            auth=TqAuth(tq_account, tq_password),
            backtest=TqBacktest(start_dt=start_dt, end_dt=end_dt),
            web_gui=False,  # 不启动 Web GUI
        )

        # 订阅分钟K线（增加数据长度以覆盖更长时间段）
        klines = api.get_kline_serial(symbol, duration_seconds=60, data_length=200000)

        # 空转回测，让 TqSdk 下载数据
        logger.info(f"  正在下载 {symbol} 的K线数据...")
        while not api.is_changing(klines.iloc[-1], "datetime"):
            api.wait_update()

        # 提取数据
        df = klines.copy()
        df = df[df["datetime"] != 0]  # 过滤无效数据

        if df.empty:
            logger.warning(f"  {symbol} 没有数据")
            api.close()
            return False

        # 转换时间格式
        df["datetime"] = pd.to_datetime(df["datetime"], unit="ns")

        # 按月份分组保存
        filename = symbol_to_filename(symbol)
        for year_month, group in df.groupby(df["datetime"].dt.to_period("M")):
            month_str = year_month.strftime("%Y%m")
            output_file = output_dir / filename / f"{month_str}.parquet"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存为 Parquet
            group.to_parquet(output_file, index=False, engine="pyarrow")
            logger.info(f"  已保存: {output_file} ({len(group)} 条记录)")

        api.close()
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
