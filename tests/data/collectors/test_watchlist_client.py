"""Tests for WatchlistClient, StockMinuteCollector.collect_from_watchlist,
and run_watchlist_minute_pipeline."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from services.data.src.collectors.watchlist_client import WatchlistClient


# ── WatchlistClient.fetch_watchlist ──────────────────────────────────────


class TestWatchlistClientFetch:
    """Tests for WatchlistClient.fetch_watchlist."""

    def test_returns_list_from_dict_response(self):
        """正常返回 {watchlist: [...]} 格式。"""
        body = {"watchlist": ["000001", "600519", "300750"]}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = body
        mock_resp.raise_for_status = MagicMock()

        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            ctx.get.return_value = mock_resp
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient(decision_service_url="http://test:8104")
            result = client.fetch_watchlist()

        assert result == ["000001", "600519", "300750"]

    def test_returns_plain_list_response(self):
        """正常返回纯列表格式。"""
        body = ["000002", "601318"]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = body
        mock_resp.raise_for_status = MagicMock()

        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            ctx.get.return_value = mock_resp
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient()
            result = client.fetch_watchlist()

        assert result == ["000002", "601318"]

    def test_returns_data_key(self):
        """支持 {data: [...]} 格式。"""
        body = {"data": ["000063"]}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = body
        mock_resp.raise_for_status = MagicMock()

        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            ctx.get.return_value = mock_resp
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient()
            result = client.fetch_watchlist()

        assert result == ["000063"]

    def test_timeout_returns_empty(self):
        """超时返回空列表。"""
        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            ctx.get.side_effect = httpx.TimeoutException("timeout")
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient(timeout=1.0)
            result = client.fetch_watchlist()

        assert result == []

    def test_connect_error_returns_empty(self):
        """连接失败返回空列表。"""
        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            ctx.get.side_effect = httpx.ConnectError("refused")
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient()
            result = client.fetch_watchlist()

        assert result == []

    def test_http_error_returns_empty(self):
        """HTTP 5xx 返回空列表。"""
        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=MagicMock()
            )
            ctx.get.return_value = mock_resp
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient()
            result = client.fetch_watchlist()

        assert result == []

    def test_unexpected_response_type_returns_empty(self):
        """非 list/dict 响应返回空列表。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = "not_a_list_or_dict"
        mock_resp.raise_for_status = MagicMock()

        with patch("services.data.src.collectors.watchlist_client.httpx.Client") as MockClient:
            ctx = MagicMock()
            ctx.get.return_value = mock_resp
            MockClient.return_value.__enter__ = MagicMock(return_value=ctx)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            client = WatchlistClient()
            result = client.fetch_watchlist()

        assert result == []


# ── StockMinuteCollector.collect_from_watchlist ──────────────────────────


class TestCollectFromWatchlist:
    """Tests for StockMinuteCollector.collect_from_watchlist integration."""

    def test_collect_from_watchlist_delegates(self):
        """collect_from_watchlist 从 client 获取列表后调用 collect。"""
        from services.data.src.collectors.stock_minute_collector import StockMinuteCollector

        mock_wl_client = MagicMock()
        mock_wl_client.fetch_watchlist.return_value = ["000001"]

        collector = StockMinuteCollector(watchlist_client=mock_wl_client)
        with patch.object(collector, "_fetch_batch", return_value=[{"symbol": "000001"}]) as mock_fetch:
            result = collector.collect_from_watchlist()

        mock_wl_client.fetch_watchlist.assert_called_once()
        assert len(result) == 1

    def test_collect_from_watchlist_no_client(self):
        """无 watchlist_client 时返回空列表。"""
        from services.data.src.collectors.stock_minute_collector import StockMinuteCollector

        collector = StockMinuteCollector()
        result = collector.collect_from_watchlist()
        assert result == []

    def test_collect_from_watchlist_empty_watchlist(self):
        """watchlist 为空时返回空列表。"""
        from services.data.src.collectors.stock_minute_collector import StockMinuteCollector

        mock_wl_client = MagicMock()
        mock_wl_client.fetch_watchlist.return_value = []

        collector = StockMinuteCollector(watchlist_client=mock_wl_client)
        result = collector.collect_from_watchlist()
        assert result == []

    def test_collect_fallback_to_watchlist_when_symbols_empty(self):
        """symbols 为空时 collect() 自动 fallback 到 watchlist_client。"""
        from services.data.src.collectors.stock_minute_collector import StockMinuteCollector

        mock_wl_client = MagicMock()
        mock_wl_client.fetch_watchlist.return_value = ["600519"]

        collector = StockMinuteCollector(watchlist_client=mock_wl_client)
        with patch.object(collector, "_fetch_batch", return_value=[{"symbol": "600519"}]):
            result = collector.collect()

        mock_wl_client.fetch_watchlist.assert_called_once()
        assert len(result) == 1


# ── run_watchlist_minute_pipeline ────────────────────────────────────────


class TestRunWatchlistMinutePipeline:
    """Tests for pipeline.run_watchlist_minute_pipeline."""

    @pytest.fixture(autouse=True)
    def _mock_polars(self):
        """Mock polars so pipeline.py can be imported without it installed."""
        import sys
        polars_mock = MagicMock()
        modules_to_mock = {
            "polars": polars_mock,
        }
        saved = {}
        for mod_name, mock_obj in modules_to_mock.items():
            saved[mod_name] = sys.modules.get(mod_name)
            sys.modules[mod_name] = mock_obj
        yield
        for mod_name, orig in saved.items():
            if orig is None:
                sys.modules.pop(mod_name, None)
            else:
                sys.modules[mod_name] = orig

    @patch("services.data.src.scheduler.pipeline.WatchlistClient")
    @patch("services.data.src.scheduler.pipeline._build_storage")
    @patch("services.data.src.scheduler.pipeline.get_config")
    def test_pipeline_happy_path(self, mock_config, mock_storage, mock_wl_cls):
        from services.data.src.scheduler.pipeline import run_watchlist_minute_pipeline

        mock_config.return_value = {}
        mock_stor = MagicMock()
        mock_stor.write_records.return_value = 5
        mock_storage.return_value = mock_stor

        mock_wl = MagicMock()
        mock_wl.fetch_watchlist.return_value = ["000001", "600519"]
        mock_wl_cls.return_value = mock_wl

        with patch(
            "services.data.src.collectors.stock_minute_collector.StockMinuteCollector"
        ) as MockCollector:
            mock_coll = MagicMock()
            mock_coll.collect.return_value = [
                {"symbol_or_indicator": "000001", "timestamp": "2026-04-12 10:01"},
                {"symbol_or_indicator": "600519", "timestamp": "2026-04-12 10:01"},
            ]
            MockCollector.return_value = mock_coll

            result = run_watchlist_minute_pipeline(decision_url="http://test:8104")

        assert "000001" in result
        assert "600519" in result

    @patch("services.data.src.scheduler.pipeline.WatchlistClient")
    @patch("services.data.src.scheduler.pipeline._build_storage")
    @patch("services.data.src.scheduler.pipeline.get_config")
    def test_pipeline_empty_watchlist(self, mock_config, mock_storage, mock_wl_cls):
        from services.data.src.scheduler.pipeline import run_watchlist_minute_pipeline

        mock_config.return_value = {}
        mock_storage.return_value = MagicMock()

        mock_wl = MagicMock()
        mock_wl.fetch_watchlist.return_value = []
        mock_wl_cls.return_value = mock_wl

        result = run_watchlist_minute_pipeline()
        assert result == {}
