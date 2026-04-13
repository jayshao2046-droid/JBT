"""数据服务集成测试"""
from __future__ import annotations

import pytest


def test_data_service_imports():
    """测试所有模块可以正常导入"""
    from src.data.validator import DataSourceValidator
    from src.data.progress_tracker import ProgressTracker
    from src.stats.quality import DataQualityCalculator
    from src.stats.health import DataSourceHealthCalculator
    from src.stats.optimizer import CollectionOptimizer
    from src.queue.manager import QueueManager

    assert DataSourceValidator is not None
    assert ProgressTracker is not None
    assert DataQualityCalculator is not None
    assert DataSourceHealthCalculator is not None
    assert CollectionOptimizer is not None
    assert QueueManager is not None


def test_validator_integration():
    """测试验证器集成"""
    from src.data.validator import DataSourceValidator

    validator = DataSourceValidator()
    config = {"token": "a" * 32}

    # 测试配置验证
    config_result = validator.validate_config("tushare", config)
    assert config_result["ok"] is True

    # 测试连接验证
    conn_result = validator.validate_connection("tushare", config)
    assert conn_result["ok"] is True

    # 测试权限验证
    perm_result = validator.validate_permissions("tushare", config)
    assert perm_result["ok"] is True


def test_quality_calculator_integration():
    """测试质量计算器集成"""
    from src.stats.quality import DataQualityCalculator

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
    assert len(metrics) == 7
    assert all(isinstance(v, float) for v in metrics.values())


def test_health_calculator_integration():
    """测试健康计算器集成"""
    from src.stats.health import DataSourceHealthCalculator
    import time

    calculator = DataSourceHealthCalculator()
    now = time.time()
    records = [
        {
            "status": "available",
            "response_time": 150,
            "last_update_time": now - 3600,
            "freshness_threshold": 24,
            "expected_symbols": 100,
            "actual_symbols": 95,
        }
    ]

    metrics = calculator.calculate_all_metrics(records)
    assert len(metrics) == 5
    assert all(isinstance(v, float) for v in metrics.values())


def test_optimizer_integration():
    """测试优化器集成"""
    from src.stats.optimizer import CollectionOptimizer

    optimizer = CollectionOptimizer()

    # 测试网格搜索
    param_grid = {"interval": [60, 300], "timeout": [10, 30]}
    results = optimizer.grid_search(param_grid, "success_rate")
    assert len(results) == 4

    # 测试自动调优
    current_params = {"interval": 300, "timeout": 30, "retry_count": 3}
    result = optimizer.auto_tune(current_params, "success_rate")
    assert "recommended_params" in result

    # 测试最佳实践
    best_practice = optimizer.recommend_best_practice("futures_minute")
    assert "recommended_params" in best_practice


def test_queue_manager_integration():
    """测试队列管理器集成"""
    from src.queue.manager import QueueManager

    manager = QueueManager()

    # 添加任务
    task_id = manager.add_task("collection", {"source": "test"}, priority=1)
    assert task_id is not None

    # 获取任务
    task = manager.get_task(task_id)
    assert task is not None
    assert task["status"] == "pending"

    # 开始任务
    success = manager.start_task(task_id)
    assert success is True

    # 完成任务
    success = manager.complete_task(task_id, success=True, result={"count": 100})
    assert success is True

    # 获取统计
    stats = manager.get_statistics()
    assert stats["total"] == 1
    assert stats["completed"] == 1


def test_progress_tracker_integration():
    """测试进度追踪器集成"""
    from src.data.progress_tracker import ProgressTracker

    tracker = ProgressTracker()

    # 开始采集
    tracker.start_collection("col-001", total_items=100)

    # 更新进度
    tracker.update_progress("col-001", completed_items=50, current_stage="处理中")

    # 获取进度
    progress = tracker.get_progress("col-001")
    assert progress is not None
    assert progress["progress_percent"] == 50.0

    # 完成采集
    tracker.complete_collection("col-001", success=True)
    progress = tracker.get_progress("col-001")
    assert progress["status"] == "completed"
