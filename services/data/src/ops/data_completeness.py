#!/usr/bin/env python3
"""
check_data_completeness.py — 每日数据完整性监控
每交易日 20:30 运行, 检查当天所有数据源是否采集完整.

检查范围:
  1) 内盘期货日线 (tushare parquet)
  2) 外盘期货日线 (parquet 目录)
  3) 持仓/仓单 (position_daily)
  4) 宏观数据 (macro_global/overseas)
  5) 情绪面 (sentiment)
  6) 波动率 (volatility_index)
  7) 航运 (shipping)

输出:
  - 终端打印汇总表
  - BotQuan_Data/logs/completeness_{date}.json

用法:
  python scripts/check_data_completeness.py              # 检查今天
  python scripts/check_data_completeness.py --date 20260320
  python scripts/check_data_completeness.py --days 3     # 检查最近 3 天

Crontab 示例 (每交易日 20:30):
  30 20 * * 1-5 cd ~/J_BotQuant && .venv/bin/python3 scripts/check_data_completeness.py
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────
DATA_DIR = Path(os.environ.get("DATA_STORAGE_ROOT", os.path.expanduser("~/jbt-data")))
PARQUET_DIR = DATA_DIR / "parquet"
LOG_DIR = DATA_DIR / "logs"

# 内盘日线目录 (在 parquet 下, 按合约目录存放)
DOMESTIC_DIRS = [
    "CZCE.MA405", "CZCE.SA405",
    "DCE.i2405", "DCE.i2410", "DCE.m2405", "DCE.p2405",
    "SHFE.au2406", "SHFE.cu2405", "SHFE.rb2405", "SHFE.rb2410",
]

# 外盘日线目录
OVERSEAS_DIRS = [
    "CBOT.ZC", "CBOT.ZS", "CBOT.ZW", "CBOT.ZL", "CBOT.ZM",
    "CME.ES", "CME.NQ",
    "COMEX.GC", "COMEX.HG", "COMEX.SI",
    "ICE.B", "ICE.CT", "ICE.SB",
    "NYMEX.CL", "NYMEX.NG", "NYMEX.HO", "NYMEX.RB",
    "NYMEX.PA", "NYMEX.PL",
]

# 宏观 parquet 目录
MACRO_DIRS = [
    "AU_cpi_yoy", "AU_unemployment",
    "CA_cpi_yoy", "CA_unemployment",
    "CN_cpi_yoy", "CN_ppi_yoy",
    "EU_cpi_yoy", "EU_gdp_yoy", "EU_ppi_mom",
    "JP_cpi_yoy", "JP_unemployment",
    "UK_cpi_yoy", "UK_gdp_yoy", "UK_unemployment",
    "US_cpi_yoy", "US_pmi", "US_ppi_yoy",
]

# 波动率
VOLATILITY_DIRS = ["300etf_qvix", "50etf_qvix", "cboe_vix", "cboe_vxn"]

# 航运
SHIPPING_DIRS = ["bdi", "bci", "bcti", "bpi"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("completeness")


def is_trading_day(dt: datetime) -> bool:
    """简单判断: 周一~周五视为交易日 (不含节假日)."""
    return dt.weekday() < 5


def check_parquet_updated(directory: Path, target_date: str) -> dict:
    """
    检查 parquet 目录下是否有 target_date 的数据.
    target_date: 'YYYYMMDD' 或 'YYYY-MM-DD'
    返回 {exists: bool, latest_file: str, file_count: int}
    """
    result = {"exists": False, "latest_file": "", "file_count": 0}
    if not directory.exists():
        return result

    parquet_files = sorted(directory.glob("*.parquet"))
    result["file_count"] = len(parquet_files)
    if parquet_files:
        result["latest_file"] = parquet_files[-1].name

    # 检查文件名或修改时间是否包含目标日期
    date_str = target_date.replace("-", "")
    for f in parquet_files:
        if date_str in f.stem or target_date in f.stem:
            result["exists"] = True
            break

    # 如果按文件名找不到, 检查最新文件的修改时间
    if not result["exists"] and parquet_files:
        latest_mtime = datetime.fromtimestamp(parquet_files[-1].stat().st_mtime)
        if latest_mtime.strftime("%Y%m%d") == date_str:
            result["exists"] = True

    return result


def check_json_updated(directory: Path, target_date: str) -> dict:
    """检查目录下 JSON 文件是否包含目标日期数据."""
    result = {"exists": False, "latest_file": "", "file_count": 0}
    if not directory.exists():
        return result

    json_files = sorted(directory.glob("*.json"))
    result["file_count"] = len(json_files)
    if json_files:
        result["latest_file"] = json_files[-1].name

    date_str = target_date.replace("-", "")
    for f in json_files:
        if date_str in f.stem or target_date in f.stem:
            result["exists"] = True
            break

    return result


def check_category(category_name: str, dirs: list, base: Path,
                   target_date: str) -> tuple:
    """
    检查一个数据类别下所有子目录.
    返回 (ok_count, total, details_list)
    """
    ok = 0
    details = []
    for d in dirs:
        info = check_parquet_updated(base / d, target_date)
        status = "✅" if info["exists"] else "❌"
        if info["exists"]:
            ok += 1
        details.append({
            "name": d,
            "status": status,
            "file_count": info["file_count"],
            "latest_file": info["latest_file"],
        })
    return ok, len(dirs), details


def run_check(target_date: str) -> dict:
    """
    对指定日期执行全量完整性检查.
    返回汇总 dict.
    """
    report = {
        "date": target_date,
        "checked_at": datetime.now().isoformat(),
        "categories": {},
        "summary": {"total": 0, "ok": 0, "missing": 0},
    }

    # 1) 内盘期货日线
    ok, total, details = check_category(
        "domestic_daily", DOMESTIC_DIRS, DATA_DIR, target_date)
    report["categories"]["domestic_daily"] = {
        "ok": ok, "total": total, "details": details}

    # 2) 外盘期货日线
    ok2, total2, details2 = check_category(
        "overseas_daily", OVERSEAS_DIRS, PARQUET_DIR, target_date)
    report["categories"]["overseas_daily"] = {
        "ok": ok2, "total": total2, "details": details2}

    # 3) 宏观数据
    ok3, total3, details3 = check_category(
        "macro", MACRO_DIRS, PARQUET_DIR, target_date)
    report["categories"]["macro"] = {
        "ok": ok3, "total": total3, "details": details3}

    # 4) 波动率
    ok4, total4, details4 = check_category(
        "volatility", VOLATILITY_DIRS, PARQUET_DIR, target_date)
    report["categories"]["volatility"] = {
        "ok": ok4, "total": total4, "details": details4}

    # 5) 航运
    ok5, total5, details5 = check_category(
        "shipping", SHIPPING_DIRS, PARQUET_DIR, target_date)
    report["categories"]["shipping"] = {
        "ok": ok5, "total": total5, "details": details5}

    # 6) 持仓 position_daily
    pos_dir = DATA_DIR / "position_daily"
    pos_info = check_parquet_updated(pos_dir, target_date)
    pos_ok = 1 if pos_info["exists"] else 0
    report["categories"]["position"] = {
        "ok": pos_ok, "total": 1,
        "details": [{"name": "position_daily", "status": "✅" if pos_ok else "❌",
                      "file_count": pos_info["file_count"],
                      "latest_file": pos_info["latest_file"]}],
    }

    # 7) 情绪面 sentiment
    sent_dir = DATA_DIR / "sentiment"
    sent_info = check_parquet_updated(sent_dir, target_date)
    sent_ok = 1 if sent_info["exists"] else 0
    report["categories"]["sentiment"] = {
        "ok": sent_ok, "total": 1,
        "details": [{"name": "sentiment", "status": "✅" if sent_ok else "❌",
                      "file_count": sent_info["file_count"],  # noqa: E127
                      "latest_file": sent_info["latest_file"]}],
    }

    # 8) 新闻 (API + RSS)
    news_api_dir = DATA_DIR / "news_api"
    news_rss_dir = DATA_DIR / "news_rss"
    news_api_info = check_json_updated(news_api_dir, target_date)
    news_rss_info = check_json_updated(news_rss_dir, target_date)
    news_ok = sum([1 for x in [news_api_info, news_rss_info] if x["exists"]])
    report["categories"]["news"] = {
        "ok": news_ok, "total": 2,
        "details": [
            {"name": "news_api", "status": "✅" if news_api_info["exists"] else "❌",
             "file_count": news_api_info["file_count"],
             "latest_file": news_api_info["latest_file"]},
            {"name": "news_rss", "status": "✅" if news_rss_info["exists"] else "❌",
             "file_count": news_rss_info["file_count"],
             "latest_file": news_rss_info["latest_file"]},
        ],
    }

    # 9) 海外宏观 (overseas macro)
    overseas_macro_dir = DATA_DIR / "macro_global" / "overseas"
    ov_info = check_parquet_updated(overseas_macro_dir, target_date)
    ov_ok = 1 if ov_info["exists"] else 0
    report["categories"]["overseas_macro"] = {
        "ok": ov_ok, "total": 1,
        "details": [{"name": "overseas_macro", "status": "✅" if ov_ok else "❌",
                      "file_count": ov_info["file_count"],  # noqa: E127
                      "latest_file": ov_info["latest_file"]}],
    }

    # ── 汇总 ──
    total_ok = sum(c["ok"] for c in report["categories"].values())
    total_all = sum(c["total"] for c in report["categories"].values())
    report["summary"]["ok"] = total_ok
    report["summary"]["total"] = total_all
    report["summary"]["missing"] = total_all - total_ok
    report["summary"]["rate"] = (
        f"{total_ok / total_all * 100:.1f}%" if total_all > 0 else "N/A")

    return report


def print_report(report: dict):
    """终端打印可读报告."""
    print(f"\n{'=' * 60}")
    print("  BotQuant 数据完整性报告")
    print(f"  日期: {report['date']}  检查时间: {report['checked_at'][:19]}")
    print(f"{'=' * 60}")

    for cat_name, cat in report["categories"].items():
        status_icon = "✅" if cat["ok"] == cat["total"] else "⚠️"
        print(f"\n{status_icon}  {cat_name}  ({cat['ok']}/{cat['total']})")
        for item in cat["details"]:
            print(f"    {item['status']}  {item['name']:<25} "
                  f"files={item['file_count']}  latest={item.get('latest_file', '-')}")

    s = report["summary"]
    print(f"\n{'─' * 60}")
    print(f"  汇总: {s['ok']}/{s['total']} ({s['rate']})  "
          f"缺失: {s['missing']}")
    print(f"{'═' * 60}\n")


def save_report(report: dict, target_date: str):
    """保存 JSON 报告."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LOG_DIR / f"completeness_{target_date}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info("报告已保存: %s", out_path)


def main():
    parser = argparse.ArgumentParser(description="BotQuant 数据完整性监控")
    parser.add_argument("--date", type=str, default=None,
                        help="检查目标日期 (YYYYMMDD), 默认今天")
    parser.add_argument("--days", type=int, default=1,
                        help="向前检查天数 (默认 1=仅当天)")
    args = parser.parse_args()

    if args.date:
        start = datetime.strptime(args.date, "%Y%m%d")
        dates = [start.strftime("%Y%m%d")]
    else:
        today = datetime.now()
        dates = []
        for i in range(args.days):
            dt = today - timedelta(days=i)
            dates.append(dt.strftime("%Y%m%d"))

    all_missing = 0
    for d in dates:
        report = run_check(d)
        print_report(report)
        save_report(report, d)
        all_missing += report["summary"]["missing"]

    if all_missing > 0:
        logger.warning("共 %d 项数据缺失, 请检查采集脚本", all_missing)
        sys.exit(1)
    else:
        logger.info("所有数据完整 ✅")


if __name__ == "__main__":
    main()
