"""
FeishuNotifier — TASK-0014 P1
发送飞书 Webhook 卡片通知，从环境变量读取配置，无真实凭证。
"""
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dispatcher import RiskEvent

logger = logging.getLogger(__name__)

_LEVEL_COLOR = {
    "P0": "red",
    "P1": "orange",
    "P2": "yellow",
}

_LEVEL_ICON = {
    "P0": "🚨",
    "P1": "⚠️",
    "P2": "🔔",
}


class FeishuNotifier:
    """飞书 Webhook 通道。通过 NOTIFY_FEISHU_ENABLED 可整体禁用。"""

    def __init__(self) -> None:
        raw = os.environ.get("NOTIFY_FEISHU_ENABLED", "false").strip().lower()
        self._enabled = raw == "true"
        self._webhook_url: str = os.environ.get("FEISHU_WEBHOOK_URL", "")

    def send(self, event: "RiskEvent") -> bool:
        """
        发送飞书卡片通知。
        - disabled → 直接返回 True（跳过即通过）
        - 成功发送 → True
        - 失败 → logging.error + 返回 False
        """
        if not self._enabled:
            logger.debug("FeishuNotifier disabled, skipping event %s", event.event_code)
            return True

        if not self._webhook_url:
            logger.error("FEISHU_WEBHOOK_URL is not set, cannot send notification")
            return False

        color = _LEVEL_COLOR.get(event.risk_level, "turquoise")
        icon = _LEVEL_ICON.get(event.risk_level, "📣")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} [SIM-{event.risk_level}] {event.event_code}: {event.message or event.reason}",
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": (
                                f"**账户:** {event.account_id or '-'}\n"
                                f"**事件代码:** {event.event_code}\n"
                                f"**原因:** {event.reason}"
                            ),
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": (
                                f"**任务:** {event.task_id} | **环境:** {event.stage_preset} | **级别:** {event.risk_level}\n"
                                f"**策略:** {event.strategy_id or '-'} | **品种:** {event.symbol or '-'}\n"
                                f"**信号:** {event.signal_id or '-'} | **追踪:** {event.trace_id or '-'}"
                            ),
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT SimTrading | {ts}",
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
                    logger.error("FeishuNotifier API error code=%s msg=%s", resp_json.get("code"), resp_json.get("msg"))
                    return False
            except (json.JSONDecodeError, AttributeError):
                pass
            return True
        except urllib.error.URLError as exc:
            logger.error("FeishuNotifier URLError for event %s: %s", event.event_code, exc)
            return False
        except Exception as exc:
            logger.error("FeishuNotifier unexpected error for event %s: %s", event.event_code, exc)
            return False
