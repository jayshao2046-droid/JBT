"""
每日汇总邮件 — TASK-0120 决策端通知体系 V1

生成包含 L1/L2/L3 统计、品种分析、失败通知、风险摘要的每日汇总邮件。
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter

from .dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


class DailyGateSummary:
    """每日门控汇总统计"""

    def __init__(self):
        self.date = datetime.now(_TZ_CST).strftime("%Y-%m-%d")

        # L1/L2/L3 统计
        self.l1_total = 0
        self.l1_passed = 0
        self.l2_total = 0
        self.l2_passed = 0
        self.l3_total = 0
        self.l3_confirmed = 0
        self.l3_rejected = 0
        self.l3_timeout = 0

        # 按品种统计
        self.symbol_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "l1_total": 0,
            "l1_passed": 0,
            "l2_total": 0,
            "l2_passed": 0,
            "l3_confirmed": 0,
        })

        # 拒绝原因统计
        self.l1_reject_reasons: Counter = Counter()
        self.l2_reject_reasons: Counter = Counter()
        self.l3_reject_reasons: Counter = Counter()

        # 失败通知统计
        self.feishu_failures = 0
        self.email_failures = 0
        self.both_failures = 0

        # 风险事件
        self.risk_events: List[Dict[str, Any]] = []

    def record_l1(self, symbol: str, passed: bool, risk_flag: Optional[str] = None):
        """记录 L1 结果"""
        self.l1_total += 1
        if passed:
            self.l1_passed += 1
        else:
            if risk_flag:
                self.l1_reject_reasons[risk_flag] += 1

        self.symbol_stats[symbol]["l1_total"] += 1
        if passed:
            self.symbol_stats[symbol]["l1_passed"] += 1

    def record_l2(self, symbol: str, passed: bool, risk_level: Optional[str] = None):
        """记录 L2 结果"""
        self.l2_total += 1
        if passed:
            self.l2_passed += 1
        else:
            if risk_level:
                self.l2_reject_reasons[risk_level] += 1

        self.symbol_stats[symbol]["l2_total"] += 1
        if passed:
            self.symbol_stats[symbol]["l2_passed"] += 1

    def record_l3(self, symbol: str, status: str, reason: Optional[str] = None):
        """记录 L3 结果"""
        self.l3_total += 1

        if status == "confirmed":
            self.l3_confirmed += 1
            self.symbol_stats[symbol]["l3_confirmed"] += 1
        elif status == "rejected":
            self.l3_rejected += 1
            if reason:
                self.l3_reject_reasons[reason] += 1
        elif status == "timeout":
            self.l3_timeout += 1
            self.l3_reject_reasons["超时"] += 1

    def record_notification_failure(self, feishu_failed: bool, email_failed: bool):
        """记录通知失败"""
        if feishu_failed and email_failed:
            self.both_failures += 1
        elif feishu_failed:
            self.feishu_failures += 1
        elif email_failed:
            self.email_failures += 1

    def add_risk_event(self, event_type: str, description: str, severity: str):
        """添加风险事件"""
        self.risk_events.append({
            "type": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now(_TZ_CST).isoformat(),
        })

    def get_pass_rate(self, passed: int, total: int) -> float:
        """计算通过率"""
        return (passed / total * 100) if total > 0 else 0.0

    def get_top_symbols(self, limit: int = 10) -> List[tuple]:
        """获取信号最多的品种 TopN"""
        sorted_symbols = sorted(
            self.symbol_stats.items(),
            key=lambda x: x[1]["l1_total"] + x[1]["l2_total"],
            reverse=True
        )
        return sorted_symbols[:limit]

    def to_email_body(self) -> str:
        """生成邮件正文（Markdown格式）"""
        lines = [
            f"## 📊 L1/L2/L3 总量与通过率",
            "",
        ]

        # 使用表格展示统计数据
        lines.extend([
            "| 门控阶段 | 总量 | 通过 | 通过率 |",
            "|---------|------|------|--------|",
            f"| L1 快速门控 | {self.l1_total} | {self.l1_passed} | {self.get_pass_rate(self.l1_passed, self.l1_total):.1f}% |",
            f"| L2 深审 | {self.l2_total} | {self.l2_passed} | {self.get_pass_rate(self.l2_passed, self.l2_total):.1f}% |",
            f"| L3 在线确认 | {self.l3_total} | {self.l3_confirmed} | {self.get_pass_rate(self.l3_confirmed, self.l3_total):.1f}% |",
            "",
        ])

        # L3 详细统计
        if self.l3_total > 0:
            lines.extend([
                f"**L3 详细**: 确认 {self.l3_confirmed} · 拒绝 {self.l3_rejected} · 超时 {self.l3_timeout}",
                "",
            ])

        # 品种分析
        lines.extend([
            "## 📈 品种命中率 Top 10",
            "",
        ])

        top_symbols = self.get_top_symbols(10)
        if top_symbols:
            for i, (symbol, stats) in enumerate(top_symbols, 1):
                l1_rate = self.get_pass_rate(stats["l1_passed"], stats["l1_total"])
                l2_rate = self.get_pass_rate(stats["l2_passed"], stats["l2_total"])
                lines.append(
                    f"**{i}. {symbol}** · L1 {stats['l1_total']}次({l1_rate:.0f}%) · "
                    f"L2 {stats['l2_total']}次({l2_rate:.0f}%) · "
                    f"L3确认 {stats['l3_confirmed']}次"
                )
        else:
            lines.append("暂无数据")

        lines.append("")

        # 拒绝原因 TopN
        has_reject_reasons = self.l1_reject_reasons or self.l2_reject_reasons or self.l3_reject_reasons

        if has_reject_reasons:
            lines.extend([
                "## 🚫 拒绝原因 Top 5",
                "",
            ])

            if self.l1_reject_reasons:
                lines.append("**L1 拒绝原因**")
                for i, (reason, count) in enumerate(self.l1_reject_reasons.most_common(5), 1):
                    lines.append(f"{i}. {reason} ({count}次)")
                lines.append("")

            if self.l2_reject_reasons:
                lines.append("**L2 拒绝原因**")
                for i, (reason, count) in enumerate(self.l2_reject_reasons.most_common(5), 1):
                    lines.append(f"{i}. {reason} ({count}次)")
                lines.append("")

            if self.l3_reject_reasons:
                lines.append("**L3 拒绝原因**")
                for i, (reason, count) in enumerate(self.l3_reject_reasons.most_common(5), 1):
                    lines.append(f"{i}. {reason} ({count}次)")
                lines.append("")

        # 失败通知统计
        total_failures = self.feishu_failures + self.email_failures + self.both_failures
        if total_failures > 0:
            lines.extend([
                "## ⚠️ 通知失败统计",
                "",
                f"飞书失败 {self.feishu_failures}次 · 邮件失败 {self.email_failures}次 · 双通道失败 {self.both_failures}次",
                "",
            ])

        # 风险摘要
        if self.risk_events:
            lines.extend([
                "## 🔴 风险摘要",
                "",
            ])

            # 按严重程度分组
            critical_events = [e for e in self.risk_events if e["severity"] == "critical"]
            warning_events = [e for e in self.risk_events if e["severity"] == "warning"]

            if critical_events:
                lines.append("**严重风险**")
                for i, event in enumerate(critical_events[:5], 1):
                    lines.append(f"{i}. [{event['type']}] {event['description']}")
                lines.append("")

            if warning_events:
                lines.append("**警告**")
                for i, event in enumerate(warning_events[:5], 1):
                    lines.append(f"{i}. [{event['type']}] {event['description']}")
                lines.append("")

        return "\n".join(lines)


def send_daily_summary(summary: DailyGateSummary) -> None:
    """
    发送每日汇总邮件

    Args:
        summary: 每日汇总统计对象
    """
    title = f"{summary.date} 决策服务门控日报"
    body = summary.to_email_body()

    event = DecisionEvent(
        event_type="DAILY",
        notify_level=NotifyLevel.NOTIFY,
        event_code=f"DAILY-GATE-{summary.date}",
        title=title,
        body=body,
    )

    dispatcher = get_dispatcher()
    dispatcher.dispatch(event)

    logger.info("Daily gate summary sent: date=%s", summary.date)


# 全局单例
_daily_summary: Optional[DailyGateSummary] = None


def get_daily_summary() -> DailyGateSummary:
    """获取当日汇总统计对象（单例）"""
    global _daily_summary

    now = datetime.now(_TZ_CST)
    current_date = now.strftime("%Y-%m-%d")

    # 如果是新的一天，重置统计
    if _daily_summary is None or _daily_summary.date != current_date:
        _daily_summary = DailyGateSummary()

    return _daily_summary
