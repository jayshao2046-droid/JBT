"""因子有效性验证 — TASK-0116

对 FactorMiner 输出的候选因子做统计有效性校验：
  - IC 显著性检验（t-test）
  - IC IR（IC/std_IC，>0.5 为有效）
  - 多空分组收益差（Top 30% vs Bottom 30%）

通过验证的因子才允许进入生产信号池。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FactorValidationResult:
    """因子验证结果。"""

    factor_name: str
    symbol: str
    ic_mean: float       # 均值 IC
    ic_std: float        # IC 标准差
    ic_ir: float         # IC IR = ic_mean / ic_std
    t_stat: float        # t 统计量
    p_value: float       # 显著性 p 值（近似）
    ls_return: float     # 多空收益差（Top30% - Bottom30%）
    passed: bool
    reason: str


class FactorValidator:
    """因子有效性验证器。

    需要提供因子值序列和对应的远期收益序列（时间对齐，同等长度）。

    示例：
        validator = FactorValidator()
        result = validator.validate("momentum_5d", "rb", factor_series, return_series)
        if result.passed:
            ...
    """

    # IC IR 阈值：>0.5 认为因子有效
    IC_IR_THRESHOLD: float = 0.3
    # p 值阈值：<0.1 认为 IC 显著
    P_VALUE_THRESHOLD: float = 0.1
    # 多空收益差下限（正值 = 多头跑赢空头）
    LS_RETURN_THRESHOLD: float = 0.0
    # 最小有效样本数
    MIN_SAMPLES: int = 20

    def validate(
        self,
        factor_name: str,
        symbol: str,
        factor_series: List[float],
        return_series: List[float],
        top_pct: float = 0.3,
    ) -> FactorValidationResult:
        """验证单个因子有效性。

        Args:
            factor_name: 因子名称
            symbol: 品种代码
            factor_series: 历史因子值序列（时间升序）
            return_series: 对应的未来收益序列
            top_pct: 多空分组比例（默认30%）

        Returns:
            FactorValidationResult
        """
        n = min(len(factor_series), len(return_series))
        if n < self.MIN_SAMPLES:
            return FactorValidationResult(
                factor_name=factor_name, symbol=symbol,
                ic_mean=0.0, ic_std=0.0, ic_ir=0.0, t_stat=0.0,
                p_value=1.0, ls_return=0.0, passed=False,
                reason=f"样本不足 (n={n} < {self.MIN_SAMPLES})",
            )

        f = np.array(factor_series[:n], dtype=float)
        r = np.array(return_series[:n], dtype=float)

        # --- IC 序列（按时间滚动10期窗口计算）---
        ic_series = self._rolling_ic(f, r, window=min(10, n // 2))
        ic_mean = float(np.mean(ic_series)) if len(ic_series) > 0 else 0.0
        ic_std = float(np.std(ic_series)) if len(ic_series) > 1 else 1.0

        ic_ir = ic_mean / ic_std if ic_std > 1e-8 else (999.0 if abs(ic_mean) > 1e-4 else 0.0)

        # --- t 统计量 ---
        t_stat, p_value = self._t_test(ic_series)

        # --- 多空收益差 ---
        ls_return = self._ls_return(f, r, top_pct=top_pct)

        # --- 综合判定 ---
        passed = (
            abs(ic_ir) >= self.IC_IR_THRESHOLD
            and p_value <= self.P_VALUE_THRESHOLD
            and ls_return >= self.LS_RETURN_THRESHOLD
        )
        if passed:
            reason = "通过：IC IR 显著，多空收益差为正"
        else:
            parts = []
            if abs(ic_ir) < self.IC_IR_THRESHOLD:
                parts.append(f"IC IR={ic_ir:.3f} < {self.IC_IR_THRESHOLD}")
            if p_value > self.P_VALUE_THRESHOLD:
                parts.append(f"p={p_value:.3f} > {self.P_VALUE_THRESHOLD}")
            if ls_return < self.LS_RETURN_THRESHOLD:
                parts.append(f"多空收益差={ls_return:.4f} < 0")
            reason = "未通过：" + "；".join(parts)

        return FactorValidationResult(
            factor_name=factor_name, symbol=symbol,
            ic_mean=ic_mean, ic_std=ic_std, ic_ir=ic_ir,
            t_stat=t_stat, p_value=p_value,
            ls_return=ls_return, passed=passed, reason=reason,
        )

    def validate_batch(
        self,
        factor_data: List[Dict],
    ) -> List[FactorValidationResult]:
        """批量验证。

        Args:
            factor_data: 列表，每条含 factor_name/symbol/factor_series/return_series
        """
        return [
            self.validate(
                factor_name=d["factor_name"],
                symbol=d.get("symbol", ""),
                factor_series=d["factor_series"],
                return_series=d["return_series"],
            )
            for d in factor_data
        ]

    # ------------------------------------------------------------------
    # 内部计算
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_ic_single(f: np.ndarray, r: np.ndarray) -> float:
        if len(f) < 2 or np.std(f) < 1e-8 or np.std(r) < 1e-8:
            return 0.0
        rf = np.argsort(np.argsort(f)).astype(float)
        rr = np.argsort(np.argsort(r)).astype(float)
        corr = np.corrcoef(rf, rr)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0

    def _rolling_ic(
        self, f: np.ndarray, r: np.ndarray, window: int
    ) -> np.ndarray:
        """滚动窗口 Rank IC 序列。"""
        n = len(f)
        ics = []
        for i in range(window, n):
            ic = self._rank_ic_single(f[i - window:i], r[i - window:i])
            ics.append(ic)
        return np.array(ics, dtype=float)

    @staticmethod
    def _t_test(ic_series: np.ndarray) -> tuple[float, float]:
        """单样本 t 检验 H0: mean(IC) = 0。返回 (t_stat, p_value)。"""
        n = len(ic_series)
        if n < 2:
            return 0.0, 1.0
        mu = float(np.mean(ic_series))
        std_ddof1 = float(np.std(ic_series, ddof=1))
        if std_ddof1 < 1e-8:
            # 方差为零：如果均值显著不为零，视为极度显著
            if abs(mu) > 1e-8:
                return 999.0, 0.001
            return 0.0, 1.0
        se = std_ddof1 / (n ** 0.5)
        t_stat = mu / se
        # 近似 p 值（利用正态分布，样本量足够时有效）
        # |t| > 1.645 → p < 0.1; |t| > 1.96 → p < 0.05
        abs_t = abs(t_stat)
        if abs_t >= 2.576:
            p_value = 0.01
        elif abs_t >= 1.960:
            p_value = 0.05
        elif abs_t >= 1.645:
            p_value = 0.10
        else:
            p_value = 0.20
        return float(t_stat), float(p_value)

    @staticmethod
    def _ls_return(
        f: np.ndarray, r: np.ndarray, top_pct: float = 0.3
    ) -> float:
        """多空分组收益差：Top-pct 均值 - Bottom-pct 均值。"""
        n = len(f)
        k = max(1, int(n * top_pct))
        sorted_idx = np.argsort(f)
        top_ret = float(np.mean(r[sorted_idx[-k:]]))
        bot_ret = float(np.mean(r[sorted_idx[:k]]))
        return top_ret - bot_ret
