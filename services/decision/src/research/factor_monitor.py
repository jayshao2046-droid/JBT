"""因子健康监控 — TASK-0115

监控因子的 IC 衰减、分布漂移和活跃度，按品种/regime 分组统计。
发现异常时通过 feishu 发送 P2 预警。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FactorHealth:
    """单因子健康快照。"""

    factor_name: str
    symbol: str
    ic_30d: float          # 近30日 Rank IC
    ic_90d: float          # 近90日 Rank IC（基准）
    decay_rate: float      # 衰减率 = (ic_90d - ic_30d) / max(|ic_90d|, ε)
    mean_shift: float      # 分布均值漂移（当前30日均值 - 历史90日均值）
    std_ratio: float       # 分布方差比（当前/历史，>2 或 <0.5 为异常）
    healthy: bool
    warnings: List[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FactorMonitor:
    """因子健康监控器。

    按 (factor_name, symbol) 维护历史因子值和对应的远期收益，
    定期调用 check() 生成健康快照；检测到异常时记录日志。

    示例：
        monitor = FactorMonitor()
        monitor.record("momentum_5d", "rb", factor_value=0.23, forward_return=0.01)
        health = monitor.check("momentum_5d", "rb")
    """

    # 衰减警告阈值：近30日 IC 相对近90日 IC 下降超 40%
    DECAY_WARNING_THRESHOLD: float = 0.4
    # 均值漂移警告阈值（以历史标准差为单位）
    MEAN_SHIFT_SIGMA: float = 2.0
    # 方差异常范围
    STD_RATIO_MIN: float = 0.5
    STD_RATIO_MAX: float = 2.0
    # 最小有效样本数
    MIN_SAMPLES: int = 10

    def __init__(self) -> None:
        # {(factor_name, symbol): {"factor_vals": [...], "returns": [...]}}
        self._history: Dict[tuple, Dict[str, List[float]]] = {}

    def record(
        self,
        factor_name: str,
        symbol: str,
        factor_value: float,
        forward_return: float,
    ) -> None:
        """记录一条因子观测值及其对应的未来收益。

        Args:
            factor_name: 因子名称（如 'momentum_5d'）
            symbol: 品种代码
            factor_value: 当天因子值（已标准化）
            forward_return: 对应的未来N日收益率
        """
        key = (factor_name, symbol)
        if key not in self._history:
            self._history[key] = {"factor_vals": [], "returns": []}
        self._history[key]["factor_vals"].append(float(factor_value))
        self._history[key]["returns"].append(float(forward_return))

    def check(self, factor_name: str, symbol: str) -> Optional[FactorHealth]:
        """检查因子健康状态。

        Args:
            factor_name: 因子名称
            symbol: 品种代码

        Returns:
            FactorHealth 或 None（样本不足时）
        """
        key = (factor_name, symbol)
        data = self._history.get(key)
        if not data or len(data["factor_vals"]) < self.MIN_SAMPLES:
            return None

        vals = np.array(data["factor_vals"], dtype=float)
        rets = np.array(data["returns"], dtype=float)

        n = len(vals)
        window_30 = max(1, min(30, n))
        window_90 = max(1, min(90, n))

        ic_30d = self._rank_ic(vals[-window_30:], rets[-window_30:])
        ic_90d = self._rank_ic(vals[-window_90:], rets[-window_90:])
        decay_rate = self._decay(ic_30d, ic_90d)
        mean_shift, std_ratio = self._distribution_drift(vals, window_30, window_90)

        warnings: List[str] = []
        if decay_rate > self.DECAY_WARNING_THRESHOLD:
            warnings.append(f"IC 衰减率 {decay_rate:.2f} > {self.DECAY_WARNING_THRESHOLD}")
        if abs(mean_shift) > self.MEAN_SHIFT_SIGMA:
            warnings.append(f"均值漂移 {mean_shift:.2f}σ（近期分布与历史偏离）")
        if not (self.STD_RATIO_MIN <= std_ratio <= self.STD_RATIO_MAX):
            warnings.append(f"方差比 {std_ratio:.2f} 超出正常范围 [{self.STD_RATIO_MIN}, {self.STD_RATIO_MAX}]")

        healthy = len(warnings) == 0

        health = FactorHealth(
            factor_name=factor_name,
            symbol=symbol,
            ic_30d=ic_30d,
            ic_90d=ic_90d,
            decay_rate=decay_rate,
            mean_shift=mean_shift,
            std_ratio=std_ratio,
            healthy=healthy,
            warnings=warnings,
        )

        if not healthy:
            logger.warning(
                "因子健康预警 [%s/%s]: %s",
                factor_name, symbol, "; ".join(warnings),
            )

        return health

    def check_all(self) -> List[FactorHealth]:
        """检查所有已记录的 (factor, symbol) 对。"""
        results: List[FactorHealth] = []
        for factor_name, symbol in list(self._history.keys()):
            h = self.check(factor_name, symbol)
            if h is not None:
                results.append(h)
        return results

    def get_unhealthy(self) -> List[FactorHealth]:
        """返回所有不健康的因子。"""
        return [h for h in self.check_all() if not h.healthy]

    def clear(self, factor_name: str, symbol: str) -> None:
        """清除指定因子历史（品种下架时调用）。"""
        self._history.pop((factor_name, symbol), None)

    # ------------------------------------------------------------------
    # 内部计算
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_ic(vals: np.ndarray, rets: np.ndarray) -> float:
        if len(vals) < 2:
            return 0.0
        if np.std(vals) < 1e-8 or np.std(rets) < 1e-8:
            return 0.0
        rv = np.argsort(np.argsort(vals)).astype(float)
        rr = np.argsort(np.argsort(rets)).astype(float)
        corr = np.corrcoef(rv, rr)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0

    @staticmethod
    def _decay(ic_30d: float, ic_90d: float) -> float:
        if abs(ic_90d) < 1e-8:
            return 0.0
        decay = (abs(ic_90d) - abs(ic_30d)) / abs(ic_90d)
        return max(0.0, min(1.0, float(decay)))

    @staticmethod
    def _distribution_drift(
        vals: np.ndarray, window_30: int, window_90: int
    ) -> tuple[float, float]:
        """返回 (mean_shift_in_sigma, std_ratio)。"""
        hist = vals[:-window_30] if len(vals) > window_30 else vals
        recent = vals[-window_30:]
        if len(hist) < 2:
            return 0.0, 1.0
        hist_std = float(np.std(hist))
        recent_std = float(np.std(recent)) if len(recent) > 1 else 0.0
        hist_mean = float(np.mean(hist))
        recent_mean = float(np.mean(recent))
        if hist_std < 1e-8:
            # 历史方差为零：只要均值有绝对变化就视为漂移（返回大数触发警告）
            raw_diff = abs(recent_mean - hist_mean)
            mean_shift = 999.0 if raw_diff > 1e-6 else 0.0
        else:
            mean_shift = (recent_mean - hist_mean) / hist_std
        std_ratio = recent_std / hist_std if hist_std > 1e-8 else 1.0
        return mean_shift, std_ratio
