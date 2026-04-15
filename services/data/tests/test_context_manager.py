"""测试上下文管理器"""
import pytest
from researcher.context_manager import ContextManager
import tempfile
import os


def test_add_and_get_analysis():
    """测试添加和获取分析"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_context.db")
        manager = ContextManager(db_path)

        # 添加分析
        manager.add_analysis(
            symbol="RB",
            analysis_type="kline_analysis",
            content="螺纹钢上涨3%",
            segment="盘前"
        )

        # 获取分析
        results = manager.get_recent_analysis("RB", hours=24, limit=10)

        assert len(results) == 1
        assert results[0]["analysis_type"] == "kline_analysis"
        assert results[0]["content"] == "螺纹钢上涨3%"


def test_get_segment_summary():
    """测试获取时段汇总"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_context.db")
        manager = ContextManager(db_path)

        # 添加多个分析
        manager.add_analysis("RB", "kline_analysis", "内容1", "盘前")
        manager.add_analysis("CU", "news_analysis", "内容2", "盘前")

        # 获取时段汇总
        results = manager.get_segment_summary("盘前")

        assert len(results) == 2
