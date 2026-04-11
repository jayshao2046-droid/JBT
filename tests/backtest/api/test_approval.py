"""tests/backtest/api/test_approval.py — TASK-0055 CG2

人工审核确认路由完整测试套件（≥ 10 用例）。
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 需要在 import app 之前 mock httpx，防止真实网络调用
with patch("httpx.get", return_value=MagicMock(status_code=200, json=lambda: [])):
    from services.backtest.src.api.app import create_app
    from services.backtest.src.api.routes.approval import _runner, get_runner


@pytest.fixture(autouse=True)
def _reset_runner():
    """每个测试前清空 runner 内部状态。"""
    _runner._results.clear()
    yield
    _runner._results.clear()


@pytest.fixture()
def client():
    app = create_app()
    return TestClient(app)


# ── 辅助 ──────────────────────────────────────────────────────────────

def _submit(client: TestClient, strategy_id: str = "test_ma_001", **overrides):
    payload = {
        "strategy_id": strategy_id,
        "start_date": "2025-01-01",
        "end_date": "2025-06-30",
        "params": {"short_window": 5, "long_window": 20},
    }
    payload.update(overrides)
    return client.post("/api/v1/approval/submit", json=payload)


FAKE_BARS = [{"close": 10.0 + i * 0.1} for i in range(60)]


# ── 测试用例 ──────────────────────────────────────────────────────────


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_submit_success(mock_post, mock_get, client):
    """1. 提交手动回测应返回 201 并包含 run_id。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: FAKE_BARS,
        raise_for_status=lambda: None,
    )
    resp = _submit(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["run_id"]
    assert data["strategy_id"] == "test_ma_001"
    assert data["status"] in ("completed", "failed")


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_submit_returns_metrics(mock_post, mock_get, client):
    """2. 成功回测应返回包含 sharpe/max_drawdown 等指标。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: FAKE_BARS,
        raise_for_status=lambda: None,
    )
    resp = _submit(client)
    data = resp.json()
    assert data["status"] == "completed"
    metrics = data["metrics"]
    for key in ("sharpe", "max_drawdown", "win_rate", "total_return", "trades_count"):
        assert key in metrics


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_submit_empty_bars_still_completes(mock_post, mock_get, client):
    """3. data 服务返回空 bars 时，回测仍应 completed（指标为零）。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: [],
        raise_for_status=lambda: None,
    )
    resp = _submit(client)
    data = resp.json()
    assert data["status"] == "completed"
    assert data["metrics"]["trades_count"] == 0


def test_submit_invalid_strategy_id(client):
    """4. strategy_id 为空时应返回 422。"""
    resp = client.post(
        "/api/v1/approval/submit",
        json={
            "strategy_id": "",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
        },
    )
    assert resp.status_code == 422


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_list_results_empty(mock_post, mock_get, client):
    """5. 初始状态列表应为空。"""
    resp = client.get("/api/v1/approval/results")
    assert resp.status_code == 200
    assert resp.json() == []


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_list_results_with_filter(mock_post, mock_get, client):
    """6. 按 strategy_id 过滤应只返回匹配项。"""
    mock_get.return_value = MagicMock(
        status_code=200, json=lambda: FAKE_BARS, raise_for_status=lambda: None,
    )
    _submit(client, strategy_id="alpha")
    _submit(client, strategy_id="beta")

    resp = client.get("/api/v1/approval/results", params={"strategy_id": "alpha"})
    data = resp.json()
    assert len(data) == 1
    assert data[0]["strategy_id"] == "alpha"


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_get_result_by_run_id(mock_post, mock_get, client):
    """7. 按 run_id 获取单个结果。"""
    mock_get.return_value = MagicMock(
        status_code=200, json=lambda: FAKE_BARS, raise_for_status=lambda: None,
    )
    run_id = _submit(client).json()["run_id"]

    resp = client.get(f"/api/v1/approval/results/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == run_id


def test_get_result_not_found(client):
    """8. 查询不存在的 run_id 应返回 404。"""
    resp = client.get("/api/v1/approval/results/nonexistent")
    assert resp.status_code == 404


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_approve_success(mock_post, mock_get, client):
    """9. 审核通过应更新 approved 和 reviewer_note。"""
    mock_get.return_value = MagicMock(
        status_code=200, json=lambda: FAKE_BARS, raise_for_status=lambda: None,
    )
    run_id = _submit(client).json()["run_id"]

    resp = client.post(
        f"/api/v1/approval/results/{run_id}/approve",
        json={"approved": True, "note": "指标达标"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["approved"] is True
    assert data["reviewer_note"] == "指标达标"


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_reject_success(mock_post, mock_get, client):
    """10. 审核拒绝应将 approved 设为 False。"""
    mock_get.return_value = MagicMock(
        status_code=200, json=lambda: FAKE_BARS, raise_for_status=lambda: None,
    )
    run_id = _submit(client).json()["run_id"]

    resp = client.post(
        f"/api/v1/approval/results/{run_id}/approve",
        json={"approved": False, "note": "回撤过大"},
    )
    assert resp.status_code == 200
    assert resp.json()["approved"] is False


def test_approve_not_found(client):
    """11. 审核不存在的 run_id 应返回 404。"""
    resp = client.post(
        "/api/v1/approval/results/bad_id/approve",
        json={"approved": True},
    )
    assert resp.status_code == 404


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_approve_running_task_rejected(mock_post, mock_get, client):
    """12. 对 running 状态的回测审核应返回 422。"""
    # 手动插入一条 running 状态的记录
    from services.backtest.src.backtest.manual_runner import ManualBacktestResult

    runner = get_runner()
    runner._results["fake_run"] = ManualBacktestResult(
        run_id="fake_run",
        strategy_id="x",
        status="running",
        start_time="2025-01-01T00:00:00+00:00",
    )

    resp = client.post(
        "/api/v1/approval/results/fake_run/approve",
        json={"approved": True},
    )
    assert resp.status_code == 422


@patch("services.backtest.src.backtest.manual_runner.httpx.get")
@patch("services.backtest.src.backtest.manual_runner.httpx.post")
def test_decision_notification_failure_does_not_break_approve(mock_post, mock_get, client):
    """13. decision 通知失败不应导致审核失败。"""
    mock_get.return_value = MagicMock(
        status_code=200, json=lambda: FAKE_BARS, raise_for_status=lambda: None,
    )
    mock_post.side_effect = Exception("connection refused")

    run_id = _submit(client).json()["run_id"]
    resp = client.post(
        f"/api/v1/approval/results/{run_id}/approve",
        json={"approved": True, "note": "ok"},
    )
    assert resp.status_code == 200
    assert resp.json()["approved"] is True
