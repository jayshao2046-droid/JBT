"""
测试晚间轮换器 (CB8)
"""
import pytest
from src.research.evening_rotation import EveningRotator


def test_rotate_empty_universe():
    """测试空股票池"""
    rotator = EveningRotator(top_n=10)
    result = rotator.rotate([])
    assert result == []


def test_rotate_returns_top_n():
    """测试返回 TOP-N 股票"""
    rotator = EveningRotator(top_n=5)
    universe = [f"60000{i}.SH" for i in range(10)]
    result = rotator.rotate(universe)
    assert len(result) == 5


def test_rotate_universe_smaller_than_top_n():
    """测试股票池小于 TOP-N"""
    rotator = EveningRotator(top_n=10)
    universe = ["600000.SH", "600001.SH", "600002.SH"]
    result = rotator.rotate(universe)
    assert len(result) == 3


def test_get_rotation_plan():
    """测试获取轮换计划"""
    rotator = EveningRotator(top_n=5)
    universe = [f"60000{i}.SH" for i in range(10)]
    rotator.rotate(universe)
    plan = rotator.get_rotation_plan()
    assert plan["plan_id"] is not None
    assert plan["top_n"] == 5
    assert len(plan["selected"]) == 5
    assert "rotated_at" in plan


def test_get_plan_before_rotation():
    """测试轮换前获取计划"""
    rotator = EveningRotator()
    plan = rotator.get_rotation_plan()
    assert plan["plan_id"] is None
    assert plan["selected"] == []


def test_score_stock_with_valid_bars():
    """测试股票评分（有效数据）"""
    rotator = EveningRotator()
    bars = [
        {"open": 10.0, "high": 10.5, "low": 9.8, "close": 10.0, "volume": 1000000, "date": "2026-04-01"},
        {"open": 10.1, "high": 10.8, "low": 10.0, "close": 10.5, "volume": 1200000, "date": "2026-04-02"},
        {"open": 10.5, "high": 11.0, "low": 10.3, "close": 10.8, "volume": 1500000, "date": "2026-04-03"}
    ]
    score = rotator._score_stock("600000.SH", bars)
    assert score > 0


def test_score_stock_empty_bars():
    """测试空 bars"""
    rotator = EveningRotator()
    score = rotator._score_stock("600000.SH", [])
    assert score == 0.0


def test_score_stock_single_bar():
    """测试单个 bar"""
    rotator = EveningRotator()
    bars = [{"open": 10.0, "high": 10.5, "low": 9.8, "close": 10.0, "volume": 1000000, "date": "2026-04-01"}]
    score = rotator._score_stock("600000.SH", bars)
    assert score == 0.0


def test_plan_structure():
    """测试计划结构"""
    rotator = EveningRotator(top_n=3)
    universe = ["600000.SH", "600001.SH", "600002.SH"]
    rotator.rotate(universe)
    plan = rotator.get_rotation_plan()
    assert "plan_id" in plan
    assert "rotated_at" in plan
    assert "top_n" in plan
    assert "selected" in plan
    assert "scores" in plan
    assert isinstance(plan["scores"], list)
