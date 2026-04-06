# TASK-0010-C: risk hooks skeleton test

import pytest

from src.risk.guards import RiskGuards


def test_risk_guards_instantiation():
    """RiskGuards 类可以被实例化，不触发 NotImplementedError。"""
    guards = RiskGuards()
    assert guards is not None


def test_risk_guards_has_reduce_only():
    """RiskGuards 存在 check_reduce_only 方法。"""
    guards = RiskGuards()
    assert hasattr(guards, "check_reduce_only")


def test_risk_guards_has_disaster_stop():
    """RiskGuards 存在 check_disaster_stop 方法。"""
    guards = RiskGuards()
    assert hasattr(guards, "check_disaster_stop")


def test_risk_guards_has_emit_alert():
    """RiskGuards 存在 emit_alert 方法。"""
    guards = RiskGuards()
    assert hasattr(guards, "emit_alert")


# TODO: 断网/断数据源下本地缓存行为验证
# 验收点（TASK-0013/TASK-0017 补充预审冻结）：
#   1. 断网时读取最近一次本地快照进行安全降级判断
#   2. 或安全拒绝开仓进入 Fail-Safe
#   3. 不得 crash，不得产出错误信号
#   4. 缓存路径：CACHE_SNAPSHOT_PATH（来自 .env.example）
#   5. 缓存过期判断：CACHE_STALE_SECONDS（来自 .env.example）
def test_offline_cache_behavior_placeholder():
    """断网/断数据源下缓存行为验证占位测试（当前 skip，等待 C 完整实现）。"""
    pytest.skip("offline cache behavior validation — pending TASK-0017 deployment pre-validation")
