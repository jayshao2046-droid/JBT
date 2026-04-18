#!/usr/bin/env python3
"""补全期货日K数据 - 2026-04-09 至 2026-04-16"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "data"))

from datetime import datetime, timedelta
from src.scheduler.pipeline import run_tushare_futures_pipeline
from src.utils.config import get_config

# 36个主力合约
SYMBOLS = [
    "A2605.DCE", "AL2605.SHF", "BU2605.SHF", "C2605.DCE", "CU2605.SHF",
    "EB2605.DCE", "FG2605.ZCE", "FU2605.SHF", "HC2605.SHF", "I2605.DCE",
    "J2605.DCE", "JD2605.DCE", "JM2605.DCE", "L2605.DCE", "LU2605.SHF",
    "M2605.DCE", "MA2605.ZCE", "NI2605.SHF", "NR2605.SHF", "P2605.DCE",
    "PB2605.SHF", "PG2605.DCE", "PP2605.DCE", "RB2605.SHF", "RU2605.SHF",
    "SC2605.INE", "SF2605.ZCE", "SM2605.ZCE", "SN2605.SHF", "SP2605.SHF",
    "SS2605.SHF", "TA2605.ZCE", "V2605.DCE", "Y2605.DCE", "ZC2605.ZCE", "ZN2605.SHF",
]

# 补采日期范围：4月9日至16日
START_DATE = datetime(2026, 4, 9)
END_DATE = datetime(2026, 4, 16)

def main():
    config = get_config()

    # 生成日期列表（跳过周末）
    dates = []
    current = START_DATE
    while current <= END_DATE:
        # 跳过周末
        if current.weekday() < 5:  # 0-4 是周一到周五
            dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    print(f"补采日期: {dates}")
    print(f"品种数量: {len(SYMBOLS)}")
    print(f"总任务数: {len(dates)} 天 × {len(SYMBOLS)} 品种 = {len(dates) * len(SYMBOLS)}")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    for date_str in dates:
        print(f"\n[{date_str}] 开始采集...")
        date_success = 0

        for symbol in SYMBOLS:
            try:
                result = run_tushare_futures_pipeline(
                    ts_code=symbol,
                    trade_date=date_str,
                    config=config,
                    symbol=symbol,
                )
                if result:
                    success_count += 1
                    date_success += 1
                    print(f"  ✓ {symbol}: {result}")
                else:
                    fail_count += 1
                    print(f"  ✗ {symbol}: 无数据")
            except Exception as e:
                fail_count += 1
                print(f"  ✗ {symbol}: {e}")

        print(f"[{date_str}] 完成: {date_success}/{len(SYMBOLS)} 成功")

    print("\n" + "=" * 60)
    print(f"补采完成: 成功 {success_count}, 失败 {fail_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
