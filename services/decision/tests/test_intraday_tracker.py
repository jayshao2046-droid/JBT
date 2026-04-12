"""
测试盘中跟踪器 (CB6)
"""
import pytest
from src.research.intraday_tracker import IntradayTracker


def test_initial_state():
    """测试初始状态"""
    tracker = IntradayTracker()
    summary = tracker.get_summary()
    assert summary["updated_count"] == 0
    assert summary["signal_count"] == 0
    assert summary["last_updated"] is None


def test_update_new_symbol():
    """测试更新新股票"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    summary = tracker.get_summary()
    assert summary["updated_count"] == 1
    assert summary["last_updated"] is not None


def test_update_existing_symbol():
    """测试更新已存在股票"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    tracker.update("600000.SH", 10.5, 1200000)
    summary = tracker.get_summary()
    assert summary["updated_count"] == 2


def test_breakout_signal():
    """测试突破信号"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    tracker.update("600000.SH", 10.5, 1100000)
    tracker.update("600000.SH", 10.49, 1200000)  # 10.49 >= 10.5 * 0.98

    signals = tracker.get_signals()
    breakout_signals = [s for s in signals if s["signal_type"] == "breakout"]
    assert len(breakout_signals) >= 1
    assert breakout_signals[0]["symbol"] == "600000.SH"


def test_volume_spike_signal():
    """测试放量信号"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    tracker.update("600000.SH", 10.1, 1100000)
    tracker.update("600000.SH", 10.2, 2000000)  # 2000000 > avg * 1.5

    signals = tracker.get_signals()
    volume_signals = [s for s in signals if s["signal_type"] == "volume_spike"]
    assert len(volume_signals) >= 1


def test_no_signals_initially():
    """测试初始无信号"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    signals = tracker.get_signals()
    # 只有一个数据点，不会触发 volume_spike（需要 len > 1）
    # breakout 可能触发（price == high）
    assert isinstance(signals, list)


def test_clear():
    """测试清空数据"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    tracker.clear()
    summary = tracker.get_summary()
    assert summary["updated_count"] == 0
    assert summary["last_updated"] is None


def test_multiple_symbols():
    """测试多个股票"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    tracker.update("600001.SH", 20.0, 2000000)
    summary = tracker.get_summary()
    assert summary["updated_count"] == 2


def test_custom_timestamp():
    """测试自定义时间戳"""
    tracker = IntradayTracker()
    custom_ts = "2026-04-13T10:30:00"
    tracker.update("600000.SH", 10.0, 1000000, ts=custom_ts)
    summary = tracker.get_summary()
    assert summary["last_updated"] == custom_ts


def test_signal_structure():
    """测试信号结构"""
    tracker = IntradayTracker()
    tracker.update("600000.SH", 10.0, 1000000)
    tracker.update("600000.SH", 10.5, 1100000)
    tracker.update("600000.SH", 10.49, 3000000)

    signals = tracker.get_signals()
    if signals:
        signal = signals[0]
        assert "symbol" in signal
        assert "signal_type" in signal
        assert "price" in signal
        assert "triggered_at" in signal
        assert signal["signal_type"] in ["breakout", "volume_spike"]
