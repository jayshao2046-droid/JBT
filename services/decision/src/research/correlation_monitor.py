"""跨品种相关性监控 — TASK-0117

监控期货品种间的价格相关性，检测相关性突变（系数从高位骤降/骤升）。
主要用于套利监控：相关性骤降 → 价差扩张 → 套利机会或风险。

覆盖 5 个 regime 下的相关性特征：
  - compression/event_driven 时相关性突变概率更高
  - high_vol 时相关性往往向 1 趋近（踩踏效应）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CorrelationSnapshot:
    """两个品种在某时刻的相关性快照。"""

    symbol_a: str
    symbol_b: str
    corr_30d: float       # 近30日价格相关系数
    corr_90d: float       # 近90日价格相关系数（基准）
    delta: float          # corr_30d - corr_90d（突变幅度）
    breakdown: bool       # True = 相关性出现显著突变
    regime_a: Optional[str] = None
    regime_b: Optional[str] = None
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CorrelationMonitor:
    """跨品种相关性监控器。

    记录各品种的收盘价序列，批量计算两两相关系数，检测突变。

    示例：
        monitor = CorrelationMonitor()
        for bar in bars_rb:
            monitor.record("rb", bar["close"])
        for bar in bars_hc:
            monitor.record("hc", bar["close"])
        snapshots = monitor.check_pair("rb", "hc")
    """

    # 相关性突变阈值：30日相关系数与90日基准偏离超过此值为突变
    BREAKDOWN_DELTA: float = 0.3
    # 最小有效样本数
    MIN_SAMPLES: int = 30

    # 预定义套利对（黑色链/有色/农产品/化工）
    DEFAULT_PAIRS: List[Tuple[str, str]] = [
        ("rb", "hc"),   # 螺纹-热卷
        ("i", "rb"),    # 铁矿-螺纹
        ("j", "jm"),    # 焦炭-焦煤
        ("cu", "al"),   # 铜-铝
        ("m", "RM"),    # 豆粕-菜粕
        ("pp", "l"),    # 聚丙烯-聚乙烯
        ("EB", "l"),    # 苯乙烯-聚乙烯
        ("ag", "au"),   # 白银-黄金
        ("c", "cs"),    # 玉米-淀粉
        ("sc", "fu"),   # 原油-燃料油
    ]

    def __init__(self) -> None:
        # {symbol: [close_price, ...]}
        self._series: Dict[str, List[float]] = {}

    def record(self, symbol: str, close: float) -> None:
        """追加一条收盘价记录。"""
        if symbol not in self._series:
            self._series[symbol] = []
        self._series[symbol].append(float(close))

    def record_batch(self, symbol: str, closes: List[float]) -> None:
        """批量追加收盘价（用于初始化历史数据）。"""
        if symbol not in self._series:
            self._series[symbol] = []
        self._series[symbol].extend([float(c) for c in closes])

    def check_pair(
        self,
        symbol_a: str,
        symbol_b: str,
        regime_a: Optional[str] = None,
        regime_b: Optional[str] = None,
    ) -> Optional[CorrelationSnapshot]:
        """检查两个品种的相关性是否发生突变。

        Args:
            symbol_a: 品种 A
            symbol_b: 品种 B
            regime_a: 品种 A 当前 regime（可选）
            regime_b: 品种 B 当前 regime（可选）

        Returns:
            CorrelationSnapshot 或 None（数据不足时）
        """
        series_a = self._series.get(symbol_a, [])
        series_b = self._series.get(symbol_b, [])
        n = min(len(series_a), len(series_b))

        if n < self.MIN_SAMPLES:
            return None

        a = np.array(series_a[-n:], dtype=float)
        b = np.array(series_b[-n:], dtype=float)

        # 转为收益率序列（更稳定）
        ra = np.diff(np.log(np.maximum(a, 1e-8)))
        rb = np.diff(np.log(np.maximum(b, 1e-8)))

        window_30 = min(29, len(ra))
        window_90 = min(89, len(ra))

        corr_30d = self._corr(ra[-window_30:], rb[-window_30:])
        corr_90d = self._corr(ra[-window_90:], rb[-window_90:])
        delta = corr_30d - corr_90d
        breakdown = abs(delta) >= self.BREAKDOWN_DELTA

        if breakdown:
            logger.warning(
                "相关性突变 [%s/%s]: 30d=%.3f, 90d=%.3f, delta=%.3f",
                symbol_a, symbol_b, corr_30d, corr_90d, delta,
            )

        return CorrelationSnapshot(
            symbol_a=symbol_a,
            symbol_b=symbol_b,
            corr_30d=corr_30d,
            corr_90d=corr_90d,
            delta=delta,
            breakdown=breakdown,
            regime_a=regime_a,
            regime_b=regime_b,
        )

    def check_all_pairs(
        self,
        pairs: Optional[List[Tuple[str, str]]] = None,
        regimes: Optional[Dict[str, str]] = None,
    ) -> List[CorrelationSnapshot]:
        """批量检查所有套利对。

        Args:
            pairs: 套利对列表，默认使用 DEFAULT_PAIRS
            regimes: {symbol: regime} 映射

        Returns:
            有数据的 CorrelationSnapshot 列表
        """
        pairs = pairs or self.DEFAULT_PAIRS
        regimes = regimes or {}
        results: List[CorrelationSnapshot] = []
        for sym_a, sym_b in pairs:
            snap = self.check_pair(
                sym_a, sym_b,
                regime_a=regimes.get(sym_a),
                regime_b=regimes.get(sym_b),
            )
            if snap is not None:
                results.append(snap)
        return results

    def get_breakdowns(
        self, pairs: Optional[List[Tuple[str, str]]] = None
    ) -> List[CorrelationSnapshot]:
        """返回发生相关性突变的套利对。"""
        return [s for s in self.check_all_pairs(pairs) if s.breakdown]

    @staticmethod
    def _corr(a: np.ndarray, b: np.ndarray) -> float:
        if len(a) < 2 or np.std(a) < 1e-8 or np.std(b) < 1e-8:
            return 0.0
        c = np.corrcoef(a, b)[0, 1]
        return float(c) if not np.isnan(c) else 0.0
