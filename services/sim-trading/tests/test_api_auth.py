"""
TASK-0067: sim-trading API 认证测试

与 data/backtest/decision 三端保持一致的 5 项认证测试：
1. 空 key 时放行所有请求
2. 有 key 但请求未带 key 时拒绝
3. 有 key 且请求带正确 key 时通过
4. health 端点免认证
5. 有 key 但请求带错误 key 时拒绝
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_no_key():
    """环境变量中无 SIM_API_KEY，认证应放行。"""
    with patch.dict(os.environ, {"SIM_API_KEY": ""}, clear=False):
        # 重新导入以应用新的环境变量
        import importlib
        import src.main
        importlib.reload(src.main)
        from src.main import app
        yield TestClient(app)


@pytest.fixture
def client_with_key():
    """环境变量中有 SIM_API_KEY，认证应生效。"""
    with patch.dict(os.environ, {"SIM_API_KEY": "test-sim-key-12345"}, clear=False):
        import importlib
        import src.main
        importlib.reload(src.main)
        from src.main import app
        yield TestClient(app)


def test_no_key_allows_all(client_no_key):
    """测试 1: 空 key 时放行所有请求。"""
    response = client_no_key.get("/api/v1/status")
    assert response.status_code in {200, 404}, "空 key 时应放行请求（404 表示路由不存在，但未被认证拦截）"


def test_with_key_no_header_rejects(client_with_key):
    """测试 2: 有 key 但请求未带 key 时拒绝。"""
    response = client_with_key.get("/api/v1/status")
    assert response.status_code == 403, "有 key 但请求未带 key 时应返回 403"
    assert "invalid or missing API key" in response.json().get("detail", "")


def test_with_key_correct_header_passes(client_with_key):
    """测试 3: 有 key 且请求带正确 key 时通过。"""
    response = client_with_key.get("/api/v1/status", headers={"X-API-Key": "test-sim-key-12345"})
    assert response.status_code in {200, 404}, "正确 key 应通过认证（404 表示路由不存在，但已通过认证）"


def test_health_endpoint_public(client_with_key):
    """测试 4: health 端点免认证。"""
    response = client_with_key.get("/health")
    assert response.status_code == 200, "/health 应免认证"
    assert response.json().get("status") == "ok"


def test_with_key_wrong_header_rejects(client_with_key):
    """测试 5: 有 key 但请求带错误 key 时拒绝。"""
    response = client_with_key.get("/api/v1/status", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403, "错误 key 应返回 403"
    assert "invalid or missing API key" in response.json().get("detail", "")
