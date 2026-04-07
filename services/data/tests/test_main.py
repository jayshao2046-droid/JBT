from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.data.src.main import app


def _make_bars(
    start: str,
    *,
    periods: int,
    base_price: float,
    volume: float = 10.0,
    open_interest_start: float = 1000.0,
) -> pd.DataFrame:
    timestamps = pd.date_range(start=start, periods=periods, freq="1min")
    values = list(range(periods))
    return pd.DataFrame(
        {
            "datetime": timestamps,
            "open": [base_price + value for value in values],
            "high": [base_price + value + 0.5 for value in values],
            "low": [base_price + value - 0.5 for value in values],
            "close": [base_price + value + 0.25 for value in values],
            "volume": [volume for _ in values],
            "open_interest": [open_interest_start + value for value in values],
        }
    )


def _write_symbol_frame(root: Path, symbol: str, frame: pd.DataFrame, file_name: str) -> None:
    target_dir = root / "futures_minute" / "1m" / symbol
    target_dir.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(target_dir / file_name, index=False)


def test_health_and_version_endpoints() -> None:
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "data",
        "version": "0.1.0-minimal",
    }

    alias_response = client.get("/api/v1/health")
    assert alias_response.status_code == 200
    assert alias_response.json() == response.json()

    version_response = client.get("/api/v1/version")
    assert version_response.status_code == 200
    assert version_response.json() == {
        "service": "data",
        "version": "0.1.0-minimal",
    }


def test_bars_exact_hit_and_symbols_listing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    exact_frame = _make_bars("2024-04-03 09:00:00", periods=5, base_price=10.0)
    continuous_frame = _make_bars("2023-04-03 09:00:00", periods=5, base_price=100.0)
    _write_symbol_frame(tmp_path, "DCE_p2605", exact_frame, "202404.parquet")
    _write_symbol_frame(tmp_path, "KQ_m_DCE_p", continuous_frame, "202304.parquet")

    client = TestClient(app)

    symbols_response = client.get("/api/v1/symbols")
    assert symbols_response.status_code == 200
    assert symbols_response.json()["count"] == 2
    assert set(symbols_response.json()["symbols"]) == {"DCE_p2605", "KQ_m_DCE_p"}

    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "DCE.p2605",
            "timeframe_minutes": 1,
            "start": "2024-04-03",
            "end": "2024-04-03",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_symbol"] == "DCE.p2605"
    assert payload["resolved_symbol"] == "DCE_p2605"
    assert payload["source_kind"] == "exact"
    assert payload["timeframe_minutes"] == 1
    assert payload["count"] == 5
    assert payload["bars"][0]["datetime"].startswith("2024-04-03T09:00:00")
    assert payload["bars"][0]["open"] == 10.0
    assert payload["bars"][0]["open_interest"] == 1000.0


def test_bars_continuous_fallback_when_exact_does_not_cover_start(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    exact_frame = _make_bars("2024-04-03 09:00:00", periods=5, base_price=10.0)
    continuous_frame = _make_bars("2023-04-03 09:00:00", periods=5, base_price=100.0)
    _write_symbol_frame(tmp_path, "DCE_p2605", exact_frame, "202404.parquet")
    _write_symbol_frame(tmp_path, "KQ_m_DCE_p", continuous_frame, "202304.parquet")

    client = TestClient(app)
    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "DCE.p2605",
            "timeframe_minutes": 1,
            "start": "2023-04-03",
            "end": "2023-04-03",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_symbol"] == "DCE.p2605"
    assert payload["resolved_symbol"] == "KQ_m_DCE_p"
    assert payload["source_kind"] == "continuous"
    assert payload["count"] == 5
    assert payload["bars"][0]["open"] == 100.0


def test_bars_resample_to_60m(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    exact_frame = _make_bars("2024-04-03 09:00:00", periods=120, base_price=1.0)
    _write_symbol_frame(tmp_path, "DCE_p2605", exact_frame, "202404.parquet")

    client = TestClient(app)
    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "DCE_p2605",
            "timeframe_minutes": 60,
            "start": "2024-04-03 09:00:00",
            "end": "2024-04-03 10:59:00",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["resolved_symbol"] == "DCE_p2605"
    assert payload["source_kind"] == "exact"
    assert payload["count"] == 2

    first_bar = payload["bars"][0]
    second_bar = payload["bars"][1]

    assert first_bar["datetime"].startswith("2024-04-03T09:00:00")
    assert first_bar["open"] == 1.0
    assert first_bar["high"] == 60.5
    assert first_bar["low"] == 0.5
    assert first_bar["close"] == 60.25
    assert first_bar["volume"] == 600.0
    assert first_bar["open_interest"] == 1059.0

    assert second_bar["datetime"].startswith("2024-04-03T10:00:00")
    assert second_bar["open"] == 61.0
    assert second_bar["high"] == 120.5
    assert second_bar["low"] == 60.5
    assert second_bar["close"] == 120.25
    assert second_bar["volume"] == 600.0
    assert second_bar["open_interest"] == 1119.0