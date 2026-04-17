"""飞书看板集成 — TASK-U0-20260417-004

实时成本监控可视化，支持：
1. 每小时推送费用摘要
2. 实时显示成本监控
3. 预警状态可视化
4. 优化进度追踪

卡片类型:
- 费用摘要卡片（每小时）
- 预警卡片（80%/100%）
- 优化进度卡片（实时）
- 日报卡片（每日18:00）
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class FeishuDashboard:
    """飞书看板集成

    提供丰富的卡片模板，用于成本监控和优化进度可视化。
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_cost_summary(self, summary: dict):
        """发送费用摘要卡片

        Args:
            summary: 成本摘要字典
                - daily_cost: 今日消耗
                - daily_budget: 每日预算
                - usage_rate: 使用率
                - monthly_cost: 本月累计
                - avg_strategy_cost: 单策略平均成本
                - status: 状态（正常/接近上限/已暂停）
        """
        # 状态颜色映射
        color_map = {
            "正常": "green",
            "接近上限": "orange",
            "已暂停": "red",
        }

        # 状态图标映射
        icon_map = {
            "正常": "✅",
            "接近上限": "⚠️",
            "已暂停": "🚨",
        }

        status = summary.get("status", "正常")
        color = color_map.get(status, "blue")
        icon = icon_map.get(status, "📊")

        # 构建卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} API 费用摘要"
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**今日消耗**\n${summary['daily_cost']:.2f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**每日预算**\n${summary['daily_budget']:.2f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**使用率**\n{summary['usage_rate']:.0%}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**状态**\n{status}"
                                }
                            },
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**本月累计**\n${summary['monthly_cost']:.2f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**单策略平均**\n${summary['avg_strategy_cost']:.4f}"
                                }
                            },
                        ]
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"更新时间: {summary.get('today', datetime.now().strftime('%Y-%m-%d'))}"
                            }
                        ]
                    }
                ]
            }
        }

        await self._send_card(card)

    async def send_optimization_progress(self, progress: dict):
        """发送优化进度卡片

        Args:
            progress: 优化进度字典
                - strategy_id: 策略ID
                - iteration: 当前迭代
                - max_iterations: 最大迭代
                - current_model: 当前模型（V3/R1）
                - trades: 交易次数
                - sharpe: Sharpe比率
                - win_rate: 胜率
                - score: 综合得分
                - v3_calls: V3调用次数
                - r1_calls: R1调用次数
                - total_cost: 总成本
        """
        # 进度条
        progress_rate = progress['iteration'] / progress['max_iterations']
        progress_bar = "█" * int(progress_rate * 20) + "░" * (20 - int(progress_rate * 20))

        # 模型图标
        model_icon = "🧠" if progress['current_model'] == "R1" else "🤖"

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{model_icon} 优化进度 - {progress['strategy_id']}"
                    },
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**进度**: {progress['iteration']}/{progress['max_iterations']}\n{progress_bar} {progress_rate:.0%}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**当前模型**\n{progress['current_model']}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**综合得分**\n{progress['score']:.4f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**交易次数**\n{progress['trades']}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Sharpe**\n{progress['sharpe']:.4f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**胜率**\n{progress['win_rate']:.2%}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**总成本**\n${progress['total_cost']:.4f}"
                                }
                            },
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"V3 调用: {progress['v3_calls']} 次 | R1 调用: {progress['r1_calls']} 次"
                        }
                    },
                ]
            }
        }

        await self._send_card(card)

    async def send_optimization_complete(self, result: dict):
        """发送优化完成卡片

        Args:
            result: 优化结果字典
                - strategy_id: 策略ID
                - success: 是否成功
                - final_score: 最终得分
                - iterations: 总迭代次数
                - v3_calls: V3调用次数
                - r1_calls: R1调用次数
                - total_cost: 总成本
                - stop_reason: 停止原因
        """
        # 成功/失败图标和颜色
        if result['success']:
            icon = "🎉"
            color = "green"
            title = "优化成功"
        else:
            icon = "⚠️"
            color = "orange"
            title = "优化完成"

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{icon} {title} - {result['strategy_id']}"
                    },
                    "template": color,
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**最终得分**\n{result['final_score']:.4f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**总迭代次数**\n{result['iterations']}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**V3 调用**\n{result['v3_calls']} 次"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**R1 调用**\n{result['r1_calls']} 次"
                                }
                            },
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**总成本**\n${result['total_cost']:.4f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**停止原因**\n{result['stop_reason']}"
                                }
                            },
                        ]
                    },
                ]
            }
        }

        await self._send_card(card)

    async def send_daily_report(self, report: dict):
        """发送每日报告卡片

        Args:
            report: 日报字典
                - date: 日期
                - strategies_optimized: 优化策略数
                - total_iterations: 总迭代次数
                - total_cost: 总成本
                - avg_cost_per_strategy: 单策略平均成本
                - success_rate: 成功率
                - top_performers: 最佳策略列表
        """
        # 构建最佳策略列表
        top_performers_text = "\n".join([
            f"{i+1}. {p['strategy_id']} - Sharpe {p['sharpe']:.4f}"
            for i, p in enumerate(report.get('top_performers', [])[:5])
        ])

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 每日优化报告 - {report['date']}"
                    },
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**优化策略数**\n{report['strategies_optimized']}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**总迭代次数**\n{report['total_iterations']}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**总成本**\n${report['total_cost']:.2f}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**单策略平均**\n${report['avg_cost_per_strategy']:.4f}"
                                }
                            },
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**成功率**: {report['success_rate']:.1%}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**Top 5 策略**\n{top_performers_text}"
                        }
                    },
                ]
            }
        }

        await self._send_card(card)

    async def _send_card(self, card: dict):
        """发送卡片到飞书

        Args:
            card: 卡片字典
        """
        if not self.webhook_url:
            logger.warning("飞书 Webhook URL 未配置，跳过发送")
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=card)
                resp.raise_for_status()

            result = resp.json()
            if result.get("code") != 0:
                logger.error(f"飞书卡片发送失败: {result}")
            else:
                logger.debug("飞书卡片发送成功")

        except Exception as e:
            logger.error(f"飞书卡片发送异常: {e}", exc_info=True)
