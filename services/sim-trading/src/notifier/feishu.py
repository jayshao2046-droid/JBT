"""
FeishuNotifier — TASK-0014 P1
发送飞书 Webhook 卡片通知，从环境变量读取配置，无真实凭证。
"""
import json
import logging
import os
import urllib.request
import urllib.error
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dispatcher import RiskEvent

logger = logging.getLogger(__name__)

_LEVEL_COLOR = {
    "P0": "red",
    "P1": "orange",
    "P2": "green",
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

        color = _LEVEL_COLOR.get(event.risk_level, "blue")
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"[{event.stage_preset.upper()}-{event.risk_level}] {event.event_code}",
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": (
                                f"**task_id**: {event.task_id}\n"
                                f"**stage_preset**: {event.stage_preset}\n"
                                f"**risk_level**: {event.risk_level}\n"
                                f"**account_id**: {event.account_id}\n"
                                f"**strategy_id**: {event.strategy_id}\n"
                                f"**symbol**: {event.symbol}\n"
                                f"**signal_id**: {event.signal_id}\n"
                                f"**trace_id**: {event.trace_id}\n"
                                f"**event_code**: {event.event_code}\n"
                                f"**reason**: {event.reason}"
                            ),
                        },
                    }
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
        except urllib.error.URLError as exc:
            logger.error("FeishuNotifier URLError for event %s: %s", event.event_code, exc)
            return False
        except Exception as exc:
            logger.error("FeishuNotifier unexpected error for event %s: %s", event.event_code, exc)
            return False
