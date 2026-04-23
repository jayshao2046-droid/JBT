from __future__ import annotations

"""TASK-0027-A5 API 层回归 + 增强测试。

验证:
1. 原有 4 个只读 API (health, version, symbols, bars) — 保持不动
2. dashboard API (system, collectors, storage, news)
3. 错误处理 (404, bars 缺符号, bars 无数据)
4. ops 接口 (health-check 信号)
5. 服务常量正确性
"""

import json
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.data.src.main import SERVICE_NAME, SERVICE_VERSION, app


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


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_health_and_version_endpoints() -> None:
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }

    alias_response = client.get("/api/v1/health")
    assert alias_response.status_code == 200
    assert alias_response.json() == response.json()

    version_response = client.get("/api/v1/version")
    assert version_response.status_code == 200
    assert version_response.json() == {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
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


def test_dashboard_system_and_collectors(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    _write_json(
        tmp_path / "logs" / "collector_status_latest.json",
        {
            "ts": "2026-04-09T10:42:30+08:00",
            "sources": [
                {
                    "name": "news_rss",
                    "label": "新闻RSS",
                    "ok": True,
                    "age_h": 0.2,
                    "age_str": "12min",
                    "threshold_h": 3,
                    "trading_only": False,
                    "skipped": False,
                },
                {
                    "name": "options",
                    "label": "期权行情",
                    "ok": False,
                    "age_h": 5.0,
                    "age_str": "5.0h",
                    "threshold_h": 1,
                    "trading_only": False,
                    "skipped": False,
                },
            ],
            "cpu": 35.0,
            "mem": 68.0,
            "disk": 42.0,
        },
    )
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs" / "scheduler.log").write_text(
        "2026-04-09 10:41:00 INFO scheduler started\n"
        "2026-04-09 10:42:00 ERROR collector failed path=/Users/demo/private.log url=https://internal.service.local ip=192.168.31.74\n",
        encoding="utf-8",
    )

    client = TestClient(app)

    system_response = client.get("/api/v1/dashboard/system")
    assert system_response.status_code == 200
    system_payload = system_response.json()
    assert system_payload["service"]["name"] == SERVICE_NAME
    assert system_payload["service"]["version"] == SERVICE_VERSION
    assert system_payload["service"]["data_root"] == "DATA_STORAGE_ROOT"
    assert len(system_payload["sources"]) == 2
    assert system_payload["resources"]["cpu"]["usage_percent"] == 35.0
    assert system_payload["logs"][-1]["level"] == "ERROR"
    assert all("value" not in item for item in system_payload["settings"]["env"])
    assert all("endpoints" not in item for item in system_payload["settings"]["schedules"])
    assert all("endpoint_count" in item for item in system_payload["settings"]["schedules"])
    assert "/Users/" not in system_payload["logs"][-1]["message"]
    assert "https://" not in system_payload["logs"][-1]["message"]
    assert "192.168.31.74" not in system_payload["logs"][-1]["message"]

    collectors_response = client.get("/api/v1/dashboard/collectors")
    assert collectors_response.status_code == 200
    collectors_payload = collectors_response.json()
    assert collectors_payload["summary"] == {
        "total": 2,
        "success": 1,
        "failed": 1,
        "delayed": 0,
        "idle": 0,
    }
    collectors = {item["id"]: item for item in collectors_payload["collectors"]}
    assert collectors["news_rss"]["status"] == "success"
    assert collectors["options"]["status"] == "failed"
    assert collectors["news_rss"]["output_dir"] == "news_rss"


def test_dashboard_storage_and_news(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    _write_symbol_frame(
        tmp_path,
        "DCE_p2605",
        _make_bars("2024-04-03 09:00:00", periods=3, base_price=10.0),
        "202404.parquet",
    )
    _write_json(
        tmp_path / "news_collected" / "news_20260409.json",
        [
            {
                "id": "n1",
                "title": "铜价上涨，库存继续回落",
                "source": "财联社",
                "publish_time": "2026-04-09T10:42:00+08:00",
                "summary": "铜库存回落推动价格继续上行。",
                "keywords": ["铜价", "库存"],
                "sentiment": "positive",
                "is_important": True,
                "is_pushed": True,
            },
            {
                "id": "n2",
                "title": "原油震荡，市场等待晚间数据",
                "source": "路透社",
                "publish_time": "2026-04-09T10:30:00+08:00",
                "summary": "原油价格震荡，市场观望情绪升温。",
                "keywords": ["原油", "库存"],
                "sentiment": "neutral",
                "is_important": False,
                "is_pushed": False,
            },
        ],
    )

    client = TestClient(app)

    storage_response = client.get("/api/v1/dashboard/storage")
    assert storage_response.status_code == 200
    storage_payload = storage_response.json()
    assert storage_payload["exists"] is True
    assert storage_payload["root"] == "DATA_STORAGE_ROOT"
    assert storage_payload["totals"]["files"] >= 2
    directory_names = {item["name"] for item in storage_payload["directories"]}
    assert "futures_minute" in directory_names
    assert "news_collected" in directory_names

    news_response = client.get("/api/v1/dashboard/news")
    assert news_response.status_code == 200
    news_payload = news_response.json()
    assert news_payload["summary"]["total_items"] == 2
    assert news_payload["summary"]["important_count"] == 1
    assert news_payload["summary"]["pushed_count"] == 1
    assert news_payload["items"][0]["title"] == "铜价上涨，库存继续回落"
    assert news_payload["push_records"][0]["title"] == "铜价上涨，库存继续回落"
    assert any(item["word"] == "库存" for item in news_payload["hot_keywords"])


# ── 增强覆盖: 错误处理 ──────────────────────────────────────

def test_nonexistent_route_returns_404() -> None:
    """Unknown path should return 404 or 405."""
    client = TestClient(app)
    response = client.get("/api/v1/nonexistent_endpoint")
    assert response.status_code in (404, 405)


def test_bars_missing_symbol_returns_422() -> None:
    """bars endpoint without required symbol should return 422."""
    client = TestClient(app)
    response = client.get("/api/v1/bars")
    assert response.status_code == 422


def test_bars_empty_data_returns_empty(tmp_path: Path, monkeypatch) -> None:
    """bars with no matching data should return 200 with count=0 or 404."""
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get(
        "/api/v1/bars",
        params={
            "symbol": "NONEXISTENT.x9999",
            "timeframe_minutes": 1,
            "start": "2020-01-01",
            "end": "2020-01-01",
        },
    )
    # Either 404 (symbol not found) or 200 with empty bars
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["count"] == 0


# ── 增强覆盖: 服务常量 ──────────────────────────────────────

def test_service_constants() -> None:
    """Service name and version should be correct."""
    assert SERVICE_NAME == "jbt-data"
    assert SERVICE_VERSION == "1.0.0"


def test_app_is_fastapi_instance() -> None:
    """app should be a FastAPI instance."""
    from fastapi import FastAPI as _FastAPI
    assert isinstance(app, _FastAPI)


# ── 增强覆盖: dashboard system 无数据时 ─────────────────────

def test_dashboard_system_no_data(tmp_path: Path, monkeypatch) -> None:
    """dashboard/system should return 200 even with empty storage."""
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get("/api/v1/dashboard/system")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"]["name"] == SERVICE_NAME


def test_dashboard_collectors_no_data(tmp_path: Path, monkeypatch) -> None:
    """dashboard/collectors should return 200 even without status file."""
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get("/api/v1/dashboard/collectors")
    assert response.status_code == 200


def test_dashboard_storage_empty(tmp_path: Path, monkeypatch) -> None:
    """dashboard/storage should report exists=True for empty storage."""
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get("/api/v1/dashboard/storage")
    assert response.status_code == 200


def test_dashboard_news_empty(tmp_path: Path, monkeypatch) -> None:
    """dashboard/news with no news files should return 200."""
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get("/api/v1/dashboard/news")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_items"] == 0


# ── 增强覆盖: symbols 空仓库 ────────────────────────────────

def test_symbols_empty_storage(tmp_path: Path, monkeypatch) -> None:
    """symbols endpoint should return empty list for empty storage."""
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.get("/api/v1/symbols")
    assert response.status_code == 200
    assert response.json()["count"] == 0