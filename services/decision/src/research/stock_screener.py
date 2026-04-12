"""全 A 股选股引擎 — TASK-0062 CB3
多因子打分 + benchmark 对比，每日输出 TOP-N 选股列表。
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class ScreenResult:
    screen_id: str
    created_at: str
    universe_size: int
    top_n: int
    ranked_list: list[dict] = field(default_factory=list)
    benchmark: Optional[Dict] = None
    screening_params: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StockScreener:
    """多因子选股引擎：momentum / volume_ratio / price_position 加权打分。"""

    def __init__(self, data_service_url: str = "http://localhost:8105") -> None:
        self.data_service_url = data_service_url.rstrip("/")
        self._results: dict[str, ScreenResult] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def screen(
        self,
        symbols: list[str],
        top_n: int = 20,
        lookback_days: int = 20,
        benchmark_symbol: Optional[str] = None,
    ) -> ScreenResult:
        """对 *symbols* 列表做多因子打分，返回 TOP-N 排名。"""
        screen_id = f"scr-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        scored: list[dict] = []
        for sym in symbols:
            try:
                bars = self._fetch_daily_bars(sym, lookback_days)
                if len(bars) < 2:
                    continue
                factors = self._score_stock(bars, lookback_days)
                scored.append({"symbol": sym, **factors})
            except Exception:
                # fetch / parse 失败的股票直接跳过
                continue

        # 按 score 降序排名
        scored.sort(key=lambda x: x["score"], reverse=True)
        ranked: list[dict] = []
        for rank, item in enumerate(scored[: top_n], start=1):
            ranked.append({
                "symbol": item["symbol"],
                "name": item.get("name", ""),
                "score": round(item["score"], 6),
                "factors": {
                    "momentum": round(item["momentum"], 6),
                    "volume_ratio": round(item["volume_ratio"], 6),
                    "price_position": round(item["price_position"], 6),
                },
                "rank": rank,
            })

        # benchmark
        bench: Optional[Dict] = None
        if benchmark_symbol:
            try:
                bench_bars = self._fetch_daily_bars(benchmark_symbol, lookback_days)
                if len(bench_bars) >= 2:
                    bench = self._calculate_benchmark(bench_bars)
                    bench["symbol"] = benchmark_symbol
            except Exception:
                bench = None

        result = ScreenResult(
            screen_id=screen_id,
            created_at=now,
            universe_size=len(symbols),
            top_n=top_n,
            ranked_list=ranked,
            benchmark=bench,
            screening_params={
                "lookback_days": lookback_days,
                "top_n": top_n,
                "benchmark_symbol": benchmark_symbol,
            },
        )
        self._results[screen_id] = result
        return result

    def get_result(self, screen_id: str) -> Optional[ScreenResult]:
        return self._results.get(screen_id)

    def list_results(self) -> list[ScreenResult]:
        return list(self._results.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_daily_bars(self, symbol: str, days: int) -> list[dict]:
        """从 data 服务获取日线 K 线。"""
        url = f"{self.data_service_url}/api/v1/stocks/bars"
        params = {
            "symbol": symbol,
            "timeframe_minutes": 1440,  # daily
            "limit": days + 10,  # extra margin
        }
        resp = httpx.get(url, params=params, timeout=15.0)
        resp.raise_for_status()
        payload = resp.json()
        bars = payload if isinstance(payload, list) else payload.get("bars", payload.get("data", []))
        # 只取最新 days 条
        return bars[-days:] if len(bars) > days else bars

    def _score_stock(self, bars: list[dict], lookback_days: int) -> dict:
        """计算单只股票的因子分数。

        因子:
          - momentum: N 日收益率
          - volume_ratio: 近 5 日均量 / 近 20 日均量
          - price_position: 当前价在 N 日高低点的位置 (0~1)
        加权: momentum*0.4 + volume_ratio*0.3 + price_position*0.3
        """
        closes = [b["close"] for b in bars]
        volumes = [b.get("volume", 0) for b in bars]
        highs = [b["high"] for b in bars]
        lows = [b["low"] for b in bars]

        # momentum
        if closes[0] != 0:
            momentum = (closes[-1] - closes[0]) / abs(closes[0])
        else:
            momentum = 0.0

        # volume_ratio
        vol_5 = sum(volumes[-5:]) / max(len(volumes[-5:]), 1)
        vol_20 = sum(volumes[-20:]) / max(len(volumes[-20:]), 1)
        volume_ratio = vol_5 / vol_20 if vol_20 > 0 else 1.0

        # price_position
        high_n = max(highs)
        low_n = min(lows)
        if high_n != low_n:
            price_position = (closes[-1] - low_n) / (high_n - low_n)
        else:
            price_position = 0.5

        # 归一化 volume_ratio 到 0~1 区间（用 sigmoid-like 映射）
        vr_norm = min(volume_ratio / 2.0, 1.0)  # 简单截断到 [0, 1]

        score = momentum * 0.4 + vr_norm * 0.3 + price_position * 0.3

        return {
            "momentum": momentum,
            "volume_ratio": volume_ratio,
            "price_position": price_position,
            "score": score,
        }

    def _calculate_benchmark(self, bars: list[dict]) -> dict:
        """计算 benchmark 的 return 和 sharpe。"""
        closes = [b["close"] for b in bars]

        # return
        if closes[0] != 0:
            return_pct = (closes[-1] - closes[0]) / abs(closes[0])
        else:
            return_pct = 0.0

        # daily returns for sharpe
        daily_returns: list[float] = []
        for i in range(1, len(closes)):
            if closes[i - 1] != 0:
                daily_returns.append((closes[i] - closes[i - 1]) / abs(closes[i - 1]))

        if len(daily_returns) >= 2:
            mean_r = sum(daily_returns) / len(daily_returns)
            var_r = sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            std_r = math.sqrt(var_r) if var_r > 0 else 0.0
            sharpe = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0
        else:
            sharpe = 0.0

        return {
            "return_pct": round(return_pct, 6),
            "sharpe": round(sharpe, 4),
        }
