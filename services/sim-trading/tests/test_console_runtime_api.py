from fastapi.testclient import TestClient

from src.api import router as router_mod
from src.gateway import simnow as simnow_mod
from src.main import app

client = TestClient(app)


class _GatewayStub:
    def __init__(self, account: dict):
        self._account = account

    @property
    def status(self):
        return {"td_connected": True}

    def _query_account(self):
        raise AssertionError("_query_account should not be called when snapshot is already present")


def test_account_endpoint_returns_local_virtual_and_ctp_snapshot():
    original_gateway = router_mod._gateway
    router_mod._gateway = _GatewayStub(
        {
            "balance": 512345.67,
            "available": 301234.56,
            "margin": 105000.0,
            "floating_pnl": 1234.5,
            "close_pnl": -345.25,
            "commission": 88.0,
            "pre_balance": 500000.0,
        }
    )
    try:
        response = client.get("/api/v1/account")
    finally:
        router_mod._gateway = original_gateway

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["local_virtual"] == {
        "label": "本地虚拟盘总本金",
        "principal": 500000.0,
        "currency": "CNY",
        "active_preset": "sim_50w",
    }

    snapshot = data["ctp_snapshot"]
    assert snapshot["connected"] is True
    assert snapshot["balance"] == 512345.67
    assert snapshot["available"] == 301234.56
    assert snapshot["margin"] == 105000.0
    assert snapshot["margin_rate"] == 20.49
    assert snapshot["floating_pnl"] == 1234.5
    assert snapshot["close_pnl"] == -345.25
    assert snapshot["commission"] == 88.0
    assert snapshot["initial_balance"] == 500000.0
    assert snapshot["net_pnl"] == 889.25
    assert snapshot["note"] == "CTP 账户快照"


def test_on_instrument_filters_non_futures_and_option_style_symbols():
    gateway = simnow_mod.SimNowGateway(
        broker_id="9999",
        user_id="demo",
        password="demo",
        md_front="tcp://md",
        td_front="tcp://td",
        instruments=["MA", "RB"],
    )

    gateway._on_instrument("MA605", "MA", simnow_mod._FUTURES_PRODUCT_CLASS, None, None)
    gateway._on_instrument("MA605P2650", "MA", simnow_mod._FUTURES_PRODUCT_CLASS, None, None)
    gateway._on_instrument("rb2605", "RB", "OPTION", 2026, 5)

    expected_expiry = simnow_mod._resolve_futures_expiry("MA605")
    assert gateway._product_to_contracts["MA"] == [("MA605", expected_expiry)]
    assert "RB" not in gateway._product_to_contracts