"""测试 — 报告生成器"""

import pytest
import os
import json
from datetime import datetime

from researcher.reporter import Reporter
from researcher.models import SymbolResearch


class TestReporter:
    """测试报告生成器"""

    def test_generate_report_id(self, tmp_path):
        """测试报告ID生成"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("researcher.config.ResearcherConfig.REPORTS_DIR", str(tmp_path))
            reporter = Reporter()

            report_id = reporter._generate_report_id("2026-04-15", "盘前")
            assert report_id == "RPT-20260415-盘前-001"

            # 创建目录后再生成
            date_dir = tmp_path / "2026-04-15"
            date_dir.mkdir()
            (date_dir / "盘前-001.json").touch()

            report_id2 = reporter._generate_report_id("2026-04-15", "盘前")
            assert report_id2 == "RPT-20260415-盘前-002"

    def test_build_futures_summary(self):
        """测试期货综述构建"""
        reporter = Reporter()

        researches = [
            SymbolResearch(
                symbol="KQ.m@SHFE.rb",
                trend="偏多",
                confidence=0.8,
                key_factors=["库存下降"],
                overnight_context="外盘上涨",
                news_highlights=["螺纹钢需求回暖"]
            ),
            SymbolResearch(
                symbol="KQ.m@SHFE.hc",
                trend="偏空",
                confidence=0.7,
                key_factors=["产量增加"]
            )
        ]

        summary = reporter._build_futures_summary(researches)

        assert summary["symbols_covered"] == 2
        assert "KQ.m@SHFE.rb" in summary["symbols"]
        assert summary["symbols"]["KQ.m@SHFE.rb"]["trend"] == "偏多"
        assert "市场" in summary["market_overview"]

    def test_build_stocks_summary(self):
        """测试股票综述构建"""
        reporter = Reporter()

        researches = [
            SymbolResearch(symbol=f"60000{i}.SH", trend="偏多", confidence=min(0.6 + i * 0.02, 0.95), key_factors=[])
            for i in range(15)
        ]

        summary = reporter._build_stocks_summary(researches)

        assert summary["symbols_covered"] == 15
        assert len(summary["top_movers"]) == 10  # 最多 10 个

    def test_compute_changes(self):
        """测试变化要点计算"""
        reporter = Reporter()

        current = [
            SymbolResearch(symbol="KQ.m@SHFE.rb", trend="偏多", confidence=0.8, key_factors=[]),
            SymbolResearch(symbol="KQ.m@SHFE.hc", trend="偏空", confidence=0.7, key_factors=[])
        ]

        previous_summary = {
            "symbols": {
                "KQ.m@SHFE.rb": {"trend": "偏空", "confidence": 0.6},
                "KQ.m@SHFE.hc": {"trend": "偏空", "confidence": 0.7}
            }
        }

        changes = reporter._compute_changes(current, previous_summary)

        assert len(changes) == 1
        assert "KQ.m@SHFE.rb" in changes[0]
        assert "偏空 转 偏多" in changes[0]

    def test_generate_report(self, tmp_path):
        """测试完整报告生成"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("researcher.config.ResearcherConfig.REPORTS_DIR", str(tmp_path))
            reporter = Reporter()

            futures_researches = [
                SymbolResearch(
                    symbol="KQ.m@SHFE.rb",
                    trend="偏多",
                    confidence=0.8,
                    key_factors=["库存下降"]
                )
            ]

            stocks_researches = [
                SymbolResearch(
                    symbol="600000.SH",
                    trend="偏多",
                    confidence=0.7,
                    key_factors=[]
                )
            ]

            crawler_stats = {
                "sources_crawled": 5,
                "articles_processed": 20,
                "failed_sources": []
            }

            report = reporter.generate_report(
                date="2026-04-15",
                segment="盘前",
                futures_researches=futures_researches,
                stocks_researches=stocks_researches,
                crawler_stats=crawler_stats
            )

            assert report.report_id.startswith("RPT-20260415-盘前")
            assert report.futures_summary["symbols_covered"] == 1
            assert report.stocks_summary["symbols_covered"] == 1

            # 检查文件是否生成
            json_path = tmp_path / "2026-04-15" / "盘前.json"
            md_path = tmp_path / "2026-04-15" / "盘前.md"

            assert json_path.exists()
            assert md_path.exists()

    def test_generate_markdown(self):
        """测试 Markdown 生成"""
        reporter = Reporter()

        from researcher.models import ResearchReport

        report = ResearchReport(
            report_id="RPT-20260415-盘前-001",
            date="2026-04-15",
            segment="盘前",
            generated_at=datetime.now(),
            futures_summary={
                "symbols_covered": 2,
                "market_overview": "期货市场整体偏多",
                "symbols": {
                    "KQ.m@SHFE.rb": {
                        "trend": "偏多",
                        "confidence": 0.8,
                        "key_factors": ["库存下降"],
                        "overnight_context": "外盘上涨"
                    }
                }
            },
            stocks_summary={
                "symbols_covered": 10,
                "market_overview": "股票市场震荡",
                "top_movers": [
                    {"symbol": "600000.SH", "trend": "偏多", "confidence": 0.75}
                ]
            },
            crawler_stats={
                "sources_crawled": 5,
                "articles_processed": 20
            },
            change_highlights=["螺纹钢从偏空转偏多"]
        )

        md_content = reporter._generate_markdown(report)

        assert "# 研究员报告" in md_content
        assert "RPT-20260415-盘前-001" in md_content
        assert "期货市场" in md_content
        assert "股票市场" in md_content
        assert "变化要点" in md_content
        assert "爬虫统计" in md_content

    def test_get_latest_report(self, tmp_path):
        """测试获取最新报告"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr("researcher.config.ResearcherConfig.REPORTS_DIR", str(tmp_path))
            reporter = Reporter()

            # 创建两个报告
            date_dir = tmp_path / "2026-04-15"
            date_dir.mkdir()

            report1 = {
                "report_id": "RPT-20260415-盘前-001",
                "date": "2026-04-15",
                "segment": "盘前",
                "generated_at": "2026-04-15T08:30:00",
                "model": "qwen3:14b",
                "futures_summary": {},
                "stocks_summary": {},
                "crawler_stats": {},
                "change_highlights": []
            }

            report2 = {
                "report_id": "RPT-20260415-午间-001",
                "date": "2026-04-15",
                "segment": "午间",
                "generated_at": "2026-04-15T11:35:00",
                "model": "qwen3:14b",
                "futures_summary": {},
                "stocks_summary": {},
                "crawler_stats": {},
                "change_highlights": []
            }

            with open(date_dir / "盘前.json", "w") as f:
                json.dump(report1, f)

            with open(date_dir / "午间.json", "w") as f:
                json.dump(report2, f)

            latest = reporter.get_latest_report()

            assert latest is not None
            assert latest.segment == "午间"  # 午间更晚
