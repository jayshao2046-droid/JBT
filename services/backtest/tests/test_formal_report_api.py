from __future__ import annotations

import sys
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
    assert run_payload["status"] == "completed"
    assert run_payload["report_path"] == f"{task_id}/report.json"
    assert run_payload["execution_profile"]["executed_formal"] is True
    assert run_payload["execution_profile"]["executed_label"] == "正式回测"
    assert run_payload["totalReturn"] is not None

    detail_response = client.get(f"/api/backtest/results/{task_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status"] == "completed"
    assert detail["source"] == "tqsdk_formal_engine"
    assert detail["execution_profile"]["executed_formal"] is True
    assert detail["report_path"] == f"{task_id}/report.json"
    assert detail["formal_report"]["job_id"] == task_id

    compat_report = client.get(f"/api/backtest/results/{task_id}/report")
    assert compat_report.status_code == 200
    compat_payload = compat_report.json()
    assert compat_payload["job_id"] == task_id
    assert compat_payload["strategy_template_id"] == "generic_formal_strategy_v1"
    assert compat_payload["strategy_yaml_filename"] == "palmoil_formal.yaml"

