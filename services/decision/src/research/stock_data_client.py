"""HTTP client for fetching stock bars from data service."""

from __future__ import annotations

from typing import Any

import httpx

from ..core.settings import get_settings


class StockDataError(RuntimeError):
    """股票数据获取失败。"""


class StockDataClient:
    """通过 data service 的 /api/v1/stocks/bars 端点获取股票 K 线数据。"""

    def __init__(self) -> None:
        self._settings = get_settings()

    def fetch_bars(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe_minutes: int = 1,
    ) -> list[dict[str, Any]]:
        """从 data service 获取股票 K 线数据。

        Args:
            symbol: 股票代码，如 000001.SZ、600519.SH。
            start_date: 开始日期，格式 YYYY-MM-DD。
            end_date: 结束日期，格式 YYYY-MM-DD。
            timeframe_minutes: K 线周期（分钟），默认 1。

        Returns:
            bars 列表，每条包含 open/high/low/close/volume 等字段。
        """
        base_url = self._settings.data_service_url.rstrip("/")
        url = f"{base_url}/api/v1/stocks/bars"
        params = {
            "symbol": symbol,
            "timeframe_minutes": timeframe_minutes,
            "start": start_date,
            "end": end_date,
        }

        try:
            response = httpx.get(
                url,
                params=params,
                timeout=self._settings.data_service_timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise StockDataError(
                f"Failed to fetch stock bars for {symbol}: {exc}"
            ) from exc

        bars = payload.get("bars") if isinstance(payload, dict) else None
        if not isinstance(bars, list):
            raise StockDataError(
                f"Data service returned invalid payload for stock {symbol}"
            )

        return bars
