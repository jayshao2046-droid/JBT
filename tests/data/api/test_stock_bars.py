"""Tests for GET /api/v1/stocks/bars — stock minute bars API."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from services.data.src.main import app

client = TestClient(app, raise_server_exceptions=False)

FAKE_STORAGE = Path("/tmp/jbt-test-stock-bars")


def _make_stock_parquet(stock_code: str, rows: list[dict]) -> None:
    """Write a test parquet file under the fake stock_minute directory."""
    target_dir = FAKE_STORAGE / "stock_minute" / stock_code
    target_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_parquet(target_dir / "data.parquet", index=False)


@pytest.fixture(autouse=True)
def _patch_storage(tmp_path: Path):
    """Redirect DATA_STORAGE_ROOT to a temp directory for every test."""
    stock_dir = tmp_path / "stock_minute" / "000001"
    stock_dir.mkdir(parents=True)
    df = pd.DataFrame(
        [
            {
                "datetime": "2026-04-01 09:31:00",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000,
                "open_interest": 0,
            },
            {
                "datetime": "2026-04-01 09:32:00",
                "open": 10.2,
                "high": 10.6,
                "low": 10.1,
                "close": 10.4,
                "volume": 1200,
                "open_interest": 0,
            },
            {
                "datetime": "2026-04-01 09:33:00",
                "open": 10.4,
                "high": 10.8,
                "low": 10.3,
                "close": 10.7,
                "volume": 800,
                "open_interest": 0,
            },
            {
                "datetime": "2026-04-01 09:34:00",
                "open": 10.7,
                "high": 11.0,
                "low": 10.5,
                "close": 10.9,
                "volume": 900,
                "open_interest": 0,
            },
        ]
    )
    df.to_parquet(stock_dir / "data.parquet", index=False)
    with patch.dict("os.environ", {"DATA_STORAGE_ROOT": str(tmp_path)}):
        yield


# ── Happy path ─────────────────────────────────────────────────

class TestHappyPath:
    def test_basic_query_pure_digits(self):
        """Pure 6-digit symbol returns bars correctly."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "000001",
                "start": "2026-04-01",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["resolved_symbol"] == "000001"
        assert body["source_kind"] == "stock_minute"
        assert body["timeframe_minutes"] == 1
        assert body["count"] == 4
        assert len(body["bars"]) == 4

    def test_symbol_with_sz_prefix(self):
        """SZ000001 resolves to 000001."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "SZ000001",
                "start": "2026-04-01",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["resolved_symbol"] == "000001"
        assert resp.json()["count"] == 4

    def test_symbol_with_dot_suffix(self):
        """000001.SZ resolves to 000001."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "000001.SZ",
                "start": "2026-04-01",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["resolved_symbol"] == "000001"

    def test_resample_to_2min(self):
        """timeframe_minutes=2 resamples bars correctly."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "000001",
                "start": "2026-04-01",
                "end": "2026-04-01",
                "timeframe_minutes": 2,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["timeframe_minutes"] == 2
        assert body["count"] < 4  # fewer bars after resampling
        assert body["count"] > 0


# ── Error handling ─────────────────────────────────────────────

class TestErrorHandling:
    def test_missing_symbol(self):
        """Missing symbol parameter → 422."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={"start": "2026-04-01", "end": "2026-04-01"},
        )
        assert resp.status_code == 422

    def test_missing_start(self):
        """Missing start parameter → 422."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={"symbol": "000001", "end": "2026-04-01"},
        )
        assert resp.status_code == 422

    def test_missing_end(self):
        """Missing end parameter → 422."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={"symbol": "000001", "start": "2026-04-01"},
        )
        assert resp.status_code == 422

    def test_end_before_start(self):
        """end < start → 422."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "000001",
                "start": "2026-04-02",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 422
        assert "end must be greater" in resp.json()["detail"]

    def test_invalid_time_format(self):
        """Garbage time string → 422."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "000001",
                "start": "not-a-date",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 422

    def test_unsupported_symbol_format(self):
        """Invalid symbol like 'AAPL' → 422."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "AAPL",
                "start": "2026-04-01",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 422
        assert "unsupported stock symbol" in resp.json()["detail"]

    def test_nonexistent_stock(self):
        """Valid format but no data directory → 404."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "999999",
                "start": "2026-04-01",
                "end": "2026-04-01",
            },
        )
        assert resp.status_code == 404
        assert "no stock minute data" in resp.json()["detail"]

    def test_empty_result_range(self):
        """Valid stock but date range outside data → 200 with count 0."""
        resp = client.get(
            "/api/v1/stocks/bars",
            params={
                "symbol": "000001",
                "start": "2020-01-01",
                "end": "2020-01-01",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
