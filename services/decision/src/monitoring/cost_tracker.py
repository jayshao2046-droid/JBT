"""API 成本监控器 — TASK-U0-20260417-004

实时追踪 API 调用费用，自动预警和熔断。

功能:
- 实时累计今日消耗
- 达到 80% 预算时自动预警
- 达到 100% 预算时自动暂停非紧急任务
- 飞书看板集成

显示内容:
- 今日消耗: $X.XX / $10.00
- 本月累计: $XXX.XX
- 单策略平均成本: $0.XX
- 预警状态: 正常 / 接近上限 / 已暂停
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """预算超支异常"""
    pass


class APIUsageTracker:
    """API 使用追踪器

    使用内存存储（生产环境应使用 Redis）
    """

    # 模型成本（美元/1K tokens）
    MODEL_COSTS = {
        "deepseek-chat": {"input": 0.00027, "output": 0.0011},      # V3
        "deepseek-reasoner": {"input": 0.00055, "output": 0.0022},  # R1
        "qwen-coder-plus": {"input": 0.0002, "output": 0.0006},     # Coder
        "qwen-plus": {"input": 0.0004, "output": 0.0012},           # Auditor
    }

    def __init__(
        self,
        daily_budget: Optional[float] = None,
        feishu_webhook_url: Optional[str] = None,
    ):
        self.daily_budget = daily_budget or float(os.getenv("DAILY_API_BUDGET", "10.0"))
        self.feishu_webhook_url = feishu_webhook_url or os.getenv("FEISHU_WEBHOOK_URL")

        # 内存存储（生产环境应使用 Redis）
        self._daily_costs: dict[str, float] = {}
        self._monthly_costs: dict[str, float] = {}
        self._strategy_costs: list[float] = []

        # 飞书看板集成
        self.feishu_dashboard = None
        if self.feishu_webhook_url:
            try:
                from .feishu_dashboard import FeishuDashboard
                self.feishu_dashboard = FeishuDashboard(self.feishu_webhook_url)
            except ImportError as e:
                logger.warning(f"飞书看板导入失败: {e}，将使用简单文本通知")

        logger.info(f"💰 API 成本监控器已启动（每日预算: ${self.daily_budget:.2f}）")

    async def track_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        strategy_id: Optional[str] = None,
    ) -> float:
        """追踪 API 调用

        Args:
            model: 模型名称
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            strategy_id: 策略 ID（可选）

        Returns:
            本次调用成本（美元）

        Raises:
            BudgetExceededError: 预算超支
        """
        # 计算成本
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        # 累计今日消耗
        today = datetime.now().strftime("%Y-%m-%d")
        self._daily_costs[today] = self._daily_costs.get(today, 0.0) + cost

        # 累计本月消耗
        month = datetime.now().strftime("%Y-%m")
        self._monthly_costs[month] = self._monthly_costs.get(month, 0.0) + cost

        # 记录单策略成本
        if strategy_id:
            self._strategy_costs.append(cost)

        total_today = self._daily_costs[today]

        logger.debug(
            f"💸 API 调用: {model} | "
            f"输入{input_tokens} + 输出{output_tokens} tokens | "
            f"成本 ${cost:.4f} | "
            f"今日累计 ${total_today:.2f}"
        )

        # 检查预算
        await self._check_budget(total_today)

        return cost

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算 API 调用成本"""
        if model not in self.MODEL_COSTS:
            logger.warning(f"未知模型 {model}，使用默认成本")
            return 0.001  # 默认成本

        costs = self.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        return input_cost + output_cost

    async def _check_budget(self, total_today: float):
        """检查预算并预警"""
        usage_rate = total_today / self.daily_budget

        if usage_rate >= 1.0:
            # 100% 预算用完
            logger.error(f"🚨 今日 API 预算已用完: ${total_today:.2f} / ${self.daily_budget:.2f}")
            await self._send_feishu_alert(
                title="🚨 API 预算超支",
                content=f"今日预算已用完: ${total_today:.2f} / ${self.daily_budget:.2f}\n\n已暂停非紧急优化任务。",
                level="error"
            )
            raise BudgetExceededError(f"今日预算已用完: ${total_today:.2f}")

        elif usage_rate >= 0.8:
            # 80% 预警
            logger.warning(f"⚠️ 今日 API 费用已达 80%: ${total_today:.2f} / ${self.daily_budget:.2f}")
            await self._send_feishu_alert(
                title="⚠️ API 预算预警",
                content=f"今日预算已达 {usage_rate:.0%}: ${total_today:.2f} / ${self.daily_budget:.2f}\n\n请注意控制使用。",
                level="warning"
            )

    async def _send_feishu_alert(self, title: str, content: str, level: str = "info"):
        """发送飞书预警"""
        if not self.feishu_webhook_url:
            return

        color_map = {
            "info": "blue",
            "warning": "orange",
            "error": "red",
        }

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": color_map.get(level, "blue"),
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "plain_text", "content": content},
                    }
                ],
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.feishu_webhook_url, json=payload)
        except Exception as e:
            logger.error(f"飞书通知发送失败: {e}")

    def get_daily_summary(self) -> dict:
        """获取今日摘要"""
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")

        total_today = self._daily_costs.get(today, 0.0)
        total_month = self._monthly_costs.get(month, 0.0)
        avg_strategy_cost = (
            sum(self._strategy_costs) / len(self._strategy_costs)
            if self._strategy_costs
            else 0.0
        )

        usage_rate = total_today / self.daily_budget

        if usage_rate >= 1.0:
            status = "已暂停"
        elif usage_rate >= 0.8:
            status = "接近上限"
        else:
            status = "正常"

        return {
            "today": today,
            "daily_cost": round(total_today, 2),
            "daily_budget": self.daily_budget,
            "usage_rate": round(usage_rate, 2),
            "monthly_cost": round(total_month, 2),
            "avg_strategy_cost": round(avg_strategy_cost, 4),
            "status": status,
        }

    async def send_hourly_report(self):
        """发送每小时费用摘要（飞书看板）"""
        summary = self.get_daily_summary()

        if self.feishu_dashboard:
            # 使用飞书看板发送富文本卡片
            await self.feishu_dashboard.send_cost_summary(summary)
        else:
            # 降级到简单文本通知
            content = f"""📊 API 费用摘要

今日消耗: ${summary['daily_cost']:.2f} / ${summary['daily_budget']:.2f} ({summary['usage_rate']:.0%})
本月累计: ${summary['monthly_cost']:.2f}
单策略平均: ${summary['avg_strategy_cost']:.4f}
状态: {summary['status']}
"""

            await self._send_feishu_alert(
                title="📊 API 费用摘要",
                content=content,
                level="info"
            )
