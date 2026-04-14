"""信号质量验证器 — TASK-0115

独立于 LLM 门控，对信号做定量校验：
  1. IC 有效性检查（因子与未来收益的信息系数）
  2. 跨行情类型一致性检查
  3. 信号衰减检测（IC 滑动窗口）
  4. 异常信号标记

所有功能纯 numpy/统计，不依赖 XGBoost 或 LLM。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_VALID_REGIMES = {"trend", "oscillation", "high_vol", "compression", "event_driven"}


@dataclass
class ValidationResult:
    """信号验证结果。"""

    symbol: str
    signal_id: str
    valid: bool
    ic: float              # 信息系数（-1 ~ +1）
    ic_decay: float        # IC 滑动窗口衰减率（0=无衰减，1=完全失效）
    regime_consistent: bool  # 信号方向与 regime 是否一致
    anomaly: bool          # 是否为异常信号
    reasons: List[str]     # 拒绝或警告原因


class SignalValidator:
    """信号质量验证器。

    使用方式：
        validator = SignalValidator()
        result = validator.validate(symbol, signal, returns, regime)
    """

    # IC 有效阈值：绝对值低于此值视为无信息
    IC_MIN_THRESHOLD: float = 0.02
    # 异常判定：信号值超过 N 个标准差
    ANOMALY_SIGMA: float = 3.0
    # IC 衰减判定：滑窗 IC 下降超过此比例视为衰减
    IC_DECAY_THRESHOLD: float = 0.5

    def validate(
        self,
        symbol: str,
        signal_id: str,
        signal_value: float,
        forward_returns: List[float],
        factor_history: Optional[List[float]] = None,
        regime: Optional[str] = None,
    ) -> ValidationResult:
        """验证单个信号质量。

        Args:
            symbol: 品种代码
            signal_id: 信号 ID
            signal_value: 当前信号值（标准化，通常 -1~+1 或 0~1）
            forward_returns: 历史同类信号对应的未来收益序列（用于 IC 计算）
            factor_history: 历史因子值序列（用于 IC 和异常检测）
            regime: 当前行情类型

        Returns:
            ValidationResult
        """
        reasons: List[str] = []

        # --- IC 计算 ---
        ic = self._calc_ic(factor_history or [], forward_returns)
        # 有号 IC 检查：因子必须与收益正向相关才视为有效信号
        # IC < 0 表示因子方向与历史收益反向，当前信号方向可能错误
        ic_valid = ic >= self.IC_MIN_THRESHOLD
        if not ic_valid:
            reasons.append(f"IC={ic:.4f} < {self.IC_MIN_THRESHOLD}，因子无信息量或方向相反")

        # --- IC 衰减检测 ---
        ic_decay = self._calc_ic_decay(factor_history or [], forward_returns)
        if ic_decay > self.IC_DECAY_THRESHOLD:
            reasons.append(f"IC 衰减率={ic_decay:.2f}，因子可能失效")

        # --- 异常信号检测 ---
        anomaly = self._is_anomaly(signal_value, factor_history or [])
        if anomaly:
            reasons.append(f"信号值={signal_value:.4f} 超过 {self.ANOMALY_SIGMA}σ 范围")

        # --- Regime 一致性 ---
        regime_consistent = self._check_regime_consistency(signal_value, regime)
        if not regime_consistent:
            reasons.append(f"信号方向与行情类型 {regime} 不一致")

        # --- 综合判定 ---
        valid = ic_valid and not anomaly and regime_consistent

        return ValidationResult(
            symbol=symbol,
            signal_id=signal_id,
            valid=valid,
            ic=ic,
            ic_decay=ic_decay,
            regime_consistent=regime_consistent,
            anomaly=anomaly,
            reasons=reasons,
        )

    def validate_batch(
        self,
        signals: List[Dict[str, Any]],
        default_regime: Optional[str] = None,
    ) -> List[ValidationResult]:
        """批量验证信号列表。

        Args:
            signals: 信号列表，每个 dict 需含：
                     symbol, signal_id, signal_value, forward_returns,
                     factor_history (可选), regime (可选)
            default_regime: 未指定 regime 时的默认值

        Returns:
            ValidationResult 列表，顺序与输入一致
        """
        results: List[ValidationResult] = []
        for sig in signals:
            results.append(
                self.validate(
                    symbol=sig.get("symbol", ""),
                    signal_id=sig.get("signal_id", ""),
                    signal_value=float(sig.get("signal_value", 0.0)),
                    forward_returns=sig.get("forward_returns", []),
                    factor_history=sig.get("factor_history"),
                    regime=sig.get("regime", default_regime),
                )
            )
        return results

    # ------------------------------------------------------------------
    # 内部计算
    # ------------------------------------------------------------------

    def _calc_ic(self, factor_vals: List[float], returns: List[float]) -> float:
        """计算 Rank IC（Spearman 相关系数）。

        要求两序列等长，长度 < 2 时返回 0.0。
        """
        if len(factor_vals) < 2 or len(returns) < 2:
            return 0.0
        n = min(len(factor_vals), len(returns))
        f = np.array(factor_vals[:n], dtype=float)
        r = np.array(returns[:n], dtype=float)
        if np.std(f) < 1e-8 or np.std(r) < 1e-8:
            return 0.0
        # Rank IC = Pearson(rank(f), rank(r))
        rf = np.argsort(np.argsort(f)).astype(float)
        rr = np.argsort(np.argsort(r)).astype(float)
        corr = np.corrcoef(rf, rr)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0

    def _calc_ic_decay(self, factor_vals: List[float], returns: List[float]) -> float:
        """计算 IC 衰减率：比较前半段与后半段 IC 的下降比例。

        返回 0.0（无衰减）~ 1.0（完全失效）。
        """
        n = min(len(factor_vals), len(returns))
        if n < 4:
            return 0.0
        mid = n // 2
        ic_early = self._calc_ic(factor_vals[:mid], returns[:mid])
        ic_late = self._calc_ic(factor_vals[mid:], returns[mid:])
        if abs(ic_early) < 1e-8:
            return 0.0
        decay = (abs(ic_early) - abs(ic_late)) / abs(ic_early)
        return max(0.0, min(1.0, float(decay)))

    def _is_anomaly(self, signal_value: float, history: List[float]) -> bool:
        """判断当前信号值是否为异常（超过历史 N σ）。"""
        if len(history) < 4:
            return False
        h = np.array(history, dtype=float)
        mu, sigma = float(np.mean(h)), float(np.std(h))
        if sigma < 1e-8:
            return False
        return abs(signal_value - mu) > self.ANOMALY_SIGMA * sigma

    @staticmethod
    def _check_regime_consistency(signal_value: float, regime: Optional[str]) -> bool:
        """检查信号方向与 regime 的一致性。

        event_driven 和 compression 期间，强方向信号（>0.7 或 <-0.7）视为不一致。
        """
        if regime is None or regime not in _VALID_REGIMES:
            return True
        if regime in ("event_driven", "compression"):
            # 这两种 regime 下不建仓，强信号视为不一致
            return abs(signal_value) <= 0.7
        return True
