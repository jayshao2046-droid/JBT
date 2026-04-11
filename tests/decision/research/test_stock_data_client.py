"""tests for StockDataClient and FactorLoader stock symbol support."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from services.decision.src.research.factor_loader import FactorLoader, FactorLoadError
from services.decision.src.research.stock_data_client import StockDataClient, StockDataError


# ---------------------------------------------------------------------------
# StockDataClient 测试
# ---------------------------------------------------------------------------

def _make_settings(**overrides):
    """构造模拟 settings 对象。"""
    defaults = {
        "data_service_url": "http://localhost:8105",
        "data_service_timeout": 10,
    }
    defaults.update(overrides)
    s = MagicMock()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_bars(n: int = 5) -> list[dict]:
    """生成 n 条模拟股票 K 线。"""
    return [
        {
            "open": 10.0 + i,
            "high": 11.0 + i,
            "low": 9.5 + i,
            "close": 10.5 + i,
            "volume": 1000 + i * 100,
        }
        for i in range(n)
    ]


class TestStockDataClientFetchBars:
    """StockDataClient.fetch_bars 正常返回。"""

    @patch("services.decision.src.research.stock_data_client.get_settings")
    @patch("services.decision.src.research.stock_data_client.httpx.get")
    def test_fetch_bars_success(self, mock_get, mock_settings):
        mock_settings.return_value = _make_settings()
        bars = _make_bars(5)
        resp = MagicMock()
        resp.json.return_value = {"bars": bars}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        client = StockDataClient()
        result = client.fetch_bars("000001.SZ", "2026-01-01", "2026-01-31")

        assert result == bars
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "/api/v1/stocks/bars" in call_kwargs[1].get("url", "") or \
               "/api/v1/stocks/bars" in str(call_kwargs)

    @patch("services.decision.src.research.stock_data_client.get_settings")
    @patch("services.decision.src.research.stock_data_client.httpx.get")
    def test_fetch_bars_with_timeframe(self, mock_get, mock_settings):
        """验证自定义 timeframe_minutes 参数传递。"""
        mock_settings.return_value = _make_settings()
        resp = MagicMock()
        resp.json.return_value = {"bars": _make_bars(3)}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        client = StockDataClient()
        client.fetch_bars("600519.SH", "2026-01-01", "2026-01-31", timeframe_minutes=5)

        call_args = mock_get.call_args
        assert call_args[1]["params"]["timeframe_minutes"] == 5


class TestStockDataClientNetworkError:
    """StockDataClient 网络错误处理。"""

    @patch("services.decision.src.research.stock_data_client.get_settings")
    @patch("services.decision.src.research.stock_data_client.httpx.get")
    def test_http_error_raises_stock_data_error(self, mock_get, mock_settings):
        mock_settings.return_value = _make_settings()
        mock_get.side_effect = httpx.ConnectError("connection refused")

        client = StockDataClient()
        with pytest.raises(StockDataError, match="Failed to fetch stock bars"):
            client.fetch_bars("000001.SZ", "2026-01-01", "2026-01-31")

    @patch("services.decision.src.research.stock_data_client.get_settings")
    @patch("services.decision.src.research.stock_data_client.httpx.get")
    def test_timeout_raises_stock_data_error(self, mock_get, mock_settings):
        mock_settings.return_value = _make_settings()
        mock_get.side_effect = httpx.ReadTimeout("read timeout")

        client = StockDataClient()
        with pytest.raises(StockDataError, match="Failed to fetch stock bars"):
            client.fetch_bars("600519.SH", "2026-01-01", "2026-01-31")


class TestStockDataClientEmptyData:
    """StockDataClient 空数据处理。"""

    @patch("services.decision.src.research.stock_data_client.get_settings")
    @patch("services.decision.src.research.stock_data_client.httpx.get")
    def test_empty_bars_returns_empty_list(self, mock_get, mock_settings):
        mock_settings.return_value = _make_settings()
        resp = MagicMock()
        resp.json.return_value = {"bars": []}
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        client = StockDataClient()
        result = client.fetch_bars("000001.SZ", "2026-01-01", "2026-01-31")
        assert result == []

    @patch("services.decision.src.research.stock_data_client.get_settings")
    @patch("services.decision.src.research.stock_data_client.httpx.get")
    def test_invalid_payload_raises_error(self, mock_get, mock_settings):
        """服务返回非 dict 或缺少 bars 键。"""
        mock_settings.return_value = _make_settings()
        resp = MagicMock()
        resp.json.return_value = "not a dict"
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        client = StockDataClient()
        with pytest.raises(StockDataError, match="invalid payload"):
            client.fetch_bars("000001.SZ", "2026-01-01", "2026-01-31")


# ---------------------------------------------------------------------------
# FactorLoader 股票代码识别测试
# ---------------------------------------------------------------------------

class TestFactorLoaderStockSymbol:
    """FactorLoader 识别股票代码格式。"""

    @pytest.mark.parametrize(
        "symbol",
        [
            "000001.SZ",
            "600519.SH",
            "300750.SZ",
            "830799.BJ",
            "000001.sz",
            "600519.sh",
        ],
    )
    def test_stock_symbols_are_supported(self, symbol):
        assert FactorLoader._is_supported_symbol(symbol) is True

    @pytest.mark.parametrize(
        "symbol",
        [
            "000001.SZ",
            "600519.SH",
            "830799.BJ",
        ],
    )
    def test_is_stock_symbol(self, symbol):
        assert FactorLoader._is_stock_symbol(symbol) is True

    @pytest.mark.parametrize(
        "symbol",
        [
            "KQ_m_IC_CFFEX",
            "rb.SHFE2510",
            "INVALID",
            "00001.SZ",
            "0000011.SH",
        ],
    )
    def test_non_stock_symbols(self, symbol):
        assert FactorLoader._is_stock_symbol(symbol) is False

    def test_futures_symbols_still_supported(self):
        """确保股票支持不影响已有期货代码识别。"""
        assert FactorLoader._is_supported_symbol("KQ_m_IC_CFFEX") is True
        assert FactorLoader._is_supported_symbol("KQ.m@IC.CFFEX") is True
        assert FactorLoader._is_supported_symbol("rb.SHFE2510") is True
