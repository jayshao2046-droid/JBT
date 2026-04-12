"""
测试盘后评估器 (CB7)
"""
import pytest
from src.research.post_market import PostMarketEvaluator


def test_evaluate_strong_rating():
    """测试强势评级（涨幅 > 5%）"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 11.0,
        "low": 9.8,
        "close": 10.6,
        "volume": 1000000,
        "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert result["rating"] == "strong"
    assert result["pct_change"] == 6.0


def test_evaluate_positive_rating():
    """测试正面评级（2% < 涨幅 <= 5%）"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 10.5,
        "low": 9.9,
        "close": 10.3,
        "volume": 1000000,
        "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert result["rating"] == "positive"
    assert result["pct_change"] == 3.0


def test_evaluate_neutral_rating():
    """测试中性评级（-2% < 涨幅 <= 2%）"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 10.2,
        "low": 9.9,
        "close": 10.1,
        "volume": 1000000,
        "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert result["rating"] == "neutral"
    assert result["pct_change"] == 1.0


def test_evaluate_weak_rating():
    """测试弱势评级（-5% < 涨幅 <= -2%）"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 10.1,
        "low": 9.6,
        "close": 9.7,
        "volume": 1000000,
        "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert result["rating"] == "weak"
    assert result["pct_change"] == -3.0


def test_evaluate_bearish_rating():
    """测试看跌评级（涨幅 <= -5%）"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 10.0,
        "low": 9.0,
        "close": 9.4,
        "volume": 1000000,
        "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert result["rating"] == "bearish"
    assert result["pct_change"] == -6.0


def test_amplitude_calculation():
    """测试振幅计算"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 11.0,
        "low": 9.0,
        "close": 10.5,
        "volume": 1000000,
        "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    # amplitude = (11 - 9) / 10 * 100 = 20
    assert result["amplitude"] == 20.0


def test_volume_ratio_calculation():
    """测试量比计算"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0,
        "high": 10.5,
        "low": 9.9,
        "close": 10.2,
        "volume": 2000000,
        "prev_close": 10.0,
        "avg_volume": 1000000
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert result["volume_ratio"] == 2.0


def test_batch_evaluate():
    """测试批量评估"""
    evaluator = PostMarketEvaluator()
    symbols_data = [
        {
            "symbol": "600000.SH",
            "daily_data": {
                "open": 10.0, "high": 10.6, "low": 9.9,
                "close": 10.6, "volume": 1000000, "prev_close": 10.0
            }
        },
        {
            "symbol": "600001.SH",
            "daily_data": {
                "open": 20.0, "high": 20.5, "low": 19.5,
                "close": 19.0, "volume": 2000000, "prev_close": 20.0
            }
        }
    ]
    report = evaluator.batch_evaluate(symbols_data)
    assert report["summary"]["total"] == 2
    assert len(report["results"]) == 2
    assert "report_id" in report


def test_get_report_after_batch():
    """测试批量评估后获取报告"""
    evaluator = PostMarketEvaluator()
    symbols_data = [
        {
            "symbol": "600000.SH",
            "daily_data": {
                "open": 10.0, "high": 10.5, "low": 9.9,
                "close": 10.3, "volume": 1000000, "prev_close": 10.0
            }
        }
    ]
    evaluator.batch_evaluate(symbols_data)
    report = evaluator.get_report()
    assert report["summary"]["total"] == 1
    assert report["report_id"] is not None


def test_get_report_empty():
    """测试未评估时获取报告"""
    evaluator = PostMarketEvaluator()
    report = evaluator.get_report()
    assert report["report_id"] is None
    assert report["summary"]["total"] == 0


def test_rating_counts_in_summary():
    """测试摘要中的评级统计"""
    evaluator = PostMarketEvaluator()
    symbols_data = [
        {
            "symbol": "600000.SH",
            "daily_data": {
                "open": 10.0, "high": 10.7, "low": 9.9,
                "close": 10.6, "volume": 1000000, "prev_close": 10.0
            }
        },
        {
            "symbol": "600001.SH",
            "daily_data": {
                "open": 20.0, "high": 21.5, "low": 19.5,
                "close": 21.2, "volume": 2000000, "prev_close": 20.0
            }
        }
    ]
    report = evaluator.batch_evaluate(symbols_data)
    rating_counts = report["summary"]["rating_counts"]
    assert "strong" in rating_counts
    assert rating_counts["strong"] == 2


def test_result_structure():
    """测试评估结果结构"""
    evaluator = PostMarketEvaluator()
    daily_data = {
        "open": 10.0, "high": 10.5, "low": 9.9,
        "close": 10.2, "volume": 1000000, "prev_close": 10.0
    }
    result = evaluator.evaluate("600000.SH", daily_data)
    assert "symbol" in result
    assert "pct_change" in result
    assert "amplitude" in result
    assert "volume_ratio" in result
    assert "rating" in result
    assert "evaluated_at" in result
