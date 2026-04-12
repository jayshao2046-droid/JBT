"""
盘后评估器 (CB7)
评估股票当日表现，生成评级报告
"""
from __future__ import annotations

import uuid
from datetime import datetime


class PostMarketEvaluator:
    """盘后评估器，分析股票当日表现并生成评级"""

    def __init__(self):
        self._last_report: dict | None = None

    def evaluate(self, symbol: str, daily_data: dict) -> dict:
        """
        评估单只股票
        daily_data: {open, high, low, close, volume, prev_close, avg_volume?}
        """
        open_price = daily_data["open"]
        high = daily_data["high"]
        low = daily_data["low"]
        close = daily_data["close"]
        volume = daily_data["volume"]
        prev_close = daily_data["prev_close"]
        avg_volume = daily_data.get("avg_volume", 1.0)

        # 涨跌幅
        pct_change = (close - prev_close) / prev_close * 100

        # 振幅
        amplitude = (high - low) / prev_close * 100

        # 量比
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # 评级
        if pct_change > 5:
            rating = "strong"
        elif pct_change > 2:
            rating = "positive"
        elif pct_change > -2:
            rating = "neutral"
        elif pct_change > -5:
            rating = "weak"
        else:
            rating = "bearish"

        return {
            "symbol": symbol,
            "pct_change": round(pct_change, 2),
            "amplitude": round(amplitude, 2),
            "volume_ratio": round(volume_ratio, 2),
            "rating": rating,
            "evaluated_at": datetime.now().isoformat()
        }

    def batch_evaluate(self, symbols_data: list[dict]) -> dict:
        """
        批量评估
        symbols_data: [{symbol, daily_data}, ...]
        """
        results = []
        for item in symbols_data:
            symbol = item["symbol"]
            daily_data = item["daily_data"]
            result = self.evaluate(symbol, daily_data)
            results.append(result)

        # 生成摘要
        rating_counts = {}
        for r in results:
            rating = r["rating"]
            rating_counts[rating] = rating_counts.get(rating, 0) + 1

        report = {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "evaluated_at": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total": len(results),
                "rating_counts": rating_counts
            }
        }

        self._last_report = report
        return report

    def get_report(self) -> dict:
        """返回最近一次批量评估结果"""
        return self._last_report or {
            "report_id": None,
            "evaluated_at": None,
            "results": [],
            "summary": {"total": 0, "rating_counts": {}}
        }
