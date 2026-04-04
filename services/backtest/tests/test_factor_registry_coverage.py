"""
TASK-0005 批次C — 因子接线覆盖测试

验证 OFFICIAL_FACTOR_BASELINE 中每个官方因子在 GenericFactorStrategy 中
均有明确的处理路径：要么在 _FACTOR_SCORE_KEYS（方向性），要么在
_NON_DIRECTIONAL_KEYS（非方向性），不允许静默跳过。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.backtest.src.backtest.factor_registry import OFFICIAL_FACTOR_BASELINE
from services.backtest.src.backtest.generic_factor_strategy import (
    _FACTOR_SCORE_KEYS,
    _NON_DIRECTIONAL_KEYS,
)


def test_all_official_factors_have_explicit_mapping():
    """每个官方因子的规范化名称必须存在于 _FACTOR_SCORE_KEYS 或 _NON_DIRECTIONAL_KEYS。"""
    missing = []
    for factor_name in OFFICIAL_FACTOR_BASELINE:
        normalized = factor_name.lower()
        in_score_keys = normalized in _FACTOR_SCORE_KEYS
        in_non_directional = normalized in _NON_DIRECTIONAL_KEYS
        if not in_score_keys and not in_non_directional:
            missing.append(factor_name)

    assert not missing, (
        f"以下官方因子在 generic_factor_strategy 中既不在 _FACTOR_SCORE_KEYS "
        f"也不在 _NON_DIRECTIONAL_KEYS，会被静默跳过：{missing}"
    )


def test_factor_score_keys_and_non_directional_keys_are_disjoint():
    """_FACTOR_SCORE_KEYS 与 _NON_DIRECTIONAL_KEYS 不应有重叠的因子名。"""
    overlap = set(_FACTOR_SCORE_KEYS.keys()) & _NON_DIRECTIONAL_KEYS
    assert not overlap, (
        f"以下 key 同时出现在 _FACTOR_SCORE_KEYS 和 _NON_DIRECTIONAL_KEYS 中，"
        f"存在歧义：{overlap}"
    )
