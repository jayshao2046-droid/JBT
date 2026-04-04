from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest import generic_factor_strategy as generic_module
from services.backtest.src.backtest.generic_factor_strategy import GenericFactorStrategy
from services.backtest.src.backtest.runner import BacktestJobInput, OnlineBacktestRunner
from services.backtest.src.backtest.session import TqSdkSessionManager
from services.backtest.src.core.settings import get_settings

GENERIC_TEMPLATE_ID = "generic-factor-live-v1"
GENERIC_SYMBOL = "SHFE.rb2501"

GENERIC_LIVE_STRATEGY_YAML = dedent(
    f"""
    template_id: "{GENERIC_TEMPLATE_ID}"
    name: "{GENERIC_TEMPLATE_ID}"
    description: "Generic factor strategy with live execution"
    version: "1.0"

    factors:
      - factor_name: "MACD"
        weight: 0.45
        params:
          fast: 6
          slow: 13
          signal: 5
      - factor_name: "RSI"
        weight: 0.35
        params:
          period: 14
      - factor_name: "VolumeRatio"
        weight: 0.20
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

    symbols:
      - "{GENERIC_SYMBOL}"

    timeframe_minutes: 5
    position_fraction: 0.12

    transaction_costs:
      slippage_per_unit: 1
      commission_per_lot_round_turn: 2

    risk:
      daily_loss_limit_yuan: 1200
      max_drawdown_pct: 0.02
    """
).strip()

GENERIC_THRESHOLD_STRATEGY_YAML = dedent(
    f"""
    template_id: "generic-factor-threshold-v1"
    name: "generic-factor-threshold-v1"
    description: "Generic factor strategy with weighted threshold fallback"
    version: "1.0"

    factors:
      - factor_name: "MACD"
        weight: 0.45
        params:
          fast: 6
          slow: 13
          signal: 5
      - factor_name: "RSI"
        weight: 0.35
        params:
          period: 14
      - factor_name: "VolumeRatio"
        weight: 0.20
        params:
          period: 10

    signal:
      long_threshold: 0.25
      short_threshold: 0.25

    symbols:
      - "{GENERIC_SYMBOL}"

    timeframe_minutes: 5
    position_fraction: 0.12

    transaction_costs:
      slippage_per_unit: 1
      commission_per_lot_round_turn: 2

    risk:
      daily_loss_limit_yuan: 1200
      max_drawdown_pct: 0.02
    """
).strip()


def test_generic_runner_enters_live_execution_and_persists_trace(tmp_path, monkeypatch):
    yaml_path = tmp_path / "generic_live_strategy.yaml"
    yaml_path.write_text(GENERIC_LIVE_STRATEGY_YAML, encoding="utf-8")
    result_root = tmp_path / "results"
    DummySim.last_instance = None
    _patch_generic_execution(monkeypatch)

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(result_root))
    monkeypatch.setenv("TQSDK_AUTH_USERNAME", "demo-user")
    monkeypatch.setenv("TQSDK_AUTH_PASSWORD", "demo-password")
    get_settings.cache_clear()

    try:
        session_manager = TqSdkSessionManager(
            settings=get_settings(),
            api_factory=_build_dummy_api_factory(enable_trades=True),
            auth_factory=DummyAuth,
            backtest_factory=DummyBacktest,
            sim_factory=DummySim,
        )
        runner = OnlineBacktestRunner(session_manager=session_manager)
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="task-0005-generic-live",
                strategy_template_id=GENERIC_TEMPLATE_ID,
                strategy_yaml_filename=yaml_path.name,
                symbol=GENERIC_SYMBOL,
                start_date=date(2024, 4, 3),
                end_date=date(2024, 4, 12),
                initial_capital=500000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.strategy_template_id == GENERIC_TEMPLATE_ID
    assert report.strategy_name == GENERIC_TEMPLATE_ID
    assert report.timeframe == "5m"
    assert report.total_trades > 0
    assert report.performance_metrics.total_trades > 0
    assert report.transaction_costs["slippage_per_unit"] == 1.0
    assert report.transaction_costs["commission_per_lot_round_turn"] == 2.0
    assert "execution_loop=wait_update_target_pos" in report.notes
    assert "execution_loop_entered=true" in report.notes
    assert _extract_int_note(report.notes, "target_updates=") >= 1
    assert _extract_int_note(report.notes, "observed_trade_records=") >= 1
    assert _extract_int_note(report.notes, "signal_transitions=") >= 2
    assert _extract_string_note(report.notes, "final_signal_state=") in {"long", "short", "flat", "blocked"}
    assert any(note.startswith("factor_snapshot.MACD=") for note in report.notes)
    assert "status=completed" in report.report_summary
    assert "total_trades=" in report.report_summary

    assert DummySim.last_instance is not None
    assert DummySim.last_instance.slippage_calls == [(GENERIC_SYMBOL, 1.0)]
    assert DummySim.last_instance.commission_calls == [(GENERIC_SYMBOL, 2.0)]

    report_file = result_root / report.job_id / "report.json"
    assert report_file.exists()
    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["total_trades"] > 0
    assert "execution_loop_entered=true" in payload["notes"]
    assert any(note.startswith("target_updates=") for note in payload["notes"])


def test_generic_strategy_uses_weighted_score_fallback_when_conditions_missing(tmp_path, monkeypatch):
    yaml_path = tmp_path / "generic_threshold_strategy.yaml"
    yaml_path.write_text(GENERIC_THRESHOLD_STRATEGY_YAML, encoding="utf-8")

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(tmp_path / "results"))
    get_settings.cache_clear()

    monkeypatch.setattr(
        GenericFactorStrategy,
        "_resolve_factor_contribution",
        lambda self, snapshot, factor_name: {
            "MACD": 1.0,
            "RSI": 0.6,
            "VolumeRatio": 0.8,
        }.get(factor_name, 0.0),
    )

    try:
        runner = OnlineBacktestRunner(
            session_manager=DummyStaticSessionManager(_build_sample_bars(count=96))
        )
        report = runner.run_job_sync(
            BacktestJobInput(
                job_id="task-0005-generic-threshold",
                strategy_template_id="generic-factor-threshold-v1",
                strategy_yaml_filename=yaml_path.name,
                symbol=GENERIC_SYMBOL,
                start_date=date(2024, 4, 3),
                end_date=date(2024, 4, 12),
                initial_capital=500000.0,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.total_trades == 0
    assert "execution_loop=static_snapshot" in report.notes
    assert "signal_state=long" in report.notes
    assert any(note.startswith("signal_score=") for note in report.notes)


class DummyAuth:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password


class DummyBacktest:
    def __init__(self, *, start_dt: date, end_dt: date) -> None:
        self.start_dt = start_dt
        self.end_dt = end_dt


class DummySim:
    last_instance: "DummySim | None" = None

    def __init__(self, *, init_balance: float) -> None:
        self.init_balance = init_balance
        self.balance = init_balance
        self.slippage_calls: list[tuple[str, float]] = []
        self.commission_calls: list[tuple[str, float]] = []
        self._slippage_by_symbol: dict[str, float] = {}
        self._commission_by_symbol: dict[str, float] = {}
        DummySim.last_instance = self

    def set_slippage(self, symbol: str, slippage: float) -> None:
        self.slippage_calls.append((symbol, float(slippage)))
        self._slippage_by_symbol[symbol] = float(slippage)

    def set_commission(self, symbol: str, commission: float) -> None:
        self.commission_calls.append((symbol, float(commission)))
        self._commission_by_symbol[symbol] = float(commission)

    def get_slippage(self, symbol: str) -> float:
        return self._slippage_by_symbol.get(symbol, 0.0)

    def get_commission(self, symbol: str) -> float:
        return self._commission_by_symbol.get(symbol, 0.0)


class DummyLiveApi:
    def __init__(
        self,
        account: DummySim,
        *,
        backtest: DummyBacktest,
        auth: DummyAuth,
        disable_print: bool = True,
        enable_trades: bool = True,
    ) -> None:
        self._account = account
        self._backtest = backtest
        self._auth = auth
        self._disable_print = disable_print
        self._enable_trades = enable_trades
        self._bars = _build_sample_bars(count=120)
        self._cursor = 0
        self._data_length = 0
        self._trade_records: dict[str, dict[str, Any]] = {}
        self._next_trade_id = 1
        self._pending_target_volume = 0
        self._net_position = 0

    def get_kline_serial(self, symbol, duration_seconds, data_length=200):
        _ = symbol
        _ = duration_seconds
        self._data_length = min(max(1, int(data_length)), len(self._bars))
        self._cursor = max(self._cursor, self._data_length - 1)
        return DummyKlineSerial(self)

    def get_quote(self, symbol):
        _ = symbol
        return DummyQuote(self)

    def wait_update(self):
        if self._cursor >= len(self._bars) - 1:
            raise generic_module._resolve_backtest_finished_exception()()
        self._cursor += 1
        self._apply_pending_target_volume()
        return True

    def is_changing(self, obj, key=None):
        _ = obj
        _ = key
        return True

    def get_account(self, account=None):
        _ = account
        return {"balance": self._account.balance}

    def get_position(self, symbol=None, account=None):
        _ = symbol
        _ = account
        return {
            "volume_long": max(self._net_position, 0),
            "volume_short": max(-self._net_position, 0),
        }

    def get_trade(self, trade_id=None, account=None):
        _ = account
        if trade_id is None:
            return dict(self._trade_records)
        return self._trade_records[trade_id]

    def set_target_volume(self, volume: int) -> None:
        self._pending_target_volume = int(volume)

    def close(self):
        return None

    @property
    def current_window(self) -> list[dict[str, Any]]:
        start = max(0, self._cursor - self._data_length + 1)
        return [dict(row) for row in self._bars[start : self._cursor + 1]]

    @property
    def current_bar(self) -> dict[str, Any]:
        return dict(self._bars[self._cursor])

    def _apply_pending_target_volume(self) -> None:
        if not self._enable_trades:
            return
        if self._pending_target_volume == self._net_position:
            return

        delta = self._pending_target_volume - self._net_position
        direction = 1 if delta > 0 else -1
        trade_price = float(self.current_bar["close"]) + direction * self._account.get_slippage(GENERIC_SYMBOL)

        for _ in range(abs(delta)):
            trade_id = f"trade-{self._next_trade_id}"
            self._trade_records[trade_id] = {
                "trade_id": trade_id,
                "price": trade_price,
                "volume": 1,
            }
            self._next_trade_id += 1
            self._account.balance -= self._account.get_commission(GENERIC_SYMBOL)

        self._net_position = self._pending_target_volume


class DummyStaticApi:
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


class DummyKlineSerial:
    def __init__(self, api: DummyLiveApi) -> None:
        self._api = api

    @property
    def iloc(self):
        return DummyILoc(self)

    def to_dict(self, *args, **kwargs):
        _ = args
        _ = kwargs
        return self._api.current_window


class DummyILoc:
    def __init__(self, serial: DummyKlineSerial) -> None:
        self._serial = serial

    def __getitem__(self, index):
        if index != -1:
            raise IndexError(index)
        window = self._serial._api.current_window
        if not window:
            raise IndexError(index)
        return dict(window[-1])


class DummyQuote:
    def __init__(self, api: DummyLiveApi) -> None:
        self._api = api
        self.volume_multiple = 10.0

    @property
    def last_price(self) -> float:
        return float(self._api.current_bar["close"])


class DummyTargetPosTask:
    def __init__(self, api: DummyLiveApi, symbol: str) -> None:
        self._api = api
        self._symbol = symbol

    def set_target_volume(self, volume: int) -> None:
        _ = self._symbol
        self._api.set_target_volume(volume)


class DummyStaticSession:
    def __init__(self, bars):
        self.api = DummyStaticApi(bars)
        self.account = object()


class DummyStaticSessionManager:
    def __init__(self, bars):
        self._bars = bars

    def build_config_from_job(self, job):
        _ = job
        return object()

    @contextmanager
    def open_session(self, config):
        _ = config
        yield DummyStaticSession(self._bars)


def _build_dummy_api_factory(*, enable_trades: bool):
    def _factory(account, *, backtest, auth, disable_print=True):
        return DummyLiveApi(
            account,
            backtest=backtest,
            auth=auth,
            disable_print=disable_print,
            enable_trades=enable_trades,
        )

    return _factory


def _patch_generic_execution(monkeypatch) -> None:
    class DummyBacktestFinished(RuntimeError):
        pass

    monkeypatch.setattr(
        generic_module,
        "_resolve_backtest_finished_exception",
        lambda: DummyBacktestFinished,
    )
    monkeypatch.setattr(
        GenericFactorStrategy,
        "build_target_pos_task",
        lambda self, **kwargs: DummyTargetPosTask(self.session.api, self.runtime_context.symbol),
    )

    def _fake_compute_merged_rows(self, bars):
        merged_rows = []
        for bar in bars:
            signal_state = bar.get("signal_state", "flat")
            merged_rows.append(
                {
                    **bar,
                    "atr": 120.0,
                    "adx": 30.0,
                    "macd_hist": 1.0 if signal_state == "long" else (-1.0 if signal_state == "short" else 0.0),
                    "rsi_slope": 0.8 if signal_state == "long" else (-0.8 if signal_state == "short" else 0.0),
                    "volume_ratio": 1.5 if signal_state in {"long", "short"} else 1.0,
                }
            )
        latest = merged_rows[-1]
        factor_snapshots = {
            "MACD": {"timestamp": latest["timestamp"], "macd_hist": latest["macd_hist"]},
            "RSI": {"timestamp": latest["timestamp"], "rsi_slope": latest["rsi_slope"]},
            "VolumeRatio": {"timestamp": latest["timestamp"], "volume_ratio": latest["volume_ratio"]},
        }
        return merged_rows, factor_snapshots

    monkeypatch.setattr(GenericFactorStrategy, "_compute_merged_rows", _fake_compute_merged_rows)


def _build_sample_bars(*, count: int):
    start = datetime(2024, 4, 3, 9, 0, tzinfo=timezone.utc)
    bars = []
    close = 3800.0

    for index in range(count):
        drift = index * 4.5
        oscillation = ((index % 6) - 2) * 1.7
        close = 3800.0 + drift + oscillation
        high = close + 12.0 + (index % 3)
        low = close - 10.0 - (index % 2)
        open_price = close - 2.0
        volume = 1600.0 + index * 28.0
        if index >= 80:
            signal_state = "short"
        elif index >= 40:
            signal_state = "long"
        else:
            signal_state = "flat"
        timestamp = start + timedelta(minutes=5 * index)
        bars.append(
            {
                "datetime": timestamp,
                "timestamp": timestamp,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "signal_state": signal_state,
            }
        )
    return bars


def _extract_int_note(notes: list[str], prefix: str) -> int:
    for note in notes:
        if note.startswith(prefix):
            return int(note.split("=", 1)[1])
    raise AssertionError(f"missing note with prefix {prefix}")


def _extract_string_note(notes: list[str], prefix: str) -> str:
    for note in notes:
        if note.startswith(prefix):
            return note.split("=", 1)[1]
    raise AssertionError(f"missing note with prefix {prefix}")