"""
DecisionFeishuNotifier — TASK-0021 F batch + 三群路由重写
飞书 Webhook 卡片通知，遵循 JBT 统一颜色标准 + 三群路由。
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

# 级别标签（中文）
_LEVEL_LABEL = {
    "P0": "报警-P0",
    "P1": "报警-P1",
    "P2": "告警-P2",
    "SIGNAL": "信号",
    "RESEARCH": "研究",
    "NOTIFY": "通知",
}

# 事件类型标签（中文）
_EVENT_TYPE_LABEL = {
    "RESEARCH": "研究",
    "SIGNAL": "信号",
    "STRATEGY": "策略",
    "DAILY": "日报",
    "SYSTEM": "系统",
    "HEALTH": "健康",
    "GATE": "门控",
}


def _first_nonempty(*values: str) -> str:
    for v in values:
        if v:
            return v
    return ""


def _get_webhook_url(level_str: str) -> str:
    """按级别选择三群 Webhook，降级到通用 URL。"""
    if level_str in ("P0", "P1", "P2"):
        return _first_nonempty(
            os.environ.get("FEISHU_ALERT_WEBHOOK_URL", ""),
            os.environ.get("FEISHU_WEBHOOK_URL", ""),
        )
    if level_str == "SIGNAL":
        return _first_nonempty(
            os.environ.get("FEISHU_TRADE_WEBHOOK_URL", ""),
            os.environ.get("FEISHU_WEBHOOK_URL", ""),
        )
    # RESEARCH / NOTIFY → 资讯群
    return _first_nonempty(
        os.environ.get("FEISHU_INFO_WEBHOOK_URL", ""),
        os.environ.get("FEISHU_WEBHOOK_URL", ""),
    )


class DecisionFeishuNotifier:
    """飞书三群路由通知器。通过 NOTIFY_FEISHU_ENABLED 整体开关。"""

    def __init__(self) -> None:
        raw = os.environ.get("NOTIFY_FEISHU_ENABLED", "false").strip().lower()
        self._enabled = raw == "true"
        # 保留向后兼容属性，供 dispatcher 检查 webhook 配置
        self._webhook_url: str = os.environ.get("FEISHU_WEBHOOK_URL", "")

    def send(self, event: "DecisionEvent") -> bool:
        if not self._enabled:
            logger.debug("FeishuNotifier disabled, skipping %s", event.event_code)
            return True

        level_str = event.notify_level.value if hasattr(event.notify_level, "value") else str(event.notify_level)
        webhook_url = _get_webhook_url(level_str)
        if not webhook_url:
            logger.error("飞书 Webhook 未配置 (level=%s)", level_str)
            return False

        color = _LEVEL_COLOR.get(level_str, "blue")
        icon = _LEVEL_ICON.get(level_str, "📋")
        level_label = _LEVEL_LABEL.get(level_str, level_str)
        event_type_label = _EVENT_TYPE_LABEL.get(event.event_type, event.event_type)
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
        title_text = f"JBT 决策 {icon} [{level_label}-{event_type_label}] {event.title}"
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title_text,
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
                                "content": f"JBT-决策 | {ts}",
                            }
                        ],
                    },
                ],
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
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
        # 研究员评分通知发到资讯群
        self._webhook_url: str = _first_nonempty(
            os.environ.get("FEISHU_INFO_WEBHOOK_URL", ""),
            os.environ.get("FEISHU_WEBHOOK_URL", ""),
        )

    async def send_researcher_score(
        self,
        report_type: str,
        report_id: str,
        score: float,
        date: str,
        hour: int,
        reasoning: str = "",
        seen_content: str = "",
    ) -> bool:
        """
        发送研究员报告评级通知

        Args:
            report_type: 报告类型（期货/股票/新闻等）
            report_id: 报告ID
            score: qwen3 评分（0-100）
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

        # 避免卡片过长，摘要截断展示
        safe_seen = (seen_content or "无").replace("\n", " ").strip()
        safe_reasoning = (reasoning or "无").replace("\n", " ").strip()
        if len(safe_seen) > 180:
            safe_seen = safe_seen[:177] + "..."
        if len(safe_reasoning) > 180:
            safe_reasoning = safe_reasoning[:177] + "..."

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
                            "content": (
                                f"**报告ID:** {report_id}\n"
                                f"**评分:** {score:.1f}/100\n"
                                f"**时段:** {date} {hour:02d}:00"
                            ),
                        },
                    },
                    {
                        "tag": "hr",
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": (
                                f"**看到内容:** {safe_seen}\n"
                                f"**评分理由:** {safe_reasoning}"
                            ),
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT-决策 | {ts}",
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

