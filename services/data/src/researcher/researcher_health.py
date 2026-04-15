"""研究员健康度飞书卡片 — 每 2 小时推送

格式类比 data 端健康报告：
  Header:  [研究员健康度] YYYY-MM-DD HH:MM
  守护进程: researcher :8199 / phi4(Studio) 可达性
  当日研报: 已生成 N 份 / 失败 N 份
  phi4 评级分布: 可采信 / 建议复核 / 建议忽略
  上次研报: HH:MM  推送 Mini: ✅/❌
  Footer:  JBT researcher | Alienware | YYYY-MM-DD HH:MM | 下次推送: H+2:00

颜色策略：
  - 全天失败数 > 3，或 phi4 可采信率 < 50%（有数据时）-> yellow
  - 其余 -> turquoise
"""

from __future__ import annotations

import datetime
import socket
from typing import Optional

import httpx

from .config import ResearcherConfig


class ResearcherHealth:
    """每 2 小时飞书健康度卡片"""

    def __init__(self, feishu_webhook: str = "", stats_tracker=None):
        self.feishu_webhook = feishu_webhook
        self.stats_tracker = stats_tracker  # DailyStatsTracker 实例，可为 None

    # ── 公开入口 ─────────────────────────────────────────────────────────

    async def send_health_card(self) -> None:
        """生成并推送健康度飞书卡片"""
        if not self.feishu_webhook:
            return

        now = datetime.datetime.now()
        next_push = (now + datetime.timedelta(hours=ResearcherConfig.HEALTH_INTERVAL_HOURS)).strftime("%H:%M")

        # 收集指标
        today = self.stats_tracker.get_today() if self.stats_tracker else {}
        generated = today.get("reports_generated", 0)
        failed    = today.get("reports_failed", 0)
        hourly    = today.get("hourly", [])

        # 置信度分布（从 hourly 拿 decision_confidence）
        confidences = [
            h.get("decision_confidence") or h.get("confidence")
            for h in hourly
            if (h.get("decision_confidence") or h.get("confidence")) is not None
        ]
        accept = sum(1 for c in confidences if c >= 0.65)
        warn   = sum(1 for c in confidences if 0.40 <= c < 0.65)
        ignore = sum(1 for c in confidences if c < 0.40)

        # 进程检活
        researcher_ok = self._check_tcp("127.0.0.1", 8199)
        phi4_ok       = self._check_phi4()

        # 上次研报
        last_time       = "—"
        last_push_ok    = None
        if hourly:
            last = hourly[-1]
            last_time    = last.get("hour_label") or f"{last.get('hour', '?'):02d}:00"
            last_push_ok = last.get("push_success")

        # 决定卡片颜色
        if failed > 3 or (confidences and accept / len(confidences) < 0.50):
            template = "yellow"
        else:
            template = "turquoise"

        researcher_status = "🟢 运行中" if researcher_ok else "🔴 已停止"
        phi4_status       = "🟢 可达"    if phi4_ok    else "🔴 不可达"

        push_status = ""
        if last_push_ok is True:
            push_status = "   推送 Mini: ✅"
        elif last_push_ok is False:
            push_status = "   推送 Mini: ❌"

        content_lines = [
            f"**守护进程**　researcher :8199 {researcher_status}　phi4(Studio) {phi4_status}",
            f"**当日研报**　已生成 {generated} 份　失败 {failed} 份",
            f"**phi4 评级分布**　🟢 可采信 {accept} 份　🟡 建议复核 {warn} 份　🔴 建议忽略 {ignore} 份",
            f"**上次研报** {last_time}{push_status}",
        ]

        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        footer = f"JBT researcher | Alienware | {ts} | 下次推送: {next_push}"

        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🔬 JBT 研究员健康报告 | {now.strftime('%H:%M')}",
                    },
                    "template": template,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "\n".join(content_lines),
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [{"tag": "plain_text", "content": footer}],
                    },
                ],
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.feishu_webhook, json=card, timeout=ResearcherConfig.HTTP_TIMEOUT_MEDIUM)
        except Exception:
            pass

    # ── 检活辅助 ─────────────────────────────────────────────────────────

    @staticmethod
    def _check_tcp(host: str, port: int, timeout: float = ResearcherConfig.HTTP_TIMEOUT_SHORT) -> bool:
        """TCP 检活"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    @staticmethod
    def _check_phi4() -> bool:
        """检查 Studio phi4 是否可达"""
        try:
            resp = httpx.post(
                ResearcherConfig.PHI4_API_URL,
                json={
                    "model": ResearcherConfig.PHI4_MODEL,
                    "prompt": "ping",
                    "stream": False,
                },
                timeout=ResearcherConfig.HTTP_TIMEOUT_SHORT,
            )
            return resp.status_code == 200
        except Exception:
            return False
