from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.manual_runner import ManualRunner
from services.backtest.src.backtest.stock_runner import StockRunner


def test_manual_runner_prefers_params_symbol_and_current_bars_api() -> None:
    runner = ManualRunner(data_service_url="http://localhost:8105")

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"bars": [{"close": 1.0}]}

    with patch("services.backtest.src.backtest.manual_runner.httpx.get", return_value=response) as mock_get:
        bars = runner._fetch_bars(
            "legacy-strategy-id",
            "2024-01-01",
            "2024-01-31",
            {"symbol": "KQ_m_SHFE_rb", "timeframe_minutes": 60},
        )

    assert bars == [{"close": 1.0}]
    params = mock_get.call_args.kwargs["params"]
    assert params == {
        "symbol": "KQ_m_SHFE_rb",
        "start": "2024-01-01",
        "end": "2024-01-31",
        "timeframe_minutes": 60,
    }


def test_manual_runner_falls_back_to_strategy_id_when_symbol_missing() -> None:
    runner = ManualRunner(data_service_url="http://localhost:8105")

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"bars": []}

    with patch("services.backtest.src.backtest.manual_runner.httpx.get", return_value=response) as mock_get:
        runner._fetch_bars(
            "RB2505",
            "2024-01-01",
            "2024-01-31",
            {},
        )

    params = mock_get.call_args.kwargs["params"]
    assert params["symbol"] == "RB2505"
    assert params["timeframe_minutes"] == 1


def test_stock_runner_uses_current_stock_bars_api() -> None:
    runner = StockRunner(data_service_url="http://localhost:8105")

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"bars": [{"close": 10.0}]}

    with patch("services.backtest.src.backtest.stock_runner.httpx.get", return_value=response) as mock_get:
        bars = runner._fetch_stock_bars("000001.SZ", "2024-01-01", "2024-01-31")

    assert bars == [{"close": 10.0}]
    params = mock_get.call_args.kwargs["params"]
    assert params == {
        "symbol": "000001.SZ",
        "start": "2024-01-01",
        "end": "2024-01-31",
        "timeframe_minutes": 1,
    }