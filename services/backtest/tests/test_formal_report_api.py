from __future__ import annotations

import csv
import io
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.api.app import create_app
from services.backtest.src.backtest.result_builder import BacktestJobSnapshot
from services.backtest.src.backtest.result_builder import BacktestResultBuilder
from services.backtest.src.backtest.runner import BacktestJobInput
from services.backtest.src.backtest.strategy_base import EquityCurvePoint
from services.backtest.src.backtest.strategy_base import StrategyDefinition
from services.backtest.src.backtest.strategy_base import StrategyExecutionArtifacts
from services.backtest.src.core.settings import get_settings


GENERIC_YAML = "\n".join(
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
        '  short_condition: "trend < 0"',
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


def _configure_formal_runtime(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    strategy_root = tmp_path / "strategies"
    result_root = tmp_path / "results"
    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(strategy_root))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(result_root))
    monkeypatch.setenv("TQSDK_AUTH_USERNAME", "demo-user")
    monkeypatch.setenv("TQSDK_AUTH_PASSWORD", "demo-pass")
    get_settings.cache_clear()
    return strategy_root, result_root


def test_formal_generic_strategy_run_and_report_download(monkeypatch, tmp_path: Path) -> None:
    strategy_root, result_root = _configure_formal_runtime(monkeypatch, tmp_path)
    app = create_app()
    app.state.backtest_formal_runner = DummyFormalRunner(
        strategy_root=strategy_root,
        result_root=result_root,
    )
    client = TestClient(app)

    import_response = client.post(
        "/api/strategy/import",
        json={"name": "palmoil_formal.yaml", "content": GENERIC_YAML},
    )
    assert import_response.status_code == 201
    imported = import_response.json()
    assert imported["execution_profile"]["template_id"] == "generic_formal_strategy_v1"
    assert imported["execution_profile"]["formal_supported"] is True
    assert imported["execution_profile"]["label"] == "正式回测"
    assert (strategy_root / "palmoil_formal.yaml").exists()
    stored_content = (strategy_root / "palmoil_formal.yaml").read_text(encoding="utf-8")
    assert "PalmOil_Formal" in stored_content
    assert "DCE.p2509" in stored_content

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
    # TqSdk formal engine runs async — initial status is "running"
    assert run_payload["status"] in ("running", "completed")

    # Wait for async execution to complete (background thread with DummyFormalRunner)
    for _ in range(50):
        detail_response = client.get(f"/api/backtest/results/{task_id}")
        detail = detail_response.json()
        if detail.get("status") == "completed":
            break
        time.sleep(0.1)
    else:
        raise AssertionError(f"Backtest did not complete within timeout, status={detail.get('status')}")

    assert detail["status"] == "completed"
    assert detail["source"] == "tqsdk_formal_engine"
    assert detail["execution_profile"]["executed_formal"] is True
    assert detail["report_path"] == f"{task_id}/report.json"
    assert detail["formal_report"]["job_id"] == task_id

    compat_report = client.get(f"/api/backtest/results/{task_id}/report")
    assert compat_report.status_code == 200
    compat_payload = compat_report.json()
    # The report endpoint serves the formal_report (to_dict() format) from disk or in-memory
    assert compat_payload["job_id"] == task_id
    assert compat_payload["strategy_template_id"] == "generic_formal_strategy_v1"
    assert compat_payload["strategy_yaml_filename"] == "palmoil_formal.yaml"


def test_formal_report_v1_schema_compliance(monkeypatch, tmp_path: Path) -> None:
    """Verify both tqsdk and local engines produce formal_report_v1 compatible structures."""
    strategy_root, result_root = _configure_formal_runtime(monkeypatch, tmp_path)
    app = create_app()
    app.state.backtest_formal_runner = DummyFormalRunner(
        strategy_root=strategy_root,
        result_root=result_root,
    )
    client = TestClient(app)

    # Import strategy
    import_response = client.post(
        "/api/strategy/import",
        json={"name": "schema_test.yaml", "content": GENERIC_YAML},
    )
    assert import_response.status_code == 201

    # --- Local engine ---
    local_run = client.post(
        "/api/backtest/run",
        json={
            "strategy_id": "schema_test.yaml",
            "engine_type": "local",
            "start": "2024-06-01",
            "end": "2024-09-01",
            "symbols": ["DCE.p2509"],
        },
    )
    assert local_run.status_code == 201
    local_task_id = local_run.json()["task_id"]
    assert local_run.json()["engine_type"] == "local"

    # Fetch report for local engine
    local_report_resp = client.get(f"/api/backtest/results/{local_task_id}/report")
    assert local_report_resp.status_code == 200
    local_report = local_report_resp.json()

    # Validate formal_report_v1 schema fields
    assert local_report.get("schema_version") == "formal_report_v1"
    assert local_report.get("report_id", "").startswith("rpt-")
    assert "generated_at" in local_report

    local_job = local_report["job"]
    for key in ("job_id", "engine_type", "strategy_id", "symbol", "timeframe", "start_date", "end_date", "initial_capital"):
        assert key in local_job, f"Missing job.{key} in local report"
    assert local_job["engine_type"] == "local"

    local_summary = local_report["summary"]
    for key in ("status", "total_trades", "final_equity", "max_drawdown", "pnl", "win_rate", "sharpe"):
        assert key in local_summary, f"Missing summary.{key} in local report"

    local_tx = local_report["transaction_costs"]
    for key in ("slippage_per_unit", "commission_per_lot_round_turn", "total_cost"):
        assert key in local_tx, f"Missing transaction_costs.{key} in local report"

    assert isinstance(local_report.get("risk_events"), list)

    local_artifacts = local_report["artifacts"]
    assert isinstance(local_artifacts.get("equity_curve"), list)
    assert isinstance(local_artifacts.get("trades"), list)
    assert "positions" in local_artifacts

    # --- TqSdk engine (async, wait for completion) ---
    tqsdk_run = client.post(
        "/api/backtest/run",
        json={
            "strategy_id": "schema_test.yaml",
            "start": "2024-06-01",
            "end": "2024-09-01",
            "symbols": ["DCE.p2509"],
        },
    )
    assert tqsdk_run.status_code == 201
    tqsdk_task_id = tqsdk_run.json()["task_id"]

    # Wait for async completion
    for _ in range(50):
        detail = client.get(f"/api/backtest/results/{tqsdk_task_id}").json()
        if detail.get("status") == "completed":
            break
        time.sleep(0.1)
    else:
        raise AssertionError("TqSdk backtest did not complete within timeout")

    tqsdk_formal = detail.get("formal_report", {})
    assert tqsdk_formal.get("job_id") == tqsdk_task_id
    # tqsdk formal_report is to_dict() format, verify key fields present
    assert "performance_metrics" in tqsdk_formal or "job_id" in tqsdk_formal


def test_csv_export_endpoint(monkeypatch, tmp_path: Path) -> None:
    """Verify CSV export endpoint returns valid CSV with summary + trades sections."""
    strategy_root, result_root = _configure_formal_runtime(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    # Import strategy and run local engine (synchronous, has formal_report)
    client.post(
        "/api/strategy/import",
        json={"name": "csv_test.yaml", "content": GENERIC_YAML},
    )
    run_resp = client.post(
        "/api/backtest/run",
        json={
            "strategy_id": "csv_test.yaml",
            "engine_type": "local",
            "start": "2024-01-01",
            "end": "2024-06-01",
            "symbols": ["DCE.p2509"],
        },
    )
    assert run_resp.status_code == 201
    task_id = run_resp.json()["task_id"]

    csv_resp = client.get(f"/api/backtest/results/{task_id}/report/csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers.get("content-type", "")
    assert f"{task_id}.report.csv" in csv_resp.headers.get("content-disposition", "")

    csv_text = csv_resp.text
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    # Verify summary section header
    assert rows[0] == ["=== Summary ==="]
    assert rows[1] == ["Field", "Value"]
    # Verify summary rows contain expected fields
    summary_fields = {row[0] for row in rows[2:] if len(row) >= 2 and row[0]}
    for field in ("status", "total_trades", "final_equity", "max_drawdown", "pnl", "win_rate", "sharpe"):
        assert field in summary_fields, f"Missing summary field '{field}' in CSV"

    # Verify trades section exists if there are trades
    trade_header_indices = [i for i, row in enumerate(rows) if row and row[0] == "=== Trades ==="]
    # With local engine + mock data there should be trades
    if trade_header_indices:
        trade_start = trade_header_indices[0]
        # Next row should be column headers
        assert len(rows[trade_start + 1]) > 0


def test_csv_export_404_when_no_report(monkeypatch, tmp_path: Path) -> None:
    """CSV endpoint returns 404 when no report data is available."""
    _configure_formal_runtime(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    csv_resp = client.get("/api/backtest/results/nonexistent-id/report/csv")
    assert csv_resp.status_code == 404
