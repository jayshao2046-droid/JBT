"""TASK-0059-S: 信号接收端点测试 — POST /api/v1/signals/receive"""
import sys
import os

# 确保 sim-trading src 在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "sim-trading"))

import pytest
from fastapi.testclient import TestClient

from src.api.router import router, _signal_queue, _received_signal_ids

# ── 构造独立 FastAPI app ──
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

ENDPOINT = "/api/v1/signals/receive"


def _valid_payload(**overrides):
    base = {
        "signal_id": "sig-test-001",
        "strategy_id": "strat-001",
        "symbol": "rb2510",
        "direction": "buy",
        "quantity": 2.0,
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def _clear_queue():
    """每个测试前清空信号队列和幂等集合。"""
    _signal_queue.clear()
    _received_signal_ids.clear()
    yield
    _signal_queue.clear()
    _received_signal_ids.clear()


# ── 1. 成功接收信号 ──
class TestSuccessReceive:
    def test_basic_receive(self):
        resp = client.post(ENDPOINT, json=_valid_payload())
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "received"
        assert body["signal_id"] == "sig-test-001"
        assert body["execution_id"] is not None
        assert body["execution_id"].startswith("exec-")
        assert body["message"] == "signal accepted"
        assert len(_signal_queue) == 1

    def test_receive_with_optional_fields(self):
        payload = _valid_payload(
            price=4500.0,
            order_type="limit",
            timestamp="2026-04-12T10:00:00Z",
            account_id="acc-001",
            risk_level="high",
            meta_data={"source": "backtest"},
        )
        resp = client.post(ENDPOINT, json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "received"


# ── 2. 缺少必填字段 ──
class TestMissingFields:
    def test_missing_signal_id(self):
        payload = _valid_payload()
        del payload["signal_id"]
        resp = client.post(ENDPOINT, json=payload)
        # Pydantic 422
        assert resp.status_code == 422

    def test_empty_signal_id(self):
        resp = client.post(ENDPOINT, json=_valid_payload(signal_id=""))
        body = resp.json()
        assert body["status"] == "rejected"
        assert "signal_id" in body["message"]

    def test_empty_strategy_id(self):
        resp = client.post(ENDPOINT, json=_valid_payload(strategy_id=""))
        body = resp.json()
        assert body["status"] == "rejected"
        assert "strategy_id" in body["message"]

    def test_empty_symbol(self):
        resp = client.post(ENDPOINT, json=_valid_payload(symbol=""))
        body = resp.json()
        assert body["status"] == "rejected"
        assert "symbol" in body["message"]


# ── 3. quantity <= 0 ──
class TestInvalidQuantity:
    def test_zero_quantity(self):
        resp = client.post(ENDPOINT, json=_valid_payload(quantity=0))
        body = resp.json()
        assert body["status"] == "rejected"
        assert "quantity" in body["message"]

    def test_negative_quantity(self):
        resp = client.post(ENDPOINT, json=_valid_payload(quantity=-5))
        body = resp.json()
        assert body["status"] == "rejected"
        assert "quantity" in body["message"]


# ── 4. 非法 direction ──
class TestInvalidDirection:
    def test_bad_direction(self):
        resp = client.post(ENDPOINT, json=_valid_payload(direction="up"))
        body = resp.json()
        assert body["status"] == "rejected"
        assert "direction" in body["message"]

    def test_all_valid_directions(self):
        for d in ("buy", "sell", "long", "short"):
            _signal_queue.clear()
            _received_signal_ids.clear()
            resp = client.post(ENDPOINT, json=_valid_payload(direction=d, signal_id=f"sig-{d}"))
            assert resp.json()["status"] == "received", f"direction={d} should be valid"


# ── 5. 重复 signal_id 幂等 ──
class TestIdempotent:
    def test_duplicate_signal_id(self):
        resp1 = client.post(ENDPOINT, json=_valid_payload(signal_id="sig-dup"))
        assert resp1.json()["status"] == "received"
        assert resp1.json()["execution_id"] is not None

        resp2 = client.post(ENDPOINT, json=_valid_payload(signal_id="sig-dup"))
        body2 = resp2.json()
        assert body2["status"] == "received"
        assert "duplicate" in body2["message"]
        assert body2["execution_id"] is None
        # 队列不应重复入队
        assert len(_signal_queue) == 1


# ── 6. 多条信号批量接收 ──
class TestBatchReceive:
    def test_sequential_signals(self):
        for i in range(5):
            resp = client.post(ENDPOINT, json=_valid_payload(signal_id=f"sig-batch-{i}"))
            assert resp.json()["status"] == "received"
        assert len(_signal_queue) == 5

    def test_mixed_valid_and_invalid(self):
        # valid
        r1 = client.post(ENDPOINT, json=_valid_payload(signal_id="sig-ok"))
        assert r1.json()["status"] == "received"
        # invalid quantity
        r2 = client.post(ENDPOINT, json=_valid_payload(signal_id="sig-bad", quantity=-1))
        assert r2.json()["status"] == "rejected"
        # queue only has the valid one
        assert len(_signal_queue) == 1
