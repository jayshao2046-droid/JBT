"""测试报告生成器"""
import pytest
from researcher.report_generator import ReportGenerator
import multiprocessing as mp


def test_report_generator_schedules():
    """测试报告时段配置"""
    stop_event = mp.Event()

    generator = ReportGenerator(stop_event)

    # 验证时段数量
    assert len(generator.schedules) == 4

    # 验证时段结构
    for schedule in generator.schedules:
        assert "hour" in schedule
        assert "minute" in schedule
        assert "segment" in schedule

    # 验证时段名称
    segments = [s["segment"] for s in generator.schedules]
    assert "盘前" in segments
    assert "午间" in segments
    assert "盘后" in segments
    assert "夜盘收盘" in segments
