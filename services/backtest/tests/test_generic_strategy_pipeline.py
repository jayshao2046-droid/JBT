from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.factor_registry import factor_registry
from services.backtest.src.backtest import generic_strategy as generic_strategy_module
from services.backtest.src.backtest.generic_strategy import _infer_legacy_indicator_specs
from services.backtest.src.backtest.runner import BacktestJobInput, OnlineBacktestRunner
from services.backtest.src.backtest.strategy_base import (
    GENERIC_FORMAL_TEMPLATE_ID,
    StrategyDefinition,
    strategy_registry,
)
from services.backtest.src.core.settings import get_settings


GENERIC_YAML = dedent(
    """
    version: "2.1"
    name: "PalmOil_5Factor_Trend_v3"
    description: "5-layer factor resonance strategy for palm oil futures (p2509)"

    symbol: p2509
    timeframe: "60m"
    initial_capital: 500000
    contract_size: 10
    price_tick: 2
    commission: 3
    slippage: 2

    factors:
      - name: trend_direction
        description: "MA20 > MA60"
        formula: "(ma20 > ma60) ? 1 : 0"
        type: "binary"

      - name: trend_strength
        description: "ADX >= 30"
        formula: "(adx >= 30) ? 1 : 0"
        type: "binary"

      - name: pullback_health
        description: "Close near MA5 within 0.2*ATR"
        formula: "(close > ma5) and ((close - ma5) / atr < 0.2) ? 1 : 0"
        type: "binary"

      - name: momentum
        description: "RSI in 50-70"
        formula: "(rsi > 50) and (rsi < 70) ? 1 : 0"
        type: "binary"

      - name: volume_confirmation
        description: "Volume > SMA(Vol,20)*1.2"
        formula: "(volume > vol_sma * 1.2) ? 1 : 0"
        type: "binary"

      - name: low_volatility
        description: "ATR/Price < 1.5%"
        formula: "(atr / close < 0.015) ? 1 : 0"
        type: "binary"

    factor_weights:
      trend_direction: 0.25
      trend_strength: 0.2
      pullback_health: 0.2
      momentum: 0.15
      volume_confirmation: 0.15
      low_volatility: 0.05

    signal_rule:
      long_condition: "sum(factor_scores) >= 4.0"
      short_condition: false

    indicators:
      - name: ma20
        type: "SMA"
        params: [close, 20]
      - name: ma60
        type: "SMA"
        params: [close, 60]
      - name: adx
        type: "ADX"
        params: [high, low, close, 14]
      - name: rsi
        type: "RSI"
        params: [close, 14]
      - name: atr
        type: "ATR"
        params: [high, low, close, 14]
      - name: ma5
        type: "SMA"
        params: [close, 5]
      - name: vol_sma
        type: "SMA"
        params: [volume, 20]

    position_size:
      method: "fixed_ratio"
      ratio: 0.6

    risk_control:
      stop_loss_atr: 1.2
      take_profit_atr: 2
      trailing_stop:
        activate_at: 1.5
        distance: 0.8
      max_drawdown: 0.12
      daily_loss_limit: 0.02%
    """
).strip()


LEGACY_FACTOR_YAML = dedent(
    """
    name: "FC-178_v3_intraday_oscillating_p2605_5m"
    description: "5分钟极简震荡策略：RSI超买超卖 + BB触底反弹"
    version: "3.0"
    category: "intraday_oscillation"

    factors:
      - factor_name: "RSI"
        weight: 0.5
        params:
          period: 14
      - factor_name: "BollingerBands"
        weight: 0.5
        params:
          period: 20
          std_dev: 2

    market_filter:
      enabled: true
      conditions:
        - "atr > 0.003 * close"
        - "adx < 20"

    signal:
      long_condition: "rsi < 30 and bb_position == 'lower_band'"
      short_condition: "rsi > 70 and bb_position == 'upper_band'"
      confirm_bars: 1

    timeframe_minutes: 5

    position_fraction: 0.06
    position_adjustment:
      method: "atr_scaling"
      base_position: 0.06
      atr_period: 14
      atr_multiplier: 1

    symbols:
      - "DCE.p2605"

    transaction_costs:
      slippage_per_unit: 1
      commission_per_lot_round_turn: 3

    risk:
      daily_loss_limit_yuan: 2000
      per_symbol_fuse_yuan: 120
      max_drawdown_pct: 0.006
      force_close_day: "14:55"
      force_close_night: "22:55"
      no_overnight: true
    """
).strip()


EXTENDED_LEGACY_FACTOR_YAML = dedent(
    """
    name: "PalmOil_Extended_Factors"
    version: "3.1"
    factors:
      - factor_name: "WMA"
        weight: 1.0
        params:
          source: close
          period: 20
          _alias: ma20
      - factor_name: "ROC"
        weight: 1.0
        params:
          source: close
          period: 5
      - factor_name: "CMF"
        weight: 1.0
        params:
          period: 20
    signal:
      long_condition: "ma20 > 0 and roc > -100 and cmf > -1"
      short_condition: false
    timeframe_minutes: 15
    position_fraction: 0.1
    symbols:
      - "DCE.p2605"
    transaction_costs:
      slippage_per_unit: 1
      commission_per_lot_round_turn: 3
    risk:
      force_close_day: "14:55"
      force_close_night: "22:55"
      no_overnight: false
    """
).strip()


def test_generic_yaml_preserves_original_formulas_and_signal(tmp_path):
    yaml_path = tmp_path / "generic_strategy.yaml"
    yaml_path.write_text(GENERIC_YAML, encoding="utf-8")

    definition = StrategyDefinition.load(yaml_path)

    assert definition.template_id == GENERIC_FORMAL_TEMPLATE_ID
    assert definition.symbols == ["p2509"]
    assert definition.timeframe_minutes == 60
    assert definition.capital_params["initial_capital"] == 500000
    assert definition.capital_params["commission"] == 3
    assert definition.capital_params["slippage"] == 2
    assert definition.signal["long_condition"] == "sum(factor_scores) >= 4.0"
    assert definition.signal["short_condition"] is False
    assert definition.factors[0].formula == "(ma20 > ma60) ? 1 : 0"
    assert definition.factors[2].formula == "(close > ma5) and ((close - ma5) / atr < 0.2) ? 1 : 0"
    assert definition.risk.as_snapshot()["daily_loss_limit"] == "0.02%"
    assert [item.name for item in definition.indicators] == ["ma20", "ma60", "adx", "rsi", "atr", "ma5", "vol_sma"]
    assert strategy_registry.resolve(GENERIC_FORMAL_TEMPLATE_ID).__name__ == "GenericStrategy"


def test_generic_required_indicators_produce_outputs_on_minimal_sample():
    bars = _build_sample_bars(count=120)

    sma = factor_registry.calculate("SMA", bars, {"source": "close", "period": 20}).latest()
    rsi = factor_registry.calculate("RSI", bars, {"source": "close", "period": 14}).latest()
    atr = factor_registry.calculate("ATR", bars, {"high": "high", "low": "low", "close": "close", "period": 14}).latest()
    adx = factor_registry.calculate("ADX", bars, {"high": "high", "low": "low", "close": "close", "period": 14}).latest()

    assert sma["sma"] is not None
    assert rsi["rsi"] is not None
    assert atr["atr"] is not None
    assert adx["adx"] is not None

    bollinger = factor_registry.calculate("BollingerBands", bars, {"period": 20, "std_dev": 2}).latest()
    donchian = factor_registry.calculate("DonchianBreakout", bars, {"entry_period": 20, "exit_period": 10}).latest()

    assert bollinger["bb_position"] is not None
    assert donchian["donchian_high"] is not None
    assert donchian["donchian_low"] is not None


def test_extended_factor_registry_registers_new_futures_indicators():
    bars = _build_sample_bars(count=180)

    expected_names = {
        "wma",
        "hma",
        "tema",
        "stochastic",
        "stochasticrsi",
        "roc",
        "mom",
        "cmo",
        "keltnerchannel",
        "ntr",
        "aroon",
        "trix",
        "linreg",
        "chaikinad",
        "cmf",
        "pvt",
        "stdev",
        "zscore",
        "bullbearpower",
        "dpo",
    }
    assert expected_names.issubset(set(factor_registry.list_factors()))

    wma = factor_registry.calculate("WMA", bars, {"source": "close", "period": 20}).latest()
    hma = factor_registry.calculate("HMA", bars, {"source": "close", "period": 20}).latest()
    stochastic = factor_registry.calculate(
        "Stochastic",
        bars,
        {"high": "high", "low": "low", "close": "close", "k_period": 14, "d_period": 3},
    ).latest()
    stoch_rsi = factor_registry.calculate(
        "StochasticRSI",
        bars,
        {"source": "close", "rsi_period": 14, "stoch_period": 14, "k_period": 3, "d_period": 3},
    ).latest()
    keltner = factor_registry.calculate(
        "KeltnerChannel",
        bars,
        {"high": "high", "low": "low", "close": "close", "ema_period": 20, "atr_period": 14, "multiplier": 2.0},
    ).latest()
    aroon = factor_registry.calculate("Aroon", bars, {"high": "high", "low": "low", "period": 25}).latest()
    trix = factor_registry.calculate("TRIX", bars, {"source": "close", "period": 15, "signal": 9}).latest()
    linreg = factor_registry.calculate("LinReg", bars, {"source": "close", "period": 20}).latest()
    cmf = factor_registry.calculate(
        "CMF",
        bars,
        {"high": "high", "low": "low", "close": "close", "volume": "volume", "period": 20},
    ).latest()
    zscore = factor_registry.calculate("ZScore", bars, {"source": "close", "period": 20}).latest()
    dpo = factor_registry.calculate("DPO", bars, {"source": "close", "period": 20}).latest()

    assert wma["wma"] is not None
    assert hma["hma"] is not None
    assert stochastic["stoch_k"] is not None
    assert stoch_rsi["stochrsi_k"] is not None
    assert keltner["keltner_mid"] is not None
    assert aroon["aroon_up"] is not None
    assert trix["trix"] is not None
    assert linreg["linreg"] is not None
    assert cmf["cmf"] is not None
    assert zscore["zscore"] is not None
    assert dpo["dpo"] is not None


def test_legacy_factor_yaml_is_promoted_to_generic_formal_template(tmp_path):
    yaml_path = tmp_path / "legacy_factor_strategy.yaml"
    yaml_path.write_text(LEGACY_FACTOR_YAML, encoding="utf-8")

    definition = StrategyDefinition.load(yaml_path)

    assert definition.template_id == GENERIC_FORMAL_TEMPLATE_ID
    assert definition.signal["long_condition"] == "rsi < 30 and bb_position == 'lower_band'"
    assert definition.market_filter["enabled"] is True
    assert definition.symbols == ["DCE.p2605"]
    assert definition.timeframe_minutes == 5


def test_legacy_factor_inference_supports_extended_factor_aliases(tmp_path):
    yaml_path = tmp_path / "extended_legacy_factor_strategy.yaml"
    yaml_path.write_text(EXTENDED_LEGACY_FACTOR_YAML, encoding="utf-8")

    definition = StrategyDefinition.load(yaml_path)
    specs = _infer_legacy_indicator_specs(
        definition,
        long_condition=definition.signal.get("long_condition"),
        short_condition=definition.signal.get("short_condition"),
        market_filter_conditions=[],
    )

    spec_names = {spec.name for spec in specs}
    spec_types = {spec.indicator_type for spec in specs}

    assert {"ma20", "roc", "cmf"}.issubset(spec_names)
    assert {"WMA", "ROC", "CMF"}.issubset(spec_types)


def test_generic_runner_keeps_yaml_values_and_completes(tmp_path, monkeypatch):
    yaml_path = tmp_path / "generic_strategy.yaml"
    yaml_path.write_text(GENERIC_YAML, encoding="utf-8")

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        runner = OnlineBacktestRunner(session_manager=DummySessionManager(_build_sample_bars(count=320)))
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="generic-check",
                strategy_template_id=GENERIC_FORMAL_TEMPLATE_ID,
                strategy_yaml_filename=yaml_path.name,
                symbol="p2509",
                start_date=date(2025, 4, 1),
                end_date=date(2026, 4, 1),
                initial_capital=500000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.transaction_costs["slippage_per_unit"] == 2
    assert report.transaction_costs["commission_per_lot_round_turn"] == 3
    assert report.risk_summary.parameters["stop_loss_atr"] == 1.2
    assert report.risk_summary.parameters["take_profit_atr"] == 2
    assert report.risk_summary.parameters["max_drawdown"] == 0.12
    assert report.risk_summary.parameters["daily_loss_limit"] == "0.02%"
    assert any(note.startswith("template=generic_formal_strategy_v1") for note in report.notes)


def test_runner_ignores_close_time_backtest_finished_for_generic_strategy(tmp_path, monkeypatch):
    yaml_path = tmp_path / "legacy_factor_strategy.yaml"
    yaml_path.write_text(LEGACY_FACTOR_YAML, encoding="utf-8")

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        runner = OnlineBacktestRunner(session_manager=DummyCloseRaisesSessionManager(_build_sample_bars(count=320)))
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="legacy-close-finished",
                strategy_template_id=GENERIC_FORMAL_TEMPLATE_ID,
                strategy_yaml_filename=yaml_path.name,
                symbol="DCE.p2605",
                start_date=date(2025, 4, 1),
                end_date=date(2026, 4, 1),
                initial_capital=500000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.failure_reason is None


def test_generic_runner_finishes_when_final_account_snapshot_hits_backtest_finished(tmp_path, monkeypatch):
    yaml_path = tmp_path / "generic_strategy.yaml"
    yaml_path.write_text(GENERIC_YAML, encoding="utf-8")

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    monkeypatch.setattr(generic_strategy_module, "_resolve_backtest_finished_exception", lambda: BacktestFinished)
    get_settings.cache_clear()

    try:
        runner = OnlineBacktestRunner(session_manager=DummyFinalSnapshotRaisesSessionManager(_build_sample_bars(count=320)))
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="generic-final-snapshot-finished",
                strategy_template_id=GENERIC_FORMAL_TEMPLATE_ID,
                strategy_yaml_filename=yaml_path.name,
                symbol="p2509",
                start_date=date(2025, 4, 1),
                end_date=date(2026, 4, 1),
                initial_capital=500000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.failure_reason is None
    assert any(note == "final_snapshot=backtest_finished" for note in report.notes)
    assert any(note == "final_finish=backtest_finished" for note in report.notes)


class DummyApi:
    def __init__(self, bars):
        self._bars = bars

    def get_kline_serial(self, symbol, duration_seconds, data_length=200):
        return list(self._bars[-data_length:])

    def get_account(self, account=None):
        return {"balance": 500000.0}

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


class BacktestFinished(BaseException):
    pass


class DummyCloseRaisesSessionManager(DummySessionManager):
    @contextmanager
    def open_session(self, config):
        yield DummySession(self._bars)
        raise BacktestFinished("回测结束")


class DummyFinalSnapshotApi(DummyApi):
    def get_account(self, account=None):
        raise BacktestFinished("回测结束")

    def get_position(self, symbol=None, account=None):
        raise BacktestFinished("回测结束")


class DummyFinalSnapshotSession(DummySession):
    def __init__(self, bars):
        self.api = DummyFinalSnapshotApi(bars)
        self.account = object()


class DummyFinalSnapshotRaisesSessionManager(DummySessionManager):
    @contextmanager
    def open_session(self, config):
        yield DummyFinalSnapshotSession(self._bars)


def _build_sample_bars(*, count: int):
    start = datetime(2025, 4, 1, 9, 0, tzinfo=timezone.utc)
    bars = []
    close = 7800.0

    for index in range(count):
        drift = index * 2.5
        oscillation = ((index % 8) - 3) * 3.0
        close = 7800.0 + drift + oscillation
        high = close + 20.0 + (index % 3)
        low = close - 16.0 - (index % 2)
        open_price = close - 2.5
        volume = 900.0 + index * 18.0 + (220.0 if index % 6 == 0 else 0.0)
        bars.append(
            {
                "timestamp": start + timedelta(minutes=60 * index),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
    return bars