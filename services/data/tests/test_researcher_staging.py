"""测试 — 暂存区 + summarizer"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.staging import StagingManager
from researcher.summarizer import Summarizer
from researcher.models import StagingRecord, SymbolResearch


class TestStagingManager:
    """测试暂存区管理器"""

    def test_init_db(self, tmp_path):
        """测试数据库初始化"""
        with patch("researcher.staging.ResearcherConfig.STAGING_DB", str(tmp_path / "test.db")):
            manager = StagingManager()
            assert manager.db_path == str(tmp_path / "test.db")

    def test_update_and_get_record(self, tmp_path):
        """测试记录更新和读取"""
        with patch("researcher.staging.ResearcherConfig.STAGING_DB", str(tmp_path / "test.db")):
            manager = StagingManager()

            record = StagingRecord(
                symbol="KQ.m@SHFE.rb",
                last_read_ts=datetime.now(),
                data_count=100,
                data_hash="abc123"
            )

            manager.update_record(record)

            last_ts = manager.get_last_read_ts("KQ.m@SHFE.rb")
            assert last_ts is not None
            assert abs((last_ts - record.last_read_ts).total_seconds()) < 1

    def test_get_incremental_first_time(self, tmp_path):
        """测试首次增量读取"""
        with patch("researcher.staging.ResearcherConfig.STAGING_DB", str(tmp_path / "test.db")):
            manager = StagingManager()

            # Mock data API 响应
            mock_data = [
                {"close": 3500, "volume": 1000, "timestamp": "2026-04-15T10:00:00"},
                {"close": 3510, "volume": 1100, "timestamp": "2026-04-15T11:00:00"}
            ]

            with patch.object(manager, "_fetch_from_data_api", return_value=mock_data):
                result = manager.get_incremental(["KQ.m@SHFE.rb"], lookback_hours=24)

                assert "KQ.m@SHFE.rb" in result
                assert len(result["KQ.m@SHFE.rb"]) == 2

    def test_get_incremental_subsequent(self, tmp_path):
        """测试后续增量读取"""
        with patch("researcher.staging.ResearcherConfig.STAGING_DB", str(tmp_path / "test.db")):
            manager = StagingManager()

            # 先插入一条记录
            record = StagingRecord(
                symbol="KQ.m@SHFE.rb",
                last_read_ts=datetime.now() - timedelta(hours=1),
                data_count=50,
                data_hash="old_hash"
            )
            manager.update_record(record)

            # Mock 新数据
            mock_data = [
                {"close": 3520, "volume": 1200, "timestamp": "2026-04-15T12:00:00"}
            ]

            with patch.object(manager, "_fetch_from_data_api", return_value=mock_data):
                result = manager.get_incremental(["KQ.m@SHFE.rb"])

                assert "KQ.m@SHFE.rb" in result
                assert len(result["KQ.m@SHFE.rb"]) == 1

    def test_get_previous_summary(self, tmp_path):
        """测试获取上期摘要"""
        with patch("researcher.config.ResearcherConfig.REPORTS_DIR", str(tmp_path)):
            manager = StagingManager()

            # 创建上期报告
            prev_date = "2026-04-14"
            prev_segment = "夜盘"
            prev_dir = tmp_path / prev_date
            prev_dir.mkdir(parents=True)

            prev_report = {
                "futures_summary": {
                    "symbols": {
                        "KQ.m@SHFE.rb": {
                            "trend": "偏多",
                            "confidence": 0.8
                        }
                    }
                }
            }

            import json
            with open(prev_dir / f"{prev_segment}.json", "w") as f:
                json.dump(prev_report, f)

            # 获取上期摘要（盘前 → 前一天夜盘）
            summary = manager.get_previous_summary("盘前", "2026-04-15")
            assert summary is not None
            assert "KQ.m@SHFE.rb" in summary["symbols"]


class TestSummarizer:
    """测试 LLM 归纳器"""

    def test_summarize_symbol_success(self):
        """测试品种归纳成功"""
        summarizer = Summarizer()

        mock_response = '{"trend": "偏多", "confidence": 0.75, "key_factors": ["库存下降", "需求增加"], "overnight_context": "外盘上涨"}'

        with patch.object(summarizer, "_call_ollama", return_value=mock_response):
            result = summarizer.summarize_symbol(
                symbol="KQ.m@SHFE.rb",
                incremental_data=[{"close": 3500, "volume": 1000}],
                previous_summary=None,
                news_items=["螺纹钢库存下降"]
            )

            assert result.symbol == "KQ.m@SHFE.rb"
            assert result.trend == "偏多"
            assert result.confidence == 0.75
            assert "库存下降" in result.key_factors

    def test_summarize_symbol_failure(self):
        """测试品种归纳失败降级"""
        summarizer = Summarizer()

        with patch.object(summarizer, "_call_ollama", side_effect=Exception("Timeout")):
            result = summarizer.summarize_symbol(
                symbol="KQ.m@SHFE.rb",
                incremental_data=[{"close": 3500, "volume": 1000}]
            )

            assert result.symbol == "KQ.m@SHFE.rb"
            assert result.trend == "观望"
            assert result.confidence == 0.0
            assert "归纳失败" in result.key_factors[0]

    def test_summarize_market_overview(self):
        """测试市场综述生成"""
        summarizer = Summarizer()

        researches = [
            SymbolResearch(symbol="KQ.m@SHFE.rb", trend="偏多", confidence=0.8, key_factors=[]),
            SymbolResearch(symbol="KQ.m@SHFE.hc", trend="偏空", confidence=0.7, key_factors=[]),
            SymbolResearch(symbol="KQ.m@SHFE.cu", trend="震荡", confidence=0.5, key_factors=[])
        ]

        overview = summarizer.summarize_market_overview(researches, "期货")

        assert "3 个品种" in overview
        assert "偏多" in overview
        assert "偏空" in overview

    def test_build_prompt_with_previous(self):
        """测试 prompt 构建（含上期摘要）"""
        summarizer = Summarizer()

        previous_summary = {
            "symbols": {
                "KQ.m@SHFE.rb": {
                    "trend": "偏空",
                    "confidence": 0.6,
                    "key_factors": ["库存增加"]
                }
            }
        }

        prompt = summarizer._build_prompt(
            symbol="KQ.m@SHFE.rb",
            incremental_data=[{"close": 3500, "volume": 1000}],
            previous_summary=previous_summary,
            news_items=["螺纹钢需求回暖"]
        )

        assert "KQ.m@SHFE.rb" in prompt
        assert "上期摘要" in prompt
        assert "偏空" in prompt
        assert "螺纹钢需求回暖" in prompt

    def test_parse_response_valid_json(self):
        """测试解析有效 JSON 响应"""
        summarizer = Summarizer()

        response = '根据分析，{"trend": "偏多", "confidence": 0.8, "key_factors": ["因素1"]}'

        result = summarizer._parse_response("KQ.m@SHFE.rb", response)

        assert result.trend == "偏多"
        assert result.confidence == 0.8

    def test_parse_response_invalid_json(self):
        """测试解析无效 JSON 响应"""
        summarizer = Summarizer()

        response = "这是一段没有 JSON 的文本"

        result = summarizer._parse_response("KQ.m@SHFE.rb", response)

        assert result.trend == "观望"
        assert result.confidence == 0.5
        assert "解析失败" in result.key_factors[0]
