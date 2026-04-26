from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_template_seed_baseline_pipeline.py"
SPEC = importlib.util.spec_from_file_location("template_seed_pipeline", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_default_universe_is_42_symbols():
    assert len(MODULE.ALL_42_SYMBOLS) == 42
    assert MODULE.normalize_symbol("rb") == "SHFE.rb"
    assert MODULE.normalize_symbol("CF") == "CZCE.CF"


def test_discover_seed_templates_falls_back_to_nested_symbol_dirs(tmp_path):
    fallback_root = tmp_path / "入库标准化"
    seed_path = fallback_root / "black_metals" / "rb" / "breakout" / "STRAT_rb_breakout_33m_001.yaml"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(
        "name: STRAT_rb_breakout_33m_001\ntimeframe_minutes: 33\nsymbols:\n  - KQ.m@SHFE.rb\n",
        encoding="utf-8",
    )

    matches = MODULE.discover_seed_templates("SHFE.rb", [fallback_root])

    assert matches == [seed_path]


def test_build_strategy_yaml_updates_timeframe_symbol_and_risk():
    seed = {
        "name": "STRAT_shfe_ru_mean_reversion_60m",
        "description": "SHFE.ru 布林带均值回归 60m",
        "timeframe_minutes": 60,
        "symbols": ["KQ.m@SHFE.ru"],
        "factors": [
            {"factor_name": "ADX", "params": {"period": 14}},
            {"factor_name": "ATR", "params": {"period": 14}},
        ],
        "signal": {
            "long_condition": "close > ema and adx > 20",
            "short_condition": "close < ema and adx > 20",
            "confirm_bars": 1,
        },
        "transaction_costs": {"slippage_per_unit": 1.0, "commission_per_lot_round_turn": 3.0},
        "risk": {"stop_loss": {"type": "atr", "atr_multiplier": 2.0}, "take_profit": {"type": "atr", "atr_multiplier": 2.4}},
        "tags": ["SHFE", "ru", "60m"],
    }

    strategy = MODULE.build_strategy_yaml(
        seed_strategy=seed,
        symbol="SHFE.ru",
        target_timeframe=5,
        source_path=Path("/tmp/STRAT_shfe_ru_mean_reversion_60m.yaml"),
        search_space={"atr_multiplier": [1.5, 3.0], "adx_threshold": [20, 30]},
    )

    assert strategy["name"] == "STRAT_shfe_ru_mean_reversion_5m"
    assert strategy["timeframe_minutes"] == 5
    assert strategy["symbols"] == ["KQ.m@SHFE.ru"]
    assert strategy["risk"]["force_close_day"] == "14:55"
    assert strategy["risk"]["no_overnight"] is True
    assert strategy["risk"]["force_close_night"] == "22:55"
    assert strategy["risk"]["stop_loss"]["type"] == "atr"
    assert strategy["risk"]["take_profit"]["type"] == "atr"
    assert "5m" in strategy["tags"]
    assert "adx > 25" in strategy["signal"]["long_condition"]


def test_evaluate_candidate_requires_completed_and_tqsdk_valid():
    baseline_report = {
        "status": "completed",
        "summary": {
            "status": "completed",
            "sharpe": 1.2,
            "max_drawdown": 0.08,
            "win_rate": 0.52,
            "total_trades": 11,
        },
    }

    accepted = MODULE.evaluate_candidate(
        baseline_report=baseline_report,
        tqsdk_valid=True,
        tqsdk_errors=[],
        thresholds=MODULE.CandidateThresholds(),
    )
    rejected = MODULE.evaluate_candidate(
        baseline_report=baseline_report,
        tqsdk_valid=False,
        tqsdk_errors=["risk.force_close_day 必须为 14:55"],
        thresholds=MODULE.CandidateThresholds(),
    )

    assert accepted["is_candidate"] is True
    assert rejected["is_candidate"] is False
    assert "risk.force_close_day 必须为 14:55" in rejected["reasons"]