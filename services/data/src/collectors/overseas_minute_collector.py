"""Overseas futures minute K-line collector — multi-source with fallback.

D107: yfinance 单源
D108: 四层数据源自动切换 + 指数退避
  Layer 1: yfinance (主源, 1min 7天 / 5min 60天)
  Layer 2: Alpha Vantage (备源1, 500次/天, premium intraday)
  Layer 3: Twelve Data (备源2, 8次/分钟免费, subprocess+curl)
  Layer 4: AkShare futures_global_hist_em (日线降级)
  限流检测: 指数退避 5→10→20 分钟
"""

from __future__ import annotations

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import os
import time
from datetime import datetime, timedelta
from typing import Any

from services.data.src.collectors.base import BaseCollector


# ── yfinance 分钟级品种 (20+1) ──────────────────────────
YFINANCE_MINUTE_MAP: dict[str, tuple[str, str, str]] = {
    # NYMEX 能源 (4)
    "NYMEX.CL": ("CL=F", "WTI原油", "NYMEX"),
    "NYMEX.NG": ("NG=F", "天然气", "NYMEX"),
    "NYMEX.HO": ("HO=F", "取暖油", "NYMEX"),
    "NYMEX.RB": ("RB=F", "汽油", "NYMEX"),
    # COMEX 金属 (5)
    "COMEX.GC": ("GC=F", "黄金", "COMEX"),
    "COMEX.SI": ("SI=F", "白银", "COMEX"),
    "COMEX.HG": ("HG=F", "铜", "COMEX"),
    "NYMEX.PA": ("PA=F", "钯", "NYMEX"),
    "NYMEX.PL": ("PL=F", "铂", "NYMEX"),
    # CME 股指/国债 (4)
    "CME.ES": ("ES=F", "标普500期货", "CME"),
    "CME.NQ": ("NQ=F", "纳斯达克期货", "CME"),
    "CBOT.YM": ("YM=F", "道琼斯期货", "CBOT"),
    "CBOT.ZB": ("ZB=F", "美国国债", "CBOT"),
    # CBOT 农产品 (5)
    "CBOT.ZC": ("ZC=F", "玉米", "CBOT"),
    "CBOT.ZS": ("ZS=F", "大豆", "CBOT"),
    "CBOT.ZW": ("ZW=F", "小麦", "CBOT"),
    "CBOT.ZM": ("ZM=F", "豆粕", "CBOT"),
    "CBOT.ZL": ("ZL=F", "豆油", "CBOT"),
    # ICE 软商品 / 农产品 (5)
    "ICE.B": ("BZ=F", "布伦特原油", "ICE"),
    "ICE.CT": ("CT=F", "棉花", "ICE"),       # CF对标
    "ICE.SB": ("SB=F", "白糖", "ICE"),       # SR对标
    "ICE.RS": ("RS=F", "油菜籽/菜籽油", "ICE"),  # OI/RM对标（新增）
    "ICE.KC": ("KC=F", "咖啡", "ICE"),
    "ICE.CC": ("CC=F", "可可", "ICE"),
    # CME 畜牧/钢铁 (2，新增)
    "CME.HE": ("HE=F", "瘦肉猪", "CME"),    # LH/JD对标
    "CME.HRC": ("HRC=F", "HRC热轧卷板", "CME"),  # RB/HC对标
    # CME 股指补（1）
    "CME.RTY": ("RTY=F", "罗素2000", "CME"),
}

# Alpha Vantage 代码映射 (备源1, premium intraday)
ALPHAVANTAGE_MAP: dict[str, str] = {
    "NYMEX.CL": "CL", "NYMEX.NG": "NG",
    "COMEX.GC": "GC", "COMEX.SI": "SI", "COMEX.HG": "HG",
    "CBOT.ZC": "ZC", "CBOT.ZS": "ZS", "CBOT.ZW": "ZW",
}

# Twelve Data 代码映射 (备源2, 免费版 8 credits/min)
# 免费版支持: CL/ES/NG/SI/HG/NQ + 部分品种
# 不支持(需 Grow/Venture plan): GC/ZC 等
TWELVEDATA_MAP: dict[str, str] = {
    "NYMEX.CL": "CL", "NYMEX.NG": "NG",
    "NYMEX.HO": "HO", "NYMEX.RB": "RB",
    "COMEX.SI": "SI", "COMEX.HG": "HG",
    "CME.ES": "ES", "CME.NQ": "NQ",
    "CBOT.YM": "YM",
    "CBOT.ZS": "ZS", "CBOT.ZW": "ZW",
    "CBOT.ZM": "ZM", "CBOT.ZL": "ZL",
    "ICE.B": "BZ", "ICE.CT": "CT", "ICE.SB": "SB",
    "NYMEX.PA": "PA", "NYMEX.PL": "PL",
}

# ── 仅日线品种 (10) → AkShare ────────────────────────────
DAILY_ONLY_MAP: dict[str, tuple[str, str, str]] = {
    "LME.AHD": ("AHD", "LME铝", "LME"),   # AL对标
    "LME.CAD": ("CAD", "LME铜", "LME"),   # CU额外
    "LME.NID": ("NID", "LME镍", "LME"),   # SS不锈钢对标
    "LME.PBD": ("PBD", "LME铅", "LME"),
    "LME.SND": ("SND", "LME锡", "LME"),
    "LME.ZSD": ("ZSD", "LME锌", "LME"),   # ZN对标
    "SGX.CN": ("CN", "富时中国A50", "SGX"),
}

# ── 限流退避状态 (模块级) ─────────────────────────────────
_backoff_state: dict[str, float] = {}  # source_name → resume_timestamp
_BACKOFF_STEPS = [300, 600, 1200]  # 5min → 10min → 20min
_backoff_level: dict[str, int] = {}  # source_name → current level


def _is_rate_limited(source: str) -> bool:
    """检查某数据源是否处于退避冷却中."""
    resume_at = _backoff_state.get(source, 0)
    return time.time() < resume_at


def _trigger_backoff(source: str) -> int:
    """触发退避, 返回冷却秒数."""
    level = _backoff_level.get(source, 0)
    wait = _BACKOFF_STEPS[min(level, len(_BACKOFF_STEPS) - 1)]
    _backoff_state[source] = time.time() + wait
    _backoff_level[source] = level + 1
    return wait


def _reset_backoff(source: str) -> None:
    """成功后重置退避状态."""
    _backoff_state.pop(source, None)
    _backoff_level.pop(source, None)


class OverseasMinuteCollector(BaseCollector):
    """Collect overseas futures minute K-line — multi-source with fallback.

    Layer 1: yfinance → 21 品种分钟级
    Layer 2: Alpha Vantage → 8 品种分钟级 (premium, 500次/天)
    Layer 3: Twelve Data → 18 品种分钟级 (免费, 8次/min)
    Layer 4: AkShare → 日线降级
    限流: 指数退避 5→10→20min
    """

    def __init__(
        self,
        *,
        symbols: list[str] | None = None,
        period: str = "5d",
        interval: str = "1m",
        **kwargs: Any,
    ) -> None:
        kwargs.pop('name', None)
        super().__init__(name="overseas_minute", **kwargs)
        self.symbols = symbols or list(YFINANCE_MINUTE_MAP.keys())
        self.period = period
        self.interval = interval
        self._av_api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
        self._td_api_key = os.environ.get("TWELVE_DATA_API_KEY", "")

    def collect(
        self,
        *,
        symbols: list[str] | None = None,
        period: str | None = None,
        interval: str | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        symbol_list = symbols or self.symbols
        cur_period = period or self.period
        cur_interval = interval or self.interval

        records: list[dict[str, Any]] = []
        failed_symbols: list[str] = []

        # Layer 1: yfinance (主源)
        if not _is_rate_limited("yfinance"):
            yf_records, yf_failed = self._fetch_yfinance(
                symbol_list=symbol_list, period=cur_period,
                interval=cur_interval, as_of=as_of,
            )
            records.extend(yf_records)
            failed_symbols = yf_failed
        else:
            self.logger.info("yfinance 处于退避冷却中, 跳过")
            failed_symbols = [s for s in symbol_list if s in YFINANCE_MINUTE_MAP]

        # Layer 2: Alpha Vantage (备源1, 仅对yfinance失败的品种)
        if failed_symbols and self._av_api_key and not _is_rate_limited("alphavantage"):
            av_targets = [s for s in failed_symbols if s in ALPHAVANTAGE_MAP]
            if av_targets:
                av_records, av_failed = self._fetch_alpha_vantage(
                    symbol_list=av_targets, interval=cur_interval,
                )
                records.extend(av_records)
                # 更新失败列表
                succeeded_av = {s for s in av_targets if s not in av_failed}
                failed_symbols = [s for s in failed_symbols if s not in succeeded_av]

        # Layer 3: Twelve Data (备源2, 仅对仍失败的品种)
        if failed_symbols and self._td_api_key and not _is_rate_limited("twelvedata"):
            td_targets = [s for s in failed_symbols if s in TWELVEDATA_MAP]
            if td_targets:
                td_records, td_failed = self._fetch_twelve_data(
                    symbol_list=td_targets, interval=cur_interval,
                )
                records.extend(td_records)
                succeeded_td = {s for s in td_targets if s not in td_failed}
                failed_symbols = [s for s in failed_symbols if s not in succeeded_td]

        # Layer 4: AkShare 日线 (最后降级, 仅对仍失败的品种取日线)
        if failed_symbols:
            ak_records = self._fetch_akshare_daily_fallback(symbol_list=failed_symbols)
            records.extend(ak_records)

        # P1-001/P1-006: 品种级采集成功率统计
        total = len(symbol_list)
        success_syms = {r["symbol_or_indicator"] for r in records}
        success_count = len(success_syms & set(symbol_list))
        zero_syms = [s for s in symbol_list if s not in success_syms]
        rate = success_count / total * 100 if total else 0
        self.logger.info(
            "外盘分钟采集汇总: %d/%d 品种成功 (%.1f%%), 0产出: %s",
            success_count, total, rate, zero_syms[:10] if zero_syms else "无",
        )
        if rate < 50:
            self.logger.warning(
                "外盘分钟采集成功率 %.1f%% 低于 50%% 阈值, "
                "请检查 API Key 配置 (AV=%s, TD=%s)",
                rate, bool(self._av_api_key), bool(self._td_api_key),
            )

        if not records:
            self.logger.error("所有外盘数据源均失败, 品种: %s", symbol_list[:5])
        return records

    def _fetch_yfinance(
        self,
        *,
        symbol_list: list[str],
        period: str,
        interval: str,
        as_of: str | None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Layer 1: yfinance 采集, 返回 (records, failed_symbols)."""
        import yfinance as yf

        records: list[dict[str, Any]] = []
        failed: list[str] = []
        rate_limited = False

        for internal_sym in symbol_list:
            mapping = YFINANCE_MINUTE_MAP.get(internal_sym)
            if not mapping:
                continue
            yf_code, cn_name, exchange = mapping

            try:
                ticker = yf.Ticker(yf_code)
                df = ticker.history(period=period, interval=interval)
                time.sleep(0.3)

                if df is None or df.empty:
                    self.logger.warning("yfinance 返回空: %s (%s), 将尝试备源", yf_code, cn_name)
                    failed.append(internal_sym)
                    continue

                for idx, row in df.iterrows():
                    records.append({
                        "source_type": "overseas_minute",
                        "symbol_or_indicator": internal_sym,
                        "timestamp": str(idx),
                        "payload": {
                            "symbol": internal_sym,
                            "yf_code": yf_code,
                            "name": cn_name,
                            "exchange": exchange,
                            "open": float(row.get("Open", 0)),
                            "high": float(row.get("High", 0)),
                            "low": float(row.get("Low", 0)),
                            "close": float(row.get("Close", 0)),
                            "volume": float(row.get("Volume", 0)),
                            "source": "yfinance",
                            "interval": interval,
                            "mode": "live",
                        },
                    })
                self.logger.info("yfinance: %s (%s) rows=%d", yf_code, cn_name, len(df))
                _reset_backoff("yfinance")

            except Exception as exc:
                exc_str = str(exc).lower()
                if "rate" in exc_str or "too many" in exc_str or "429" in exc_str:
                    if not rate_limited:
                        wait = _trigger_backoff("yfinance")
                        self.logger.warning("yfinance 限流, 退避 %ds: %s", wait, exc)
                        rate_limited = True
                    failed.append(internal_sym)
                else:
                    self.logger.warning("yfinance 失败 %s: %s", yf_code, exc)
                    failed.append(internal_sym)

        return records, failed

    def _fetch_alpha_vantage(
        self,
        *,
        symbol_list: list[str],
        interval: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Layer 2: Alpha Vantage 备源 (500次/天, JSON API)."""
        import json
        import urllib.request

        records: list[dict[str, Any]] = []
        failed: list[str] = []
        # Map interval: 1m→1min, 5m→5min etc
        av_interval = interval.replace("m", "min") if interval.endswith("m") else interval

        for internal_sym in symbol_list:
            av_code = ALPHAVANTAGE_MAP.get(internal_sym)
            if not av_code:
                failed.append(internal_sym)
                continue

            url = (
                f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY"
                f"&symbol={av_code}&interval={av_interval}"
                f"&apikey={self._av_api_key}&outputsize=compact&datatype=json"
            )

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "BotQuant/4.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())

                ts_key = f"Time Series ({av_interval})"
                ts_data = data.get(ts_key, {})

                if not ts_data:
                    # 可能限流或无数据
                    if "Note" in data or "Information" in data:
                        wait = _trigger_backoff("alphavantage")
                        self.logger.warning("Alpha Vantage 限流, 退避 %ds", wait)
                    failed.append(internal_sym)
                    continue

                mapping = YFINANCE_MINUTE_MAP.get(internal_sym)
                cn_name = mapping[1] if mapping else av_code
                exchange = mapping[2] if mapping else ""

                for ts_str, bar in ts_data.items():
                    records.append({
                        "source_type": "overseas_minute",
                        "symbol_or_indicator": internal_sym,
                        "timestamp": ts_str,
                        "payload": {
                            "symbol": internal_sym,
                            "name": cn_name,
                            "exchange": exchange,
                            "open": float(bar.get("1. open", 0)),
                            "high": float(bar.get("2. high", 0)),
                            "low": float(bar.get("3. low", 0)),
                            "close": float(bar.get("4. close", 0)),
                            "volume": float(bar.get("5. volume", 0)),
                            "source": "alpha_vantage",
                            "interval": interval,
                            "mode": "live",
                        },
                    })

                self.logger.info("Alpha Vantage: %s rows=%d", av_code, len(ts_data))
                _reset_backoff("alphavantage")
                time.sleep(1.5)  # AV 5次/分钟限制

            except Exception as exc:
                self.logger.warning("Alpha Vantage 失败 %s: %s", av_code, exc)
                failed.append(internal_sym)

        return records, failed

    def _fetch_twelve_data(
        self,
        *,
        symbol_list: list[str],
        interval: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Layer 3: Twelve Data 备源 (免费 8 credits/min, subprocess+curl).

        Note: Mini Python 3.9.6 urllib SSL 与 Twelve Data TLS 不兼容,
        因此使用 subprocess 调用 curl 绕过 SSL 问题。
        """
        import json
        import subprocess

        records: list[dict[str, Any]] = []
        failed: list[str] = []
        # Map interval: 1m→1min, 5m→5min
        td_interval = interval.replace("m", "min") if interval.endswith("m") else interval
        credits_used = 0

        for internal_sym in symbol_list:
            td_code = TWELVEDATA_MAP.get(internal_sym)
            if not td_code:
                failed.append(internal_sym)
                continue

            # 免费版 8 credits/min — 保守限制每轮最多 7 次
            if credits_used >= 7:
                self.logger.info("Twelve Data credits 本轮用尽, 剩余品种跳过")
                failed.append(internal_sym)
                continue

            url = (
                f"https://api.twelvedata.com/time_series"
                f"?symbol={td_code}&interval={td_interval}"
                f"&outputsize=30&apikey={self._td_api_key}"
            )

            try:
                proc = subprocess.run(
                    ["curl", "-s", "--max-time", "15", url],
                    capture_output=True, text=True, timeout=20,
                )
                if proc.returncode != 0:
                    self.logger.warning("Twelve Data curl 失败 %s: rc=%d", td_code, proc.returncode)
                    failed.append(internal_sym)
                    continue

                data = json.loads(proc.stdout)
                credits_used += 1

                if "values" not in data:
                    msg = data.get("message", data.get("code", "unknown"))
                    if "run out of API credits" in str(msg):
                        wait = _trigger_backoff("twelvedata")
                        self.logger.warning("Twelve Data 限流, 退避 %ds", wait)
                        failed.append(internal_sym)
                        break
                    elif "Grow" in str(msg) or "Venture" in str(msg):
                        self.logger.debug("Twelve Data 付费品种: %s", td_code)
                    else:
                        self.logger.warning("Twelve Data 无数据 %s: %s", td_code, str(msg)[:60])
                    failed.append(internal_sym)
                    continue

                mapping = YFINANCE_MINUTE_MAP.get(internal_sym)
                cn_name = mapping[1] if mapping else td_code
                exchange = mapping[2] if mapping else ""

                for bar in data["values"]:
                    records.append({
                        "source_type": "overseas_minute",
                        "symbol_or_indicator": internal_sym,
                        "timestamp": bar.get("datetime", ""),
                        "payload": {
                            "symbol": internal_sym,
                            "name": cn_name,
                            "exchange": exchange,
                            "open": float(bar.get("open", 0)),
                            "high": float(bar.get("high", 0)),
                            "low": float(bar.get("low", 0)),
                            "close": float(bar.get("close", 0)),
                            "volume": float(bar.get("volume", 0)),
                            "source": "twelve_data",
                            "interval": interval,
                            "mode": "live",
                        },
                    })

                self.logger.info("Twelve Data: %s rows=%d", td_code, len(data["values"]))
                _reset_backoff("twelvedata")
                time.sleep(8.5)  # 8 credits/min → ~7.5s between calls

            except Exception as exc:
                self.logger.warning("Twelve Data 失败 %s: %s", td_code, exc)
                failed.append(internal_sym)

        return records, failed

    def _fetch_akshare_daily_fallback(
        self,
        *,
        symbol_list: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 4: AkShare 日线降级 (当所有分钟源失败时取最新日线)."""
        import akshare as ak

        records: list[dict[str, Any]] = []
        for internal_sym in symbol_list:
            mapping = YFINANCE_MINUTE_MAP.get(internal_sym)
            if not mapping:
                continue
            _, cn_name, exchange = mapping
            # 尝试东方财富全球期货日线
            try:
                # 使用 yfinance 代码去掉 =F 后缀
                sym_code = mapping[0].replace("=F", "")
                df = ak.futures_global_hist_em(symbol=sym_code)
                time.sleep(0.5)
                if df is not None and not df.empty:
                    # 仅取最近1天作为降级数据
                    row = df.iloc[-1]
                    records.append({
                        "source_type": "overseas_minute",
                        "symbol_or_indicator": internal_sym,
                        "timestamp": str(row.get("date", row.get("日期", ""))),
                        "payload": {
                            "symbol": internal_sym,
                            "name": cn_name,
                            "exchange": exchange,
                            "open": float(row.get("open", row.get("开盘", 0))),
                            "high": float(row.get("high", row.get("最高", 0))),
                            "low": float(row.get("low", row.get("最低", 0))),
                            "close": float(row.get("close", row.get("收盘", row.get("最新价", 0)))),
                            "volume": float(row.get("volume", row.get("成交量", 0))),
                            "source": "akshare_daily_fallback",
                            "interval": "1d",
                            "mode": "live",
                        },
                    })
                    self.logger.info("AkShare日线降级: %s (%s)", internal_sym, cn_name)
            except Exception as exc:
                self.logger.debug("AkShare日线降级失败 %s: %s", internal_sym, exc)

        return records

    def collect_daily_only(
        self,
        *,
        symbols: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """采集仅日线品种 (LME/SGX/JPX) via AkShare."""
        import akshare as ak

        symbol_list = symbols or list(DAILY_ONLY_MAP.keys())
        records: list[dict[str, Any]] = []

        for internal_sym in symbol_list:
            mapping = DAILY_ONLY_MAP.get(internal_sym)
            if not mapping:
                continue
            em_code, cn_name, exchange = mapping

            try:
                df = ak.futures_foreign_hist(symbol=em_code)
                time.sleep(0.5)
                if df is None or df.empty:
                    # 备用: 东方财富
                    df = ak.futures_global_hist_em(symbol=em_code)
                    time.sleep(0.5)

                if df is not None and not df.empty:
                    # P1-004: 数据新鲜度检查
                    date_col = next(
                        (c for c in ("date", "日期", "trade_date") if c in df.columns),
                        None,
                    )
                    if date_col:
                        latest_date = df[date_col].max()
                        try:
                            latest_dt = datetime.strptime(str(latest_date)[:10], "%Y-%m-%d")
                            stale_days = (datetime.utcnow() - latest_dt).days
                            if stale_days > 7:
                                self.logger.warning(
                                    "日线数据陈旧: %s (%s) 最新日期=%s, 距今=%d天",
                                    internal_sym, cn_name, str(latest_date)[:10], stale_days,
                                )
                        except (ValueError, TypeError):
                            pass
                    for _, row in df.iterrows():
                        ts = str(row.get("date", row.get("日期", "")))
                        records.append({
                            "source_type": "overseas_daily",
                            "symbol_or_indicator": internal_sym,
                            "timestamp": ts,
                            "payload": {
                                "symbol": internal_sym,
                                "em_code": em_code,
                                "name": cn_name,
                                "exchange": exchange,
                                "open": float(row.get("open", row.get("开盘", 0))),
                                "high": float(row.get("high", row.get("最高", 0))),
                                "low": float(row.get("low", row.get("最低", 0))),
                                "close": float(row.get("close", row.get("收盘", row.get("最新价", 0)))),
                                "volume": float(row.get("volume", row.get("总量", row.get("成交量", 0)))),
                                "source": "akshare_daily",
                                "mode": "live",
                            },
                        })
                    self.logger.info(
                        "AkShare 日线采集: %s (%s) rows=%d",
                        em_code, cn_name, len(df),
                    )
            except Exception as exc:
                self.logger.warning("日线采集失败 %s: %s", em_code, exc)

        return records
