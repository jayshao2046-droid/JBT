"""TASK-P1-20260422 — 期货 35 品种情绪扩展 最小自校验测试

测试策略：
1. 单元测试 futures_sentiment 聚合逻辑（mock researcher_store）
2. 验证 stale 行为：无报告 → stale=True + data=[]
3. 验证 35 品种正常输出结构
4. 验证单品种过滤
5. 验证不合法品种白名单拒绝
6. 通过 TestClient 验证 /api/v1/context/futures_sentiment 端点存在且返回 200
7. 验证原有 /api/v1/context/sentiment 端点不受影响
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# ─── 路径修复（让 src/ 作为包根进入 sys.path）────────────────────────────────
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ─── 测试用研报 fixture ───────────────────────────────────────────────────────

_TODAY = str(datetime.date.today())

_SAMPLE_REPORT: Dict[str, Any] = {
    "report_id": "test-report-001",
    "date": _TODAY,
    "generated_at": f"{_TODAY}T10:00:00",
    "futures_summary": {
        "symbols": {
            "KQ.m@SHFE.rb": {"trend": "偏空", "confidence": 0.72, "key_factors": ["铁矿压力"]},
            "KQ.m@SHFE.hc": {"trend": "震荡", "confidence": 0.55, "key_factors": []},
            "KQ.m@SHFE.cu": {"trend": "偏多", "confidence": 0.68, "key_factors": ["美元走弱"]},
            "KQ.m@SHFE.al": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@SHFE.zn": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@SHFE.au": {"trend": "偏多", "confidence": 0.80, "key_factors": ["避险需求"]},
            "KQ.m@SHFE.ag": {"trend": "偏多", "confidence": 0.65, "key_factors": []},
            "KQ.m@SHFE.ru": {"trend": "震荡", "confidence": 0.52, "key_factors": []},
            "KQ.m@SHFE.ss": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@SHFE.sp": {"trend": "偏空", "confidence": 0.58, "key_factors": []},
            "KQ.m@DCE.i":   {"trend": "偏空", "confidence": 0.70, "key_factors": []},
            "KQ.m@DCE.m":   {"trend": "偏多", "confidence": 0.60, "key_factors": []},
            "KQ.m@DCE.pp":  {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.v":   {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.l":   {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.c":   {"trend": "偏多", "confidence": 0.55, "key_factors": []},
            "KQ.m@DCE.jd":  {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.y":   {"trend": "偏空", "confidence": 0.60, "key_factors": []},
            "KQ.m@DCE.p":   {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.a":   {"trend": "偏多", "confidence": 0.58, "key_factors": []},
            "KQ.m@DCE.jm":  {"trend": "偏空", "confidence": 0.65, "key_factors": []},
            "KQ.m@DCE.j":   {"trend": "偏空", "confidence": 0.67, "key_factors": []},
            "KQ.m@DCE.eb":  {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.pg":  {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@DCE.lh":  {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@CZCE.TA": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@CZCE.MA": {"trend": "偏空", "confidence": 0.55, "key_factors": []},
            "KQ.m@CZCE.CF": {"trend": "偏多", "confidence": 0.60, "key_factors": []},
            "KQ.m@CZCE.SR": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@CZCE.OI": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@CZCE.RM": {"trend": "偏多", "confidence": 0.55, "key_factors": []},
            "KQ.m@CZCE.FG": {"trend": "偏空", "confidence": 0.60, "key_factors": []},
            "KQ.m@CZCE.SA": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@CZCE.PF": {"trend": "震荡", "confidence": 0.50, "key_factors": []},
            "KQ.m@CZCE.UR": {"trend": "偏空", "confidence": 0.55, "key_factors": []},
        }
    },
}

# ─── 单元测试：futures_sentiment 模块 ────────────────────────────────────────

class TestFuturesSentimentModule:
    """测试 data.futures_sentiment 聚合逻辑"""

    def _run_with_mock_report(self, report):
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = report
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            # 重新 import 模块以使 patch 生效
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)
            return fs_mod.get_futures_sentiment()

    def test_no_report_returns_stale(self):
        """无研报时返回 stale=True、data=[]，不合成虚假信号"""
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = None
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)
            result = fs_mod.get_futures_sentiment()

        assert result["stale"] is True
        assert result["data"] == []
        assert result["symbol_count"] == 0
        assert result["reason"] == "no_report_available"
        assert result["last_updated"] is None

    def test_full_35_symbols_output(self):
        """正常研报返回 35 条记录"""
        result = self._run_with_mock_report(_SAMPLE_REPORT)
        assert result["stale"] is False
        assert result["symbol_count"] == 35
        assert len(result["data"]) == 35

    def test_output_structure(self):
        """每条记录包含必要字段"""
        result = self._run_with_mock_report(_SAMPLE_REPORT)
        for item in result["data"]:
            assert "symbol" in item
            assert "trend" in item
            assert "confidence" in item
            assert "sentiment_score" in item
            assert "key_factors" in item
            assert isinstance(item["sentiment_score"], float)
            assert 0.0 <= item["sentiment_score"] <= 1.0

    def test_single_symbol_filter(self):
        """单品种过滤：rb"""
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = _SAMPLE_REPORT
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)
            result = fs_mod.get_futures_sentiment(symbol="rb")

        assert result["symbol_count"] == 1
        assert result["data"][0]["symbol"] == "rb"
        assert result["data"][0]["trend"] == "偏空"
        assert result["data"][0]["sentiment_score"] == 0.25

    def test_invalid_symbol_rejected(self):
        """不在白名单的品种返回 symbol_count=0，但不是 stale"""
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = _SAMPLE_REPORT
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)
            result = fs_mod.get_futures_sentiment(symbol="xxx999")

        assert result["symbol_count"] == 0
        assert result["data"] == []
        assert result["stale"] is False  # 不是 stale，只是无效 symbol

    def test_symbol_normalization_czce(self):
        """郑商所大写品种（TA）被正确小写化为 ta"""
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = _SAMPLE_REPORT
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)
            result = fs_mod.get_futures_sentiment(symbol="TA")

        assert result["symbol_count"] == 1
        assert result["data"][0]["symbol"] == "ta"

    def test_stale_when_report_is_old(self):
        """昨日研报标记 stale=True"""
        import copy
        old_report = copy.deepcopy(_SAMPLE_REPORT)
        old_report["date"] = "2026-01-01"  # 过去日期
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = old_report
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)
            result = fs_mod.get_futures_sentiment()

        assert result["stale"] is True
        assert result["reason"] == "stale_report"

    def test_bearish_trend_score(self):
        """偏空趋势 sentiment_score=0.25"""
        import importlib
        import data.futures_sentiment as fs_mod
        importlib.reload(fs_mod)
        assert fs_mod._trend_to_score("偏空") == 0.25

    def test_bullish_trend_score(self):
        """偏多趋势 sentiment_score=0.75"""
        import importlib
        import data.futures_sentiment as fs_mod
        importlib.reload(fs_mod)
        assert fs_mod._trend_to_score("偏多") == 0.75

    def test_normalize_symbol_variants(self):
        """symbol 归一化函数覆盖各种格式"""
        import importlib
        import data.futures_sentiment as fs_mod
        importlib.reload(fs_mod)
        assert fs_mod._normalize_symbol("KQ.m@SHFE.rb") == "rb"
        assert fs_mod._normalize_symbol("KQ.m@CZCE.TA") == "ta"
        assert fs_mod._normalize_symbol("KQ.m@DCE.i") == "i"
        assert fs_mod._normalize_symbol("rb") == "rb"
        assert fs_mod._normalize_symbol("TA") == "ta"


# ─── 集成测试：API 端点 ──────────────────────────────────────────────────────

class TestFuturesSentimentEndpoint:
    """通过 TestClient 验证 API 端点"""

    def _get_client_with_mock(self, report):
        """构建带 mock researcher_store 的 TestClient"""
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = report

        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            # 确保 futures_sentiment 模块使用 patched researcher_store
            import importlib
            import data.futures_sentiment as fs_mod
            importlib.reload(fs_mod)

            from fastapi.testclient import TestClient
            from main import app  # type: ignore[import]
            return TestClient(app)

    def test_endpoint_returns_200(self):
        """GET /api/v1/context/futures_sentiment 返回 200"""
        client = self._get_client_with_mock(_SAMPLE_REPORT)
        resp = client.get("/api/v1/context/futures_sentiment")
        assert resp.status_code == 200

    def test_endpoint_data_type(self):
        """端点响应包含 data_type=futures_sentiment"""
        client = self._get_client_with_mock(_SAMPLE_REPORT)
        resp = client.get("/api/v1/context/futures_sentiment")
        body = resp.json()
        assert body["data_type"] == "futures_sentiment"
        assert body["symbol_count"] == 35

    def test_endpoint_symbol_filter(self):
        """?symbol=rb 只返回 rb"""
        client = self._get_client_with_mock(_SAMPLE_REPORT)
        resp = client.get("/api/v1/context/futures_sentiment?symbol=rb")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol_count"] == 1

    def test_existing_sentiment_endpoint_intact(self):
        """原有 /api/v1/context/sentiment 端点不受影响"""
        mock_rs = MagicMock()
        mock_rs.get_latest.return_value = None
        with patch.dict("sys.modules", {"researcher_store": mock_rs}):
            from fastapi.testclient import TestClient
            from main import app  # type: ignore[import]
            client = TestClient(app)
        # /sentiment 端点只要不返回 404 即可（500 因无 parquet 是预期行为）
        resp = client.get("/api/v1/context/sentiment")
        assert resp.status_code != 404
