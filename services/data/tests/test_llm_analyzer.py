"""测试 LLM 分析器"""
import pytest
from researcher.llm_analyzer import LLMAnalyzer
import multiprocessing as mp


def test_llm_analyzer_config():
    """测试 LLM 分析器配置"""
    queue = mp.Queue()
    stop_event = mp.Event()

    analyzer = LLMAnalyzer(queue, stop_event)

    # 验证配置
    assert analyzer.model == "qwen3:14b"
    assert "localhost" in analyzer.ollama_url
    assert analyzer.report_buffer == []


def test_analyze_kline_alert():
    """测试 K 线异常分析"""
    queue = mp.Queue()
    stop_event = mp.Event()

    analyzer = LLMAnalyzer(queue, stop_event)

    event = {
        "type": "kline_alert",
        "symbol": "RB",
        "change_pct": 3.5,
        "timestamp": "2026-04-16T10:00:00"
    }

    # 注意：实际调用 Ollama 可能失败，这里只测试结构
    result = analyzer._analyze_kline_alert(event)

    assert result is not None
    assert result["type"] == "kline_analysis"
    assert result["symbol"] == "RB"
