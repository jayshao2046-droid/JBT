"""策略参数优化器 — TASK-0122-B

基于 Optuna 贝叶斯优化，对 YAML 策略的因子参数进行调优。

设计原则（激进→收敛）：
- qwen3 只在每个策略调用一次（生成基础代码，缓存复用）
- IS（前 80% 数据）: Optuna 100 trials 分两阶段优化
  Phase 1（前 40 trial）: 最大化交易次数，鼓励频繁开仓
  Phase 2（后 60 trial）: 最大化 sharpe * sqrt(trades)，在有量基础上优化质量
- OOS（后 20% 数据）: 放宽验证，留给 XGBoost 二次过滤

OOS 验收标准（放宽 — 允许有亏有赚，只排除极端）：
  - OOS Sharpe ≥ 0.3
  - OOS 交易次数 ≥ 30
  - OOS 胜率 ≥ 30%
  - OOS 最大回撤 ≤ 8%
  - IS/OOS Sharpe 比值 ≤ 3.0（放宽过拟合阈值）
"""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any, Optional

import optuna

from .yaml_signal_executor import YAMLSignalExecutor, SignalBacktestResult

logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)


class StrategyParamOptimizer:
    """Optuna 驱动的策略参数优化器。"""

    # OOS 验收标准（放宽 — 激进→收敛策略）
    OOS_MIN_SHARPE: float = 0.3          # OOS Sharpe ≥ 0.3
    OOS_MAX_IS_OOS_RATIO: float = 3.0    # 放宽过拟合防护
    OOS_MIN_TRADES: int = 30             # OOS 最少交易次数
    OOS_MIN_WIN_RATE: float = 0.30       # OOS 胜率 ≥ 30%
    OOS_MAX_DRAWDOWN: float = 0.08       # OOS 最大回撤 ≤ 8%
    IS_RATIO: float = 0.80               # 前 80% 作为 IS
    PHASE1_TRIALS: int = 40              # Phase 1 占前 40 trials

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

        phase1_trials = self.PHASE1_TRIALS

        def objective(trial: optuna.Trial) -> float:
            params = self._suggest_params(trial, param_space)
            result = self.executor._run_backtest(
                strategy_name, bars_is, base_code, strategy, params
            )
            if result.status == "failed" or result.trades_count < 3:
                return -1.0

            # Phase 1（前 N trials）: 最大化交易次数
            if trial.number < phase1_trials:
                return float(result.trades_count)

            # Phase 2: sharpe * sqrt(trades) — 在有量的基础上优化质量
            trades = max(1, result.trades_count)
            return float(result.sharpe_ratio) * (trades ** 0.5)

        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)

        best_params = dict(study.best_params)
        logger.info(
            "优化完成: %s | best value=%.4f | params=%s",
            strategy_name, study.best_value, best_params,
        )

        # 5b. 零交易检测 — 所有 trial 均未产生有效交易
        if study.best_value <= -1.0:
            diagnosis = self._diagnose_zero_trades(strategy, bars_is, base_code)
            logger.warning(
                "零交易: %s | %s", strategy_name, diagnosis["diagnosis_text"],
            )
            return {
                "error": "zero_trades",
                "zero_trades_diagnosis": diagnosis,
                "best_params": best_params,
                "generated_code": base_code,
                "is_start": full_start,
                "is_end": is_end,
                "oos_start": oos_start,
                "oos_end": full_end,
                "n_trials": self.n_trials,
            }

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
                    lo = max(2, int(v * 0.3))
                    hi = max(lo + 2, int(v * 3.0))
                    space[k] = {"type": "int", "low": lo, "high": hi, "original": v}
                elif isinstance(v, float) and v > 0:
                    lo = round(v * 0.3, 4)
                    hi = round(v * 3.0, 4)
                    space[k] = {"type": "float", "low": lo, "high": hi, "original": v}

        # ATR 止损/止盈乘数（优先读取 risk.stop_loss/risk.take_profit，兼容旧根级字段）
        risk_section = strategy.get("risk", {}) if isinstance(strategy.get("risk"), dict) else {}
        for section_key, param_key in [("stop_loss", "stop_atr_mult"), ("take_profit", "take_atr_mult")]:
            sect = risk_section.get(section_key)
            if not isinstance(sect, dict):
                sect = strategy.get(section_key, {})
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

        # fast < slow 硬约束（同时兼容 fast_period/slow_period 和 fast/slow 两种命名）
        for fast_k, slow_k in (("fast_period", "slow_period"), ("fast", "slow")):
            if fast_k in params and slow_k in params:
                if params[slow_k] <= params[fast_k]:
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

    # ------------------------------------------------------------------
    # Zero-trade diagnosis
    # ------------------------------------------------------------------

    def _diagnose_zero_trades(
        self,
        strategy: dict,
        bars: list[dict],
        base_code: str,
    ) -> dict[str, Any]:
        """诊断零交易原因：计算各指标在真实数据上的分布，对比 YAML 中的阈值。

        Returns:
            {
              diagnosis_text: str,           # 人类可读诊断
              tight_conditions: list[dict],  # 过严条件明细
              suggested_relaxations: dict,   # critic-compatible 放宽建议
            }
        """
        from .yaml_signal_executor import (
            _ta_adx, _ta_atr, _ta_rsi, _ta_bollinger,
            _ta_volume_ratio, _ta_macd, _ta_cci,
        )

        n = len(bars)
        if n < 50:
            return {
                "diagnosis_text": "IS 数据不足，无法诊断",
                "tight_conditions": [],
                "suggested_relaxations": {},
            }

        closes = [float(b.get("close", 0)) for b in bars]
        highs = [float(b.get("high", 0)) for b in bars]
        lows = [float(b.get("low", 0)) for b in bars]
        volumes = [float(b.get("volume", 0)) for b in bars]

        warm_up = 30
        indicators: dict[str, list[float]] = {
            "adx": _ta_adx(highs, lows, closes, 14)[warm_up:],
            "rsi": _ta_rsi(closes, 14)[warm_up:],
            "atr": _ta_atr(highs, lows, closes, 14)[warm_up:],
            "volume_ratio": _ta_volume_ratio(volumes, 10)[warm_up:],
            "cci": _ta_cci(highs, lows, closes, 20)[warm_up:],
        }
        _, _, macd_hist = _ta_macd(closes)
        indicators["macd_hist"] = macd_hist[warm_up:]
        bb_upper, bb_mid, bb_lower = _ta_bollinger(closes, 20, 2.0)
        indicators["bb_bandwidth"] = [
            (bb_upper[i] - bb_lower[i]) / bb_mid[i] if bb_mid[i] > 0 else 0
            for i in range(warm_up, n)
        ]
        close_sub = closes[warm_up:]
        indicators["atr_pct"] = [
            indicators["atr"][i] / close_sub[i] if close_sub[i] > 0 else 0
            for i in range(len(indicators["atr"]))
        ]

        # 收集 YAML 中的全部条件字符串
        signal = strategy.get("signal", {})
        market_filter = strategy.get("market_filter", {})
        all_conditions: list[tuple[str, str]] = []
        for cond in market_filter.get("conditions", []):
            all_conditions.append(("market_filter", cond))
        if signal.get("long_condition"):
            all_conditions.append(("long_condition", signal["long_condition"]))
        if signal.get("short_condition"):
            all_conditions.append(("short_condition", signal["short_condition"]))

        threshold_patterns = [
            (r"adx\s*>\s*([\d.]+)", "adx", ">"),
            (r"adx\s*<\s*([\d.]+)", "adx", "<"),
            (r"rsi\s*>\s*([\d.]+)", "rsi", ">"),
            (r"rsi\s*<\s*([\d.]+)", "rsi", "<"),
            (r"atr\s*>\s*([\d.]+)\s*\*\s*close", "atr_pct", ">"),
            (r"volume_ratio\s*>\s*([\d.]+)", "volume_ratio", ">"),
            (r"volume_ratio\s*<\s*([\d.]+)", "volume_ratio", "<"),
            (r"bb_bandwidth\s*>\s*([\d.]+)", "bb_bandwidth", ">"),
            (r"bb_bandwidth\s*<\s*([\d.]+)", "bb_bandwidth", "<"),
            (r"cci\s*>\s*([\d.]+)", "cci", ">"),
            (r"cci\s*<\s*-?([\d.]+)", "cci", "<"),
        ]

        tight_conditions: list[dict] = []
        suggested_relaxations: dict[str, str] = {}
        diagnosis_parts: list[str] = []

        for source, cond_str in all_conditions:
            for pattern, ind_key, operator in threshold_patterns:
                match = re.search(pattern, cond_str, re.IGNORECASE)
                if not match:
                    continue
                threshold_str = match.group(1)
                threshold = float(threshold_str)
                data = indicators.get(ind_key, [])
                if not data:
                    continue
                valid = [v for v in data if abs(v) > 1e-10 or ind_key in ("rsi", "cci")]
                if not valid:
                    continue

                if operator == ">":
                    pass_pct = sum(1 for v in valid if v > threshold) / len(valid) * 100
                else:
                    pass_pct = sum(1 for v in valid if v < threshold) / len(valid) * 100

                if pass_pct >= 15:
                    continue  # 不算过严

                d_min, d_max = min(valid), max(valid)
                d_mean = sum(valid) / len(valid)
                # 建议值：让 ~70% 的数据满足条件
                sorted_v = sorted(valid, reverse=(operator == "<"))
                idx_30 = int(len(sorted_v) * 0.30)
                suggested = sorted_v[min(idx_30, len(sorted_v) - 1)]

                tight_conditions.append({
                    "source": source,
                    "condition": cond_str,
                    "indicator": ind_key,
                    "operator": operator,
                    "threshold": threshold,
                    "threshold_str": threshold_str,
                    "pass_pct": round(pass_pct, 1),
                    "data_range": [round(d_min, 4), round(d_max, 4)],
                    "data_mean": round(d_mean, 4),
                    "suggested_value": round(suggested, 4),
                })

                diagnosis_parts.append(
                    f"{source} 中 '{ind_key} {operator} {threshold_str}' "
                    f"仅 {pass_pct:.1f}% K线满足"
                    f"（范围 {d_min:.4f}~{d_max:.4f}，均值 {d_mean:.4f}），"
                    f"建议放宽至 {suggested:.4f}"
                )

                # 生成 critic-compatible 的 key
                if ind_key == "atr_pct":
                    relax_key = "atr_threshold"
                elif ind_key == "rsi":
                    if source == "long_condition":
                        relax_key = "rsi_long_threshold"
                    elif source == "short_condition":
                        relax_key = "rsi_short_threshold"
                    else:
                        relax_key = "rsi_threshold"
                elif ind_key == "adx":
                    relax_key = "adx_threshold"
                elif ind_key == "volume_ratio":
                    relax_key = "volume_ratio_threshold"
                else:
                    relax_key = f"{ind_key}_threshold"
                suggested_relaxations[relax_key] = str(round(suggested, 4))

        if not diagnosis_parts:
            current_confirm_bars = int(signal.get("confirm_bars", 1) or 1)
            market_conditions = market_filter.get("conditions", [])

            if current_confirm_bars > 1:
                suggested_relaxations["confirm_bars"] = str(max(1, current_confirm_bars - 1))
            else:
                suggested_relaxations["reduce_and_conditions"] = "1"
                if len(market_conditions) > 1:
                    suggested_relaxations["drop_market_filter_tail"] = "1"

            diagnosis_parts.append(
                "各单项阈值均有 ≥15% K线满足，问题可能是多条件 AND 组合交集为空，"
                "建议减少 AND 条件数量或降低 confirm_bars"
            )
            tight_conditions.append({
                "source": "combination",
                "condition": "AND 条件组合过严",
                "suggestion": "减少条件或降低 confirm_bars",
            })

        return {
            "diagnosis_text": "; ".join(diagnosis_parts),
            "tight_conditions": tight_conditions,
            "suggested_relaxations": suggested_relaxations,
        }

    # ------------------------------------------------------------------
    # Narrowed param space for warm-start
    # ------------------------------------------------------------------

    def _extract_narrowed_param_space(
        self, strategy: dict, previous_params: dict,
    ) -> dict[str, dict]:
        """以上轮最优参数为中心，收窄搜索至 ±30%，用 step 保证高效离散搜索。"""
        base_space = self._extract_param_space(strategy)
        narrowed: dict[str, dict] = {}

        for k, spec in base_space.items():
            if k not in previous_params:
                narrowed[k] = spec
                continue

            center = previous_params[k]
            if spec["type"] == "int":
                center = int(center)
                delta = max(2, int(abs(center) * 0.3))
                lo = max(spec["low"], center - delta)
                hi = min(spec["high"], center + delta)
                if hi <= lo:
                    hi = lo + 2
                narrowed[k] = {
                    "type": "int", "low": lo, "high": hi,
                    "original": center, "step": 1,
                }
            else:
                center = float(center)
                delta = max(0.01, abs(center) * 0.3)
                lo = max(spec["low"], round(center - delta, 6))
                hi = min(spec["high"], round(center + delta, 6))
                if hi <= lo:
                    hi = round(lo + 0.01, 6)
                # ~20 discrete points in the narrowed range
                step = round((hi - lo) / 20, 6) or 0.001
                narrowed[k] = {
                    "type": "float", "low": lo, "high": hi,
                    "original": center, "step": step,
                }

        return narrowed

    # ------------------------------------------------------------------
    # Warm-start re-optimization
    # ------------------------------------------------------------------

    async def reoptimize_recycled(
        self,
        strategy: dict,
        full_start: str,
        full_end: str,
        previous_params: dict,
    ) -> dict[str, Any]:
        """Warm-start 调优：以上轮最优参数为中心收窄搜索。

        与首轮 optimize 相比：
        - 参数搜索空间围绕 previous_params 收窄至 ±30%
        - suggest_float(step=...) 保证高效离散搜索
        - study.enqueue_trial() 注入上轮最优参数作为首个 trial
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

        # 2. 拉取 IS / OOS 数据
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

        # 3. 生成基础代码
        base_code, err = await self.executor._generate_signal_code(strategy, None)
        if err:
            return {"error": f"基础代码生成失败: {err}"}

        # 4. 收窄参数空间
        narrowed_space = self._extract_narrowed_param_space(strategy, previous_params)
        if not narrowed_space:
            return {"error": "无可优化的数值型因子参数"}

        strategy_name = strategy.get("name", "reopt")
        # warm-start 阶段，Phase 1 缩短（已有方向性）
        phase1_trials = min(self.PHASE1_TRIALS, self.n_trials // 3)

        # 5. Optuna warm-start 优化
        def objective(trial: optuna.Trial) -> float:
            params: dict[str, Any] = {}
            for k, v in narrowed_space.items():
                if v["type"] == "int":
                    params[k] = trial.suggest_int(
                        k, v["low"], v["high"], step=v.get("step", 1),
                    )
                else:
                    step = v.get("step")
                    if step and step > 0:
                        params[k] = trial.suggest_float(
                            k, v["low"], v["high"], step=step,
                        )
                    else:
                        params[k] = trial.suggest_float(k, v["low"], v["high"])
            # fast/slow 硬约束（同时兼容两种命名）
            for fast_k, slow_k in (("fast_period", "slow_period"), ("fast", "slow")):
                if fast_k in params and slow_k in params:
                    if params[slow_k] <= params[fast_k]:
                        raise optuna.exceptions.TrialPruned()

            result = self.executor._run_backtest(
                strategy_name, bars_is, base_code, strategy, params,
            )
            if result.status == "failed" or result.trades_count < 3:
                return -1.0
            if trial.number < phase1_trials:
                return float(result.trades_count)
            trades = max(1, result.trades_count)
            return float(result.sharpe_ratio) * (trades ** 0.5)

        study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        # 注入上轮最优参数作为首个 trial
        seed = {k: v for k, v in previous_params.items() if k in narrowed_space}
        if seed:
            study.enqueue_trial(seed)
            logger.info("Warm-start: 注入上轮最优参数 %s", list(seed.keys()))

        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)

        best_params = dict(study.best_params)
        logger.info(
            "Warm-start 完成: %s | best=%.4f | params=%s",
            strategy_name, study.best_value, best_params,
        )

        # 零交易检测
        if study.best_value <= -1.0:
            diagnosis = self._diagnose_zero_trades(strategy, bars_is, base_code)
            return {
                "error": "zero_trades",
                "zero_trades_diagnosis": diagnosis,
                "best_params": best_params,
                "generated_code": base_code,
                "recycled": True,
                "previous_params": previous_params,
                "n_trials": self.n_trials,
            }

        # 6. IS 最优参数
        is_result = self.executor._run_backtest(
            strategy_name, bars_is, base_code, strategy, best_params,
        )

        # 7. OOS 验证
        oos_result = self.executor._run_backtest(
            strategy_name, bars_oos, base_code, strategy, best_params,
        )

        # 8. OOS 验收
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
            "recycled": True,
            "previous_params": previous_params,
        }
