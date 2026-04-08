"""JBT 数据端飞书通知 — 三群路由 + 卡片发送。

Webhook 路由：
  报警群 (FEISHU_ALERT_WEBHOOK_URL) ← P0/P1/P2
  交易群 (FEISHU_TRADE_WEBHOOK_URL) ← 采集通知/数据新鲜度
  资讯群 (FEISHU_INFO_WEBHOOK_URL)  ← 新闻/设备健康/系统通知

遵循 JBT 统一通知颜色与卡片标准。
必须使用 msg_type: "interactive" + 卡片结构，禁止纯文本。
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from services.data.src.notify.dispatcher import DataEvent

logger = logging.getLogger(__name__)


class FeishuSender:
    """飞书卡片发送器。直接发送预构建的 card payload。"""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._timeout = timeout

    def send(self, *, webhook_url: str, event: "DataEvent") -> bool:
        """发送 DataEvent 对应的飞书卡片。

        card payload 由 card_templates 构建，此处只做 HTTP POST。
        """
        if not webhook_url:
            logger.warning("feishu webhook_url is empty, skipping: %s", event.event_code)
            return False

        from services.data.src.notify.card_templates import alert_card
        from services.data.src.notify.dispatcher import NotifyType

        # 根据 event 类型构建 card — 调用方也可传入预构建的 card
        card = alert_card(
            level=event.notify_type.value,
            title=event.title,
            body_md=event.body_md,
            trace_md=event.trace_md,
        )
        return self.send_card(webhook_url=webhook_url, payload=card)

    def send_card(self, webhook_url: str = "", payload: dict[str, Any] | None = None, **kw: Any) -> bool:
        """直接发送任意 card payload 到指定 webhook。

        支持位置参数: send_card(url, card) 或关键字: send_card(webhook_url=url, payload=card)
        """
        url = webhook_url or kw.get("webhook_url", "")
        data = payload or kw.get("payload")
        if not url or not data:
            logger.warning("feishu webhook_url/payload empty, skipping")
            return False

        try:
            resp = httpx.post(url, json=data, timeout=self._timeout)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code", 0) != 0:
                logger.error("feishu API error: %s", result)
                return False
            logger.info("feishu card sent OK")
            return True
        except Exception as exc:
            logger.error("feishu send failed: %s", exc)
            return False

