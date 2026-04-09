"""
test_reporting.py — TASK-0021 F batch
单元测试：研究摘要与日报生成
"""
import unittest.mock as mock

import pytest

from src.reporting.research_summary import ResearchSummary, ResearchSummaryBuilder
from src.reporting.daily import DailyReporter, DailyStats


# ── ResearchSummaryBuilder 测试 ──────────────────────────────────────────────

def _sample_result(status: str = "completed") -> dict:
    return {
        "strategy_id": "S001",
        "model_id": "XGBoost",
        "status": status,
        "started_at": "2026-04-08 09:00:00",
        "finished_at": "2026-04-08 09:05:30",
        "train_sharpe": 1.45,
        "train_accuracy": 0.72,
        "cv_mean_score": 1.38,
        "cv_std_score": 0.12,
        "best_params": {"n_estimators": 300, "max_depth": 6},
        "best_value": 1.41,
        "n_trials": 50,
        "shap_summary": {"factor_A": 0.35, "factor_B": -0.22, "factor_C": 0.18},
        "onnx_path": "/runtime/models/s001.onnx",
        "onnx_verified": True,
    }


def test_builder_from_session_result_completed():
    result = _sample_result("completed")
    summary = ResearchSummaryBuilder.from_session_result("sess-001", result)
    assert summary.session_id == "sess-001"
    assert summary.strategy_id == "S001"
    assert summary.status == "completed"
    assert summary.train_sharpe == 1.45
    assert summary.n_trials == 50
    assert summary.onnx_verified is True
    assert "factor_A" in summary.top_features


def test_builder_duration_calculation():
    result = _sample_result()
    summary = ResearchSummaryBuilder.from_session_result("sess-time", result)
    assert summary.duration_seconds == 330.0   # 5min30s


def test_builder_top_features_sorted_by_abs():
    result = _sample_result()
    result["shap_summary"] = {"f1": 0.1, "f2": -0.5, "f3": 0.3}
    summary = ResearchSummaryBuilder.from_session_result("sess-shap", result)
    assert summary.top_features[0] == "f2"  # highest abs
    assert summary.top_features[1] == "f3"


def test_builder_failed_status():
    result = _sample_result("failed")
    result["error_message"] = "OOM"
    summary = ResearchSummaryBuilder.from_session_result("sess-fail", result)
    assert summary.status == "failed"
    assert summary.error_message == "OOM"


def test_summary_to_notify_body_completed():
    result = _sample_result("completed")
    summary = ResearchSummaryBuilder.from_session_result("sess-body", result)
    body = summary.to_notify_body()
    assert "sess-body" in body
    assert "Sharpe" in body
    assert "ONNX" in body


def test_summary_to_notify_body_failed():
    result = _sample_result("failed")
    result["error_message"] = "Timeout"
    summary = ResearchSummaryBuilder.from_session_result("sess-err", result)
    body = summary.to_notify_body()
    assert "Timeout" in body


def test_summary_to_dict():
    result = _sample_result()
    summary = ResearchSummaryBuilder.from_session_result("sess-dict", result)
    d = summary.to_dict()
    assert d["session_id"] == "sess-dict"
    assert d["train_sharpe"] == 1.45
    assert d["onnx_verified"] is True


# ── DailyReporter 测试 ────────────────────────────────────────────────────────

def _make_reporter() -> DailyReporter:
    reporter = DailyReporter()
    # 替换 dispatcher 为 mock
    reporter._dispatcher = mock.MagicMock()
    reporter._dispatcher.dispatch.return_value = None
    # 隔离运行态数据源，避免测试污染
    reporter._build_runtime_counts = lambda: ({k: 0 for k in reporter._counters}, [])
    return reporter


def test_daily_reporter_generate_empty():
    reporter = _make_reporter()
    stats = reporter.generate("2026-04-08")
    assert stats.report_date == "2026-04-08"
    assert stats.signals_generated == 0
    assert stats.research_sessions_total == 0


def test_daily_reporter_increment():
    reporter = _make_reporter()
    reporter.increment("signals_generated", 5)
    reporter.increment("signals_approved", 3)
    reporter.increment("research_sessions_total", 2)
    reporter.increment("research_sessions_completed", 2)
    stats = reporter.generate("2026-04-08")
    assert stats.signals_generated == 5
    assert stats.signals_approved == 3
    assert stats.research_sessions_completed == 2


def test_daily_reporter_add_research_summary():
    reporter = _make_reporter()
    reporter.add_research_summary({"session_id": "s1", "status": "completed"})
    stats = reporter.generate("2026-04-08")
    assert len(stats.research_summaries) == 1
    assert stats.research_summaries[0]["session_id"] == "s1"


def test_daily_reporter_reset():
    reporter = _make_reporter()
    reporter.increment("signals_generated", 10)
    reporter.add_research_summary({"x": 1})
    reporter.reset()
    stats = reporter.generate("2026-04-08")
    assert stats.signals_generated == 0
    assert len(stats.research_summaries) == 0


def test_daily_reporter_send_dispatches_event():
    reporter = _make_reporter()
    reporter.increment("strategies_active", 3)
    reporter.send_daily_report("2026-04-08")
    reporter._dispatcher.dispatch.assert_called_once()
    event = reporter._dispatcher.dispatch.call_args[0][0]
    assert event.event_code == "DAILY-2026-04-08"
    assert "NOTIFY" in str(event.notify_level)


def test_daily_stats_to_dict():
    reporter = _make_reporter()
    reporter.increment("publishes_to_sim", 2)
    reporter.increment("publishes_success", 2)
    stats = reporter.generate("2026-04-08")
    d = stats.to_dict()
    assert d["publishes_to_sim"] == 2
    assert d["publishes_success"] == 2


def test_daily_stats_to_notify_body():
    reporter = _make_reporter()
    reporter.increment("signals_generated", 7)
    reporter.increment("signals_approved", 4)
    stats = reporter.generate("2026-04-08")
    body = stats.to_notify_body()
    assert "2026-04-08" in body
    assert "7" in body
    assert "4" in body
