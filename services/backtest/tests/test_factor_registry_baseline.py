from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.factor_registry import OFFICIAL_FACTOR_BASELINE, factor_registry


def test_factor_registry_contains_full_33_factor_baseline_and_excludes_myfactor():
    expected = sorted(name.lower() for name in OFFICIAL_FACTOR_BASELINE)

    assert len(expected) == 33
    assert "myfactor" not in expected
    assert factor_registry.list_factors() == expected


def test_all_baseline_factors_produce_outputs_on_rich_sample():
    bars = _build_sample_bars(count=96, include_external_columns=True)

    for factor_name in OFFICIAL_FACTOR_BASELINE:
        result = factor_registry.calculate(factor_name, bars, _factor_params(factor_name))
        latest = result.latest()

        assert latest["timestamp"] == bars[-1]["timestamp"]
        assert any(
            key != "timestamp" and latest[key] is not None
            for key in latest
        ), factor_name


def test_external_dependency_factors_fall_back_to_neutral_when_columns_are_missing():
    bars = _build_sample_bars(count=72, include_external_columns=False)

    implied_vol = factor_registry.calculate("ImpliedVolatility", bars).latest()
    basis_spread = factor_registry.calculate("BasisSpread", bars).latest()
    news_sentiment = factor_registry.calculate("NewsSentiment", bars).latest()
    inventory_factor = factor_registry.calculate("InventoryFactor", bars).latest()
    warehouse_receipt_factor = factor_registry.calculate("WarehouseReceiptFactor", bars).latest()

    assert implied_vol["implied_volatility"] == 0.0
    assert basis_spread["basis_spread"] == 0.0
    assert news_sentiment["news_sentiment"] == 0.0
    assert inventory_factor["inventory_factor"] == 0.0
    assert warehouse_receipt_factor["warehouse_receipt_factor"] == 0.0


def _factor_params(factor_name: str):
    params = {
        "ADX": {"period": 14},
        "ATR": {"period": 14},
        "BollingerBands": {"period": 20, "stddev": 2},
        "CCI": {"period": 20},
        "DEMA": {"period": 20},
        "EMA": {"period": 20},
        "Ichimoku": {"conversion_period": 9, "base_period": 26, "span_b_period": 52},
        "MACD": {"fast": 6, "slow": 13, "signal": 5},
        "MFI": {"period": 14},
        "OBV": {},
        "ParabolicSAR": {"step": 0.02, "max_step": 0.2},
        "RSI": {"period": 14},
        "SMA": {"period": 20},
        "Supertrend": {"period": 10, "multiplier": 3},
        "VolumeRatio": {"period": 10},
        "VWAP": {},
        "WilliamsR": {"period": 14},
        "GarmanKlass": {"period": 20},
        "HistoricalVol": {"period": 20},
        "ImpliedVolatility": {},
        "VolatilityFactor": {"period": 20},
        "BasisSpread": {},
        "CointResidual": {"hedge_ratio": 1.0},
        "SpreadCrosscommodity": {},
        "SpreadCrossperiod": {},
        "SpreadRatio": {},
        "ZScoreSpread": {"period": 20},
        "NewsSentiment": {},
        "SocialSentiment": {},
        "SentimentFactor": {},
        "InventoryFactor": {},
        "OpenInterestFactor": {},
        "WarehouseReceiptFactor": {},
    }
    return dict(params.get(factor_name, {}))


def _build_sample_bars(*, count: int, include_external_columns: bool):
    start = datetime(2024, 4, 3, 9, 0, tzinfo=timezone.utc)
    bars = []

    for index in range(count):
        base_close = 100.0 + index * 0.8 + ((index % 9) - 4) * 0.35
        open_price = base_close - 0.5 + ((index % 3) - 1) * 0.1
        high = max(open_price, base_close) + 1.2 + (index % 4) * 0.1
        low = min(open_price, base_close) - 1.0 - (index % 3) * 0.1
        volume = 1200.0 + index * 30.0 + (180.0 if index % 7 == 0 else 0.0)
        bar = {
            "timestamp": start + timedelta(minutes=5 * index),
            "open": open_price,
            "high": high,
            "low": low,
            "close": base_close,
            "volume": volume,
        }
        if include_external_columns:
            bar.update(
                {
                    "spot_price": base_close - 1.4 + ((index % 5) - 2) * 0.15,
                    "pair_close": base_close * 0.92 + ((index % 6) - 3) * 0.25,
                    "crosscommodity_close": base_close * 1.03 + ((index % 4) - 2) * 0.2,
                    "crossperiod_close": base_close * 1.01 + ((index % 5) - 2) * 0.18,
                    "benchmark_close": base_close * 0.97 + ((index % 7) - 3) * 0.22,
                    "far_close": base_close * 1.015 + ((index % 6) - 3) * 0.16,
                    "open_interest": 50000.0 + index * 130.0 + ((index % 5) - 2) * 35.0,
                    "inventory": 2500.0 - index * 4.0 + ((index % 6) - 3) * 8.0,
                    "warehouse_receipts": 900.0 - index * 1.5 + ((index % 8) - 4) * 2.5,
                    "implied_volatility": 0.18 + (index % 10) * 0.002,
                    "news_sentiment": ((index % 9) - 4) / 10.0,
                    "social_sentiment": ((index % 7) - 3) / 12.0,
                }
            )
        bars.append(bar)
    return bars