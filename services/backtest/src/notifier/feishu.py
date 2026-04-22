"""
BacktestFeishuNotifier — JBT 回测端飞书通知
回测完成/失败推送到 INFO/ALERT 群，遵循 JBT 统一卡片格式。
"""
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))

_COLOR_MAP = {
    "done": "turquoise",
    "failed": "orange",
    "error": "red",
}

_ICON_MAP = {
    "done": "📣",
    "failed": "⚠️",
    "error": "🚨",
}

_LEVEL_LABEL_MAP = {
    "done": "通知",
    "failed": "报警-P1",
    "error": "报警-P0",
}


def _first_nonempty(*values: str) -> str:
    for v in values:
        if v:
            return v
    return ""


def _get_webhook(status: str) -> str:
    """按状态选择 Webhook URL。"""
    if status in ("failed", "error"):
        return _first_nonempty(
            os.environ.get("FEISHU_ALERT_WEBHOOK_URL", ""),
            os.environ.get("FEISHU_WEBHOOK_URL", ""),
        )
    return _first_nonempty(
        os.environ.get("FEISHU_INFO_WEBHOOK_URL", ""),
        os.environ.get("FEISHU_WEBHOOK_URL", ""),
    )


def send_backtest_card(
    *,
    status: str,
    run_id: str,
    strategy_id: str,
    elapsed_sec: float,
    metrics: dict,
) -> bool:
    """
    发送回测结果卡片。

    Args:
        status: "done" / "failed" / "error"
        run_id: 回测任务 ID
        strategy_id: 策略 ID
        elapsed_sec: 耗时（秒）
        metrics: 回测指标字典

    Returns:
        True 发送成功
    """
    webhook_url = _get_webhook(status)
    if not webhook_url:
        logger.debug("backtest feishu webhook not configured, skip notify")
        return False

    ts = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")
    color = _COLOR_MAP.get(status, "blue")
    icon = _ICON_MAP.get(status, "📋")
    level_label = _LEVEL_LABEL_MAP.get(status, "通知")

    status_text = "完成" if status == "done" else "失败"
    title_text = f"JBT 回测 {icon} [{level_label}-回测] {strategy_id} {status_text}"

    # 构建指标摘要
    sharpe = metrics.get("sharpe_ratio", metrics.get("sharpe", "-"))
    returns = metrics.get("total_return", metrics.get("returns", "-"))
    max_dd = metrics.get("max_drawdown", metrics.get("max_dd", "-"))
    error_msg = metrics.get("error", "")

    if status == "done":
        body_md = (
            f"**策略:** {strategy_id}\n"
            f"**任务ID:** {run_id}\n"
            f"**夏普比:** {sharpe}\n"
            f"**总收益:** {returns}\n"
            f"**最大回撤:** {max_dd}\n"
            f"**耗时:** {elapsed_sec:.1f}s"
        )
    else:
        body_md = (
            f"**策略:** {strategy_id}\n"
            f"**任务ID:** {run_id}\n"
            f"**错误:** {str(error_msg)[:200]}\n"
            f"**耗时:** {elapsed_sec:.1f}s"
        )

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title_text},
                "template": color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": body_md},
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": f"JBT-回测 | {ts}"}],
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
            resp.read()
        return True
    except urllib.error.URLError as exc:
        logger.warning("backtest feishu send failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("backtest feishu unexpected error: %s", exc)
        return False
