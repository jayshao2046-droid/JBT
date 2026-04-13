# Market movers calculator (SIMWEB-01 P1-7)

from typing import List, Dict, Any, Optional


class MarketMoverCalculator:
    """市场异动监控计算器"""

    def calculate_price_change_rate(
        self, instruments: List[Dict[str, Any]], top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """计算涨速排行榜"""
        movers = []

        for inst in instruments:
            current_price = inst.get("last_price") or inst.get("price")
            prev_close = inst.get("prev_close") or inst.get("pre_settlement_price")

            if current_price and prev_close and prev_close > 0:
                change_rate = (current_price - prev_close) / prev_close * 100
                movers.append(
                    {
                        "symbol": inst.get("instrument_id") or inst.get("symbol"),
                        "name": inst.get("name", ""),
                        "current_price": current_price,
                        "prev_close": prev_close,
                        "change_rate": round(change_rate, 2),
                    }
                )

        # 按涨速排序
        movers.sort(key=lambda x: abs(x["change_rate"]), reverse=True)
        return movers[:top_n]

    def calculate_amplitude(
        self, instruments: List[Dict[str, Any]], top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """计算振幅排行榜"""
        movers = []

        for inst in instruments:
            high_price = inst.get("highest_price") or inst.get("high")
            low_price = inst.get("lowest_price") or inst.get("low")
            prev_close = inst.get("prev_close") or inst.get("pre_settlement_price")

            if high_price and low_price and prev_close and prev_close > 0:
                amplitude = (high_price - low_price) / prev_close * 100
                movers.append(
                    {
                        "symbol": inst.get("instrument_id") or inst.get("symbol"),
                        "name": inst.get("name", ""),
                        "high": high_price,
                        "low": low_price,
                        "amplitude": round(amplitude, 2),
                    }
                )

        # 按振幅排序
        movers.sort(key=lambda x: x["amplitude"], reverse=True)
        return movers[:top_n]

    def calculate_volume_surge(
        self, instruments: List[Dict[str, Any]], top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """计算成交量异动排行榜"""
        movers = []

        for inst in instruments:
            current_volume = inst.get("volume") or 0
            avg_volume = inst.get("avg_volume") or inst.get("prev_volume") or 1

            if current_volume > 0 and avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                movers.append(
                    {
                        "symbol": inst.get("instrument_id") or inst.get("symbol"),
                        "name": inst.get("name", ""),
                        "current_volume": current_volume,
                        "avg_volume": avg_volume,
                        "volume_ratio": round(volume_ratio, 2),
                    }
                )

        # 按成交量比率排序
        movers.sort(key=lambda x: x["volume_ratio"], reverse=True)
        return movers[:top_n]

    def get_market_movers(
        self, instruments: List[Dict[str, Any]], top_n: int = 10
    ) -> Dict[str, Any]:
        """获取完整的市场异动数据"""
        return {
            "price_movers": self.calculate_price_change_rate(instruments, top_n),
            "amplitude_movers": self.calculate_amplitude(instruments, top_n),
            "volume_movers": self.calculate_volume_surge(instruments, top_n),
        }
