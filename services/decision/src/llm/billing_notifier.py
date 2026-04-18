"""LLM 计费飞书定时推送 — 每小时整点发送模型用量与费用报告。

支持:
- 每小时自动推送（整点后 1 分钟触发）
- 手动触发当前时段报告
- 飞书卡片格式，含模型/组件明细 + 预算进度条
"""

import asyncio
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from .billing import get_billing_tracker

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))

# 模块级单例引用
_notifier_instance: Optional["BillingNotifier"] = None


class BillingNotifier:
    """每小时推送 LLM 计费报告到飞书。"""

    def __init__(self) -> None:
        self._webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "")
        self._enabled = (
            os.environ.get("BILLING_NOTIFY_ENABLED", "true").strip().lower() == "true"
        )
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """启动后台定时推送任务。"""
        global _notifier_instance
        _notifier_instance = self

        if not self._enabled:
            logger.info("计费通知已关闭 (BILLING_NOTIFY_ENABLED=false)")
            return

        if not self._webhook_url:
            logger.warning("FEISHU_WEBHOOK_URL 未设置，计费通知无法推送")
            return

        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("💰 计费通知定时器已启动（每小时整点推送）")

    async def _scheduler_loop(self) -> None:
        """等到下一个整点 +1min，然后每小时执行一次。"""
        now = datetime.now(_TZ_CST)
        next_run = (now + timedelta(hours=1)).replace(
            minute=1, second=0, microsecond=0
        )
        wait_seconds = (next_run - now).total_seconds()
        logger.info(
            "计费通知: 首次推送将在 %s (%d 秒后)",
            next_run.strftime("%H:%M"), int(wait_seconds),
        )

        await asyncio.sleep(wait_seconds)

        while True:
            try:
                await self._send_hourly_report()
            except Exception as exc:
                logger.error("计费通知推送失败: %s", exc, exc_info=True)

            # 清理旧记录并持久化
            tracker = get_billing_tracker()
            last_hour = datetime.now(_TZ_CST) - timedelta(hours=1)
            tracker.flush_hourly(last_hour)
            tracker.cleanup_old_records(keep_hours=48)

            await asyncio.sleep(3600)

    # ------------------------------------------------------------------
    # 报告发送
    # ------------------------------------------------------------------

    async def _send_hourly_report(self) -> bool:
        """发送上一小时的计费报告。"""
        tracker = get_billing_tracker()

        last_hour = datetime.now(_TZ_CST) - timedelta(hours=1)
        hourly = tracker.get_hourly_summary(last_hour)
        daily = tracker.get_daily_summary()

        if hourly["total_calls"] == 0:
            logger.info("上一小时无 LLM 调用，跳过推送")
            return True

        card = self._build_card(hourly, daily, last_hour)
        return self._send_feishu(card)

    async def send_current_report(self) -> bool:
        """手动发送当前小时 + 今日累计报告。"""
        if not self._webhook_url:
            return False

        tracker = get_billing_tracker()
        hourly = tracker.get_hourly_summary()
        daily = tracker.get_daily_summary()

        if hourly["total_calls"] == 0 and daily["total_calls"] == 0:
            return self._send_feishu(self._build_empty_card())

        card = self._build_card(hourly, daily, datetime.now(_TZ_CST))
        return self._send_feishu(card)

    # ------------------------------------------------------------------
    # 飞书卡片构建
    # ------------------------------------------------------------------

    def _build_card(
        self, hourly: Dict[str, Any], daily: Dict[str, Any], hour: datetime
    ) -> Dict[str, Any]:
        ts = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")
        hour_str = hour.strftime("%H:00")
        date_str = hour.strftime("%Y-%m-%d")

        # ── 模型明细 ────
        model_lines = []
        for model, stats in sorted(
            hourly["by_model"].items(),
            key=lambda x: x[1]["total_cost"],
            reverse=True,
        ):
            if stats["total_cost"] > 0:
                cost_str = f"¥{stats['total_cost']:.4f}"
            else:
                cost_str = "免费🏠"
            model_lines.append(
                f"**{model}**\n"
                f"  调用 {stats['calls']}次 | "
                f"入 {stats['input_tokens']:,} | "
                f"出 {stats['output_tokens']:,} | "
                f"{cost_str}"
            )
        model_text = "\n".join(model_lines) if model_lines else "无调用记录"

        # ── 组件明细 ────
        comp_parts = []
        for comp, stats in sorted(
            hourly["by_component"].items(),
            key=lambda x: x[1]["total_cost"],
            reverse=True,
        ):
            cost = f"¥{stats['total_cost']:.4f}" if stats["total_cost"] > 0 else "免费"
            comp_parts.append(f"{comp}: {stats['calls']}次 {cost}")
        comp_text = " | ".join(comp_parts) if comp_parts else "-"

        # ── 预算进度 ────
        budget_pct = daily.get("budget_usage_pct", 0)
        budget_bar = self._budget_bar(budget_pct)

        # ── 颜色 / 图标 ────
        budget = daily.get("budget", 10)
        if daily["total_cost"] > budget * 0.8:
            color, icon = "red", "🚨"
        elif daily["total_cost"] > budget * 0.5:
            color, icon = "orange", "⚠️"
        else:
            color, icon = "turquoise", "💰"

        summary_text = (
            f"**本时段费用:** ¥{hourly['total_cost']:.4f}\n"
            f"**调用次数:** {hourly['total_calls']}次 "
            f"(本地 {hourly['local_calls']} | 在线 {hourly['online_calls']})\n"
            f"**Token 用量:** "
            f"入 {hourly['total_input_tokens']:,} | "
            f"出 {hourly['total_output_tokens']:,}"
        )

        daily_text = (
            f"**今日累计:** ¥{daily['total_cost']:.4f} / ¥{budget:.2f}\n"
            f"**预算剩余:** ¥{daily.get('budget_remaining', 0):.4f} "
            f"({budget_bar})\n"
            f"**今日调用:** {daily['total_calls']}次 "
            f"(本地 {daily['local_calls']} | 在线 {daily['online_calls']})"
        )

        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} LLM 计费报告 | {date_str} {hour_str}",
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": summary_text},
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**📊 模型明细:**\n{model_text}",
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**🔧 组件明细:** {comp_text}",
                        },
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": daily_text},
                    },
                    {"tag": "hr"},
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT Decision 计费系统 | {ts}",
                            }
                        ],
                    },
                ],
            },
        }

    def _build_empty_card(self) -> Dict[str, Any]:
        ts = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "💰 LLM 计费报告 | 当前无调用",
                    },
                    "template": "turquoise",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "当前时段暂无 LLM 调用记录。",
                        },
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT Decision 计费系统 | {ts}",
                            }
                        ],
                    },
                ],
            },
        }

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    @staticmethod
    def _budget_bar(pct: float) -> str:
        """生成预算进度条。"""
        filled = min(10, int(pct / 10))
        return "▓" * filled + "░" * (10 - filled) + f" {pct:.1f}%"

    def _send_feishu(self, payload: Dict[str, Any]) -> bool:
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

            try:
                resp_json = json.loads(resp_body)
                if resp_json.get("code", 0) != 0:
                    logger.error("飞书 API 错误: %s", resp_json)
                    return False
            except json.JSONDecodeError:
                pass

            logger.info("计费报告已推送到飞书")
            return True

        except Exception as exc:
            logger.error("飞书推送失败: %s", exc)
            return False


def get_billing_notifier() -> Optional[BillingNotifier]:
    """获取已启动的通知器实例。"""
    return _notifier_instance
