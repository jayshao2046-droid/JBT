"""
回测报告构建器测试 — TASK-0060 CA3
"""
from __future__ import annotations

import pytest

from services.decision.src.research.sandbox_engine import SandboxResult
from services.decision.src.research.report_builder import ReportBuilder, BacktestReport


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_sandbox_result(
    backtest_id: str = "sandbox-abc123",
    trades: list | None = None,
    status: str = "completed",
    initial_capital: float = 1_000_000,
    final_capital: float = 1_050_000,
) -> SandboxResult:
    if trades is None:
        trades = [
            {"type": "buy", "price": 100.0, "qty": 10, "bar_index": 20, "datetime": "2025-01-15T09:30:00"},
            {"type": "sell", "price": 110.0, "qty": 10, "pnl": 100.0, "bar_index": 25, "datetime": "2025-01-20T09:30:00"},
            {"type": "buy", "price": 108.0, "qty": 10, "bar_index": 30, "datetime": "2025-02-05T09:30:00"},
            {"type": "sell", "price": 105.0, "qty": 10, "pnl": -30.0, "bar_index": 35, "datetime": "2025-02-10T09:30:00"},
            {"type": "buy", "price": 106.0, "qty": 10, "bar_index": 40, "datetime": "2025-03-01T09:30:00"},
            {"type": "sell", "price": 115.0, "qty": 10, "pnl": 90.0, "bar_index": 45, "datetime": "2025-03-10T09:30:00"},
        ]
    return SandboxResult(
        backtest_id=backtest_id,
        status=status,
        start_time="2025-01-01T00:00:00",
        end_time="2025-03-31T00:00:00",
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=round((final_capital - initial_capital) / initial_capital, 6),
        sharpe_ratio=1.25,
        max_drawdown=0.03,
        win_rate=0.67,
        trades_count=len([t for t in trades if t.get("type") == "sell"]),
        trades=trades,
        performance_metrics={},
    )


@pytest.fixture
def builder() -> ReportBuilder:
    return ReportBuilder()


@pytest.fixture
def sandbox_result() -> SandboxResult:
    return _make_sandbox_result()


# ---------------------------------------------------------------------------
# Tests — build_from_sandbox
# ---------------------------------------------------------------------------

class TestBuildFromSandbox:
    def test_build_creates_report(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        assert isinstance(report, BacktestReport)
        assert report.report_id.startswith("rpt-")
        assert report.backtest_id == "sandbox-abc123"
        assert report.strategy_id == "strat-001"
        assert report.asset_type == "futures"

    def test_build_summary_fields(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        s = report.summary
        assert s["total_return"] == sandbox_result.total_return
        assert s["sharpe_ratio"] == sandbox_result.sharpe_ratio
        assert s["max_drawdown"] == sandbox_result.max_drawdown
        assert s["win_rate"] == sandbox_result.win_rate
        assert s["trades_count"] == sandbox_result.trades_count
        assert s["initial_capital"] == 1_000_000
        assert s["final_capital"] == 1_050_000

    def test_build_stores_in_cache(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        assert builder.get_report(report.report_id) is report


# ---------------------------------------------------------------------------
# Tests — monthly_returns
# ---------------------------------------------------------------------------

class TestMonthlyReturns:
    def test_monthly_aggregation(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        months = {m["month"]: m["pnl"] for m in report.monthly_returns}
        assert "2025-01" in months
        assert months["2025-01"] == 100.0
        assert "2025-02" in months
        assert months["2025-02"] == -30.0
        assert "2025-03" in months
        assert months["2025-03"] == 90.0

    def test_empty_trades_monthly(self, builder: ReportBuilder):
        result = _make_sandbox_result(trades=[], final_capital=1_000_000)
        report = builder.build_from_sandbox(result, strategy_id="strat-002")
        assert report.monthly_returns == []


# ---------------------------------------------------------------------------
# Tests — risk_metrics
# ---------------------------------------------------------------------------

class TestRiskMetrics:
    def test_risk_metrics_values(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        rm = report.risk_metrics
        assert rm["max_consecutive_losses"] == 1  # only 1 loss
        assert rm["avg_win"] > 0
        assert rm["avg_loss"] < 0
        assert rm["profit_factor"] != 0

    def test_empty_trades_risk(self, builder: ReportBuilder):
        result = _make_sandbox_result(trades=[], final_capital=1_000_000)
        report = builder.build_from_sandbox(result, strategy_id="strat-002")
        rm = report.risk_metrics
        assert rm["max_consecutive_losses"] == 0
        assert rm["avg_win"] == 0.0
        assert rm["avg_loss"] == 0.0
        assert rm["profit_factor"] == 0.0

    def test_all_losses(self, builder: ReportBuilder):
        trades = [
            {"type": "sell", "price": 95, "qty": 10, "pnl": -50.0, "bar_index": 1, "datetime": "2025-01-05T09:30:00"},
            {"type": "sell", "price": 90, "qty": 10, "pnl": -80.0, "bar_index": 2, "datetime": "2025-01-10T09:30:00"},
        ]
        result = _make_sandbox_result(trades=trades, final_capital=870_000)
        report = builder.build_from_sandbox(result, strategy_id="strat-003")
        rm = report.risk_metrics
        assert rm["max_consecutive_losses"] == 2
        assert rm["profit_factor"] == 0.0
        assert rm["avg_win"] == 0.0


# ---------------------------------------------------------------------------
# Tests — export_json / export_html
# ---------------------------------------------------------------------------

class TestExport:
    def test_export_json(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        data = builder.export_json(report.report_id)
        assert data is not None
        assert data["report_id"] == report.report_id
        assert "summary" in data
        assert "trade_log" in data
        assert "monthly_returns" in data
        assert "risk_metrics" in data

    def test_export_json_not_found(self, builder: ReportBuilder):
        assert builder.export_json("nonexistent") is None

    def test_export_html(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        html = builder.export_html(report.report_id)
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert report.report_id in html
        assert "回测报告" in html
        assert "绩效摘要" in html
        assert "风险指标" in html
        assert "月度收益" in html
        assert "交易记录" in html

    def test_export_html_not_found(self, builder: ReportBuilder):
        assert builder.export_html("nonexistent") is None


# ---------------------------------------------------------------------------
# Tests — list / get
# ---------------------------------------------------------------------------

class TestListGet:
    def test_get_report_found(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        report = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        assert builder.get_report(report.report_id) is report

    def test_get_report_not_found(self, builder: ReportBuilder):
        assert builder.get_report("nonexistent") is None

    def test_list_all(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        r1 = builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        r2 = builder.build_from_sandbox(sandbox_result, strategy_id="strat-002")
        reports = builder.list_reports()
        assert len(reports) == 2
        ids = {r.report_id for r in reports}
        assert r1.report_id in ids
        assert r2.report_id in ids

    def test_list_filter_by_strategy(self, builder: ReportBuilder, sandbox_result: SandboxResult):
        builder.build_from_sandbox(sandbox_result, strategy_id="strat-001")
        builder.build_from_sandbox(sandbox_result, strategy_id="strat-002")
        filtered = builder.list_reports(strategy_id="strat-001")
        assert len(filtered) == 1
        assert filtered[0].strategy_id == "strat-001"
