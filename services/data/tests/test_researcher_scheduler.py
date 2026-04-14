"""测试 — 研究员调度器"""

import pytest
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from researcher.scheduler import ResearcherScheduler


class TestResearcherScheduler:
    """测试研究员调度器"""

    @pytest.mark.asyncio
    async def test_execute_segment_success(self):
        """测试执行时段成功"""
        scheduler = ResearcherScheduler()

        # Mock 所有依赖
        with patch.object(scheduler, '_check_resources', return_value=True):
            with patch.object(scheduler.staging_manager, 'get_incremental', return_value={}):
                with patch.object(scheduler, '_crawl_news_with_urgent_detection', return_value={"sources_crawled": 0, "articles_processed": 0, "failed_sources": [], "news_items": []}):
                    with patch.object(scheduler, '_summarize_futures', return_value=[]):
                        with patch.object(scheduler, '_summarize_stocks', return_value=[]):
                            with patch.object(scheduler.reporter, 'generate_report') as mock_report:
                                with patch.object(scheduler.notifier, 'notify_report_done', new_callable=AsyncMock):
                                    with patch.object(scheduler, '_push_to_data_api', new_callable=AsyncMock):
                                        mock_report.return_value = MagicMock(report_id="RPT-TEST-001")

                                        result = await scheduler.execute_segment("盘前")

                                        # 调试输出
                                        if not result["success"]:
                                            print(f"Error: {result.get('error')}")

                                        assert result["success"] is True
                                        assert "report_id" in result

    @pytest.mark.asyncio
    async def test_execute_segment_resource_check_fail(self):
        """测试资源检查失败"""
        scheduler = ResearcherScheduler()

        with patch.object(scheduler, '_check_resources', return_value=False):
            result = await scheduler.execute_segment("盘前")

            assert result["success"] is False
            assert "资源不足" in result["error"]

    def test_check_resources_no_psutil(self):
        """测试无 psutil 时资源检查"""
        scheduler = ResearcherScheduler()

        with patch("researcher.scheduler.PSUTIL_AVAILABLE", False):
            result = scheduler._check_resources()
            assert result is True  # 无 psutil 时应该返回 True

    @pytest.mark.asyncio
    async def test_crawl_news(self):
        """测试爬虫采集"""
        scheduler = ResearcherScheduler()

        with patch.object(scheduler.source_registry, 'get_active_sources', return_value=[]):
            with patch.object(scheduler.notifier, 'notify_urgent', new_callable=AsyncMock):
                stats = await scheduler._crawl_news_with_urgent_detection("08:00")

                assert "sources_crawled" in stats
                assert "articles_processed" in stats
                assert "failed_sources" in stats
                assert "news_items" in stats

    def test_summarize_futures(self):
        """测试期货归纳"""
        scheduler = ResearcherScheduler()

        data = {
            "KQ.m@SHFE.rb": [{"close": 3500, "volume": 1000}]
        }

        with patch.object(scheduler.summarizer, 'summarize_symbol') as mock_summarize:
            from researcher.models import SymbolResearch
            mock_summarize.return_value = SymbolResearch(
                symbol="KQ.m@SHFE.rb",
                trend="偏多",
                confidence=0.8,
                key_factors=[]
            )

            researches = scheduler._summarize_futures(data, "盘前")

            assert len(researches) == 1
            assert researches[0].symbol == "KQ.m@SHFE.rb"
