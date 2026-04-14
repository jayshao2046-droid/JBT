"""测试 — 研究员 API"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 需要先导入 main 创建 app
from main import app

client = TestClient(app)


class TestResearcherAPI:
    """测试研究员 API"""

    def test_get_status(self):
        """测试获取状态"""
        response = client.get("/api/v1/researcher/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "next_schedule" in data

    def test_get_sources(self):
        """测试获取采集源列表"""
        response = client.get("/api/v1/researcher/sources")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_source(self):
        """测试创建采集源"""
        source = {
            "source_id": "test_source",
            "name": "测试源",
            "url_pattern": "https://example.com",
            "mode": "code",
            "parser": "article_list",
            "schedule": ["盘前"],
            "enabled": True,
            "priority": 5,
            "timeout": 30
        }

        response = client.post("/api/v1/researcher/sources", json=source)
        assert response.status_code == 200

        data = response.json()
        assert data["source_id"] == "test_source"

    def test_update_source(self):
        """测试更新采集源"""
        # 先创建
        source = {
            "source_id": "test_source_2",
            "name": "测试源2",
            "url_pattern": "https://example.com",
            "mode": "code",
            "parser": "article_list",
            "schedule": ["盘前"],
            "enabled": True,
            "priority": 5,
            "timeout": 30
        }
        client.post("/api/v1/researcher/sources", json=source)

        # 更新
        updates = {"priority": 10}
        response = client.put("/api/v1/researcher/sources/test_source_2", json=updates)
        assert response.status_code == 200

    def test_delete_source(self):
        """测试删除采集源"""
        # 先创建
        source = {
            "source_id": "test_source_3",
            "name": "测试源3",
            "url_pattern": "https://example.com",
            "mode": "code",
            "parser": "article_list",
            "schedule": ["盘前"],
            "enabled": True,
            "priority": 5,
            "timeout": 30
        }
        client.post("/api/v1/researcher/sources", json=source)

        # 删除
        response = client.delete("/api/v1/researcher/sources/test_source_3")
        assert response.status_code == 200

    def test_get_latest_report_not_found(self):
        """测试获取最新报告（无报告）"""
        with patch("api.routes.researcher_route.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            response = client.get("/api/v1/researcher/report/latest")
            assert response.status_code == 404

    def test_get_reports_by_date_not_found(self):
        """测试获取指定日期报告（无报告）"""
        response = client.get("/api/v1/researcher/report/2099-12-31")
        assert response.status_code == 404

    def test_trigger_research_invalid_segment(self):
        """测试手动触发（无效时段）"""
        response = client.post("/api/v1/researcher/trigger?segment=invalid")
        assert response.status_code == 400
