"""交易参数调优引擎 — TASK-0061 CA4
网格搜索交易参数，以真实 Sharpe/最大回撤/胜率为目标函数。
"""
from __future__ import annotations

import itertools
import math
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

import httpx


@dataclass
class OptimizationResult:
    opt_id: str
    strategy_id: str
    status: str  # pending / running / completed / failed
    created_at: str
    completed_at: str | None
    best_params: dict
    best_score: float
    objective: str  # sharpe / max_drawdown / win_rate / total_return
    all_trials: list[dict] = field(default_factory=list)
    total_trials: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TradeOptimizer:
    """网格搜索交易参数，以真实回测指标为评分。"""

    def __init__(self, data_service_url: str = "http://localhost:8105") -> None:
        self.data_service_url = data_service_url.rstrip("/")
        self._results: dict[str, OptimizationResult] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(
        self,
        strategy_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        param_grid: dict[str, list],
        objective: str = "sharpe",
        asset_type: str = "futures",
    ) -> OptimizationResult:
        opt_id = f"opt-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        result = OptimizationResult(
            opt_id=opt_id,
            strategy_id=strategy_id,
            status="running",
            created_at=now,
            completed_at=None,
            best_params={},
            best_score=float("-inf"),
            objective=objective,
        )

        if not param_grid:
            result.status = "completed"
            result.completed_at = datetime.now(timezone.utc).isoformat()
            result.total_trials = 0
            self._results[opt_id] = result
            return result

        # Cartesian product of parameter grid
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))

        trials: list[dict] = []
        best_score = float("-inf")
        best_params: dict = {}

        try:
            bars = self._fetch_bars(symbol, start_date, end_date, asset_type)
        except Exception as exc:
            result.status = "failed"
            result.completed_at = datetime.now(timezone.utc).isoformat()
            result.all_trials = [{"error": str(exc)}]
            self._results[opt_id] = result
            return result

        for combo in combinations:
            params = dict(zip(keys, combo))
            try:
                metrics = self._run_single_backtest(bars, params, asset_type)
                score = self._calculate_objective(metrics, objective)
            except Exception:
                metrics = {}
                score = float("-inf")

            trial = {"params": params, "metrics": metrics, "score": score}
            trials.append(trial)

            if score > best_score:
                best_score = score
                best_params = params

        result.status = "completed"
        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.best_params = best_params
        result.best_score = best_score
        result.all_trials = trials
        result.total_trials = len(trials)
        self._results[opt_id] = result
        return result

    def get_result(self, opt_id: str) -> OptimizationResult | None:
        return self._results.get(opt_id)

    def list_results(self, strategy_id: str | None = None) -> list[OptimizationResult]:
        if strategy_id is None:
            return list(self._results.values())
        return [r for r in self._results.values() if r.strategy_id == strategy_id]

    # ------------------------------------------------------------------
    # Internal: fetch bars (sync)
    # ------------------------------------------------------------------

    def _fetch_bars(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        asset_type: str,
    ) -> list[dict]:
        if asset_type == "stock":
            url = f"{self.data_service_url}/api/v1/stocks/bars"
        else:
            url = f"{self.data_service_url}/api/v1/bars"

        params = {"symbol": symbol, "start": start_date, "end": end_date}
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()

        data = resp.json()
        bars: list[dict] = data if isinstance(data, list) else data.get("bars", data.get("data", []))
        return bars

    # ------------------------------------------------------------------
    # Internal: single backtest with given params
    # ------------------------------------------------------------------

    def _run_single_backtest(
        self,
        bars: list[dict],
        params: dict,
        asset_type: str = "futures",
    ) -> dict[str, Any]:
        """Execute a simple MA-crossover strategy with *params* on *bars*,
        return metrics dict: sharpe, max_drawdown, win_rate, total_return, trades_count.
        """
        fast_period: int = params.get("fast_period", 5)
        slow_period: int = params.get("slow_period", 20)
        stop_loss: float | None = params.get("stop_loss")
        take_profit: float | None = params.get("take_profit")
        initial_capital: float = 1_000_000.0
        position_size: float = params.get("position_size", 0.1)

        closes = [float(b.get("close", b.get("Close", 0))) for b in bars]
        if len(closes) < slow_period:
            return {
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "total_return": 0.0,
                "trades_count": 0,
            }

        capital = initial_capital
        peak_capital = initial_capital
        max_dd = 0.0
        position = 0.0
        entry_price = 0.0
        pnls: list[float] = []

        for i in range(slow_period, len(closes)):
            sma_fast = sum(closes[i - fast_period : i]) / fast_period
            sma_slow = sum(closes[i - slow_period : i]) / slow_period
            price = closes[i]

            # Check stop-loss / take-profit on open position
            if position > 0 and entry_price > 0:
                unrealized_pct = (price - entry_price) / entry_price
                if stop_loss is not None and unrealized_pct <= -abs(stop_loss):
                    pnl = (price - entry_price) * position
                    capital += pnl
                    pnls.append(pnl)
                    position = 0.0
                    entry_price = 0.0
                    # Track drawdown
                    if capital > peak_capital:
                        peak_capital = capital
                    dd = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0.0
                    max_dd = max(max_dd, dd)
                    continue
                if take_profit is not None and unrealized_pct >= abs(take_profit):
                    pnl = (price - entry_price) * position
                    capital += pnl
                    pnls.append(pnl)
                    position = 0.0
                    entry_price = 0.0
                    if capital > peak_capital:
                        peak_capital = capital
                    dd = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0.0
                    max_dd = max(max_dd, dd)
                    continue

            # Buy signal
            if sma_fast > sma_slow and position == 0.0:
                qty = (capital * position_size) / price if price > 0 else 0
                if qty > 0:
                    position = qty
                    entry_price = price

            # Sell signal
            elif sma_fast < sma_slow and position > 0:
                pnl = (price - entry_price) * position
                capital += pnl
                pnls.append(pnl)
                position = 0.0
                entry_price = 0.0

            # Track drawdown
            if capital > peak_capital:
                peak_capital = capital
            dd = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0.0
            max_dd = max(max_dd, dd)

        # Close remaining position
        if position > 0 and closes:
            pnl = (closes[-1] - entry_price) * position
            capital += pnl
            pnls.append(pnl)
            if capital > peak_capital:
                peak_capital = capital
            dd = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0.0
            max_dd = max(max_dd, dd)

        total_return = (capital - initial_capital) / initial_capital if initial_capital else 0.0
        win_count = sum(1 for p in pnls if p > 0)
        win_rate = win_count / len(pnls) if pnls else 0.0

        # Annualized Sharpe (assume 250 trading days)
        if len(pnls) >= 2:
            mean_pnl = sum(pnls) / len(pnls)
            std_pnl = math.sqrt(sum((p - mean_pnl) ** 2 for p in pnls) / (len(pnls) - 1))
            sharpe = (mean_pnl / std_pnl * math.sqrt(250)) if std_pnl > 0 else 0.0
        else:
            sharpe = 0.0

        return {
            "sharpe": round(sharpe, 4),
            "max_drawdown": round(max_dd, 6),
            "win_rate": round(win_rate, 4),
            "total_return": round(total_return, 6),
            "trades_count": len(pnls),
        }

    # ------------------------------------------------------------------
    # Internal: objective scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_objective(metrics: dict, objective: str) -> float:
        """Return a score where *higher is better*."""
        if objective == "sharpe":
            return metrics.get("sharpe", 0.0)
        if objective == "max_drawdown":
            # Lower drawdown is better → negate
            return -metrics.get("max_drawdown", 1.0)
        if objective == "win_rate":
            return metrics.get("win_rate", 0.0)
        if objective == "total_return":
            return metrics.get("total_return", 0.0)
        return metrics.get("sharpe", 0.0)
