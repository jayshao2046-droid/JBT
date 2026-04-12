"""
晚间轮换器 (CB8)
对股票池进行晚间重新评分和轮换
"""
from __future__ import annotations

import uuid
from datetime import datetime


class EveningRotator:
    """晚间轮换器，重新评分并选出 TOP-N 股票"""

    def __init__(self, top_n: int = 30, data_service_url: str = "http://localhost:8105"):
        self.top_n = top_n
        self.data_service_url = data_service_url
        self._last_plan: dict | None = None

    def rotate(self, universe: list[str], lookback_days: int = 20) -> list[str]:
        """
        对 universe 中的股票重新评分，返回 TOP-N 代码列表
        注意：此实现不实际调用 data service，需要外部传入 bars 数据
        """
        if not universe:
            return []

        # 简化实现：返回前 top_n 个股票（实际应该根据评分排序）
        # 实际使用时需要外部传入 bars 数据并调用 _score_stock
        selected = universe[:self.top_n]

        # 生成轮换计划
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        self._last_plan = {
            "plan_id": plan_id,
            "rotated_at": datetime.now().isoformat(),
            "top_n": self.top_n,
            "selected": selected,
            "scores": [{"symbol": s, "score": 0.0} for s in selected]
        }

        return selected

    def get_rotation_plan(self) -> dict:
        """返回最近一次轮换计划"""
        return self._last_plan or {
            "plan_id": None,
            "rotated_at": None,
            "top_n": self.top_n,
            "selected": [],
            "scores": []
        }

    def _score_stock(self, symbol: str, bars: list[dict]) -> float:
        """
        内部打分：momentum * 0.5 + volume_ratio * 0.3 + price_position * 0.2
        bars: [{open, high, low, close, volume, date}, ...]
        """
        if not bars or len(bars) < 2:
            return 0.0

        # 动量：最新价 / 首价 - 1
        first_close = bars[0]["close"]
        last_close = bars[-1]["close"]
        momentum = (last_close - first_close) / first_close if first_close > 0 else 0.0

        # 量比：最新成交量 / 平均成交量
        volumes = [b["volume"] for b in bars]
        avg_volume = sum(volumes) / len(volumes) if volumes else 1.0
        last_volume = bars[-1]["volume"]
        volume_ratio = last_volume / avg_volume if avg_volume > 0 else 1.0

        # 价格位置：(最新价 - 最低价) / (最高价 - 最低价)
        highs = [b["high"] for b in bars]
        lows = [b["low"] for b in bars]
        max_high = max(highs)
        min_low = min(lows)
        price_range = max_high - min_low
        price_position = (last_close - min_low) / price_range if price_range > 0 else 0.5

        # 综合评分
        score = momentum * 0.5 + volume_ratio * 0.3 + price_position * 0.2
        return score
