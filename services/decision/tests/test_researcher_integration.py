"""测试研究员报告集成到决策端"""
import pytest
from unittest.mock import Mock, patch
from decision.src.llm.researcher_loader import ResearcherLoader
from decision.src.llm.researcher_scorer import ResearcherScorer
from decision.src.llm.pipeline import LLMPipeline


def test_researcher_loader_init():
    """测试研究员加载器初始化"""
    loader = ResearcherLoader("http://192.168.31.76:8105")
    assert loader.data_service_url == "http://192.168.31.76:8105"
    assert loader.api_endpoint == "http://192.168.31.76:8105/api/v1/researcher/reports"


def test_researcher_scorer_init():
    """测试研究员评分器初始化"""
    scorer = ResearcherScorer()
    assert scorer.event_weights is not None
    assert "K线异动" in scorer.event_weights
    assert "重大新闻" in scorer.event_weights


def test_researcher_scorer_score_report():
    """测试报告评分"""
    scorer = ResearcherScorer()

    # 模拟报告
    report = {
        "timestamp": "2026-04-16T10:00:00Z",
        "segment": "盘前",
        "summary": "市场整体平稳",
        "analyses": [
            {
                "symbol": "RB",
                "event_type": "K线异动",
                "content": "螺纹钢主力合约突破前高"
            },
            {
                "symbol": "HC",
                "event_type": "重大新闻",
                "content": "热卷库存大幅下降"
            }
        ]
    }

    # 评分
    watched_symbols = {"RB", "HC", "I"}
    current_positions = {"RB"}

    score = scorer.score_report(report, watched_symbols, current_positions)

    # 验证评分在 0-1 之间
    assert 0.0 <= score <= 1.0
    # 由于有持仓品种和关注品种，评分应该较高
    assert score > 0.5


def test_researcher_scorer_timeliness():
    """测试时效性评分"""
    scorer = ResearcherScorer()

    # 1 小时内的报告
    recent_report = {
        "timestamp": "2026-04-16T10:00:00Z",
        "analyses": []
    }

    # 24 小时前的报告
    old_report = {
        "timestamp": "2026-04-15T10:00:00Z",
        "analyses": []
    }

    recent_score = scorer._score_timeliness(recent_report)
    old_score = scorer._score_timeliness(old_report)

    # 新报告评分应该高于旧报告
    assert recent_score > old_score


def test_researcher_scorer_relevance():
    """测试相关性评分"""
    scorer = ResearcherScorer()

    report = {
        "analyses": [
            {"symbol": "RB", "event_type": "K线异动"},
            {"symbol": "HC", "event_type": "重大新闻"},
            {"symbol": "I", "event_type": "一般新闻"}
        ]
    }

    # 有持仓和关注品种
    watched_symbols = {"RB", "HC"}
    current_positions = {"RB"}

    score_with_relevance = scorer._score_relevance(
        report, watched_symbols, current_positions
    )

    # 无持仓和关注品种
    score_without_relevance = scorer._score_relevance(
        report, set(), set()
    )

    # 有相关性的评分应该更高
    assert score_with_relevance > score_without_relevance


def test_researcher_scorer_importance():
    """测试重要性评分"""
    scorer = ResearcherScorer()

    # 高重要性报告（多个 K 线异动）
    high_importance_report = {
        "analyses": [
            {"event_type": "K线异动"},
            {"event_type": "K线异动"},
            {"event_type": "重大新闻"}
        ]
    }

    # 低重要性报告（一般新闻）
    low_importance_report = {
        "analyses": [
            {"event_type": "一般新闻"},
            {"event_type": "一般新闻"}
        ]
    }

    high_score = scorer._score_importance(high_importance_report)
    low_score = scorer._score_importance(low_importance_report)

    # 高重要性评分应该更高
    assert high_score > low_score


def test_researcher_scorer_filter_high_value():
    """测试筛选高价值报告"""
    scorer = ResearcherScorer()

    reports = [
        {
            "timestamp": "2026-04-16T10:00:00Z",
            "analyses": [
                {"symbol": "RB", "event_type": "K线异动"}
            ]
        },
        {
            "timestamp": "2026-04-16T09:00:00Z",
            "analyses": [
                {"symbol": "XX", "event_type": "一般新闻"}
            ]
        }
    ]

    watched_symbols = {"RB"}
    current_positions = {"RB"}

    high_value_reports = scorer.filter_high_value_reports(
        reports, watched_symbols, current_positions, threshold=0.5
    )

    # 应该至少筛选出一份高价值报告
    assert len(high_value_reports) >= 1
    # 每份报告应该有评分
    for report in high_value_reports:
        assert "_score" in report
        assert report["_score"] >= 0.5


@patch('decision.src.llm.researcher_loader.requests.get')
def test_researcher_loader_get_latest_report(mock_get):
    """测试获取最新报告"""
    loader = ResearcherLoader("http://192.168.31.76:8105")

    # 模拟 API 响应
    mock_response = Mock()
    mock_response.json.return_value = {
        "success": True,
        "reports": [
            {
                "timestamp": "2026-04-16T10:00:00Z",
                "segment": "盘前",
                "summary": "市场整体平稳"
            }
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # 获取报告
    report = loader.get_latest_report()

    # 验证
    assert report is not None
    assert report["segment"] == "盘前"
    mock_get.assert_called_once()


@patch('decision.src.llm.researcher_loader.requests.get')
def test_researcher_loader_get_reports_since(mock_get):
    """测试获取最近 N 小时的报告"""
    loader = ResearcherLoader("http://192.168.31.76:8105")

    # 模拟 API 响应
    mock_response = Mock()
    mock_response.json.return_value = {
        "success": True,
        "reports": [
            {"timestamp": "2026-04-16T10:00:00Z"},
            {"timestamp": "2026-04-16T09:00:00Z"}
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # 获取报告
    reports = loader.get_reports_since(hours=24)

    # 验证
    assert len(reports) == 2
    mock_get.assert_called_once()


def test_researcher_loader_extract_key_points():
    """测试提取关键要点"""
    loader = ResearcherLoader("http://192.168.31.76:8105")

    report = {
        "summary": "市场整体平稳",
        "analyses": [
            {
                "event_type": "K线异动",
                "content": "螺纹钢主力合约突破前高"
            },
            {
                "event_type": "重大新闻",
                "content": "热卷库存大幅下降"
            }
        ]
    }

    key_points = loader.extract_key_points(report)

    # 验证
    assert len(key_points) >= 2
    assert any("市场概况" in point for point in key_points)
    assert any("K线异动" in point for point in key_points)


def test_researcher_loader_format_for_llm():
    """测试格式化报告供 LLM 使用"""
    loader = ResearcherLoader("http://192.168.31.76:8105")

    report = {
        "timestamp": "2026-04-16T10:00:00Z",
        "segment": "盘前",
        "summary": "市场整体平稳",
        "analyses": [
            {
                "event_type": "K线异动",
                "symbol": "RB",
                "content": "螺纹钢主力合约突破前高"
            }
        ]
    }

    formatted = loader.format_for_llm(report)

    # 验证
    assert "研究员报告" in formatted
    assert "盘前" in formatted
    assert "市场概况" in formatted
    assert "关键事件" in formatted
    assert "RB" in formatted


def test_pipeline_has_researcher_components():
    """测试 Pipeline 包含研究员组件"""
    pipeline = LLMPipeline()

    # 验证研究员组件已初始化
    assert hasattr(pipeline, 'researcher_loader')
    assert hasattr(pipeline, 'researcher_scorer')
    assert isinstance(pipeline.researcher_loader, ResearcherLoader)
    assert isinstance(pipeline.researcher_scorer, ResearcherScorer)
