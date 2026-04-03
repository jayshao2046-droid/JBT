from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest import fc_224_strategy as fc_224_module
from services.backtest.src.backtest.fc_224_strategy import FC224Strategy, FC_224_TEMPLATE_ID
from services.backtest.src.backtest.runner import BacktestJobInput, OnlineBacktestRunner
from services.backtest.src.backtest.session import TqSdkSessionManager
from services.backtest.src.core.settings import get_settings

FC_224_YAML = dedent(
    f"""
    name: "{FC_224_TEMPLATE_ID}"
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
    """
).strip()


def test_fc_224_formal_run_persists_trace_and_applies_transaction_costs(tmp_path, monkeypatch):
    yaml_path = tmp_path / "FC-_5_cf_v1.yaml"
    yaml_path.write_text(FC_224_YAML, encoding="utf-8")
    result_root = tmp_path / "results"
    DummySim.last_instance = None
    _patch_fc_224_execution(monkeypatch)

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
            BacktestJobInput.build_fc_224_formal_run(
                job_id="task-0003-r2-completed",
                strategy_yaml_filename=yaml_path.name,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "completed"
    assert report.strategy_name == FC_224_TEMPLATE_ID
    assert report.symbol == "CZCE.CF605"
    assert report.timeframe == "5m"
    assert report.start_date == date(2024, 4, 3)
    assert report.end_date == date(2026, 4, 3)
    assert report.initial_capital == 1000000.0
    assert report.transaction_costs["slippage_per_unit"] == 1.0
    assert report.transaction_costs["commission_per_lot_round_turn"] == 8.0
    assert "status=completed" in report.report_summary
    assert "slippage_per_unit=1" in report.report_summary
    assert "commission_per_lot_round_turn=8" in report.report_summary
    assert report.total_trades > 0
    assert report.performance_metrics.total_trades > 0
    assert "execution_loop_entered=true" in report.notes

    assert DummySim.last_instance is not None
    assert DummySim.last_instance.slippage_calls == [("CZCE.CF605", 1.0)]
    assert DummySim.last_instance.commission_calls == [("CZCE.CF605", 8.0)]

    report_file = result_root / report.job_id / "report.json"
    assert report_file.exists()
    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload["strategy_name"] == FC_224_TEMPLATE_ID
    assert payload["timeframe"] == "5m"
    assert payload["start_date"] == "2024-04-03"
    assert payload["end_date"] == "2026-04-03"
    assert payload["initial_capital"] == 1000000.0
    assert payload["transaction_costs"]["slippage_per_unit"] == 1.0
    assert payload["transaction_costs"]["commission_per_lot_round_turn"] == 8.0
    assert payload["status"] == "completed"
    assert payload["total_trades"] > 0


def test_fc_224_formal_run_persists_blocked_trace_when_credentials_missing(tmp_path, monkeypatch):
    yaml_path = tmp_path / "FC-_5_cf_v1.yaml"
    yaml_path.write_text(FC_224_YAML, encoding="utf-8")
    result_root = tmp_path / "results"

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(result_root))
    monkeypatch.delenv("TQSDK_AUTH_USERNAME", raising=False)
    monkeypatch.delenv("TQSDK_AUTH_PASSWORD", raising=False)
    get_settings.cache_clear()

    try:
        runner = OnlineBacktestRunner()
        report = runner.run_job_sync(
            BacktestJobInput.build_fc_224_formal_run(
                job_id="task-0003-r2-blocked",
                strategy_yaml_filename=yaml_path.name,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "failed"
    assert report.failure_reason == (
        "TQSDK_AUTH_USERNAME and TQSDK_AUTH_PASSWORD must be configured before formal backtest execution"
    )
    assert report.strategy_name == FC_224_TEMPLATE_ID
    assert report.timeframe == "5m"
    assert report.start_date == date(2024, 4, 3)
    assert report.end_date == date(2026, 4, 3)
    assert report.initial_capital == 1000000.0
    assert report.transaction_costs["slippage_per_unit"] == 1.0
    assert report.transaction_costs["commission_per_lot_round_turn"] == 8.0
    assert "status=failed" in report.report_summary
    assert "failure_reason=TQSDK_AUTH_USERNAME and TQSDK_AUTH_PASSWORD must be configured before formal backtest execution" in report.report_summary

    report_file = result_root / report.job_id / "report.json"
    assert report_file.exists()
    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["failure_reason"] == report.failure_reason
    assert payload["strategy_name"] == FC_224_TEMPLATE_ID
    assert payload["timeframe"] == "5m"
    assert payload["transaction_costs"]["slippage_per_unit"] == 1.0
    assert payload["transaction_costs"]["commission_per_lot_round_turn"] == 8.0


def test_fc_224_formal_run_rejects_zero_trade_completed_result(tmp_path, monkeypatch):
    yaml_path = tmp_path / "FC-_5_cf_v1.yaml"
    yaml_path.write_text(FC_224_YAML, encoding="utf-8")
    result_root = tmp_path / "results"
    DummySim.last_instance = None
    _patch_fc_224_execution(monkeypatch)

    monkeypatch.setenv("TQSDK_STRATEGY_YAML_DIR", str(tmp_path))
    monkeypatch.setenv("BACKTEST_RESULT_DIR", str(result_root))
    monkeypatch.setenv("TQSDK_AUTH_USERNAME", "demo-user")
    monkeypatch.setenv("TQSDK_AUTH_PASSWORD", "demo-password")
    get_settings.cache_clear()

    try:
        session_manager = TqSdkSessionManager(
            settings=get_settings(),
            api_factory=_build_dummy_api_factory(enable_trades=False),
            auth_factory=DummyAuth,
            backtest_factory=DummyBacktest,
            sim_factory=DummySim,
        )
        runner = OnlineBacktestRunner(session_manager=session_manager)
        report = runner.run_job_sync(
            BacktestJobInput.build_fc_224_formal_run(
                job_id="task-0003-r3-zero-trades",
                strategy_yaml_filename=yaml_path.name,
            )
        )
    finally:
        get_settings.cache_clear()

    assert report.status == "failed"
    assert report.total_trades == 0
    assert report.failure_reason is not None
    assert "策略执行逻辑未闭环" in report.failure_reason
    assert "formal_result_rejected=true" in report.notes
    assert "status=failed" in report.report_summary

    report_file = result_root / report.job_id / "report.json"
    assert report_file.exists()
    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["total_trades"] == 0
    assert "策略执行逻辑未闭环" in payload["failure_reason"]


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


class DummyApi:
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
        self._data_length = min(max(1, int(data_length)), len(self._bars))
        self._cursor = max(self._cursor, self._data_length - 1)
        return DummyKlineSerial(self)

    def get_quote(self, symbol):
        return DummyQuote(self)

    def wait_update(self):
        if self._cursor >= len(self._bars) - 1:
            raise fc_224_module._resolve_backtest_finished_exception()()
        self._cursor += 1
        self._apply_pending_target_volume()
        return True

    def is_changing(self, obj, key=None):
        return True

    def get_account(self, account=None):
        return {"balance": self._account.balance}

    def get_position(self, symbol=None, account=None):
        return {
            "volume_long": max(self._net_position, 0),
            "volume_short": max(-self._net_position, 0),
        }

    def get_trade(self, trade_id=None, account=None):
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
        symbol = "CZCE.CF605"
        trade_price = float(self.current_bar["close"]) + direction * self._account.get_slippage(symbol)

        for _ in range(abs(delta)):
            trade_id = f"trade-{self._next_trade_id}"
            self._trade_records[trade_id] = {
                "trade_id": trade_id,
                "price": trade_price,
                "volume": 1,
            }
            self._next_trade_id += 1
            self._account.balance -= self._account.get_commission(symbol)

        self._net_position = self._pending_target_volume


class DummyKlineSerial:
    def __init__(self, api: DummyApi) -> None:
        self._api = api

    @property
    def iloc(self):
        return DummyILoc(self)

    def to_dict(self, *args, **kwargs):
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
    def __init__(self, api: DummyApi) -> None:
        self._api = api
        self.volume_multiple = 5.0

    @property
    def last_price(self) -> float:
        return float(self._api.current_bar["close"])


class DummyTargetPosTask:
    def __init__(self, api: DummyApi, symbol: str) -> None:
        self._api = api
        self._symbol = symbol

    def set_target_volume(self, volume: int) -> None:
        self._api.set_target_volume(volume)


def _build_dummy_api_factory(*, enable_trades: bool):
    def _factory(account, *, backtest, auth, disable_print=True):
        return DummyApi(
            account,
            backtest=backtest,
            auth=auth,
            disable_print=disable_print,
            enable_trades=enable_trades,
        )

    return _factory


def _patch_fc_224_execution(monkeypatch) -> None:
    class DummyBacktestFinished(RuntimeError):
        pass

    monkeypatch.setattr(
        fc_224_module,
        "_resolve_backtest_finished_exception",
        lambda: DummyBacktestFinished,
    )
    monkeypatch.setattr(
        FC224Strategy,
        "build_target_pos_task",
        lambda self, **kwargs: DummyTargetPosTask(self.session.api, self.runtime_context.symbol),
    )

    def _fake_compute_indicator_rows(self, bars, config):
        rows = []
        for bar in bars:
            signal_state = bar.get("signal_state", "flat")
            rows.append(
                {
                    **bar,
                    "atr": 120.0,
                    "adx": 30.0,
                    "macd_hist": 1.0 if signal_state == "long" else (-1.0 if signal_state == "short" else 0.0),
                    "rsi_slope": 1.0 if signal_state == "long" else (-1.0 if signal_state == "short" else 0.0),
                    "volume_ratio": 1.5 if signal_state in {"long", "short"} else 1.0,
                }
            )
        return rows

    monkeypatch.setattr(FC224Strategy, "_compute_indicator_rows", _fake_compute_indicator_rows)


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
        signal_state = "long" if index >= 40 else "flat"
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
