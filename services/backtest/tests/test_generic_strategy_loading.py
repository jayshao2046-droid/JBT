from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.core.settings import get_settings
from services.backtest.src.backtest.runner import BacktestJobInput, OnlineBacktestRunner
from services.backtest.src.backtest.strategy_base import StrategyDefinition, strategy_registry

GENERIC_TEMPLATE_ID = "generic-factor-bundle-v1"
FC_224_TEMPLATE_ID = "FC-224_v3_intraday_trend_cf605_5m"

GENERIC_STRATEGY_YAML = dedent(
    """
    template_id: "generic-factor-bundle-v1"
    name: "generic-factor-bundle-v1"
    description: "Generic factor snapshot strategy"
    version: "1.0"

    factors:
      - factor_name: "BollingerBands"
        params:
          period: 20
          stddev: 2
      - factor_name: "NewsSentiment"
      - factor_name: "InventoryFactor"
      - factor_name: "SpreadRatio"

    symbols:
      - "SHFE.rb2501"

    timeframe_minutes: 5

    transaction_costs:
      slippage_per_unit: 1
      commission_per_lot_round_turn: 2

    risk:
      daily_loss_limit_yuan: 1200
      max_drawdown_pct: 0.02
    """
).strip()


def test_unknown_template_id_resolves_to_generic_fallback(tmp_path):
    yaml_path = tmp_path / "generic_strategy.yaml"
    yaml_path.write_text(GENERIC_STRATEGY_YAML, encoding="utf-8")

    definition = StrategyDefinition.load(yaml_path, expected_template_id=GENERIC_TEMPLATE_ID)

    assert definition.template_id == GENERIC_TEMPLATE_ID
    assert [item.factor_name for item in definition.factors] == [
        "BollingerBands",
        "NewsSentiment",
        "InventoryFactor",
        "SpreadRatio",
    ]
    assert strategy_registry.resolve(GENERIC_TEMPLATE_ID).__name__ == "GenericFactorStrategy"
    assert strategy_registry.resolve(FC_224_TEMPLATE_ID).__name__ == "FC224Strategy"


def test_generic_runner_completes_minimal_factor_snapshot_path(tmp_path, monkeypatch):
    yaml_path = tmp_path / "generic_strategy.yaml"
    yaml_path.write_text(GENERIC_STRATEGY_YAML, encoding="utf-8")

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(tmp_path / "results"))
    get_settings.cache_clear()

    try:
        runner = OnlineBacktestRunner(session_manager=DummySessionManager(_build_sample_bars(count=96)))
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="generic-loading-check",
                strategy_template_id=GENERIC_TEMPLATE_ID,
                strategy_yaml_filename=yaml_path.name,
                symbol="SHFE.rb2501",
                start_date=date(2024, 4, 3),
                end_date=date(2024, 4, 12),
                initial_capital=500000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.strategy_template_id == GENERIC_TEMPLATE_ID
    assert report.total_trades == 0
    assert report.risk_summary.source == "yaml"
    assert "generic_template_fallback=true" in report.notes
    assert any(note.startswith("requested_template_id=") for note in report.notes)
    assert any(note.startswith("factor_snapshot.BollingerBands=") for note in report.notes)


class DummyApi:
    def __init__(self, bars):
        self._bars = bars

    def get_kline_serial(self, symbol, duration_seconds, data_length=200):
        _ = symbol
        _ = duration_seconds
        return list(self._bars[-data_length:])

    def get_account(self, account=None):
        _ = account
        return {"balance": 500000.0}

    def get_position(self, symbol=None, account=None):
        _ = symbol
        _ = account
        return {"volume": 0}

    def close(self):
        return None


class DummySession:
    def __init__(self, bars):
        self.api = DummyApi(bars)
        self.account = object()


class DummySessionManager:
    def __init__(self, bars):
        self._bars = bars

    def build_config_from_job(self, job):
        _ = job
        return object()

    @contextmanager
    def open_session(self, config):
        _ = config
        yield DummySession(self._bars)


def _build_sample_bars(*, count: int):
    start = datetime(2024, 4, 3, 9, 0, tzinfo=timezone.utc)
    bars = []

    for index in range(count):
        close = 3800.0 + index * 4.0 + ((index % 8) - 4) * 1.1
        open_price = close - 1.2 + ((index % 3) - 1) * 0.3
        high = max(open_price, close) + 3.0 + (index % 4) * 0.2
        low = min(open_price, close) - 2.8 - (index % 3) * 0.2
        bars.append(
            {
                "timestamp": start + timedelta(minutes=5 * index),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": 8000.0 + index * 120.0,
                "pair_close": close * 0.95 + ((index % 5) - 2) * 0.4,
                "inventory": 12000.0 - index * 15.0 + ((index % 7) - 3) * 11.0,
                "news_sentiment": ((index % 9) - 4) / 10.0,
            }
        )
    return bars