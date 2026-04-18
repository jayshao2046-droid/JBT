"""策略参数优化器 — TASK-0122-B

基于 Optuna 贝叶斯优化，对 YAML 策略的因子参数进行调优。

设计原则：
- qwen3 只在每个策略调用一次（生成基础代码，缓存复用）
- IS（前 80% 数据）: Optuna 100 trials 优化 Sharpe
- OOS（后 20% 数据）: 硬性验证，不达标则标记未通过（不降级）

OOS 验收标准（全部满足）：
  - OOS Sharpe ≥ 0.8
  - OOS 交易次数 ≥ 20
  - IS/OOS Sharpe 比值 ≤ 2.0（防过拟合）
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

import optuna

from .yaml_signal_executor import YAMLSignalExecutor, SignalBacktestResult

logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)


class StrategyParamOptimizer:
    """Optuna 驱动的策略参数优化器。"""

    # OOS 验收硬标准（对齐最新评估方案）
    OOS_MIN_SHARPE: float = 1.5          # OOS Sharpe ≥ 1.5
    OOS_MAX_IS_OOS_RATIO: float = 2.0    # 过拟合防护
    OOS_MIN_TRADES: int = 20             # OOS 最少交易次数
    OOS_MIN_WIN_RATE: float = 0.50       # OOS 胜率 ≥ 50%
    OOS_MAX_DRAWDOWN: float = 0.02       # OOS 最大回撤 ≤ 2%
    IS_RATIO: float = 0.80               # 前 80% 作为 IS

    def __init__(
        self,
        executor: Optional[YAMLSignalExecutor] = None,
        n_trials: int = 100,
    ) -> None:
        self.executor = executor or YAMLSignalExecutor()
        self.n_trials = n_trials

    async def optimize(
        self,
        strategy: dict,
        full_start: str,
        full_end: str,
    ) -> dict[str, Any]:
        """对策略执行 IS 优化 + OOS 验证。

        Args:
            strategy: YAML 策略配置字典
            full_start: 全量数据起始（含 5 年历史）YYYY-MM-DD
            full_end:   全量数据结束 YYYY-MM-DD

        Returns:
            {
              best_params, is_result, oos_result,
              passed_oos, oos_verdict,
              is_end, oos_start, n_trials
            }
            或 {"error": "..."}
        """
        # 1. 切分 IS / OOS
        d_start = date.fromisoformat(full_start)
        d_end = date.fromisoformat(full_end)
        total_days = (d_end - d_start).days
        is_days = int(total_days * self.IS_RATIO)
        is_end_d = d_start + timedelta(days=is_days)
        oos_start_d = is_end_d + timedelta(days=1)

        is_end = is_end_d.isoformat()
        oos_start = oos_start_d.isoformat()

        # 2. 拉取 IS / OOS 数据（各一次）
        symbol = self.executor._extract_symbol(strategy)
        tf = int(strategy.get("timeframe_minutes", 60))

        try:
            bars_is = await self.executor._fetch_bars(symbol, full_start, is_end, tf)
            bars_oos = await self.executor._fetch_bars(symbol, oos_start, full_end, tf)
        except RuntimeError as e:
            return {"error": str(e)}

        if len(bars_is) < 100:
            return {"error": f"IS 数据不足: {len(bars_is)} 根（需要 ≥ 100）"}
        if len(bars_oos) < 50:
            return {"error": f"OOS 数据不足: {len(bars_oos)} 根（需要 ≥ 50）"}

        # 3. qwen3 只生成一次基础代码（参数从 objective 里覆盖）
        base_code, err = await self.executor._generate_signal_code(strategy, None)
        if err:
            return {"error": f"基础代码生成失败: {err}"}

        # 4. 提取参数搜索空间
        param_space = self._extract_param_space(strategy)
        if not param_space:
            return {"error": "无可优化的数值型因子参数"}

        # 5. Optuna IS 优化（同步 objective，不重复调 LLM）
        strategy_name = strategy.get("name", "opt")

        def objective(trial: optuna.Trial) -> float:
            params = self._suggest_params(trial, param_space)
            result = self.executor._run_backtest(
                strategy_name, bars_is, base_code, strategy, params
            )
            if result.status == "failed" or result.trades_count < 5:
                return -10.0
            return float(result.sharpe_ratio)

        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)

        best_params = dict(study.best_params)
        logger.info(
            "优化完成: %s | best IS Sharpe=%.4f | params=%s",
            strategy_name, study.best_value, best_params,
        )

        # 6. IS 最优参数完整指标
        is_result = self.executor._run_backtest(
            strategy_name, bars_is, base_code, strategy, best_params
        )

        # 7. OOS 验证（不优化，只验证）
        oos_result = self.executor._run_backtest(
            strategy_name, bars_oos, base_code, strategy, best_params
        )

        # 8. OOS 硬性验收
        oos_verdict = self._check_oos(is_result, oos_result)

        return {
            "best_params": best_params,
            "is_result": is_result.to_dict(),
            "oos_result": oos_result.to_dict(),
            "passed_oos": oos_verdict["passed"],
            "oos_verdict": oos_verdict,
            "is_start": full_start,
            "is_end": is_end,
            "oos_start": oos_start,
            "oos_end": full_end,
            "n_trials": self.n_trials,
            "generated_code": base_code,
        }

    # ------------------------------------------------------------------
    # Parameter space extraction
    # ------------------------------------------------------------------

    def _extract_param_space(self, strategy: dict) -> dict[str, dict]:
        """从 YAML factors 自动提取数值型参数的 Optuna 搜索空间。"""
        space: dict[str, dict] = {}

        for factor in strategy.get("factors", []):
            params = factor.get("params", {})
            for k, v in params.items():
                if isinstance(v, int) and v > 0:
                    lo = max(2, int(v * 0.5))
                    hi = max(lo + 2, int(v * 2.0))
                    space[k] = {"type": "int", "low": lo, "high": hi, "original": v}
                elif isinstance(v, float) and v > 0:
                    lo = round(v * 0.5, 4)
                    hi = round(v * 2.0, 4)
                    space[k] = {"type": "float", "low": lo, "high": hi, "original": v}

        # ATR 止损/止盈乘数
        risk = strategy.get("risk", {})
        for section_key, param_key in [("stop_loss", "stop_atr_mult"), ("take_profit", "take_atr_mult")]:
            sect = risk.get(section_key, {})
            if isinstance(sect, dict) and "atr_multiplier" in sect:
                v = float(sect["atr_multiplier"])
                space[param_key] = {"type": "float", "low": 0.5, "high": 5.0, "original": v}

        # position_fraction（顶层）
        pf = strategy.get("position_fraction")
        if isinstance(pf, (int, float)) and pf > 0:
            space["position_fraction"] = {
                "type": "float", "low": 0.03, "high": 0.15, "original": float(pf)
            }

        return space

    def _suggest_params(self, trial: optuna.Trial, space: dict) -> dict[str, Any]:
        """生成一组 trial 参数，并应用 fast/slow 约束。"""
        params: dict[str, Any] = {}
        for k, v in space.items():
            if v["type"] == "int":
                params[k] = trial.suggest_int(k, v["low"], v["high"])
            else:
                params[k] = trial.suggest_float(k, v["low"], v["high"])

        # fast_period < slow_period 硬约束（违反 → 标记 infeasible）
        if "fast_period" in params and "slow_period" in params:
            if params["slow_period"] <= params["fast_period"]:
                # 将 trial 标记为不可行（Optuna ≥ 3.0 支持 TrialPruned 作为 infeasible 代理）
                raise optuna.exceptions.TrialPruned()

        return params

    # ------------------------------------------------------------------
    # OOS verification
    # ------------------------------------------------------------------

    def _check_oos(
        self,
        is_result: SignalBacktestResult,
        oos_result: SignalBacktestResult,
    ) -> dict[str, Any]:
        """OOS 硬性验收，无降级。全部条件必须满足。"""
        oos_sharpe_ok = oos_result.sharpe_ratio >= self.OOS_MIN_SHARPE
        oos_trades_ok = oos_result.trades_count >= self.OOS_MIN_TRADES
        oos_win_rate_ok = oos_result.win_rate >= self.OOS_MIN_WIN_RATE
        oos_drawdown_ok = oos_result.max_drawdown <= self.OOS_MAX_DRAWDOWN

        is_oos_ratio_ok = True
        is_oos_ratio: Optional[float] = None
        if is_result.sharpe_ratio > 0 and oos_result.sharpe_ratio > 0:
            is_oos_ratio = round(is_result.sharpe_ratio / oos_result.sharpe_ratio, 3)
            is_oos_ratio_ok = is_oos_ratio <= self.OOS_MAX_IS_OOS_RATIO

        passed = oos_sharpe_ok and oos_trades_ok and oos_win_rate_ok and oos_drawdown_ok and is_oos_ratio_ok

        verdict: dict[str, Any] = {
            "passed": passed,
            "oos_sharpe": round(oos_result.sharpe_ratio, 4),
            "oos_sharpe_ok": oos_sharpe_ok,
            "oos_sharpe_threshold": self.OOS_MIN_SHARPE,
            "oos_trades": oos_result.trades_count,
            "oos_trades_ok": oos_trades_ok,
            "oos_trades_threshold": self.OOS_MIN_TRADES,
            "oos_win_rate": round(oos_result.win_rate, 4),
            "oos_win_rate_ok": oos_win_rate_ok,
            "oos_win_rate_threshold": self.OOS_MIN_WIN_RATE,
            "oos_max_drawdown": round(oos_result.max_drawdown, 4),
            "oos_drawdown_ok": oos_drawdown_ok,
            "oos_drawdown_threshold": self.OOS_MAX_DRAWDOWN,
            "is_oos_ratio": is_oos_ratio,
            "is_oos_ratio_ok": is_oos_ratio_ok,
            "is_oos_ratio_threshold": self.OOS_MAX_IS_OOS_RATIO,
            "is_sharpe": round(is_result.sharpe_ratio, 4),
            "is_trades": is_result.trades_count,
        }

        if not passed:
            reasons = []
            if not oos_sharpe_ok:
                reasons.append(f"OOS Sharpe {oos_result.sharpe_ratio:.4f} < {self.OOS_MIN_SHARPE}")
            if not oos_trades_ok:
                reasons.append(f"OOS 交易次数 {oos_result.trades_count} < {self.OOS_MIN_TRADES}")
            if not oos_win_rate_ok:
                reasons.append(f"OOS 胜率 {oos_result.win_rate:.2%} < {self.OOS_MIN_WIN_RATE:.0%}")
            if not oos_drawdown_ok:
                reasons.append(f"OOS 最大回撤 {oos_result.max_drawdown:.2%} > {self.OOS_MAX_DRAWDOWN:.0%}")
            if not is_oos_ratio_ok:
                reasons.append(f"IS/OOS Sharpe 比 {is_oos_ratio} > {self.OOS_MAX_IS_OOS_RATIO}（过拟合）")
            verdict["fail_reasons"] = reasons

        return verdict
