"""
pytest 配置文件 - 提供统一的测试 fixtures
"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """默认测试客户端 - 无认证（SIM_API_KEY 为空）"""
    with patch.dict(os.environ, {"SIM_API_KEY": ""}, clear=False):
        import importlib
        import src.main
        importlib.reload(src.main)
        from src.main import app
        yield TestClient(app)


@pytest.fixture
def authed_client():
    """带认证的测试客户端 - 自动添加 X-API-Key header"""
    test_key = "test-sim-key-12345"
    with patch.dict(os.environ, {"SIM_API_KEY": test_key}, clear=False):
        import importlib
        import src.main
        importlib.reload(src.main)
        from src.main import app

        class AuthedTestClient(TestClient):
            def request(self, method, url, **kwargs):
                headers = kwargs.get("headers", {})
                headers["X-API-Key"] = test_key
                kwargs["headers"] = headers
                return super().request(method, url, **kwargs)

        yield AuthedTestClient(app)
