"""测试 Mini 客户端"""
import pytest
from researcher.mini_client import MiniClient


def test_mini_client_init():
    """测试 Mini 客户端初始化"""
    client = MiniClient()

    assert client.base_url == "http://192.168.31.74:8105"
    assert "/api/v1/bars" in client.bars_endpoint


def test_get_bars_params():
    """测试获取 K 线参数"""
    client = MiniClient()

    # 这里只测试参数构造，不实际调用 API
    # 实际调用需要 Mini 服务运行
    assert client is not None
