"""
DecisionFeishuNotifier — TASK-0021 F batch
飞书 Webhook 卡片通知，遵循 JBT 统一颜色标准。
"""
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dispatcher import DecisionEvent, NotifyLevel

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))

# ── JBT 统一颜色映射 ─────────────────────────────────────────────────────────
_LEVEL_COLOR = {
    "P0": "red",
    "P1": "orange",
    "P2": "yellow",
    "SIGNAL": "grey",
    "RESEARCH": "blue",
    "NOTIFY": "turquoise",
}

_LEVEL_ICON = {
    "P0": "🚨",
    "P1": "⚠️",
    "P2": "🔔",
    "SIGNAL": "📊",
    "RESEARCH": "📈",
    "NOTIFY": "📣",
}


class DecisionFeishuNotifier:
    """飞书 Webhook 通道。通过 NOTIFY_FEISHU_ENABLED 整体开关。"""

    def __init__(self) -> None:
        raw = os.environ.get("NOTIFY_FEISHU_ENABLED", "false").strip().lower()
        self._enabled = raw == "true"
        self._webhook_url: str = os.environ.get("FEISHU_WEBHOOK_URL", "")

    def send(self, event: "DecisionEvent") -> bool:
        if not self._enabled:
            logger.debug("FeishuNotifier disabled, skipping %s", event.event_code)
            return True

        if not self._webhook_url:
            logger.error("FEISHU_WEBHOOK_URL not set")
            return False

        level_str = event.notify_level.value if hasattr(event.notify_level, "value") else str(event.notify_level)
        color = _LEVEL_COLOR.get(level_str, "blue")
        icon = _LEVEL_ICON.get(level_str, "📋")
        ts = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")

        # 追踪信息行
        track_parts = []
        if event.strategy_id:
            track_parts.append(f"**策略:** {event.strategy_id}")
        if event.model_id:
            track_parts.append(f"**模型:** {event.model_id}")
        if event.signal_id:
            track_parts.append(f"**信号:** {event.signal_id}")
        if event.session_id:
            track_parts.append(f"**会话:** {event.session_id}")
        if event.trace_id:
            track_parts.append(f"**追踪:** {event.trace_id}")
        track_line = " | ".join(track_parts) if track_parts else "-"

        body_text = f"**{event.event_code}**\n{event.body}"
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} [DECISION-{level_str}] {event.title}",
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": body_text,
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": track_line,
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT Decision | {ts}",
                            }
                        ],
                    },
                ],
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode("utf-8")
                logger.debug("Feishu response: %s", resp_body)
            try:
                resp_json = json.loads(resp_body)
                if resp_json.get("code", 0) != 0:
                    logger.error(
                        "FeishuNotifier API error code=%s msg=%s",
                        resp_json.get("code"), resp_json.get("msg"),
                    )
                    return False
            except (json.JSONDecodeError, AttributeError):
                pass
            return True
        except urllib.error.URLError as exc:
            logger.error("FeishuNotifier URLError event=%s: %s", event.event_code, exc)
            return False
        except Exception as exc:
            logger.error("FeishuNotifier unexpected error event=%s: %s", event.event_code, exc)
            return False


class FeishuNotifier:
    """简化的飞书通知器，用于研究员评级通知"""

    def __init__(self) -> None:
        self._webhook_url: str = os.environ.get("FEISHU_WEBHOOK_URL", "")

    async def send_researcher_score(
        self,
        report_type: str,
        report_id: str,
        score: float,
        date: str,
        hour: int
    ) -> bool:
        """
        发送研究员报告评级通知

        Args:
            report_type: 报告类型（期货/股票/新闻等）
            report_id: 报告ID
            score: phi4 评分（0-100）
            date: 日期
            hour: 小时

        Returns:
            True 表示发送成功
        """
        if not self._webhook_url:
            logger.warning("FEISHU_WEBHOOK_URL not set, skip researcher score notification")
            return False

        ts = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")

        # 根据评分选择颜色
        if score >= 80:
            color = "green"
            icon = "✅"
        elif score >= 60:
            color = "blue"
            icon = "📊"
        elif score >= 40:
            color = "yellow"
            icon = "⚠️"
        else:
            color = "red"
            icon = "❌"

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} 研究员报告评级 | {report_type}",
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**报告ID:** {report_id}\n**评分:** {score:.1f}/100\n**时段:** {date} {hour:02d}:00",
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"phi4 评级 | {ts}",
                            }
                        ],
                    },
                ],
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode("utf-8")
                logger.debug("Feishu response: %s", resp_body)
            return True
        except Exception as exc:
            logger.error("FeishuNotifier send_researcher_score error: %s", exc)
            return False

