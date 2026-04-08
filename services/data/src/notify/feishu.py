"""JBT 数据端飞书通知 — 全新实现（非迁移）。

遵循 JBT 统一通知颜色与卡片标准（card_header_colors）。
必须使用 msg_type: "interactive" + 卡片结构，禁止纯文本。

通知类型 → 模板颜色映射：
  报警 P0 → red       🚨
  报警 P1 → orange    ⚠️
  报警 P2 → yellow    🔔
  交易   → grey       📊
  资讯   → blue       📈
  新闻   → wathet     📰
  通知   → turquoise  📣

此模块需 Jay.S 签单确认后才正式嵌入启动服务。
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# 通知类型 → (飞书 template, 图标)
_TYPE_MAP: dict[str, tuple[str, str]] = {
    "P0": ("red", "🚨"),
    "P1": ("orange", "⚠️"),
    "P2": ("yellow", "🔔"),
    "TRADE": ("grey", "📊"),
    "INFO": ("blue", "📈"),
    "NEWS": ("wathet", "📰"),
    "NOTIFY": ("turquoise", "📣"),
}

SERVICE_NAME = "JBT data-service"


def _build_card(
    *,
    title: str,
    notify_type: str,
    body_md: str,
    footer_info: str = "",
    trace_md: str = "",
) -> dict[str, Any]:
    """Build a Feishu interactive card."""
    template, icon = _TYPE_MAP.get(notify_type, ("turquoise", "📣"))
    stage = "DATA"

    elements: list[dict[str, Any]] = [
        {"tag": "div", "text": {"tag": "lark_md", "content": body_md}},
        {"tag": "hr"},
    ]
    if trace_md:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": trace_md}})
        elements.append({"tag": "hr"})

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append({
        "tag": "note",
        "elements": [
            {"tag": "plain_text", "content": f"{SERVICE_NAME} | {timestamp}"}
        ],
    })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"{icon} [{stage}-{notify_type}] {title}"},
                "template": template,
            },
            "elements": elements,
        },
    }


def send_feishu(
    *,
    webhook_url: str,
    title: str,
    notify_type: str = "NOTIFY",
    body_md: str,
    trace_md: str = "",
    timeout: float = 10.0,
) -> bool:
    """Send a Feishu card notification.

    Returns True if sent successfully, False otherwise.
    """
    if not webhook_url:
        logger.warning("feishu webhook_url is empty, skipping notification")
        return False

    card = _build_card(
        title=title,
        notify_type=notify_type,
        body_md=body_md,
        trace_md=trace_md,
    )

    try:
        resp = httpx.post(webhook_url, json=card, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code", 0) != 0:
            logger.error("feishu API error: %s", result)
            return False
        logger.info("feishu notification sent: %s", title)
        return True
    except Exception as exc:
        logger.error("feishu send failed: %s — %s", title, exc)
        return False
