"""TASK-0119 批次 A — data 服务安全测试。

验证 P0 高危漏洞修复：
1. P0-1: API 认证绕过防护
2. P0-2: 命令注入防护
3. P0-3: 审计日志记录
4. P1-4: 飞书 Token 泄露防护
5. P1-7: Tushare Token 安全读取
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def test_api_key_not_configured_rejects_protected_endpoints(monkeypatch):
    """P0-1: 未配置 API Key 时，保护端点应返回 503。"""
    monkeypatch.delenv("DATA_API_KEY", raising=False)

    # 重新导入以应用环境变量更改
    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    # 公开端点应正常访问
    response = client.get("/health")
    assert response.status_code == 200

    # 保护端点应返回 503
    response = client.get("/api/v1/symbols")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_api_key_configured_accepts_valid_key(monkeypatch, tmp_path):
    """P0-1: 配置 API Key 后，有效密钥应通过验证。"""
    test_key = "test-api-key-12345"
    monkeypatch.setenv("DATA_API_KEY", test_key)
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))

    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    # 带有效 API Key 的请求应通过
    response = client.get("/api/v1/symbols", headers={"X-API-Key": test_key})
    assert response.status_code == 200


def test_api_key_configured_rejects_invalid_key(monkeypatch, tmp_path):
    """P0-1: 配置 API Key 后，无效密钥应被拒绝。"""
    test_key = "test-api-key-12345"
    monkeypatch.setenv("DATA_API_KEY", test_key)
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))

    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    # 无 API Key 的请求应被拒绝
    response = client.get("/api/v1/symbols")
    assert response.status_code == 403

    # 错误 API Key 的请求应被拒绝
    response = client.get("/api/v1/symbols", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403


def test_ops_restart_collector_validates_plist_id_format(monkeypatch, tmp_path):
    """P0-2: ops 端点应严格验证 plist_id 格式，防止命令注入。"""
    ops_secret = "test-ops-secret"
    monkeypatch.setenv("DATA_OPS_SECRET", ops_secret)
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))

    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    # 白名单中的合法采集器
    response = client.post(
        "/api/v1/ops/restart-collector?collector=data_scheduler",
        headers={"X-Ops-Token": ops_secret}
    )
    # 可能返回 404（plist 不存在）或 200（成功），但不应是 400（格式错误）
    assert response.status_code in (200, 404, 504)

    # 不在白名单中的采集器应返回 422
    response = client.post(
        "/api/v1/ops/restart-collector?collector=malicious_collector",
        headers={"X-Ops-Token": ops_secret}
    )
    assert response.status_code == 422
    assert "unknown collector" in response.json()["detail"]


def test_ops_restart_collector_requires_valid_token(monkeypatch, tmp_path):
    """P0-2: ops 端点应验证操作令牌。"""
    ops_secret = "test-ops-secret"
    monkeypatch.setenv("DATA_OPS_SECRET", ops_secret)
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))

    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    # 无令牌应被拒绝
    response = client.post("/api/v1/ops/restart-collector?collector=data_scheduler")
    assert response.status_code == 403

    # 错误令牌应被拒绝
    response = client.post(
        "/api/v1/ops/restart-collector?collector=data_scheduler",
        headers={"X-Ops-Token": "wrong-token"}
    )
    assert response.status_code == 403


def test_ops_restart_collector_logs_audit_trail(monkeypatch, tmp_path, caplog):
    """P0-3: ops 端点应记录审计日志。"""
    ops_secret = "test-ops-secret"
    monkeypatch.setenv("DATA_OPS_SECRET", ops_secret)
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))

    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    with caplog.at_level("INFO"):
        response = client.post(
            "/api/v1/ops/restart-collector?collector=data_scheduler",
            headers={"X-Ops-Token": ops_secret}
        )

    # 应记录审计日志（包含调用者信息）
    assert any("OPS: restart_collector called by" in record.message for record in caplog.records)


def test_feishu_card_no_token_in_url():
    """P1-4: 飞书卡片按钮 URL 不应包含敏感 token。"""
    from services.data.src.notify.card_templates import alert_p0_with_buttons

    card = alert_p0_with_buttons(
        title="测试告警",
        body_md="测试内容",
        source_name="test_collector",
        ops_base_url="http://localhost:8105",
        ops_token="secret-token-12345"
    )

    # 检查卡片中的所有 URL
    card_str = str(card)
    assert "secret-token" not in card_str
    assert "token=" not in card_str.lower()

    # 验证按钮 URL 格式正确
    actions = card["card"]["elements"][1]["actions"]
    restart_button = actions[0]
    assert "collector=" in restart_button["url"]
    assert "token" not in restart_button["url"].lower()


def test_tushare_collector_reads_token_from_env_only(monkeypatch):
    """P1-7: Tushare 采集器应仅从环境变量读取 token。"""
    test_token = "test-tushare-token-12345"
    monkeypatch.setenv("TUSHARE_TOKEN", test_token)

    from services.data.src.collectors.tushare_full_collector import TushareFullCollector

    collector = TushareFullCollector(config={})
    assert collector.token == test_token


def test_tushare_collector_no_file_read_attempt(monkeypatch, tmp_path):
    """P1-7: Tushare 采集器不应尝试读取 .env 文件。"""
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)

    # 创建一个 .env 文件（不应被读取）
    env_file = tmp_path / ".env"
    env_file.write_text("TUSHARE_TOKEN=file-token-should-not-be-used")

    from services.data.src.collectors.tushare_full_collector import TushareFullCollector

    collector = TushareFullCollector(config={})
    # Token 应为空，而不是从文件读取
    assert collector.token == ""


def test_public_paths_accessible_without_auth(monkeypatch, tmp_path):
    """验证公开路径无需认证即可访问。"""
    monkeypatch.setenv("DATA_API_KEY", "test-key")
    monkeypatch.setenv("DATA_STORAGE_ROOT", str(tmp_path))

    import importlib
    import services.data.src.main as main_module
    importlib.reload(main_module)

    client = TestClient(main_module.app)

    # 公开路径应无需 API Key
    public_paths = [
        "/health",
        "/api/v1/health",
        "/api/v1/version",
    ]

    for path in public_paths:
        response = client.get(path)
        assert response.status_code == 200, f"Public path {path} should be accessible"
