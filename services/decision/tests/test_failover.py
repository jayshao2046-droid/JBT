"""测试 FailoverManager 备用方案功能。

TASK-0025 / Token: tok-e2c4419a
"""
import pytest
from unittest.mock import Mock, patch
import os


def test_failover_state_machine_normal_to_failover():
    """测试状态机转换：NORMAL → FAILOVER。"""
    from src.publish.failover import FailoverManager, FailoverState

    manager = FailoverManager(
        sim_trading_url="http://localhost:8101",
        probe_interval=1,
        fail_threshold=3,
    )

    assert manager.get_state() == FailoverState.NORMAL

    # Mock health_check 返回 False
    with patch.object(manager, 'check_health', return_value=False):
        # 第 1 次失败
        manager.probe_and_update_state()
        assert manager.get_state() == FailoverState.NORMAL

        # 第 2 次失败
        manager._last_probe_time = 0  # 重置探测时间
        manager.probe_and_update_state()
        assert manager.get_state() == FailoverState.NORMAL

        # 第 3 次失败 → 转换到 FAILOVER
        manager._last_probe_time = 0
        manager.probe_and_update_state()
        assert manager.get_state() == FailoverState.FAILOVER


def test_failover_state_machine_failover_to_recovering():
    """测试状态机转换：FAILOVER → RECOVERING。"""
    from src.publish.failover import FailoverManager, FailoverState

    manager = FailoverManager(fail_threshold=1, recover_threshold=2)
    manager._state = FailoverState.FAILOVER

    # Mock health_check 返回 True
    with patch.object(manager, 'check_health', return_value=True):
        manager.probe_and_update_state()
        assert manager.get_state() == FailoverState.RECOVERING


def test_failover_state_machine_recovering_to_normal():
    """测试状态机转换：RECOVERING → NORMAL。"""
    from src.publish.failover import FailoverManager, FailoverState

    manager = FailoverManager(recover_threshold=2, probe_interval=1)
    manager._state = FailoverState.RECOVERING
    manager._consecutive_successes = 1

    # Mock health_check 返回 True
    with patch.object(manager, 'check_health', return_value=True):
        manager._last_probe_time = 0
        manager.probe_and_update_state()
        assert manager.get_state() == FailoverState.NORMAL


def test_close_position_rejects_open():
    """测试仅平仓约束：开仓请求被拒绝。"""
    from src.publish.failover import FailoverManager, FailoverState

    manager = FailoverManager()
    manager._state = FailoverState.FAILOVER

    # 尝试开仓
    result = manager.close_position(symbol="rb2505", volume=1, direction="BUY")

    assert result["success"] is False
    assert result["reason"] == "failover_mode_open_rejected"
    assert "禁止开仓" in result["message"]


def test_close_position_accepts_close():
    """测试仅平仓约束：平仓请求被接受。"""
    from src.publish.failover import FailoverManager, FailoverState

    # 设置 SimNow 凭证
    os.environ["SIMNOW_BROKER_ID"] = "9999"
    os.environ["SIMNOW_USER_ID"] = "test_user"
    os.environ["SIMNOW_PASSWORD"] = "test_pass"
    os.environ["SIMNOW_TD_FRONT"] = "tcp://180.168.146.187:10130"

    manager = FailoverManager()
    manager._state = FailoverState.FAILOVER

    # 平仓请求
    result = manager.close_position(symbol="rb2505", volume=1, direction="CLOSE_TODAY")

    assert result["success"] is True
    assert result["reason"] == "failover_close_submitted"
    assert "order_id" in result


def test_health_check_success():
    """测试健康检查成功。"""
    from src.publish.failover import FailoverManager

    manager = FailoverManager(sim_trading_url="http://localhost:8101")

    # Mock urllib.request.urlopen
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        assert manager.check_health() is True


def test_health_check_failure():
    """测试健康检查失败。"""
    from src.publish.failover import FailoverManager
    import urllib.error

    manager = FailoverManager(sim_trading_url="http://localhost:8101")

    # Mock urllib.request.urlopen 抛出异常
    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Connection refused")):
        assert manager.check_health() is False


def test_credentials_from_env():
    """测试凭证从环境变量读取（不硬编码）。"""
    from src.publish.failover import FailoverManager

    os.environ["SIMNOW_BROKER_ID"] = "test_broker"
    os.environ["SIMNOW_USER_ID"] = "test_user"
    os.environ["SIMNOW_PASSWORD"] = "test_password"
    os.environ["SIMNOW_TD_FRONT"] = "tcp://test:10130"

    manager = FailoverManager()

    assert manager._simnow_broker_id == "test_broker"
    assert manager._simnow_user_id == "test_user"
    assert manager._simnow_password == "test_password"
    assert manager._simnow_td_front == "tcp://test:10130"


def test_close_position_requires_credentials():
    """测试平仓操作需要完整凭证。"""
    from src.publish.failover import FailoverManager, FailoverState

    # 清空凭证
    os.environ.pop("SIMNOW_BROKER_ID", None)
    os.environ.pop("SIMNOW_USER_ID", None)

    manager = FailoverManager()
    manager._state = FailoverState.FAILOVER

    result = manager.close_position(symbol="rb2505", volume=1, direction="CLOSE_TODAY")

    assert result["success"] is False
    assert result["reason"] == "simnow_credentials_missing"


def test_sim_adapter_health_check():
    """测试 SimTradingAdapter.health_check() 方法。"""
    from src.publish.sim_adapter import SimTradingAdapter

    adapter = SimTradingAdapter()

    # Mock urllib.request.urlopen
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        assert adapter.health_check() is True
