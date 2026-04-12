"""
盘中跟踪器 (CB6)
实时跟踪股票价格和成交量，检测突破和放量信号
"""
from __future__ import annotations

from datetime import datetime


class IntradayTracker:
    """盘中跟踪器，监控股票实时数据并生成信号"""

    def __init__(self):
        self._snapshots: dict[str, dict] = {}  # symbol -> {price, volume, ts, first_price, high, volumes}
        self._updated_count = 0
        self._last_updated: str | None = None

    def update(self, symbol: str, price: float, volume: float, ts: str | None = None) -> None:
        """更新股票快照"""
        now = ts or datetime.now().isoformat()

        if symbol not in self._snapshots:
            # 首次记录
            self._snapshots[symbol] = {
                "price": price,
                "volume": volume,
                "ts": now,
                "first_price": price,
                "high": price,
                "volumes": [volume]
            }
        else:
            snapshot = self._snapshots[symbol]
            snapshot["price"] = price
            snapshot["volume"] = volume
            snapshot["ts"] = now
            snapshot["high"] = max(snapshot["high"], price)
            snapshot["volumes"].append(volume)

        self._updated_count += 1
        self._last_updated = now

    def get_signals(self) -> list[dict]:
        """返回触发信号的股票列表"""
        signals = []

        for symbol, snapshot in self._snapshots.items():
            price = snapshot["price"]
            volume = snapshot["volume"]
            high = snapshot["high"]
            volumes = snapshot["volumes"]

            # 突破信号：当前价接近当日最高价（98%以上）
            if price >= high * 0.98:
                signals.append({
                    "symbol": symbol,
                    "signal_type": "breakout",
                    "price": price,
                    "triggered_at": snapshot["ts"]
                })

            # 放量信号：当前成交量 > 历史平均成交量 * 1.5
            if len(volumes) > 1:
                # 使用历史平均（不包含当前值）
                avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
                if volume > avg_volume * 1.5:
                    signals.append({
                        "symbol": symbol,
                        "signal_type": "volume_spike",
                        "price": price,
                        "triggered_at": snapshot["ts"]
                    })

        return signals

    def get_summary(self) -> dict:
        """返回跟踪摘要"""
        return {
            "updated_count": self._updated_count,
            "signal_count": len(self.get_signals()),
            "last_updated": self._last_updated
        }

    def clear(self) -> None:
        """清空当日数据"""
        self._snapshots.clear()
        self._updated_count = 0
        self._last_updated = None
