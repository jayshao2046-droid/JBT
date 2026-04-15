"""研报置信度评审器 — phi4-reasoning:14b LLM 语义评级 + 飞书通知

优先使用 Studio phi4-reasoning:14b（192.168.31.142:11434）进行真实语义评级；
phi4 不可达或超时时自动 fallback 到三维加权数学算法，不中断主流程。

分级标准：
  >= 0.65 -> 可采信   (turquoise)
  0.40~0.64 -> 建议复核 (yellow)
  < 0.40  -> 建议忽略  (orange)
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import httpx

from .config import ResearcherConfig

if TYPE_CHECKING:
    from .models import ResearchReport


class ReportReviewer:
    """对每份研报进行 phi4 LLM 语义置信度评级，写回 daily_stats，并发飞书通知。"""

    # 数学 fallback 权重（phi4 不可达时使用）
    _W_NEWS        = 0.30
    _W_TREND       = 0.40
    _W_CONSISTENCY = 0.30

    def __init__(self, feishu_webhook: str = "", stats_tracker=None):
        self.feishu_webhook = feishu_webhook or os.getenv("FEISHU_WEBHOOK_URL", "")
        self.stats_tracker = stats_tracker  # DailyStatsTracker 实例，可为 None

    # ── 公开入口 ─────────────────────────────────────────────────────────

    async def review_and_notify(self, report: "ResearchReport") -> Dict[str, Any]:
        """
        对报告评级并发飞书通知。

        Returns:
            {"confidence": 0.72, "reason": "...", "level": "可采信", "fallback": False}
        """
        confidence, reason, fallback_used = self._evaluate(report)
        level = self._level(confidence)

        # 回写 daily_stats
        if self.stats_tracker:
            self.stats_tracker.record_decision_review(
                report_id=report.report_id,
                confidence=confidence,
                reason=reason,
            )

        # 飞书通知（静默期跳过）
        if not self._is_silent():
            await self._send_feishu(report, confidence, level, reason, fallback_used)

        return {"confidence": confidence, "reason": reason, "level": level, "fallback": fallback_used}

    # ── phi4 LLM 评级 ─────────────────────────────────────────────────────

    def _build_phi4_summary(self, report: "ResearchReport") -> Dict[str, Any]:
        """从研报提取 phi4 所需摘要信息"""
        symbol_data = report.futures_summary.get("symbols", {})
        bullish = sum(1 for v in symbol_data.values() if isinstance(v, dict) and v.get("trend") in ("偏多", "上涨", "多头"))
        bearish = sum(1 for v in symbol_data.values() if isinstance(v, dict) and v.get("trend") in ("偏空", "下跌", "空头"))
        neutral = len(symbol_data) - bullish - bearish
        news_count = report.crawler_stats.get("articles_processed", 0)
        overview = report.futures_summary.get("market_overview", "")[:400]
        return {
            "symbol_count": len(symbol_data),
            "news_count": news_count,
            "market_overview": overview,
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
        }

    def _call_phi4(self, summary: Dict[str, Any]) -> Tuple[float, str]:
        """
        调用 Studio phi4-reasoning:14b 进行语义置信度评级。
        返回 (confidence, reason)；失败则抛出异常。
        """
        prompt = (
            "你是量化研究分析师。请对以下期货市场研究报告进行置信度评级。\n\n"
            f"研报摘要：\n"
            f"- 覆盖品种数：{summary['symbol_count']}\n"
            f"- 新闻来源数：{summary['news_count']}\n"
            f"- 市场研判（节选）：{summary['market_overview']}\n"
            f"- 品种趋势分布：多头={summary['bullish']} 空头={summary['bearish']} 中性={summary['neutral']}\n\n"
            "请根据研报的信息丰富度、逻辑一致性、多空依据充分性，给出综合置信度评分（0.0~1.0）和简短理由。\n\n"
            '输出格式（仅 JSON，不要加其他文字）：\n'
            '{"confidence": 0.72, "reason": "信息来源充分，多空逻辑清晰"}'
        )
        payload = {
            "model": ResearcherConfig.PHI4_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        resp = httpx.post(
            ResearcherConfig.PHI4_API_URL,
            json=payload,
            timeout=ResearcherConfig.PHI4_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "{}")
        data = json.loads(raw)
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        reason = str(data.get("reason", "phi4 语义评级"))
        return confidence, reason

    # ── 数学 fallback ─────────────────────────────────────────────────────

    def _math_score(self, report: "ResearchReport") -> Tuple[float, str]:
        """数学三维加权评分（phi4 不可达时使用）"""
        dims: Dict[str, float] = {}

        sources = max(report.crawler_stats.get("sources_crawled", 1), 1)
        articles = report.crawler_stats.get("articles_processed", 0)
        dims["news_relevance"] = min(articles / (sources * 3), 1.0)

        symbol_data = report.futures_summary.get("symbols", {})
        confidences = [
            float(v.get("confidence", 0.5))
            for v in symbol_data.values()
            if isinstance(v, dict)
        ]
        dims["trend_alignment"] = sum(confidences) / len(confidences) if confidences else 0.5

        trends = [v.get("trend", "震荡") for v in symbol_data.values() if isinstance(v, dict)]
        if trends:
            from collections import Counter
            counts = Counter(trends)
            total = len(trends)
            k = len(counts)
            if k == 1:
                consistency = 1.0
            else:
                entropy = -sum((c / total) * math.log(c / total) for c in counts.values())
                max_entropy = math.log(k)
                consistency = 1.0 - (entropy / max_entropy)
        else:
            consistency = 0.5
        dims["cross_consistency"] = round(consistency, 4)

        score = round(
            dims["news_relevance"]     * self._W_NEWS
            + dims["trend_alignment"]  * self._W_TREND
            + dims["cross_consistency"]* self._W_CONSISTENCY,
            4,
        )
        reason = (
            f"数学降级(phi4不可达): "
            f"news={dims['news_relevance']:.2f}x{self._W_NEWS}, "
            f"trend={dims['trend_alignment']:.2f}x{self._W_TREND}, "
            f"consistency={dims['cross_consistency']:.2f}x{self._W_CONSISTENCY}"
        )
        return score, reason

    # ── 统一评级入口 ──────────────────────────────────────────────────────

    def _evaluate(self, report: "ResearchReport") -> Tuple[float, str, bool]:
        """
        尝试 phi4 评级，失败则 fallback 数学算法。
        返回 (confidence, reason, fallback_used)
        """
        summary = self._build_phi4_summary(report)
        try:
            confidence, reason = self._call_phi4(summary)
            return confidence, reason, False
        except Exception:
            confidence, reason = self._math_score(report)
            return confidence, reason, True

    @staticmethod
    def _level(confidence: float) -> str:
        if confidence >= 0.65:
            return "可采信"
        if confidence >= 0.40:
            return "建议复核"
        return "建议忽略"

    @staticmethod
    def _is_silent() -> bool:
        now = datetime.now()
        return (now.hour == 23 and now.minute >= 30) or now.hour < 8

    # ── 飞书通知 ─────────────────────────────────────────────────────────

    async def _send_feishu(
        self,
        report: "ResearchReport",
        confidence: float,
        level: str,
        reason: str,
        fallback_used: bool,
    ) -> None:
        if not self.feishu_webhook:
            return

        if confidence >= 0.65:
            template, icon = "turquoise", "🟢"
        elif confidence >= 0.40:
            template, icon = "yellow", "🟡"
        else:
            template, icon = "orange", "🔴"

        hour = report.generated_at.strftime("%H:%M")
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbols_count = len(report.futures_summary.get("symbols", {}))
        tag = "（数学降级）" if fallback_used else "（phi4 语义）"

        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": (
                            f"{icon} [JBT 研报评级] {report.date} {hour} — "
                            f"{level} ({confidence:.0%})"
                        ),
                    },
                    "template": template,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": (
                                f"**报告ID** `{report.report_id}`\n"
                                f"**置信度** `{confidence:.2f}` — **{level}** {tag}\n"
                                f"**覆盖品种** {symbols_count} 个"
                            ),
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**评级理由**\n{reason}",
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT 研报评级 | {ts} | {'Studio phi4' if not fallback_used else 'Alienware 数学'}",
                            }
                        ],
                    },
                ],
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.feishu_webhook, json=card, timeout=ResearcherConfig.HTTP_TIMEOUT_MEDIUM)
        except Exception:
            pass
