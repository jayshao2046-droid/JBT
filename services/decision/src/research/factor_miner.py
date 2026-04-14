"""因子挖掘模块 — TASK-0116

从期货 OHLCV K 线数据中挖掘候选因子：
  - 动量因子（5日/20日涨幅）
  - 均值回归因子（价格 vs 移动均线偏离）
  - 量价背离因子（价涨量缩/量价同向）
  - 波动率因子（ATR、历史波动率）
  - 综合打分输出

所有指标纯 numpy 实现，不依赖 talib / pandas。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CandidateFactor:
    """候选因子描述。"""

    name: str
    symbol: str
    value: float            # 当前标准化因子值（z-score）
    raw_value: float        # 原始值（未标准化）
    category: str           # "momentum" | "mean_reversion" | "vol_price" | "volatility"
    lookback: int           # 回望期（K 线根数）
    metadata: Dict[str, Any] = field(default_factory=dict)


class FactorMiner:
    """期货因子挖掘器。

    输入：OHLCV K 线列表（按时间升序，每条含 open/high/low/close/volume）
    输出：CandidateFactor 列表

    示例：
        bars = [{"open":100,"high":105,"low":99,"close":103,"volume":1000}, ...]
        miner = FactorMiner()
        factors = miner.mine(symbol="rb", bars=bars)
    """

    # 各因子的回望窗口（可按品种覆写）
    MOMENTUM_WINDOWS: List[int] = [5, 20]
    MA_REVERSION_WINDOWS: List[int] = [10, 20]
    ATR_WINDOW: int = 14
    VOL_WINDOW: int = 20

    def mine(
        self,
        symbol: str,
        bars: List[Dict[str, Any]],
        windows: Optional[Dict[str, List[int]]] = None,
    ) -> List[CandidateFactor]:
        """挖掘所有候选因子。

        Args:
            symbol: 品种代码
            bars: OHLCV K 线列表（至少需要 max(windows)+1 根）
            windows: 自定义各类因子回望期

        Returns:
            CandidateFactor 列表（长度不定，依有效窗口数量而定）
        """
        if len(bars) < 2:
            return []

        closes = np.array([b["close"] for b in bars], dtype=float)
        highs = np.array([b.get("high", b["close"]) for b in bars], dtype=float)
        lows = np.array([b.get("low", b["close"]) for b in bars], dtype=float)
        volumes = np.array([b.get("volume", 0.0) for b in bars], dtype=float)

        w = windows or {}
        mom_wins = w.get("momentum", self.MOMENTUM_WINDOWS)
        ma_wins = w.get("mean_reversion", self.MA_REVERSION_WINDOWS)

        factors: List[CandidateFactor] = []

        # --- 动量因子 ---
        for lb in mom_wins:
            if len(closes) > lb:
                f = self._momentum(closes, lb)
                if f is not None:
                    factors.append(CandidateFactor(
                        name=f"momentum_{lb}d",
                        symbol=symbol,
                        value=self._zscore(closes[:-1], f),
                        raw_value=f,
                        category="momentum",
                        lookback=lb,
                    ))

        # --- 均值回归因子 ---
        for lb in ma_wins:
            if len(closes) > lb:
                f = self._ma_deviation(closes, lb)
                if f is not None:
                    factors.append(CandidateFactor(
                        name=f"ma_dev_{lb}d",
                        symbol=symbol,
                        value=self._zscore(closes[:-1], f),
                        raw_value=f,
                        category="mean_reversion",
                        lookback=lb,
                    ))

        # --- 量价背离因子 ---
        if len(closes) >= 5 and len(volumes) >= 5:
            f = self._vol_price_divergence(closes, volumes, window=5)
            if f is not None:
                factors.append(CandidateFactor(
                    name="vol_price_div_5d",
                    symbol=symbol,
                    value=f,
                    raw_value=f,
                    category="vol_price",
                    lookback=5,
                ))

        # --- 波动率因子（ATR） ---
        atr_lb = self.ATR_WINDOW
        if len(closes) > atr_lb:
            f = self._atr(highs, lows, closes, atr_lb)
            if f is not None:
                factors.append(CandidateFactor(
                    name=f"atr_{atr_lb}d",
                    symbol=symbol,
                    value=self._zscore(closes[:-1], f),
                    raw_value=f,
                    category="volatility",
                    lookback=atr_lb,
                    metadata={"atr_pct": f / closes[-1] if closes[-1] > 0 else 0.0},
                ))

        # --- 历史波动率因子 ---
        vol_lb = self.VOL_WINDOW
        if len(closes) > vol_lb:
            f = self._hist_vol(closes, vol_lb)
            if f is not None:
                factors.append(CandidateFactor(
                    name=f"hist_vol_{vol_lb}d",
                    symbol=symbol,
                    value=self._zscore(closes[:-1], f),
                    raw_value=f,
                    category="volatility",
                    lookback=vol_lb,
                ))

        return factors

    # ------------------------------------------------------------------
    # 因子计算
    # ------------------------------------------------------------------

    @staticmethod
    def _momentum(closes: np.ndarray, window: int) -> Optional[float]:
        """N日收益率。"""
        if len(closes) <= window:
            return None
        if closes[-window - 1] <= 0:
            return None
        return float((closes[-1] - closes[-window - 1]) / closes[-window - 1])

    @staticmethod
    def _ma_deviation(closes: np.ndarray, window: int) -> Optional[float]:
        """当前价格与 N日均线的偏离度。"""
        ma = float(np.mean(closes[-window:]))
        if ma <= 0:
            return None
        return float((closes[-1] - ma) / ma)

    @staticmethod
    def _vol_price_divergence(
        closes: np.ndarray, volumes: np.ndarray, window: int = 5
    ) -> Optional[float]:
        """量价背离因子：价格涨跌方向 × 成交量变化方向的相关性取反。

        正值 = 量价同向（追涨杀跌），负值 = 量价背离（反转信号）。
        """
        if len(closes) < window + 1 or len(volumes) < window + 1:
            return None
        price_changes = np.diff(closes[-window - 1:])
        vol_changes = np.diff(volumes[-window - 1:])
        if np.std(price_changes) < 1e-8 or np.std(vol_changes) < 1e-8:
            return 0.0
        corr = float(np.corrcoef(price_changes, vol_changes)[0, 1])
        return corr if not np.isnan(corr) else 0.0

    @staticmethod
    def _atr(
        highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, window: int
    ) -> Optional[float]:
        """平均真实波幅（ATR）。"""
        if len(closes) < window + 1:
            return None
        tr = np.maximum(
            highs[-window:] - lows[-window:],
            np.maximum(
                np.abs(highs[-window:] - closes[-window - 1:-1]),
                np.abs(lows[-window:] - closes[-window - 1:-1]),
            ),
        )
        return float(np.mean(tr))

    @staticmethod
    def _hist_vol(closes: np.ndarray, window: int) -> Optional[float]:
        """历史收益率标准差（年化前）。"""
        if len(closes) < window + 1:
            return None
        returns = np.diff(np.log(closes[-window - 1:]))
        return float(np.std(returns)) if len(returns) > 1 else None

    @staticmethod
    def _zscore(history: np.ndarray, value: float) -> float:
        """将当前值相对历史序列标准化为 z-score；历史方差为 0 时返回 0。"""
        if len(history) < 2:
            return 0.0
        mu, sigma = float(np.mean(history)), float(np.std(history))
        if sigma < 1e-8:
            return 0.0
        return (value - mu) / sigma
