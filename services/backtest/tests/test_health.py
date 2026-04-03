from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.api.app import create_app
from services.backtest.src.api.routes.health import healthcheck
from services.backtest.src.main import app


def test_app_exposes_health_route() -> None:
    route_paths = {route.path for route in app.router.routes}
    assert "/api/v1/health" in route_paths


def test_healthcheck_returns_backtest_metadata() -> None:
    response = healthcheck()
    assert response.status == "ok"
    assert response.service == "backtest"
    assert response.asset_type == "futures"
    assert response.risk_config_source == "yaml"


def test_create_app_returns_fastapi_instance() -> None:
    instance = create_app()
    assert instance.title == "JBT Backtest Service"
    assert any(route.path == "/api/v1/health" for route in instance.router.routes)