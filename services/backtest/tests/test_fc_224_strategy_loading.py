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
from services.backtest.src.backtest.factor_registry import factor_registry
from services.backtest.src.backtest.runner import BacktestJobInput, OnlineBacktestRunner
from services.backtest.src.backtest.strategy_base import StrategyDefinition, strategy_registry

FC_224_TEMPLATE_ID = "FC-224_v3_intraday_trend_cf605_5m"

FC_224_YAML = dedent(
    """
    name: "FC-224_v3_intraday_trend_cf605_5m"
    description: "5-min momentum strategy: MACD crossover + RSI trend + volume confirmation"
    version: "3.0"
    category: "intraday_momentum"

    factors:
      - factor_name: "MACD"
        weight: 0.40
        params:
          fast: 6
          slow: 13
          signal: 5
      - factor_name: "RSI"
        weight: 0.35
        params:
          period: 14
      - factor_name: "VolumeRatio"
        weight: 0.25
        params:
          period: 10

    market_filter:
      enabled: true
      conditions:
        - "atr > 0.005 * close"
        - "adx > 20"

    signal:
      long_condition: "macd_hist > 0 and rsi_slope > 0 and volume_ratio > 1.2"
      short_condition: "macd_hist < 0 and rsi_slope < 0 and volume_ratio > 1.2"
      confirm_bars: 1

    timeframe_minutes: 5

    position_fraction: 0.07
    position_adjustment:
      method: "atr_scaling"
      base_position: 0.07
      atr_period: 14
      atr_multiplier: 1.0

    symbols:
      - "CZCE.CF605"

    transaction_costs:
      slippage_per_unit: 1
      commission_per_lot_round_turn: 8

    risk:
      daily_loss_limit_yuan: 2000
      per_symbol_fuse_yuan: 140
      max_drawdown_pct: 0.007
      force_close_day: "14:55"
      force_close_night: "22:55"
      no_overnight: true

    tags: ["v3", "intraday", "momentum", "5m", "filtered", "cotton"]
    """
).strip()


def test_fc_224_yaml_parses_and_template_is_registered(tmp_path):
    yaml_path = tmp_path / "fc_224.yaml"
    yaml_path.write_text(FC_224_YAML, encoding="utf-8")

    definition = StrategyDefinition.load(yaml_path, expected_template_id=FC_224_TEMPLATE_ID)

    assert definition.template_id == FC_224_TEMPLATE_ID
    assert definition.timeframe_minutes == 5
    assert definition.symbols == ["CZCE.CF605"]
    assert [item.factor_name for item in definition.factors] == ["MACD", "RSI", "VolumeRatio"]
    assert definition.market_filter["conditions"] == ["atr > 0.005 * close", "adx > 20"]
    assert definition.signal["confirm_bars"] == 1
    assert definition.transaction_costs["commission_per_lot_round_turn"] == 8
    assert definition.risk.as_snapshot()["max_drawdown_pct"] == 0.007
    assert strategy_registry.resolve(FC_224_TEMPLATE_ID).__name__ == "FC224Strategy"


def test_required_fc_224_factors_produce_outputs_on_minimal_sample():
    bars = _build_sample_bars(count=64)

    macd = factor_registry.calculate("MACD", bars, {"fast": 6, "slow": 13, "signal": 5}).latest()
    rsi = factor_registry.calculate("RSI", bars, {"period": 14}).latest()
    volume_ratio = factor_registry.calculate("VolumeRatio", bars, {"period": 10}).latest()
    atr = factor_registry.calculate("ATR", bars, {"period": 14}).latest()
    adx = factor_registry.calculate("ADX", bars, {"period": 14}).latest()

    assert macd["macd_hist"] is not None
    assert rsi["rsi_slope"] is not None
    assert volume_ratio["volume_ratio"] is not None
    assert atr["atr"] is not None
    assert adx["adx"] is not None


def test_fc_224_runner_keeps_yaml_risk_snapshot(tmp_path, monkeypatch):
    yaml_path = tmp_path / "fc_224.yaml"
    yaml_path.write_text(FC_224_YAML, encoding="utf-8")

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        runner = OnlineBacktestRunner(session_manager=DummySessionManager(_build_sample_bars(count=80)))
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="fc-224-check",
                strategy_template_id=FC_224_TEMPLATE_ID,
                strategy_yaml_filename=yaml_path.name,
                symbol="CZCE.CF605",
                start_date=date(2024, 4, 3),
                end_date=date(2026, 4, 3),
                initial_capital=1000000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.risk_summary.parameters["daily_loss_limit_yuan"] == 2000
    assert report.risk_summary.parameters["per_symbol_fuse_yuan"] == 140
    assert report.risk_summary.parameters["max_drawdown_pct"] == 0.007
    assert report.risk_summary.parameters["no_overnight"] is True
    assert any(note.startswith("signal_state=") for note in report.notes)


class DummyApi:
    def __init__(self, bars):
        self._bars = bars

    def get_kline_serial(self, symbol, duration_seconds, data_length=200):
        return list(self._bars[-data_length:])

    def get_account(self, account=None):
        return {"balance": 1000000.0}

    def get_position(self, symbol=None, account=None):
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
        return object()

    @contextmanager
    def open_session(self, config):
        yield DummySession(self._bars)


def _build_sample_bars(*, count: int):
    start = datetime(2024, 4, 3, 9, 0, tzinfo=timezone.utc)
    bars = []
    close = 15000.0

    for index in range(count):
        drift = index * 7.5
        oscillation = ((index % 6) - 2) * 3.0
        close = 15000.0 + drift + oscillation
        high = close + 22.0 + (index % 3)
        low = close - 18.0 - (index % 2)
        open_price = close - 4.0
        volume = 1200.0 + index * 35.0 + (300.0 if index % 5 == 0 else 0.0)
        bars.append(
            {
                "timestamp": start + timedelta(minutes=5 * index),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
    return bars