"""采集参数优化器测试"""
from __future__ import annotations

import pytest

from src.stats.optimizer import CollectionOptimizer


def test_grid_search():
    optimizer = CollectionOptimizer()
    param_grid = {
        "interval": [60, 300],
        "timeout": [10, 30],
    }
    results = optimizer.grid_search(param_grid, "success_rate")
    assert len(results) == 4
    assert all("params" in r for r in results)
    assert all("score" in r for r in results)


def test_auto_tune():
    optimizer = CollectionOptimizer()
    current_params = {"interval": 300, "timeout": 30, "retry_count": 3}
    result = optimizer.auto_tune(current_params, "success_rate")
    assert "recommended_params" in result
    assert "expected_score" in result
    assert "improvement" in result


def test_recommend_best_practice():
    optimizer = CollectionOptimizer()
    result = optimizer.recommend_best_practice("futures_minute")
    assert "source_type" in result
    assert "recommended_params" in result
    assert "description" in result
    assert result["recommended_params"]["interval"] == 60


def test_recommend_best_practice_unknown():
    optimizer = CollectionOptimizer()
    result = optimizer.recommend_best_practice("unknown_source")
    assert "recommended_params" in result
    assert result["recommended_params"]["interval"] == 300
