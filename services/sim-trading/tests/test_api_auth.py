"""
TASK-0067: sim-trading API 认证测试

与 data/backtest/decision 三端保持一致的 5 项认证测试：
1. 空 key 时仅本机请求放行
2. 有 key 但请求未带 key 时拒绝
3. 有 key 且请求带正确 key 时通过
4. health 端点免认证
5. 有 key 但请求带错误 key 时拒绝
"""
import asyncio
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request


@pytest.fixture
def client_no_key():
    """环境变量中无 SIM_API_KEY，本机测试客户端应放行。"""
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
    """测试 1: 空 key 时，本机请求仍可用于本地开发。"""
    response = client_no_key.get("/api/v1/status")
    assert response.status_code in {200, 404}, "本机空 key 请求应放行（404 表示路由不存在，但未被认证拦截）"


def test_no_key_rejects_remote_request():
    """测试 1b: 空 key 时，远端请求必须被锁死。"""
    with patch.dict(os.environ, {"SIM_API_KEY": "", "JBT_ENV": "development"}, clear=False):
        import importlib
        import src.main
        importlib.reload(src.main)

        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/status",
                "headers": [],
                "client": ("192.168.31.233", 64064),
                "server": ("testserver", 80),
                "scheme": "http",
                "query_string": b"",
                "root_path": "",
                "http_version": "1.1",
            }
        )

        with pytest.raises(Exception) as exc_info:
            asyncio.run(src.main._verify_api_key(request, api_key=None))

        exc = exc_info.value
        assert getattr(exc, "status_code", None) == 503
        assert "remote access is locked" in getattr(exc, "detail", "")


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
