"""
FeishuNotifier — TASK-NOTIFY-20260423-A
飞书三群路由卡片通知。
- FEISHU_ALERT_WEBHOOK_URL → 报警群 (P0/P1/P2 风控事件)
- FEISHU_TRADE_WEBHOOK_URL → 交易群 (成交/订单/信号/门控)
- FEISHU_INFO_WEBHOOK_URL  → 资讯群 (心跳/系统/收盘汇总)
回退：三个 URL 缺失时统一用 FEISHU_WEBHOOK_URL。
标题格式：JBT 模拟交易 {icon} [{级别}-{类别}] {标题}
落款：JBT-模拟交易 | YYYY-MM-DD HH:MM:SS
"""
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .dispatcher import RiskEvent

logger = logging.getLogger(__name__)

CN_TZ = timezone(timedelta(hours=8))

# ---- 颜色 / 图标 映射（全服务统一规范） ----
_LEVEL_COLOR = {"P0": "red", "P1": "orange", "P2": "yellow"}
_LEVEL_ICON  = {"P0": "🚨", "P1": "⚠️",     "P2": "🔔"}

_CATEGORY_COLOR = {
    "TRADE":      "grey",
    "ORDER":      "grey",
    "SIGNAL":     "blue",
    "GATE":       "blue",
    "NOTIFY":     "turquoise",
    "SYSTEM":     "turquoise",
    "SESSION":    "turquoise",
    "RESEARCH":   "blue",
}
_CATEGORY_ICON = {
    "TRADE":      "📊",
    "ORDER":      "📊",
    "SIGNAL":     "📈",
    "GATE":       "📈",
    "NOTIFY":     "📣",
    "SYSTEM":     "📣",
    "SESSION":    "📣",
    "RESEARCH":   "📈",
}
# 中文类别标签
_CATEGORY_LABEL = {
    "TRADE":    "成交",
    "ORDER":    "订单",
    "SIGNAL":   "信号",
    "GATE":     "门控",
    "NOTIFY":   "通知",
    "SYSTEM":   "系统",
    "SESSION":  "收盘",
    "RESEARCH": "研报",
}


def _cn_now() -> str:
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _get_webhook(category: str, risk_level: str) -> str:
    """按 category / risk_level 选择目标 Webhook URL。"""
    fallback = os.environ.get("FEISHU_WEBHOOK_URL", "")
    # 报警群：P0/P1/P2 风控
    if risk_level in ("P0", "P1", "P2"):
        return os.environ.get("FEISHU_ALERT_WEBHOOK_URL", fallback)
    # 交易群：成交、订单、信号、门控
    if category in ("TRADE", "ORDER", "SIGNAL", "GATE"):
        return os.environ.get("FEISHU_TRADE_WEBHOOK_URL", fallback)
    # 资讯群：其余（心跳/收盘汇总/系统）
    return os.environ.get("FEISHU_INFO_WEBHOOK_URL", fallback)


def _make_card(event: "RiskEvent", pending_banner: str = "") -> dict:
    """构造标准飞书卡片 payload。"""
    ts = _cn_now()
    category = (event.category or "NOTIFY").upper()
    level = event.risk_level or ""

    # 选颜色 & 图标
    if level in _LEVEL_COLOR:
        color = _LEVEL_COLOR[level]
        icon  = _LEVEL_ICON[level]
        type_label = level
    else:
        color = _CATEGORY_COLOR.get(category, "turquoise")
        icon  = _CATEGORY_ICON.get(category, "📣")
        type_label = _CATEGORY_LABEL.get(category, category)

    cat_label = _CATEGORY_LABEL.get(category, category)
    title_text = event.message or event.reason or event.event_code

    # 核心信息区
    core_lines = []
    if level in ("P0", "P1", "P2"):
        core_lines.append(f"**风险等级：** {level}")
    core_lines.append(f"**事件代码：** {event.event_code}")
    if event.reason:
        core_lines.append(f"**原因：** {event.reason}")
    if event.account_id:
        core_lines.append(f"**账户：** {event.account_id}")
    if event.symbol:
        core_lines.append(f"**品种：** {event.symbol}")
    if event.message and event.message != event.reason:
        core_lines.append(f"**说明：** {event.message}")
    if pending_banner:
        core_lines.append(f"\n{pending_banner}")
    core_md = "\n".join(core_lines)

    # 追踪信息区
    trace_lines = []
    if event.strategy_id:
        trace_lines.append(f"**策略：** {event.strategy_id}")
    if event.signal_id:
        trace_lines.append(f"**信号 ID（signal_id）：** {event.signal_id}")
    if event.trace_id:
        trace_lines.append(f"**追踪 ID（trace_id）：** {event.trace_id}")
    trace_lines.append(f"**任务：** {event.task_id}　　**环境：** {event.stage_preset}")
    trace_md = "\n".join(trace_lines) if trace_lines else f"**任务：** {event.task_id}"

    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": core_md}},
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md", "content": trace_md}},
        {"tag": "hr"},
        {"tag": "note", "elements": [{"tag": "plain_text", "content": f"JBT-模拟交易 | {ts}"}]},
    ]

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"JBT 模拟交易 {icon} [{type_label}-{cat_label}] {title_text}",
                },
                "template": color,
            },
            "elements": elements,
        },
    }


def _do_send(webhook_url: str, payload: dict, event_code: str) -> bool:
    """底层 HTTP 推送，返回是否成功。"""
    if not webhook_url:
        logger.error("[feishu] Webhook URL 未配置，事件 %s 无法推送", event_code)
        return False
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            webhook_url, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8")
        logger.debug("[feishu] 响应: %s", resp_body)
        try:
            resp_json = json.loads(resp_body)
            if resp_json.get("code", 0) != 0:
                logger.error("[feishu] API 错误 code=%s msg=%s",
                             resp_json.get("code"), resp_json.get("msg"))
                return False
        except (json.JSONDecodeError, AttributeError):
            pass
        return True
    except urllib.error.URLError as exc:
        logger.error("[feishu] 网络错误 事件=%s: %s", event_code, exc)
        return False
    except Exception as exc:
        logger.error("[feishu] 未知错误 事件=%s: %s", event_code, exc)
        return False


class FeishuNotifier:
    """
    飞书三群路由通知器。
    通过 NOTIFY_FEISHU_ENABLED 可整体禁用。
    """

    def __init__(self) -> None:
        raw = os.environ.get("NOTIFY_FEISHU_ENABLED", "false").strip().lower()
        self._enabled = raw == "true"

    def send(self, event: "RiskEvent", pending_banner: str = "") -> bool:
        """
        发送飞书卡片。
        - disabled → 直接返回 True（跳过即通过）
        - 按 category / risk_level 路由到对应群
        - 成功 → True；失败 → False（上层记 alarm.log）
        """
        if not self._enabled:
            logger.debug("[feishu] 通道已禁用，跳过事件 %s", event.event_code)
            return True

        category = (event.category or "NOTIFY").upper()
        webhook_url = _get_webhook(category, event.risk_level)
        payload = _make_card(event, pending_banner=pending_banner)
        return _do_send(webhook_url, payload, event.event_code)


def send_raw_feishu_card(webhook_url: str, payload: dict) -> bool:
    """外部直接调用：发送自定义飞书卡片（不经过 FeishuNotifier）。"""
    return _do_send(webhook_url, payload, "raw_card")
