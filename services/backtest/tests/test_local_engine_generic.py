from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.api.app import create_app
from services.backtest.src.api.routes import backtest as backtest_module
from services.backtest.src.api.routes.support import get_compat_state
from services.backtest.src.backtest.local_engine import DataProvider
from services.backtest.src.backtest.local_engine import LoadedBars
from services.backtest.src.backtest.local_engine import LocalBacktestEngine
from services.backtest.src.backtest.local_engine import LocalBacktestParams
from services.backtest.src.backtest.local_engine import MockDataProvider
from services.backtest.src.core.settings import get_settings


GENERIC_LOCAL_YAML = dedent(
    """
    name: "generic_local.yaml"
    template_id: "generic_formal_strategy_v1"
    timeframe_minutes: 1
    symbols:
      - "DCE.p2605"
    factors:
      - factor_name: "EMA_Cross"
        weight: 1.0
        params:
          fast_period: 2
          slow_period: 4
      - factor_name: "ADX"
        weight: 1.0
        params:
          period: 3
      - factor_name: "ATR"
        weight: 1.0
        params:
          period: 3
    signal:
      long_condition: "ema_cross > 0"
      short_condition: "ema_cross < 0"
      confirm_bars: 1
    market_filter:
      enabled: true
      conditions:
        - "adx >= 0"
    position_size:
      method: "fixed_lots"
      lots: 1
    transaction_costs:
      slippage_per_unit: 0
      commission_per_lot_round_turn: 0
    risk:
      max_drawdown: 0.5
      daily_loss_limit: 0.5
      force_close_day: "14:55"
      force_close_night: "22:55"
      no_overnight: true
      stop_loss:
        type: "atr"
        atr_multiplier: 0.6
      take_profit:
        type: "atr"
        atr_multiplier: 0.6
    initial_capital: 100000
    contract_size: 1
    price_tick: 0
    """
).strip()


class TrendFlipProvider(DataProvider):
    def load_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 1,
    ):
        return self.load_bars_with_metadata(symbol, start_date, end_date, timeframe_minutes).bars

    def load_bars_with_metadata(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe_minutes: int = 1,
    ) -> LoadedBars:
        from services.backtest.src.backtest.local_engine import Bar

        bars = []
        timestamp = datetime(2024, 4, 3, 9, 0, tzinfo=timezone.utc)
        prices = []
        prices.extend(100.0 + index * 0.6 for index in range(55))
        prices.extend(133.0 - index * 1.0 for index in range(55))
        prices.extend(78.0 + index * 0.5 for index in range(20))

        for index, close_price in enumerate(prices):
            open_price = prices[index - 1] if index > 0 else close_price
            high_price = max(open_price, close_price) + 0.4
            low_price = min(open_price, close_price) - 0.4
            bars.append(
                Bar(
                    timestamp=timestamp,
                    open=round(open_price, 4),
                    high=round(high_price, 4),
                    low=round(low_price, 4),
                    close=round(close_price, 4),
                    volume=2000.0 + index,
                    open_interest=5000.0 + index,
                )
            )
            timestamp += timedelta(minutes=max(1, timeframe_minutes))

        return LoadedBars(
            requested_symbol=symbol,
            resolved_symbol="KQ_m_DCE_p",
            source_kind="continuous",
            bars=bars,
        )


def test_local_engine_without_yaml_keeps_mvp_path() -> None:
    engine = LocalBacktestEngine(data_provider=MockDataProvider())
    report = engine.run(
        LocalBacktestParams(
            job_id="mvp-local-001",
            symbols=["DCE.p2605"],
            start_date=date(2024, 4, 3),
            end_date=date(2024, 4, 5),
            initial_capital=100000.0,
            timeframe_minutes=60,
        )
    )

    assert report.summary["status"] == "completed"
    assert any(note == "local_engine=MVP" for note in report.notes)
    assert report.job["requested_symbol"] == "DCE.p2605"
    assert report.job["executed_data_symbol"] == "DCE.p2605"
    assert report.job["source_kind"] == "mock"


def test_local_engine_with_yaml_and_custom_provider_produces_generic_trades(tmp_path: Path, monkeypatch) -> None:
    strategy_root = tmp_path / "strategies"
    strategy_root.mkdir(parents=True, exist_ok=True)
    (strategy_root / "generic_local.yaml").write_text(GENERIC_LOCAL_YAML, encoding="utf-8")
    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(strategy_root))
    get_settings.cache_clear()

    engine = LocalBacktestEngine(data_provider=TrendFlipProvider())
    report = engine.run(
        LocalBacktestParams(
            job_id="generic-local-001",
            symbols=["DCE.p2605"],
            requested_symbol="DCE.p2605",
            strategy_yaml_filename="generic_local.yaml",
            strategy_id="generic_local.yaml",
            start_date=date(2024, 4, 3),
            end_date=date(2024, 4, 3),
            initial_capital=100000.0,
            timeframe_minutes=1,
        )
    )

    trades = list(report.artifacts["trades"])
    assert report.summary["status"] == "completed"
    assert any(note == "local_engine=generic_yaml" for note in report.notes)
    assert len(trades) >= 1
    assert any(trade["side"] in {"long", "short"} for trade in trades)
    assert report.job["requested_symbol"] == "DCE.p2605"
    assert report.job["executed_data_symbol"] == "KQ_m_DCE_p"
    assert report.job["source_kind"] == "continuous"


def test_local_backtest_route_preserves_requested_and_executed_symbols(tmp_path: Path, monkeypatch) -> None:
    strategy_root = tmp_path / "strategies"
    result_root = tmp_path / "results"
    strategy_root.mkdir(parents=True, exist_ok=True)
    result_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(strategy_root))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(result_root))
    monkeypatch.setenv("JBT_DATA_API_URL", "http://unit-test-data:8105")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)

    import_response = client.post(
        "/api/strategy/import",
        json={"name": "generic_local.yaml", "content": GENERIC_LOCAL_YAML},
    )
    assert import_response.status_code == 201

    original_api_provider = backtest_module.ApiDataProvider

    def _provider_factory(_: str) -> TrendFlipProvider:
        return TrendFlipProvider()

    backtest_module.ApiDataProvider = _provider_factory  # type: ignore[assignment]
    try:
        run_response = client.post(
            "/api/backtest/run",
            json={
                "strategy_id": "generic_local.yaml",
                "engine_type": "local",
                "start": "2024-04-03",
                "end": "2024-04-03",
                "symbols": ["DCE.p2605"],
            },
        )
    finally:
        backtest_module.ApiDataProvider = original_api_provider  # type: ignore[assignment]

    assert run_response.status_code == 201
    task_id = run_response.json()["task_id"]

    detail_response = client.get(f"/api/backtest/results/{task_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["payload"]["requested_symbol"] == "DCE.p2605"
    assert detail["payload"]["executed_data_symbol"] == "KQ_m_DCE_p"
    assert detail["payload"]["source_kind"] == "continuous"
    assert len(detail["trades"]) >= 1

    report_response = client.get(f"/api/backtest/results/{task_id}/report")
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["job"]["requested_symbol"] == "DCE.p2605"
    assert report_payload["job"]["executed_data_symbol"] == "KQ_m_DCE_p"
    assert report_payload["job"]["source_kind"] == "continuous"

    state = get_compat_state(type("Req", (), {"app": app})(), touch=False)
    assert task_id in state["results"]