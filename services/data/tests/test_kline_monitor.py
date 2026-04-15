"""测试 K 线监控器"""
import pytest
from researcher.kline_monitor import KlineMonitor
from researcher.session_detector import get_current_session
import multiprocessing as mp


def test_kline_monitor_symbols():
    """测试品种列表"""
    queue = mp.Queue()
    stop_event = mp.Event()

    monitor = KlineMonitor(queue, stop_event)

    # 验证品种数量
    assert len(monitor.symbols) == 35

    # 验证包含主要品种
    assert "IF" in monitor.symbols
    assert "RB" in monitor.symbols
    assert "CU" in monitor.symbols


def test_session_detector():
    """测试时段检测"""
    session = get_current_session()

    assert session in ["domestic_day", "domestic_night", "overnight"]
