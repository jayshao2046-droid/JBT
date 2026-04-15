"""
期货/股票沙箱回测引擎 — TASK-0056 CA2'
支持 asset_type='futures'|'stock'，通过 httpx 从 data 服务取 bars，
模拟均线交叉策略执行，返回绩效指标。
"""
from __future__ import annotations

import asyncio
import math
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx


@dataclass
class SandboxResult:
    backtest_id: str
    status: str  # completed / failed
    start_time: str
    end_time: str
    initial_capital: float
    final_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades_count: int
    trades: list = field(default_factory=list)
    performance_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SandboxEngine:
    """支持 asset_type='futures'|'stock' 的快速沙箱回测引擎。"""

    def __init__(self, data_service_url: str = "http://localhost:8105") -> None:
        self.data_service_url = data_service_url.rstrip("/")
        # 安全修复：P2-5 - 添加并发锁保护缓存
        self._cache: dict[str, list[dict]] = {}
        self._cache_lock = asyncio.Lock()

    async def run_backtest(
        self,
        strategy_config: dict,
        start_time: str,
        end_time: str,
        asset_type: str = "futures",
        initial_capital: float = 1_000_000,
        symbols: Optional[List[str]] = None,
    ) -> SandboxResult:
        backtest_id = f"sandbox-{uuid.uuid4().hex[:12]}"
        ts_start = datetime.now(timezone.utc).isoformat()

        if asset_type not in ("futures", "stock"):
            return SandboxResult(
                backtest_id=backtest_id,
                status="failed",
                start_time=ts_start,
                end_time=datetime.now(timezone.utc).isoformat(),
                initial_capital=initial_capital,
                final_capital=initial_capital,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                trades_count=0,
                trades=[],
                performance_metrics={"error": f"unsupported asset_type: {asset_type}"},
            )

        if not symbols:
            symbols = [strategy_config.get("symbol", "KQ_m_CFFEX_IF")]

        all_trades: list[dict] = []
        final_capital = initial_capital

        try:
            for symbol in symbols:
                bars = await self._fetch_bars(symbol, start_time, end_time, asset_type)
                if len(bars) < 2:
                    continue
                # Stock: auto-detect GEM/STAR board price limit (20%)
                effective_config = strategy_config
                if asset_type == "stock" and symbol.startswith(("300", "688")):
                    effective_config = {**strategy_config, "price_limit": 0.20}
                result = self._execute_strategy(
                    bars, effective_config, final_capital, asset_type,
                )
                final_capital = result["final_capital"]
                all_trades.extend(result["trades"])
        except Exception as exc:
            return SandboxResult(
                backtest_id=backtest_id,
                status="failed",
                start_time=ts_start,
                end_time=datetime.now(timezone.utc).isoformat(),
                initial_capital=initial_capital,
                final_capital=initial_capital,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                trades_count=0,
                trades=[],
                performance_metrics={"error": str(exc)},
            )

        total_return = (final_capital - initial_capital) / initial_capital if initial_capital else 0.0
        metrics = self._calculate_metrics(all_trades, initial_capital, final_capital)

        ts_end = datetime.now(timezone.utc).isoformat()
        return SandboxResult(
            backtest_id=backtest_id,
            status="completed",
            start_time=ts_start,
            end_time=ts_end,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=round(total_return, 6),
            sharpe_ratio=metrics["sharpe_ratio"],
            max_drawdown=metrics["max_drawdown"],
            win_rate=metrics["win_rate"],
            trades_count=len(all_trades),
            trades=all_trades,
            performance_metrics=metrics,
        )

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    async def _fetch_bars(
        self,
        symbol: str,
        start: str,
        end: str,
        asset_type: str,
    ) -> list[dict]:
        cache_key = f"{asset_type}:{symbol}:{start}:{end}"

        # 安全修复：P1-2 - 在锁内完成检查和获取，避免 TOCTOU 竞态条件
        async with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

            # 在锁内执行 HTTP 请求，确保同一 cache_key 不会并发请求
            if asset_type == "stock":
                url = f"{self.data_service_url}/api/v1/stocks/bars"
            else:
                url = f"{self.data_service_url}/api/v1/bars"

            params = {"symbol": symbol, "start": start, "end": end}

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()

            data = resp.json()
            bars: list[dict] = data if isinstance(data, list) else data.get("bars", data.get("data", []))

            self._cache[cache_key] = bars
            return bars

    # ------------------------------------------------------------------
    # Strategy execution (simple moving-average crossover)
    # ------------------------------------------------------------------

    def _execute_strategy(
        self,
        bars: list[dict],
        strategy_config: dict,
        initial_capital: float,
        asset_type: str = "futures",
    ) -> dict[str, Any]:
        short_window: int = strategy_config.get("short_window", 5)
        long_window: int = strategy_config.get("long_window", 20)
        position_size: float = strategy_config.get("position_size", 0.1)

        # Stock-specific parameters
        is_stock = asset_type == "stock"
        price_limit: float = strategy_config.get("price_limit", 0.10)
        allow_short: bool = strategy_config.get("allow_short", False)

        closes = [float(b.get("close", b.get("Close", 0))) for b in bars]
        if len(closes) < long_window:
            return {"final_capital": initial_capital, "trades": []}

        capital = initial_capital
        position = 0.0
        entry_price = 0.0
        trades: list[dict] = []
        buy_bar_date: Optional[str] = None  # T+1 tracking for stock

        for i in range(long_window, len(closes)):
            sma_short = sum(closes[i - short_window : i]) / short_window
            sma_long = sum(closes[i - long_window : i]) / long_window
            price = closes[i]

            # Bug-5 修复：边界条件检查 - 跳过无效价格
            if price <= 0 or sma_short <= 0 or sma_long <= 0:
                continue

            # Stock: skip bar if price hits limit-up / limit-down
            if is_stock and i > 0:
                prev_close = closes[i - 1]
                if prev_close > 0 and abs(price / prev_close - 1) >= price_limit:
                    continue

            # Buy signal: short MA crosses above long MA
            if sma_short > sma_long and position == 0.0:
                qty = (capital * position_size) / price
                if qty > 0:
                    position = qty
                    entry_price = price
                    if is_stock:
                        buy_bar_date = self._bar_date(bars[i])
                    trades.append({
                        "type": "buy",
                        "price": price,
                        "qty": round(qty, 4),
                        "bar_index": i,
                    })

            # Sell signal: short MA crosses below long MA
            elif sma_short < sma_long and position > 0:
                # Stock: T+1 — cannot sell on the same day as buy
                if is_stock and buy_bar_date is not None:
                    if self._bar_date(bars[i]) == buy_bar_date:
                        continue
                pnl = (price - entry_price) * position
                capital += pnl
                trades.append({
                    "type": "sell",
                    "price": price,
                    "qty": round(position, 4),
                    "pnl": round(pnl, 2),
                    "bar_index": i,
                })
                position = 0.0
                entry_price = 0.0
                buy_bar_date = None

            # Stock: ignore short signals when allow_short is False
            elif sma_short < sma_long and position == 0.0:
                if is_stock and not allow_short:
                    continue

        # Close any remaining position at last bar
        # Bug-5 修复：边界条件检查 - 验证最后价格有效性
        if position > 0 and closes:
            last_price = closes[-1]
            if last_price > 0 and entry_price > 0:
                pnl = (last_price - entry_price) * position
                capital += pnl
                trades.append({
                    "type": "sell",
                    "price": last_price,
                    "qty": round(position, 4),
                    "pnl": round(pnl, 2),
                    "bar_index": len(closes) - 1,
                })
            else:
                # 价格无效，强制平仓但不计算盈亏
                logger.warning(
                    f"Invalid last_price={last_price} or entry_price={entry_price}, "
                    f"force closing position without PnL calculation"
                )

        return {"final_capital": capital, "trades": trades}

    @staticmethod
    def _bar_date(bar: dict) -> str:
        """Extract date string (YYYY-MM-DD) from bar's datetime field."""
        dt_str = bar.get("datetime", bar.get("date", bar.get("Date", "")))
        return dt_str[:10] if dt_str else ""

    # ------------------------------------------------------------------
    # Performance metrics
    # ------------------------------------------------------------------

    def _calculate_metrics(
        self,
        trades: list[dict],
        initial_capital: float,
        final_capital: float,
    ) -> dict[str, Any]:
        total_return = (final_capital - initial_capital) / initial_capital if initial_capital else 0.0

        sell_trades = [t for t in trades if t.get("type") == "sell"]
        pnls = [t.get("pnl", 0.0) for t in sell_trades]

        win_count = sum(1 for p in pnls if p > 0)
        win_rate = win_count / len(pnls) if pnls else 0.0

        # Sharpe ratio (annualized, assume 250 trading days)
        sharpe_ratio = 0.0
        if len(pnls) >= 2:
            returns = [p / initial_capital for p in pnls]
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
            std_ret = math.sqrt(variance) if variance > 0 else 0.0
            if std_ret > 0:
                sharpe_ratio = (mean_ret / std_ret) * math.sqrt(250)

        # Max drawdown
        max_drawdown = 0.0
        if pnls:
            equity = initial_capital
            peak = equity
            for p in pnls:
                equity += p
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak if peak > 0 else 0.0
                if dd > max_drawdown:
                    max_drawdown = dd

        return {
            "total_return": round(total_return, 6),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 6),
            "win_rate": round(win_rate, 4),
            "win_count": win_count,
            "loss_count": len(pnls) - win_count,
            "total_trades": len(pnls),
        }
