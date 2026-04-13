"""数据质量和健康统计测试"""
from __future__ import annotations

import pytest

from src.stats.quality import DataQualityCalculator
from src.stats.health import DataSourceHealthCalculator


def test_calculate_completeness():
    calculator = DataQualityCalculator()
    collections = [
        {"expected_count": 100, "actual_count": 95},
        {"expected_count": 200, "actual_count": 190},
    ]
    completeness = calculator.calculate_completeness(collections)
    assert completeness == 95.0


def test_calculate_timeliness():
    calculator = DataQualityCalculator()
    collections = [
        {"scheduled_time": 1000, "actual_time": 1100, "delay_threshold": 300},
        {"scheduled_time": 2000, "actual_time": 2050, "delay_threshold": 300},
    ]
    timeliness = calculator.calculate_timeliness(collections)
    assert timeliness == 100.0


def test_calculate_accuracy():
    calculator = DataQualityCalculator()
    collections = [
        {"validation_errors": 0},
        {"validation_errors": 0},
        {"validation_errors": 1},
    ]
    accuracy = calculator.calculate_accuracy(collections)
    assert accuracy == pytest.approx(66.67, rel=0.01)


def test_calculate_consistency():
    calculator = DataQualityCalculator()
    collections = [
        {"schema_violations": 0},
        {"schema_violations": 0},
    ]
    consistency = calculator.calculate_consistency(collections)
    assert consistency == 100.0


def test_calculate_success_rate():
    calculator = DataQualityCalculator()
    collections = [
        {"status": "success"},
        {"status": "success"},
        {"status": "failed"},
    ]
    success_rate = calculator.calculate_success_rate(collections)
    assert success_rate == pytest.approx(66.67, rel=0.01)


def test_calculate_avg_latency():
    calculator = DataQualityCalculator()
    collections = [
        {"start_time": 1000, "end_time": 1100},
        {"start_time": 2000, "end_time": 2150},
    ]
    avg_latency = calculator.calculate_avg_latency(collections)
    assert avg_latency == 125.0


def test_calculate_error_rate():
    calculator = DataQualityCalculator()
    collections = [
        {"status": "success"},
        {"status": "failed"},
        {"status": "failed"},
    ]
    error_rate = calculator.calculate_error_rate(collections)
    assert error_rate == pytest.approx(66.67, rel=0.01)


def test_calculate_all_metrics():
    calculator = DataQualityCalculator()
    collections = [
        {
            "expected_count": 100,
            "actual_count": 95,
            "scheduled_time": 1000,
            "actual_time": 1100,
            "delay_threshold": 300,
            "validation_errors": 0,
            "schema_violations": 0,
            "status": "success",
            "start_time": 1000,
            "end_time": 1100,
        }
    ]
    metrics = calculator.calculate_all_metrics(collections)
    assert "completeness" in metrics
    assert "timeliness" in metrics
    assert "accuracy" in metrics


def test_calculate_availability():
    calculator = DataSourceHealthCalculator()
    records = [
        {"status": "available"},
        {"status": "available"},
        {"status": "error"},
    ]
    availability = calculator.calculate_availability(records)
    assert availability == pytest.approx(66.67, rel=0.01)


def test_calculate_response_time():
    calculator = DataSourceHealthCalculator()
    records = [
        {"response_time": 100},
        {"response_time": 200},
    ]
    response_time = calculator.calculate_response_time(records)
    assert response_time == 150.0


def test_calculate_error_rate_health():
    calculator = DataSourceHealthCalculator()
    records = [
        {"status": "available"},
        {"status": "error"},
    ]
    error_rate = calculator.calculate_error_rate(records)
    assert error_rate == 50.0


def test_calculate_freshness():
    calculator = DataSourceHealthCalculator()
    import time
    now = time.time()
    records = [
        {"last_update_time": now - 3600, "freshness_threshold": 24},
        {"last_update_time": now - 7200, "freshness_threshold": 24},
    ]
    freshness = calculator.calculate_freshness(records)
    assert freshness > 90.0


def test_calculate_coverage():
    calculator = DataSourceHealthCalculator()
    records = [
        {"expected_symbols": 100, "actual_symbols": 95},
        {"expected_symbols": 200, "actual_symbols": 190},
    ]
    coverage = calculator.calculate_coverage(records)
    assert coverage == 95.0
