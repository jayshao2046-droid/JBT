"""TASK-0018 批次 C — local 引擎与路由层测试

测试场景：
  (a) 最小参数发起本地回测，产出符合 formal_report_v1 的报告对象。
  (b) EngineRouter 正确分发 tqsdk / local（validate_engine_type + route_local）。
  (c) 不支持的 engine_type 值通过 POST /api/v1/jobs 返回 HTTP 422。
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.api.app import create_app
from services.backtest.src.api.routes import jobs as _jobs_module
from services.backtest.src.backtest.engine_router import (
    EngineRouter,
    EngineTypeError,
    resolve_engine_type,
)
from services.backtest.src.backtest.local_engine import (
    LocalBacktestEngine,
    LocalBacktestParams,
    LocalBacktestReport,
    MockDataProvider,
)


# ─────────────────────────────────────────────────────────────────────────────
# 场景 (a)：最小参数发起本地回测，产出报告对象
# ─────────────────────────────────────────────────────────────────────────────

def test_local_engine_minimal_params_produces_report() -> None:
    """engine_type=local：最小四字段（symbols/start_date/end_date/initial_capital）可产出报告。"""
    params = LocalBacktestParams(
        job_id="test-job-001",
        symbols=["MOCK.TEST001"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        initial_capital=1_000_000.0,
    )
    engine = LocalBacktestEngine()
    report = engine.run(params)

    assert isinstance(report, LocalBacktestReport)
    assert report.schema_version == "formal_report_v1"
    assert report.report_id.startswith("rpt-")
    assert report.job["engine_type"] == "local"
    assert report.job["symbol"] == "MOCK.TEST001"
    assert report.summary["status"] == "completed"
    assert isinstance(report.summary["total_trades"], int)
    assert isinstance(report.summary["final_equity"], float)
    assert isinstance(report.summary["max_drawdown"], float)
    assert 0.0 <= report.summary["win_rate"] <= 1.0
    assert isinstance(report.transaction_costs["total_cost"], float)
    assert isinstance(report.risk_events, list)
    assert "formal_report_v1" in report.to_dict()["schema_version"]


def test_local_engine_report_equity_is_numeric() -> None:
    """final_equity 必须为正数（initial_capital 扣除成本后权益）。"""
    params = LocalBacktestParams(
        job_id="test-job-002",
        symbols=["MOCK.CF605"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 30),
        initial_capital=500_000.0,
        timeframe_minutes=60,
        slippage_per_unit=1.0,
        commission_per_lot_round_turn=8.0,
    )
    engine = LocalBacktestEngine(data_provider=MockDataProvider())
    report = engine.run(params)

    assert report.summary["final_equity"] > 0
    assert report.summary["max_drawdown"] >= 0.0
    assert report.transaction_costs["slippage_per_unit"] == 1.0
    assert report.transaction_costs["commission_per_lot_round_turn"] == 8.0


def test_local_engine_from_dict() -> None:
    """LocalBacktestParams.from_dict 可接受 dict 形式的最小参数。"""
    params = LocalBacktestParams.from_dict({
        "symbols": ["MOCK.RB2505"],
        "start_date": "2024-04-01",
        "end_date": "2024-12-31",
        "initial_capital": 200_000.0,
    })
    assert params.symbols == ["MOCK.RB2505"]
    assert params.start_date == date(2024, 4, 1)
    assert params.end_date == date(2024, 12, 31)
    assert params.initial_capital == 200_000.0

    engine = LocalBacktestEngine()
    report = engine.run(params)
    assert report.summary["status"] == "completed"


def test_local_engine_end_before_start_raises() -> None:
    """end_date < start_date 应抛出 ValueError。"""
    import pytest

    params = LocalBacktestParams(
        job_id="test-bad-dates",
        symbols=["MOCK.CF605"],
        start_date=date(2025, 6, 1),
        end_date=date(2025, 1, 1),
        initial_capital=1_000_000.0,
    )
    with pytest.raises(ValueError, match="end_date must be >= start_date"):
        LocalBacktestEngine().run(params)


# ─────────────────────────────────────────────────────────────────────────────
# 场景 (b)：EngineRouter 正确分发 tqsdk / local
# ─────────────────────────────────────────────────────────────────────────────

def test_resolve_engine_type_default_is_tqsdk() -> None:
    """未提供 engine_type（None）时默认返回 tqsdk，保持既有路径兼容。"""
    assert resolve_engine_type(None) == "tqsdk"


def test_resolve_engine_type_tqsdk() -> None:
    assert resolve_engine_type("tqsdk") == "tqsdk"


def test_resolve_engine_type_local() -> None:
    assert resolve_engine_type("local") == "local"


def test_resolve_engine_type_case_insensitive() -> None:
    """engine_type 大小写容错。"""
    assert resolve_engine_type("LOCAL") == "local"
    assert resolve_engine_type("TqSdk") == "tqsdk"


def test_resolve_engine_type_unsupported_raises() -> None:
    """不支持的值应抛出 EngineTypeError。"""
    import pytest

    with pytest.raises(EngineTypeError):
        resolve_engine_type("invalid_engine")


def test_engine_router_validate_tqsdk() -> None:
    router = EngineRouter()
    assert router.validate_engine_type("tqsdk") == "tqsdk"
    assert router.validate_engine_type(None) == "tqsdk"


def test_engine_router_validate_local() -> None:
    router = EngineRouter()
    assert router.validate_engine_type("local") == "local"


def test_engine_router_validate_unsupported_raises() -> None:
    import pytest

    router = EngineRouter()
    with pytest.raises(EngineTypeError):
        router.validate_engine_type("binance_spot")


def test_engine_router_route_local_produces_report() -> None:
    """EngineRouter.route_local 正确分发到 LocalBacktestEngine 并返回报告。"""
    router = EngineRouter()
    params = LocalBacktestParams(
        job_id="router-test-001",
        symbols=["MOCK.P2509"],
        start_date=date(2024, 6, 1),
        end_date=date(2024, 9, 30),
        initial_capital=300_000.0,
        timeframe_minutes=240,
    )
    report = router.route_local(params)

    assert isinstance(report, LocalBacktestReport)
    assert report.job["engine_type"] == "local"
    assert report.schema_version == "formal_report_v1"


# ─────────────────────────────────────────────────────────────────────────────
# 场景 (c)：不支持的 engine_type 通过 API 返回 422
# ─────────────────────────────────────────────────────────────────────────────

def _make_client() -> TestClient:
    # 每次新建客户端前清空共享 job store，保证测试间状态隔离
    _jobs_module._JOB_STORE.clear()
    return TestClient(create_app())


_VALID_TQSDK_PAYLOAD = {
    "strategy_template_id": "generic_formal_strategy_v1",
    "strategy_yaml_filename": "fc_test.yaml",
    "symbol": "CZCE.CF605",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 1_000_000.0,
}


def test_api_create_job_invalid_engine_type_returns_422() -> None:
    """POST /api/v1/jobs 传入不支持的 engine_type 应返回 422。"""
    client = _make_client()
    payload = {**_VALID_TQSDK_PAYLOAD, "engine_type": "unknown_engine"}
    resp = client.post("/api/v1/jobs", json=payload)
    assert resp.status_code == 422


def test_api_create_job_unsupported_fx_engine_returns_422() -> None:
    """engine_type='fx_spot' 也应返回 422。"""
    client = _make_client()
    payload = {**_VALID_TQSDK_PAYLOAD, "engine_type": "fx_spot"}
    resp = client.post("/api/v1/jobs", json=payload)
    assert resp.status_code == 422
    detail = resp.json().get("detail", "")
    assert "engine_type" in detail.lower() or "unsupported" in detail.lower()


def test_api_create_job_no_engine_type_defaults_tqsdk() -> None:
    """未传 engine_type 时应成功创建并返回 engine_type=tqsdk。"""
    client = _make_client()
    resp = client.post("/api/v1/jobs", json=_VALID_TQSDK_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["engine_type"] == "tqsdk"
    assert body["execution_stage"] == "batch_a_skeleton"


def test_api_create_job_explicit_tqsdk_engine() -> None:
    """显式传 engine_type='tqsdk' 应等同于默认行为。"""
    client = _make_client()
    payload = {**_VALID_TQSDK_PAYLOAD, "engine_type": "tqsdk"}
    resp = client.post("/api/v1/jobs", json=payload)
    assert resp.status_code == 201
    assert resp.json()["engine_type"] == "tqsdk"


def test_api_create_job_local_engine_sets_correct_stage() -> None:
    """engine_type='local' 应成功创建并返回 execution_stage=batch_c_local_engine。"""
    client = _make_client()
    payload = {**_VALID_TQSDK_PAYLOAD, "engine_type": "local"}
    resp = client.post("/api/v1/jobs", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["engine_type"] == "local"
    assert body["execution_stage"] == "batch_c_local_engine"
