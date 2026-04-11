"""回测报告构建器 — TASK-0060 CA3
将 SandboxResult 转为结构化报告，支持 JSON/HTML 导出。
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from .sandbox_engine import SandboxResult


@dataclass
class BacktestReport:
    report_id: str
    backtest_id: str
    strategy_id: str
    asset_type: str  # futures / stock
    created_at: str
    summary: dict = field(default_factory=dict)
    trade_log: list = field(default_factory=list)
    monthly_returns: list = field(default_factory=list)
    risk_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReportBuilder:
    """从 SandboxResult 构建结构化报告，支持 JSON/HTML 导出。"""

    def __init__(self) -> None:
        self._reports: dict[str, BacktestReport] = {}

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_from_sandbox(
        self,
        result: SandboxResult,
        strategy_id: str,
        asset_type: str = "futures",
    ) -> BacktestReport:
        report_id = f"rpt-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        summary = {
            "total_return": result.total_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate,
            "trades_count": result.trades_count,
            "initial_capital": result.initial_capital,
            "final_capital": result.final_capital,
        }

        trade_log = [dict(t) for t in result.trades]
        monthly_returns = self._calculate_monthly_returns(result.trades)
        risk_metrics = self._calculate_risk_metrics(result.trades)

        report = BacktestReport(
            report_id=report_id,
            backtest_id=result.backtest_id,
            strategy_id=strategy_id,
            asset_type=asset_type,
            created_at=now,
            summary=summary,
            trade_log=trade_log,
            monthly_returns=monthly_returns,
            risk_metrics=risk_metrics,
        )
        self._reports[report_id] = report
        return report

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_report(self, report_id: str) -> BacktestReport | None:
        return self._reports.get(report_id)

    def list_reports(self, strategy_id: str | None = None) -> list[BacktestReport]:
        if strategy_id is None:
            return list(self._reports.values())
        return [r for r in self._reports.values() if r.strategy_id == strategy_id]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_json(self, report_id: str) -> dict | None:
        report = self._reports.get(report_id)
        if report is None:
            return None
        return report.to_dict()

    def export_html(self, report_id: str) -> str | None:
        report = self._reports.get(report_id)
        if report is None:
            return None
        return self._render_html(report)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_monthly_returns(trades: list) -> list[dict]:
        """从交易列表聚合月度收益。仅统计有 pnl 的 sell 交易。"""
        monthly: dict[str, float] = defaultdict(float)
        for t in trades:
            pnl = t.get("pnl")
            if pnl is None:
                continue
            dt_str = t.get("datetime", t.get("date", ""))
            if len(dt_str) >= 7:
                month_key = dt_str[:7]  # YYYY-MM
            else:
                month_key = "unknown"
            monthly[month_key] += pnl

        return [{"month": k, "pnl": round(v, 2)} for k, v in sorted(monthly.items())]

    @staticmethod
    def _calculate_risk_metrics(trades: list) -> dict:
        """计算风险指标：最大连续亏损次数、盈亏比、平均盈利/平均亏损。"""
        sell_trades = [t for t in trades if t.get("type") == "sell"]
        pnls = [t.get("pnl", 0.0) for t in sell_trades]

        # Max consecutive losses
        max_consecutive_losses = 0
        current_streak = 0
        for p in pnls:
            if p < 0:
                current_streak += 1
                if current_streak > max_consecutive_losses:
                    max_consecutive_losses = current_streak
            else:
                current_streak = 0

        # Avg win / avg loss
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        # Profit factor = gross_profit / abs(gross_loss)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0

        return {
            "max_consecutive_losses": max_consecutive_losses,
            "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else "inf",
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
        }

    @staticmethod
    def _render_html(report: BacktestReport) -> str:
        """用 f-string 模板生成简洁的 HTML 报告。"""
        s = report.summary
        rows_summary = "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in s.items()
        )

        rows_trades = ""
        for t in report.trade_log:
            cols = "".join(f"<td>{v}</td>" for v in t.values())
            rows_trades += f"<tr>{cols}</tr>"

        trade_headers = ""
        if report.trade_log:
            trade_headers = "".join(f"<th>{k}</th>" for k in report.trade_log[0].keys())

        rows_monthly = ""
        for m in report.monthly_returns:
            rows_monthly += f"<tr><td>{m['month']}</td><td>{m['pnl']}</td></tr>"

        rows_risk = "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in report.risk_metrics.items()
        )

        return f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>回测报告 {report.report_id}</title>
<style>
body{{font-family:sans-serif;margin:20px}}
table{{border-collapse:collapse;width:100%;margin-bottom:20px}}
th,td{{border:1px solid #ccc;padding:6px 10px;text-align:left}}
th{{background:#f5f5f5}}
h1{{color:#333}}h2{{color:#555}}
</style></head>
<body>
<h1>回测报告</h1>
<p>报告 ID: {report.report_id} | 回测 ID: {report.backtest_id}</p>
<p>策略: {report.strategy_id} | 资产类型: {report.asset_type} | 生成时间: {report.created_at}</p>

<h2>绩效摘要</h2>
<table><tr><th>指标</th><th>值</th></tr>{rows_summary}</table>

<h2>风险指标</h2>
<table><tr><th>指标</th><th>值</th></tr>{rows_risk}</table>

<h2>月度收益</h2>
<table><tr><th>月份</th><th>盈亏</th></tr>{rows_monthly}</table>

<h2>交易记录</h2>
<table><tr>{trade_headers}</tr>{rows_trades}</table>
</body></html>"""
