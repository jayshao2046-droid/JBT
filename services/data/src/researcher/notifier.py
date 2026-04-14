"""推送 — 飞书卡片(Jay版) + Mini data API(决策版)"""

import os
import httpx
from typing import Dict, Any
from datetime import datetime

from .models import ResearchReport


class ResearcherNotifier:
    """研究员通知器"""

    def __init__(self):
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
        self.data_api_url = os.getenv("DATA_API_URL", "http://192.168.31.76:8105")

    async def notify_report_done(self, report: ResearchReport):
        """
        通知报告完成

        Args:
            report: 研究报告
        """
        # 1. 飞书卡片（Jay 版 Markdown - blue 模板精炼版）
        await self._send_feishu_card(report)

        # 2. 决策版 JSON 已在 reporter.py 中保存到文件
        # 决策端通过 API 读取

    async def notify_report_fail(self, hour: str, error: str):
        """
        通知报告失败

        Args:
            hour: 小时（如 "08"）
            error: 错误信息
        """
        await self._send_feishu_alert(hour, error)

    async def notify_urgent(self, headline: str, source: str, url: str):
        """
        通知突发紧急事件（red 模板 P0 报警）

        Args:
            headline: 新闻标题
            source: 来源
            url: 原文链接
        """
        await self._send_feishu_urgent(headline, source, url)

    @staticmethod
    def _is_feishu_silent() -> bool:
        """飞书静默期：23:30 之后至 08:00 不推送（推理继续，只静默飞书）"""
        now = datetime.now()
        return (now.hour == 23 and now.minute >= 30) or now.hour < 8

    async def _send_feishu_card(self, report: ResearchReport):
        """发送飞书卡片（blue 模板 - 精炼版）"""
        if not self.feishu_webhook:
            return
        if self._is_feishu_silent():
            return  # 静默期（23:30-08:00），不推送飞书

        # 提取小时
        hour = report.generated_at.strftime('%H')
        minute = report.generated_at.strftime('%M')

        # 构建精炼的期货研判
        futures_brief = self._build_futures_brief(report.futures_summary)

        # 构建要闻摘要
        news_brief = self._build_news_brief(report.crawler_stats)

        # 综合研判
        market_view = report.futures_summary.get('market_overview', '市场平稳运行')

        # 采集统计
        sources_count = report.crawler_stats.get('sources_crawled', 0)
        articles_count = report.crawler_stats.get('articles_processed', 0)

        # 构建飞书卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📈 [JBT 数据研究员-{hour}:00] {report.date}"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**期货研判**\n{futures_brief}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**要闻摘要**\n{news_brief}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**综合研判**\n{market_view}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT 数据研究员 | {hour}:{minute} | 采集{sources_count}源{articles_count}篇 | Alienware"
                            }
                        ]
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.feishu_webhook, json=card, timeout=10.0)
        except Exception:
            pass  # 发送失败不影响主流程

    def _build_futures_brief(self, futures_summary: Dict[str, Any]) -> str:
        """构建精炼的期货研判（按偏多/偏空/震荡分组）"""
        symbols = futures_summary.get('symbols', {})

        bullish = []
        bearish = []
        neutral = []

        for sym, detail in symbols.items():
            trend = detail.get('trend', '震荡')
            change_pct = detail.get('change_pct', 0.0)

            # 简化品种名
            sym_short = sym.split('@')[-1].split('.')[-1] if '@' in sym else sym

            if '偏多' in trend or '上涨' in trend:
                bullish.append(f"{sym_short} +{change_pct:.1f}%")
            elif '偏空' in trend or '下跌' in trend:
                bearish.append(f"{sym_short} {change_pct:.1f}%")
            else:
                neutral.append(sym_short)

        lines = []
        if bearish:
            lines.append(f"🔴 偏空: {', '.join(bearish[:5])}")
        if bullish:
            lines.append(f"🟢 偏多: {', '.join(bullish[:5])}")
        if neutral:
            lines.append(f"⚪ 震荡: {', '.join(neutral[:5])}")

        return '\n'.join(lines) if lines else '市场平稳'

    def _build_news_brief(self, crawler_stats: Dict[str, Any]) -> str:
        """构建要闻摘要（最多5条，标注来源）"""
        news_items = crawler_stats.get('news_items', [])

        if not news_items:
            return '• 暂无重要资讯'

        lines = []
        for item in news_items[:5]:
            source = item.get('source', '未知')
            title = item.get('title', '')
            lines.append(f"• {source}: {title}")

        return '\n'.join(lines)

    async def _send_feishu_alert(self, hour: str, error: str):
        if self._is_feishu_silent():
            return  # 静默期（23:30-08:00），不推送飞书
        """发送飞书告警（orange 模板）"""
        if not self.feishu_webhook:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"⚠️ [JBT 数据研究员-报警] 执行失败"
                    },
                    "template": "orange"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**时段**: {hour}:00\n**错误**: {error}\n**时间**: {timestamp}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT 数据研究员 | {timestamp} | Alienware"
                            }
                        ]
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.feishu_webhook, json=card, timeout=10.0)
        except Exception:
            pass

    async def _send_feishu_urgent(self, headline: str, source: str, url: str):
        """发送突发紧急卡片（red 模板 P0 报警）"""
        if not self.feishu_webhook:
            return

        detected_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 [JBT 数据研究员-紧急] {headline[:30]}..."
                    },
                    "template": "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**标题**: {headline}\n**来源**: {source}\n**链接**: {url}\n**发现时间**: {detected_at}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"JBT 数据研究员 | 突发紧急 | Alienware"
                            }
                        ]
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.feishu_webhook, json=card, timeout=10.0)
        except Exception:
            pass
