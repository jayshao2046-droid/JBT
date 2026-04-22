"""
trade_push.py — TASK-NOTIFY-20260423-A
成交回报 / 订单状态即时推送器。
无静默窗口限制，无去重，直接推飞书交易群（FEISHU_TRADE_WEBHOOK_URL）。
"""
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# 中国标准时区（UTC+8）
CN_TZ = timezone(timedelta(hours=8))

# 连续拒单计数器（同一 symbol 连续拒单 >=5 升级 ALERT）
_reject_count: dict = {}
_REJECT_ESCALATION_THRESHOLD = 5


def _cn_now() -> str:
    """返回中国时间字符串 YYYY-MM-DD HH:MM:SS。"""
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _get_trade_webhook() -> str:
    """获取交易群 Webhook URL，优先 FEISHU_TRADE_WEBHOOK_URL，回退 FEISHU_WEBHOOK_URL。"""
    return (
        os.environ.get("FEISHU_TRADE_WEBHOOK_URL", "")
        or os.environ.get("FEISHU_WEBHOOK_URL", "")
    )


def _get_alert_webhook() -> str:
    """获取报警群 Webhook URL，优先 FEISHU_ALERT_WEBHOOK_URL，回退 FEISHU_WEBHOOK_URL。"""
    return (
        os.environ.get("FEISHU_ALERT_WEBHOOK_URL", "")
        or os.environ.get("FEISHU_WEBHOOK_URL", "")
    )


def _send_card(webhook_url: str, payload: dict) -> bool:
    """发送飞书卡片，返回是否成功。"""
    if not webhook_url:
        logger.warning("[trade_push] Webhook URL 未配置，跳过推送")
        return False
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8")
        try:
            resp_json = json.loads(body)
            if resp_json.get("code", 0) != 0:
                logger.error("[trade_push] 飞书 API 错误 code=%s msg=%s",
                             resp_json.get("code"), resp_json.get("msg"))
                return False
        except (json.JSONDecodeError, AttributeError):
            pass
        return True
    except urllib.error.URLError as exc:
        logger.error("[trade_push] 网络错误: %s", exc)
        return False
    except Exception as exc:
        logger.error("[trade_push] 未知错误: %s", exc)
        return False


def push_trade_fill(fill_data: dict) -> bool:
    """
    成交回报即时推送到交易群。
    无静默限制，无去重。
    fill_data 字段（均可缺省）：
      symbol(品种代码), direction(买卖方向), volume(成交手数),
      price(成交价格), account(账户ID), strategy(策略名),
      signal_id(信号ID), pnl(本次盈亏), today_pnl(今日累计盈亏)
    """
    symbol = fill_data.get("symbol", "-")
    direction = fill_data.get("direction", "-")  # 多/空/买/卖
    volume = fill_data.get("volume", "-")
    price = fill_data.get("price", "-")
    account = fill_data.get("account", "-")
    strategy = fill_data.get("strategy", "-")
    signal_id = fill_data.get("signal_id", "-")
    pnl = fill_data.get("pnl", "-")
    today_pnl = fill_data.get("today_pnl", "-")
    ts = _cn_now()

    # 格式化盈亏显示
    pnl_str = f"{pnl:+.2f}" if isinstance(pnl, (int, float)) else str(pnl)
    today_pnl_str = f"{today_pnl:+.2f}" if isinstance(today_pnl, (int, float)) else str(today_pnl)

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"JBT 模拟交易 📈 [模拟-成交] {symbol} {direction} {volume}手 @{price}",
                },
                "template": "grey",  # 交易类固定灰色
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**品种：** {symbol}　　**方向：** {direction}　　"
                            f"**手数：** {volume}手\n"
                            f"**成交价：** {price}　　**本次盈亏：** {pnl_str}\n"
                            f"**今日累计盈亏：** {today_pnl_str}"
                        ),
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**账户：** {account}　　**策略：** {strategy}\n"
                            f"**信号 ID（signal_id）：** {signal_id}"
                        ),
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": f"JBT-模拟交易 | {ts}"}],
                },
            ],
        },
    }
    return _send_card(_get_trade_webhook(), payload)


def push_order_status(order_data: dict) -> bool:
    """
    订单状态变化推送到交易群（仅终态：全成/拒单/撤单/部成）。
    拒单连续 >= 5 笔同一品种时，升级推送到报警群 P1。
    order_data 字段：
      symbol, status(全成/拒单/撤单/部成), direction, volume,
      filled_volume(已成交量), price, account, reject_reason(拒单原因)
    """
    symbol = order_data.get("symbol", "-")
    status = order_data.get("status", "-")       # 全成 / 拒单 / 撤单 / 部成
    direction = order_data.get("direction", "-")
    volume = order_data.get("volume", "-")
    filled_volume = order_data.get("filled_volume", "-")
    price = order_data.get("price", "-")
    account = order_data.get("account", "-")
    reject_reason = order_data.get("reject_reason", "")
    ts = _cn_now()

    # 拒单连续计数
    is_reject = status == "拒单"
    if is_reject:
        _reject_count[symbol] = _reject_count.get(symbol, 0) + 1
        reject_cnt = _reject_count[symbol]
    else:
        _reject_count[symbol] = 0  # 非拒单则重置
        reject_cnt = 0

    # 拒单颜色 orange，其他 grey
    color = "orange" if is_reject else "grey"
    icon = "⚠️" if is_reject else "📈"
    type_label = "订单-拒单" if is_reject else f"订单-{status}"

    core_content = (
        f"**品种：** {symbol}　　**方向：** {direction}\n"
        f"**委托量：** {volume}手　　**已成交：** {filled_volume}手\n"
        f"**委托价：** {price}　　**状态：** {status}"
    )
    if is_reject and reject_reason:
        core_content += f"\n**拒单原因：** {reject_reason}"

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"JBT 模拟交易 {icon} [模拟-{type_label}]",
                },
                "template": color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": core_content},
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**账户：** {account}"},
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": f"JBT-模拟交易 | {ts}"}],
                },
            ],
        },
    }

    # 发到交易群
    ok = _send_card(_get_trade_webhook(), payload)

    # 连续拒单 >= 5 笔 → 额外发报警群 P1
    if is_reject and reject_cnt >= _REJECT_ESCALATION_THRESHOLD:
        alert_payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"JBT 模拟交易 ⚠️ [P1-报警] {symbol} 连续拒单 {reject_cnt} 笔",
                    },
                    "template": "orange",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": (
                                f"**品种：** {symbol}　　**账户：** {account}\n"
                                f"**连续拒单次数：** {reject_cnt} 笔\n"
                                f"**最近拒单原因：** {reject_reason or '-'}\n"
                                f"请检查保证金余额、涨跌停限制或风控参数。"
                            ),
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [{"tag": "plain_text", "content": f"JBT-模拟交易 | {ts}"}],
                    },
                ],
            },
        }
        _send_card(_get_alert_webhook(), alert_payload)

    return ok
