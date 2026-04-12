"""股票策略模板 — TASK-0069 CB1

三类日线股票策略模板：短线、中线、长线。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseStockTemplate(ABC):
    """股票策略模板基类。"""

    name: str
    holding_days: int
    required_factors: list[str]

    @abstractmethod
    def entry_signal(self, df: pd.DataFrame) -> bool:
        """判断入场信号。

        Args:
            df: 日线 K 线数据，包含 open/high/low/close/volume 等字段。

        Returns:
            True 表示产生入场信号，False 表示无信号。
        """

    @abstractmethod
    def exit_signal(self, df: pd.DataFrame, entry_price: float) -> bool:
        """判断离场信号。

        Args:
            df: 日线 K 线数据。
            entry_price: 入场价格。

        Returns:
            True 表示产生离场信号，False 表示继续持有。
        """

    def to_dict(self) -> dict[str, Any]:
        """返回模板信息字典。"""
        return {
            "name": self.name,
            "holding_days": self.holding_days,
            "required_factors": self.required_factors,
        }


class ShortTermStockTemplate(BaseStockTemplate):
    """短线股票策略模板（1~5 日）。

    基于动量和成交量因子：
    - 入场：5 日动量 > 3%，成交量放大 > 1.5 倍
    - 离场：止盈 8% 或止损 4%
    """

    name = "short_term"
    holding_days = 3
    required_factors = ["momentum_5d", "volume_ratio_5d"]

    def entry_signal(self, df: pd.DataFrame) -> bool:
        if len(df) < 5:
            return False

        closes = df["close"].values
        volumes = df["volume"].values

        # 5 日动量
        momentum_5d = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0.0

        # 成交量比率（近 5 日均量 / 前 5 日均量）
        vol_recent = volumes[-5:].mean()
        vol_prev = volumes[-10:-5].mean() if len(volumes) >= 10 else vol_recent
        volume_ratio = vol_recent / vol_prev if vol_prev > 0 else 1.0

        return momentum_5d > 0.03 and volume_ratio > 1.5

    def exit_signal(self, df: pd.DataFrame, entry_price: float) -> bool:
        if df.empty or entry_price <= 0:
            return False

        current_price = df["close"].iloc[-1]
        return_pct = (current_price - entry_price) / entry_price

        # 止盈 8% 或止损 4%
        return return_pct >= 0.08 or return_pct <= -0.04


class MidTermStockTemplate(BaseStockTemplate):
    """中线股票策略模板（5~20 日）。

    基于趋势和均线因子：
    - 入场：5 日均线上穿 20 日均线，价格在 20 日高点 80% 以上
    - 离场：5 日均线下穿 20 日均线
    """

    name = "mid_term"
    holding_days = 10
    required_factors = ["sma_5", "sma_20", "price_position_20d"]

    def entry_signal(self, df: pd.DataFrame) -> bool:
        if len(df) < 20:
            return False

        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values

        # 均线
        sma_5 = closes[-5:].mean()
        sma_20 = closes[-20:].mean()
        sma_5_prev = closes[-6:-1].mean()
        sma_20_prev = closes[-21:-1].mean() if len(closes) >= 21 else sma_20

        # 金叉
        golden_cross = sma_5 > sma_20 and sma_5_prev <= sma_20_prev

        # 价格位置（当前价在 20 日高低点的位置）
        high_20 = highs[-20:].max()
        low_20 = lows[-20:].min()
        price_position = (
            (closes[-1] - low_20) / (high_20 - low_20) if high_20 != low_20 else 0.5
        )

        return golden_cross and price_position >= 0.8

    def exit_signal(self, df: pd.DataFrame, entry_price: float) -> bool:
        if len(df) < 20:
            return False

        closes = df["close"].values

        sma_5 = closes[-5:].mean()
        sma_20 = closes[-20:].mean()

        # 死叉
        return sma_5 < sma_20


class LongTermStockTemplate(BaseStockTemplate):
    """长线股票策略模板（20 日+）。

    基于价值和基本面因子（简化版，仅用技术指标模拟）：
    - 入场：20 日均线向上，价格回调到均线附近（-5% ~ +2%）
    - 离场：跌破 20 日均线 5% 以上
    """

    name = "long_term"
    holding_days = 30
    required_factors = ["sma_20", "sma_60"]

    def entry_signal(self, df: pd.DataFrame) -> bool:
        if len(df) < 60:
            return False

        closes = df["close"].values

        # 均线
        sma_20 = closes[-20:].mean()
        sma_60 = closes[-60:].mean()
        sma_20_prev = closes[-21:-1].mean() if len(closes) >= 21 else sma_20

        # 20 日均线向上
        ma_uptrend = sma_20 > sma_20_prev and sma_20 > sma_60

        # 价格回调到均线附近
        current_price = closes[-1]
        distance_to_ma = (current_price - sma_20) / sma_20 if sma_20 > 0 else 0.0

        return ma_uptrend and -0.05 <= distance_to_ma <= 0.02

    def exit_signal(self, df: pd.DataFrame, entry_price: float) -> bool:
        if len(df) < 20:
            return False

        closes = df["close"].values
        sma_20 = closes[-20:].mean()
        current_price = closes[-1]

        # 跌破 20 日均线 5% 以上
        return current_price < sma_20 * 0.95


def get_all_templates() -> list[BaseStockTemplate]:
    """返回所有股票策略模板实例。"""
    return [
        ShortTermStockTemplate(),
        MidTermStockTemplate(),
        LongTermStockTemplate(),
    ]
