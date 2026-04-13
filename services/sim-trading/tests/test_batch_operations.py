# Tests for batch operations (SIMWEB-01 P1-3)

import pytest
from src.ledger.service import LedgerService


class TestBatchOperations:
    """测试批量操作功能"""

    def test_ledger_equity_history(self):
        """测试权益历史记录"""
        ledger = LedgerService()

        # 记录权益快照
        ledger.record_equity_snapshot(100000.0)
        ledger.record_equity_snapshot(105000.0)
        ledger.record_equity_snapshot(103000.0)

        # 获取历史
        history = ledger.get_equity_history()
        assert len(history) == 3
        assert history[0]["equity"] == 100000.0
        assert history[1]["equity"] == 105000.0
        assert history[2]["equity"] == 103000.0

    def test_ledger_equity_history_with_time_range(self):
        """测试按时间范围查询权益历史"""
        from datetime import datetime, timedelta

        ledger = LedgerService()

        now = datetime.now()
        ledger.record_equity_snapshot(100000.0)
        ledger.record_equity_snapshot(105000.0)

        # 查询最近 1 小时
        start_time = now - timedelta(hours=1)
        history = ledger.get_equity_history(start_time=start_time)
        assert len(history) >= 2

    def test_ledger_equity_history_limit(self):
        """测试权益历史数据量限制"""
        ledger = LedgerService()

        # 记录大量数据
        for i in range(100):
            ledger.record_equity_snapshot(100000.0 + i * 100)

        history = ledger.get_equity_history()
        assert len(history) == 100
        assert len(ledger._equity_history) <= 50000  # 不超过限制
