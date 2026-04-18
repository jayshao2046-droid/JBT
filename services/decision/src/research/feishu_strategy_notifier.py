"""飞书策略完成通知器 — TASK-0127

每个策略完成后，发送富文本卡片通知到飞书。

通知内容包括：
- 品种、策略名、类型、因子
- 所有策略参数
- 本地回测结果
- TqSdk 回测结果
- 最终评分与等级
- 调优次数
- 落盘位置
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class FeishuStrategyNotifier:
    """飞书策略完成通知器"""

    def __init__(self, webhook_url: str):
        """初始化飞书通知器

        Args:
            webhook_url: 飞书 Webhook URL
        """
        self.webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def notify_strategy_completed(
        self,
        symbol: str,
        strategy_name: str,
        category: str,
        factors: list[str],
        params: dict[str, Any],
        local_result: dict[str, Any],
        tqsdk_result: dict[str, Any],
        final_score: int,
        grade: str,
        optimization_trials: int,
        storage_path: str,
    ) -> bool:
        """发送策略完成通知

        Args:
            symbol: 品种代码
            strategy_name: 策略名称
            category: 策略类型
            factors: 因子列表
            params: 策略参数
            local_result: 本地回测结果
            tqsdk_result: TqSdk 回测结果
            final_score: 最终评分
            grade: 等级（S/A/B/C/D）
            optimization_trials: 调优次数
            storage_path: 落盘位置

        Returns:
            是否发送成功
        """
        try:
            # 构建卡片内容
            card = self._build_card(
                symbol=symbol,
                strategy_name=strategy_name,
                category=category,
                factors=factors,
                params=params,
                local_result=local_result,
                tqsdk_result=tqsdk_result,
                final_score=final_score,
                grade=grade,
                optimization_trials=optimization_trials,
                storage_path=storage_path,
            )

            # 发送到飞书
            response = await self._client.post(self.webhook_url, json=card)
            response.raise_for_status()

            logger.info(f"✅ 飞书通知已发送: {strategy_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 飞书通知发送失败 ({strategy_name}): {e}")
            return False

    def _build_card(
        self,
        symbol: str,
        strategy_name: str,
        category: str,
        factors: list[str],
        params: dict[str, Any],
        local_result: dict[str, Any],
        tqsdk_result: dict[str, Any],
        final_score: int,
        grade: str,
        optimization_trials: int,
        storage_path: str,
    ) -> dict[str, Any]:
        """构建飞书卡片"""

        # 等级图标
        grade_icons = {
            "S": "🌟",
            "A": "✅",
            "B": "⚠️",
            "C": "❌",
            "D": "🚫",
        }
        grade_icon = grade_icons.get(grade, "❓")

        # 准入状态
        can_deploy = grade in ("S", "A")
        deploy_status = "✅ 可纳入生产候选" if can_deploy else "❌ 不可上线"

        # 因子列表
        factors_str = "、".join(factors) if factors else "N/A"

        # 策略参数（精简显示）
        timeframe = params.get("timeframe_minutes", "N/A")
        position_fraction = params.get("position_fraction", "N/A")
        stop_loss = params.get("stop_loss", {})
        take_profit = params.get("take_profit", {})
        stop_loss_atr = stop_loss.get("atr_multiplier", "N/A") if isinstance(stop_loss, dict) else "N/A"
        take_profit_atr = take_profit.get("atr_multiplier", "N/A") if isinstance(take_profit, dict) else "N/A"

        risk = params.get("risk", {})
        force_close_day = risk.get("force_close_day", "N/A") if isinstance(risk, dict) else "N/A"
        no_overnight = risk.get("no_overnight", False) if isinstance(risk, dict) else False

        # 本地回测结果
        local_sharpe = local_result.get("sharpe_ratio", 0)
        local_drawdown = local_result.get("max_drawdown", 0) * 100
        local_win_rate = local_result.get("win_rate", 0) * 100
        local_annual_return = local_result.get("annualized_return", 0) * 100
        local_trades = local_result.get("trades_count", 0)

        # TqSdk 回测结果
        tqsdk_sharpe = tqsdk_result.get("sharpe_ratio", 0)
        tqsdk_drawdown = tqsdk_result.get("max_drawdown", 0) * 100
        tqsdk_win_rate = tqsdk_result.get("win_rate", 0) * 100
        tqsdk_annual_return = tqsdk_result.get("annualized_return", 0) * 100
        tqsdk_trades = tqsdk_result.get("trades_count", 0)

        # 构建卡片内容
        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 [LLM-STRATEGY] 策略完成通知
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【基本信息】
品种：{symbol}
策略名：{strategy_name}
类型：{category}
因子：{factors_str}

【策略参数】
timeframe: {timeframe}m
position_fraction: {position_fraction}
stop_loss_atr: {stop_loss_atr}
take_profit_atr: {take_profit_atr}
force_close_day: {force_close_day}
no_overnight: {no_overnight}

【本地回测结果】
Sharpe: {local_sharpe:.2f} | 回撤: {local_drawdown:.1f}% | 胜率: {local_win_rate:.1f}%
年化: {local_annual_return:.1f}% | 交易次数: {local_trades}

【TqSdk 回测结果】
Sharpe: {tqsdk_sharpe:.2f} | 回撤: {tqsdk_drawdown:.1f}% | 胜率: {tqsdk_win_rate:.1f}%
年化: {tqsdk_annual_return:.1f}% | 交易次数: {tqsdk_trades}

【评分结果】
最终得分：{final_score}/100 ({grade_icon} {grade} 级)
调优次数：{optimization_trials} trials
准入状态：{deploy_status}

【落盘位置】
{storage_path}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JBT decision | {datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")}
"""

        # 飞书卡片格式
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 [LLM-STRATEGY] {strategy_name} 完成",
                    },
                    "template": "turquoise" if can_deploy else "orange",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content,
                        },
                    },
                ],
            },
        }

        return card

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
