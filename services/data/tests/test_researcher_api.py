"""测试 — 研究员 API"""

import pytest
import sys
import os
import importlib
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
        with patch("api.routes.researcher_route._load_latest_report", return_value=None):
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


# ── 研报存档 API 测试（Batch B）──────────────────────────────────────────────

_SAMPLE_REPORT = {
    "report_id": "RPT-TEST-20260115-12-00-001",
    "date": "2026-01-15",
    "segment": "12-00",
    "hour": "12-00",
    "generated_at": "2026-01-15T12:00:00",
    "market_overview": "测试市场总览：螺纹钢偏强，铜价震荡",
    "symbols": {
        "rb": {"trend": "偏多", "confidence": 0.78, "news": []},
        "cu": {"trend": "震荡", "confidence": 0.52, "news": []},
    },
    "confidence": 0.72,
    "confidence_reason": "phi4 测试：信息来源充分",
}


class TestResearcherStoreAPI:
    """测试研报存档三端点 POST/GET/LIST"""

    def test_post_report_success(self, tmp_path, monkeypatch):
        """POST /api/v1/researcher/reports 存档成功"""
        import researcher_store as _rs
        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")

        response = client.post("/api/v1/researcher/reports", json=_SAMPLE_REPORT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["report_id"] == _SAMPLE_REPORT["report_id"]

    def test_get_latest_not_found(self, tmp_path, monkeypatch):
        """GET /api/v1/researcher/report/latest 404 when empty"""
        import researcher_store as _rs
        from researcher.config import ResearcherConfig

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(ResearcherConfig, "REPORTS_DIR", str(reports_dir))

        response = client.get("/api/v1/researcher/report/latest?date=1999-01-01")
        assert response.status_code == 404

    def test_get_latest_after_post(self, tmp_path, monkeypatch):
        """POST 后 GET /api/v1/researcher/report/latest 返回该研报"""
        import researcher_store as _rs
        from researcher.config import ResearcherConfig

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(ResearcherConfig, "REPORTS_DIR", str(reports_dir))

        client.post("/api/v1/researcher/reports", json=_SAMPLE_REPORT)
        resp = client.get(f"/api/v1/researcher/report/latest?date={_SAMPLE_REPORT['date']}")
        assert resp.status_code == 200
        assert resp.json()["report_id"] == _SAMPLE_REPORT["report_id"]

    def test_get_latest_falls_back_to_history(self, tmp_path, monkeypatch):
        """当日无报告时，latest 应回退到最近一份历史研报"""
        import researcher_store as _rs
        from researcher.config import ResearcherConfig

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        historical_report = {
            **_SAMPLE_REPORT,
            "report_id": "RPT-TEST-HISTORY-001",
            "date": "2026-01-14",
            "generated_at": "2026-01-14T12:00:00",
        }

        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(ResearcherConfig, "REPORTS_DIR", str(reports_dir))

        client.post("/api/v1/researcher/reports", json=historical_report)
        resp = client.get("/api/v1/researcher/report/latest")

        assert resp.status_code == 200
        assert resp.json()["report_id"] == historical_report["report_id"]

    def test_list_reports_empty(self, tmp_path, monkeypatch):
        """GET /api/v1/researcher/reports 空日期返回空列表"""
        import researcher_store as _rs
        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")

        response = client.get("/api/v1/researcher/reports?date=1999-12-31")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_reports_after_post(self, tmp_path, monkeypatch):
        """POST 后 GET /api/v1/researcher/reports 返回摘要列表"""
        import researcher_store as _rs
        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")

        client.post("/api/v1/researcher/reports", json=_SAMPLE_REPORT)
        resp = client.get(f"/api/v1/researcher/reports?date={_SAMPLE_REPORT['date']}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["report_id"] == _SAMPLE_REPORT["report_id"]
        assert items[0]["symbol_count"] == 2

    def test_status_resource_status_uses_probe_result(self):
        """/status 不再把资源状态硬编码为 true"""
        with patch(
            "api.routes.researcher_route._get_resource_status",
            return_value={"alienware_reachable": False, "ollama_available": True},
        ):
            response = client.get("/api/v1/researcher/status")

        assert response.status_code == 200
        assert response.json()["resource_status"] == {
            "alienware_reachable": False,
            "ollama_available": True,
        }

    def test_researcher_config_importable(self):
        """researcher.config 不应在导入阶段因 logger 未定义而失败"""
        mod = importlib.reload(importlib.import_module("researcher.config"))

        assert getattr(mod, "logger", None) is not None
        assert hasattr(mod.ResearcherConfig, "DAILY_KLINE_TRIGGER_HOUR")

    def test_post_idempotent(self, tmp_path, monkeypatch):
        """相同 report_id 二次 POST 应覆盖，列表中仍只有一条"""
        import researcher_store as _rs
        monkeypatch.setattr(_rs, "STORE_ROOT", tmp_path)
        monkeypatch.setattr(_rs, "DB_PATH", tmp_path / "test.db")

        client.post("/api/v1/researcher/reports", json=_SAMPLE_REPORT)
        updated = {**_SAMPLE_REPORT, "confidence": 0.90}
        client.post("/api/v1/researcher/reports", json=updated)
        resp = client.get(f"/api/v1/researcher/reports?date={_SAMPLE_REPORT['date']}")
        items = resp.json()
        assert len(items) == 1
        assert items[0]["confidence"] == pytest.approx(0.90, abs=0.01)
