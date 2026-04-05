from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.api.app import create_app
from services.backtest.src.backtest import generic_strategy as _generic_strategy
from services.backtest.src.backtest.result_builder import BacktestJobSnapshot
from services.backtest.src.backtest.result_builder import BacktestResultBuilder
from services.backtest.src.backtest.runner import BacktestJobInput
from services.backtest.src.backtest.strategy_base import EquityCurvePoint
from services.backtest.src.backtest.strategy_base import StrategyDefinition
from services.backtest.src.backtest.strategy_base import StrategyExecutionArtifacts
from services.backtest.src.core.settings import get_settings


def _configure_runtime_dirs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path / "strategies"))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(tmp_path / "results"))
    get_settings.cache_clear()


def _make_client(monkeypatch=None, tmp_path: Path | None = None) -> TestClient:
    if monkeypatch is not None and tmp_path is not None:
        _configure_runtime_dirs(monkeypatch, tmp_path)
    return TestClient(create_app())


FORMAL_GENERIC_YAML = "\n".join(
    [
        'name: "PalmOil_Formal"',
        'symbol: "DCE.p2509"',
        'timeframe: "60m"',
        'initial_capital: 800000',
        'contract_size: 10',
        'price_tick: 2',
        'commission: 8',
        'slippage: 1',
        'factors:',
        '  - factor_name: "trend"',
        '    formula: "(ma_fast > ma_slow) ? 1 : 0"',
        'factor_weights:',
        '  trend: 1.0',
        'indicators:',
        '  - name: "ma_fast"',
        '    type: "SMA"',
        '    params: [5]',
        '  - name: "ma_slow"',
        '    type: "SMA"',
        '    params: [20]',
        'signal_rule:',
        '  long_condition: "trend > 0"',
        '  short_condition: false',
        '  confirm_bars: 1',
        'position_size:',
        '  method: "fixed_ratio"',
        '  ratio: 0.3',
        'risk_control:',
        '  max_drawdown: 0.12',
        '  daily_loss_limit: 0.02',
        '  no_overnight: true',
    ]
)


class DummyFormalRunner:
    def __init__(self, *, strategy_root: Path, result_root: Path) -> None:
        self._strategy_root = strategy_root
        self._builder = BacktestResultBuilder(result_root=result_root)

    def run_job_sync(self, job_input: BacktestJobInput) -> Any:
        if not isinstance(job_input, BacktestJobInput):
            job_input = BacktestJobInput.from_mapping(job_input)

        strategy_path = self._strategy_root / job_input.strategy_yaml_filename
        definition = StrategyDefinition.load(
            strategy_path,
            expected_template_id=job_input.strategy_template_id,
        )
        completed_at = datetime.now().astimezone()
        artifacts = StrategyExecutionArtifacts(
            equity_curve=[
                EquityCurvePoint(
                    timestamp=completed_at - timedelta(days=2),
                    equity=job_input.initial_capital,
                    drawdown=0.0,
                    position=0,
                    pnl=0.0,
                    cum_pnl=0.0,
                ),
                EquityCurvePoint(
                    timestamp=completed_at - timedelta(days=1),
                    equity=job_input.initial_capital + 2500.0,
                    drawdown=0.0,
                    position=1,
                    pnl=2500.0,
                    cum_pnl=2500.0,
                ),
                EquityCurvePoint(
                    timestamp=completed_at,
                    equity=job_input.initial_capital + 2000.0,
                    drawdown=0.000624,
                    position=0,
                    pnl=-500.0,
                    cum_pnl=2000.0,
                ),
            ],
            trade_pnls=[2500.0, -500.0],
            notes=["dummy_formal_runner=true"],
            completed_at=completed_at,
        )
        report = self._builder.build(
            BacktestJobSnapshot(
                job_id=job_input.job_id,
                strategy_template_id=job_input.strategy_template_id,
                strategy_yaml_filename=job_input.strategy_yaml_filename,
                symbol=job_input.symbol,
                start_date=job_input.start_date,
                end_date=job_input.end_date,
                initial_capital=job_input.initial_capital,
            ),
            definition,
            artifacts,
        )
        self._builder.write_report(report)
        return report


def _make_formal_client(monkeypatch, tmp_path: Path) -> TestClient:
    _configure_runtime_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("TQSDK_AUTH_USERNAME", "demo-user")
    monkeypatch.setenv("TQSDK_AUTH_PASSWORD", "demo-pass")
    get_settings.cache_clear()
    app = create_app()
    app.state.backtest_formal_runner = DummyFormalRunner(
        strategy_root=tmp_path / "strategies",
        result_root=tmp_path / "results",
    )
    return TestClient(app)


def _import_formal_strategy(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/strategy/import",
        json={"name": "palmoil_formal.yaml", "content": FORMAL_GENERIC_YAML},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["execution_profile"]["template_id"] == "generic_formal_strategy_v1"
    assert payload["execution_profile"]["formal_supported"] is True
    return payload


def _install_fake_tqsdk(monkeypatch) -> None:
    class FakeQuote:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeTqAuth:
        def __init__(self, username: str, password: str) -> None:
            self.username = username
            self.password = password

    class FakeTqApi:
        def __init__(self, *args, **kwargs) -> None:
            self._quotes = {
                "KQ.m@SHFE.rb": FakeQuote(underlying_symbol="SHFE.rb2601"),
                "KQ.m@DCE.i": FakeQuote(underlying_symbol="DCE.i2601"),
                "KQ.m@DCE.m": FakeQuote(underlying_symbol="DCE.m2601"),
                "KQ.m@CZCE.CF": FakeQuote(underlying_symbol="CZCE.CF601"),
                "KQ.m@CZCE.MA": FakeQuote(underlying_symbol="CZCE.MA601"),
                "SHFE.rb2601": FakeQuote(last_price=3572.0, pre_close=3550.0, open_interest=120000.0, volume=58000.0),
                "DCE.i2601": FakeQuote(last_price=786.0, pre_close=781.0, open_interest=98000.0, volume=42000.0),
                "DCE.m2601": FakeQuote(last_price=3098.0, pre_close=3084.0, open_interest=87000.0, volume=31000.0),
                "CZCE.CF601": FakeQuote(last_price=13980.0, pre_close=13920.0, open_interest=45000.0, volume=18000.0),
                "CZCE.MA601": FakeQuote(last_price=2490.0, pre_close=2480.0, open_interest=36000.0, volume=16000.0),
            }

        def query_quotes(self, *, ins_class: str, expired: bool = False):
            if ins_class == "CONT":
                return [
                    "KQ.m@SHFE.rb",
                    "KQ.m@DCE.i",
                    "KQ.m@DCE.m",
                    "KQ.m@CZCE.CF",
                    "KQ.m@CZCE.MA",
                ]
            if ins_class == "FUTURE":
                return [
                    "SHFE.rb2601",
                    "DCE.i2601",
                    "DCE.m2601",
                    "CZCE.CF601",
                    "CZCE.MA601",
                ]
            return []

        def get_quote(self, symbol: str):
            return self._quotes[symbol]

        def wait_update(self, deadline=None):
            return True

        def close(self):
            return None

    monkeypatch.setitem(sys.modules, "tqsdk", SimpleNamespace(TqApi=FakeTqApi, TqAuth=FakeTqAuth))


def test_app_keeps_v1_health_and_jobs_skeleton_routes() -> None:
    app = create_app()
    route_paths = {route.path for route in app.router.routes}

    assert "/api/health" in route_paths
    assert "/api/v1/health" in route_paths
    assert "/api/v1/jobs" in route_paths
    assert "/api/v1/jobs/{job_id}" in route_paths

    client = TestClient(app)

    compat_health_response = client.get("/api/health")
    assert compat_health_response.status_code == 200

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload["status"] == "ok"
    assert health_payload["risk_config_source"] == "yaml"


def test_app_registers_task_0007_batch_b_routes() -> None:
    app = create_app()
    route_paths = {route.path for route in app.router.routes}

    expected_paths = {
        "/api/backtest/summary",
        "/api/backtest/results",
        "/api/backtest/run",
        "/api/backtest/results/{task_id}",
        "/api/backtest/adjust",
        "/api/backtest/history/{strategy_id}",
        "/api/backtest/results/{task_id}/equity",
        "/api/backtest/results/{task_id}/trades",
        "/api/backtest/results/{task_id}/report",
        "/api/backtest/progress/{task_id}",
        "/api/backtest/cancel/{task_id}",
        "/api/backtest/equity-curve",
        "/api/backtest/results/batch",
        "/api/strategies",
        "/api/strategy/import",
        "/api/strategy/{name}",
        "/api/strategy/export/{name}",
        "/api/system/status",
        "/api/system/logs",
        "/api/market/quotes",
        "/api/market/main-contracts",
    }

    assert expected_paths.issubset(route_paths)


def test_import_and_export_strategy_roundtrip(monkeypatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path)
    yaml_text = "\n".join(
        [
            'name: "demo_strategy.yaml"',
            'template_id: "demo-template"',
            'symbols:',
            '  - "SHFE.rb2505"',
            'signal:',
            '  confirm_bars: 1',
        ]
    )

    response = client.post(
        "/api/strategy/import",
        json={"name": "demo_strategy.yaml", "content": yaml_text},
    )
    assert response.status_code == 201
    imported = response.json()
    assert imported["name"] == "demo_strategy.yaml"
    assert imported["status"] == "local"
    assert imported["created_at"] > 0
    assert imported["execution_profile"]["template_id"] == "demo-template"
    assert imported["execution_profile"]["formal_supported"] is False
    assert imported["execution_profile"]["label"] == "兼容预览"

    strategies = client.get("/api/strategies")
    assert strategies.status_code == 200
    assert any(item["name"] == "demo_strategy.yaml" for item in strategies.json())

    exported = client.get("/api/strategy/export/demo_strategy.yaml")
    assert exported.status_code == 200
    assert exported.text == yaml_text


def test_import_nested_strategy_yaml_keeps_symbol_metadata(monkeypatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path)
    yaml_text = "\n".join(
        [
            'strategy:',
            '  name: "油脂多因子策略"',
            '  description: "nested metadata"',
            '  version: "1.2"',
            'parameters:',
            '  symbol: "p2505"',
            '  timeframe: 15',
            '  initial_capital: 800000',
            'indicators:',
            '  - name: "SMA"',
            '    alias: "ma_fast"',
            '    params:',
            '      timeperiod: 5',
        ]
    )

    response = client.post(
        "/api/strategy/import",
        json={"name": "nested_strategy.yaml", "content": yaml_text},
    )
    assert response.status_code == 201
    imported = response.json()
    assert imported["symbols"] == ["p2505"]
    assert imported["strategy"]["description"] == "nested metadata"
    assert imported["strategy"]["version"] == "1.2"
    assert imported["params"]["timeframe_minutes"] == 15
    assert "execution_profile" in imported
    assert imported["execution_profile"]["formal_supported"] is False


def test_run_results_detail_and_progress_minimal_chain(monkeypatch, tmp_path: Path) -> None:
    client = _make_formal_client(monkeypatch, tmp_path)
    _import_formal_strategy(client)

    run_response = client.post(
        "/api/backtest/run",
        json={
            "strategy_id": "palmoil_formal.yaml",
            "start": "2024-01-03",
            "end": "2024-03-29",
            "symbols": ["DCE.p2509"],
        },
    )
    assert run_response.status_code == 201
    run_payload = run_response.json()
    task_id = run_payload["task_id"]
    assert run_payload["status"] == "completed"
    assert run_payload["report_path"] == f"{task_id}/report.json"
    assert run_payload["totalReturn"] is not None

    results_response = client.get("/api/backtest/results")
    assert results_response.status_code == 200
    results = results_response.json()
    assert len(results) == 1
    result = results[0]
    assert result["id"] == task_id
    assert result["payload"]["strategy"]["id"] == "palmoil_formal.yaml"
    assert result["status"] == "completed"
    assert result["totalTrades"] >= 1
    assert result["total_trades"] >= 1
    assert result["submitted_at"] > 0
    assert result["report_path"] == f"{task_id}/report.json"
    assert result["execution_profile"]["executed_label"] == "正式回测"
    assert result["execution_profile"]["executed_formal"] is True
    assert result["execution_profile"]["can_execute_formal"] is True

    detail_response = client.get(f"/api/backtest/results/{task_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == task_id
    assert isinstance(detail["trades"], list)
    assert isinstance(detail["equity_curve"], list)
    assert detail["payload"]["contract"] == "DCE.p2509"
    assert detail["source"] == "tqsdk_formal_engine"
    assert detail["execution_profile"]["executed_label"] == "正式回测"
    assert "正式引擎生成" in detail["execution_profile"]["executed_reason"]
    assert detail["formal_report"]["job_id"] == task_id

    trades_response = client.get(f"/api/backtest/results/{task_id}/trades")
    assert trades_response.status_code == 200
    trades = trades_response.json()
    assert isinstance(trades, list)
    if trades:
        assert {"symbol", "date", "direction", "offset", "price", "volume", "profit", "commission"}.issubset(trades[0].keys())

    equity_response = client.get(f"/api/backtest/results/{task_id}/equity")
    assert equity_response.status_code == 200
    equity = equity_response.json()
    assert len(equity) >= 2
    assert any(key in equity[0] for key in ("equity", "nav", "value"))

    progress_response = client.get(f"/api/backtest/progress/{task_id}")
    assert progress_response.status_code == 200
    progress = progress_response.json()
    assert progress["task_id"] == task_id
    assert progress["status"] == "completed"
    assert progress["progress"] == 100
    assert progress["current_date"] is not None


def test_system_market_and_summary_endpoints_return_expected_shapes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setitem(sys.modules, "tqsdk", SimpleNamespace())
    client = _make_formal_client(monkeypatch, tmp_path)
    _import_formal_strategy(client)
    run_response = client.post(
        "/api/backtest/run",
        json={"strategy_id": "palmoil_formal.yaml", "start": "2024-01-02", "end": "2024-02-28", "symbols": ["DCE.p2509"]},
    )
    assert run_response.status_code == 201

    summary_response = client.get("/api/backtest/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert {"running_count", "standby_count", "archived_count", "logs", "market_time"}.issubset(summary.keys())
    assert isinstance(summary["logs"], list)
    assert summary["archived_count"] >= 1

    system_status = client.get("/api/system/status")
    assert system_status.status_code == 200
    system_payload = system_status.json()
    assert {"cpu", "memory", "disk", "latency", "cpuHistory", "memoryHistory", "services", "formal_engine"}.issubset(system_payload.keys())
    assert isinstance(system_payload["cpuHistory"], list)
    assert isinstance(system_payload["memoryHistory"], list)
    assert system_payload["services"][0]["uptime"]
    assert {"ready", "auth_configured", "backtest_mode", "registered_templates", "reason"}.issubset(system_payload["formal_engine"].keys())

    system_logs = client.get("/api/system/logs")
    assert system_logs.status_code == 200
    assert "compatibility layer" in system_logs.text

    quotes = client.get("/api/market/quotes")
    assert quotes.status_code == 200
    quotes_payload = quotes.json()
    assert isinstance(quotes_payload, list)
    assert {"symbol", "price", "change"}.issubset(quotes_payload[0].keys())

    contracts = client.get("/api/market/main-contracts")
    assert contracts.status_code == 200
    contracts_payload = contracts.json()
    assert isinstance(contracts_payload["contracts"], list)
    assert contracts_payload["contracts"]
    assert contracts_payload["source"] == "service_local_compatibility"
    assert isinstance(contracts_payload["categories"], list)
    assert len(contracts_payload["categories"]) >= 10
    assert contracts_payload["note"].startswith("兼容层本地主力合约清单")


def test_market_endpoints_prefer_tqsdk_when_available(monkeypatch, tmp_path: Path) -> None:
    _configure_runtime_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("TQSDK_AUTH_USERNAME", "demo-user")
    monkeypatch.setenv("TQSDK_AUTH_PASSWORD", "demo-pass")
    get_settings.cache_clear()
    _install_fake_tqsdk(monkeypatch)
    client = TestClient(create_app())

    contracts_response = client.get("/api/market/main-contracts")
    assert contracts_response.status_code == 200
    contracts_payload = contracts_response.json()
    assert contracts_payload["source"] == "tqsdk_realtime_main_contracts"
    assert {"SHFE.rb2601", "DCE.i2601", "DCE.m2601", "CZCE.CF601", "CZCE.MA601"}.issubset(
        set(contracts_payload["contracts"])
    )
    assert contracts_payload["note"].startswith("TqSdk 实时主力合约清单")

    quotes_response = client.get("/api/market/quotes")
    assert quotes_response.status_code == 200
    quotes_payload = quotes_response.json()
    assert len(quotes_payload) == 5
    assert quotes_payload[0]["symbol"] == "SHFE.rb2601"
    assert quotes_payload[0]["source"] == "tqsdk_realtime_quotes"
    assert quotes_payload[0]["price"] == 3572.0
    assert quotes_payload[0]["change"] > 0


def test_market_main_contracts_fallback_when_tqsdk_unavailable(monkeypatch, tmp_path: Path) -> None:
    _configure_runtime_dirs(monkeypatch, tmp_path)
    monkeypatch.setitem(sys.modules, "tqsdk", SimpleNamespace())
    client = TestClient(create_app())

    contracts_response = client.get("/api/market/main-contracts")
    assert contracts_response.status_code == 200
    contracts_payload = contracts_response.json()
    assert contracts_payload["source"] == "service_local_compatibility"
    assert contracts_payload["contracts"]
    assert contracts_payload["note"].startswith("兼容层本地主力合约清单")

    quotes_response = client.get("/api/market/quotes")
    assert quotes_response.status_code == 200
    quotes_payload = quotes_response.json()
    assert quotes_payload[0]["source"] == "service_local"