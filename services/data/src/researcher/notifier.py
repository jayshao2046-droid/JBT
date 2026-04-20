"""推送 — 飞书卡片(Jay版) + Mini data API(决策版)"""

import os
import httpx
from typing import Dict, Any
from datetime import datetime
import logging

from .models import ResearchReport, ReportBatch
from .config import ResearcherConfig


logger = logging.getLogger(__name__)


class ResearcherNotifier:
    """研究员通知器"""

    def __init__(self):
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL", "")
        self.data_api_url = os.getenv("DATA_API_URL", "http://192.168.31.76:8105")

    async def _post_feishu(self, payload: Dict[str, Any], timeout: float = 10.0, retries: int = 2) -> bool:
        """发送飞书消息并校验业务返回码。"""
        if not self.feishu_webhook:
            logger.warning("FEISHU_WEBHOOK_URL is empty, skip sending")
            return False

        last_error = ""
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(self.feishu_webhook, json=payload, timeout=timeout)
                if resp.status_code != 200:
                    last_error = f"http={resp.status_code} body={resp.text[:300]}"
                else:
                    body = resp.json()
                    code = body.get("code", -1)
                    if code == 0:
                        return True
                    last_error = f"code={code} msg={body.get('msg', '')}"
            except Exception as e:
                last_error = str(e)

            if attempt < retries:
                logger.warning("Feishu send failed, retry=%s/%s, reason=%s", attempt + 1, retries, last_error)

        logger.error("Feishu send failed after retries: %s", last_error)
        return False

    async def notify_batch_done(self, batch: ReportBatch):
        """
        通知批次报告完成

        Args:
            batch: 报告批次
        """
        # 飞书卡片（汇总通知）
        await self._send_feishu_batch_card(batch)

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
                                "content": f"JBT 资讯 | JBT 数据研究员 | {hour}:{minute} | 采集{sources_count}源{articles_count}篇 | Alienware"
                            }
                        ]
                    }
                ]
            }
        }

        try:
            await self._post_feishu(card, timeout=ResearcherConfig.HTTP_TIMEOUT_MEDIUM)
        except Exception:
            logger.exception("Unexpected error when sending report card")

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

    async def _send_feishu_batch_card(self, batch: ReportBatch):
        """发送批次报告飞书卡片（汇总通知）"""
        if self._is_feishu_silent():
            return  # 静默期（23:30-08:00），不推送飞书

        if not self.feishu_webhook:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 统计各类报告
        report_types = []
        if batch.futures_report:
            report_types.append("期货")
        if batch.stocks_report:
            report_types.append("股票")
        if batch.news_report:
            report_types.append("新闻")
        if batch.rss_report:
            report_types.append("RSS")
        if batch.sentiment_report:
            report_types.append("情绪")

        source_summary = ', '.join(report_types) if report_types else "无"

        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "template": "blue",
                    "title": {
                        "content": f"📊 研究员批次报告 | {batch.batch_id}",
                        "tag": "plain_text"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**批次时间**: {timestamp}\n**报告数量**: {batch.total_reports}\n**数据源**: {source_summary}",
                            "tag": "lark_md"
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
                                "content": f"生成于 {timestamp} | Alienware 研究员"
                            }
                        ]
                    }
                ]
            }
        }

        await self._post_feishu(card)

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
                                "content": f"JBT 资讯 | JBT 数据研究员 | {timestamp} | Alienware"
                            }
                        ]
                    }
                ]
            }
        }

        try:
            await self._post_feishu(card, timeout=10.0)
        except Exception:
            logger.exception("Unexpected error when sending alert card")

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
                                "content": f"JBT 资讯 | JBT 数据研究员 | 突发紧急 | Alienware"
                            }
                        ]
                    }
                ]
            }
        }

        try:
            await self._post_feishu(card, timeout=10.0)
        except Exception:
            logger.exception("Unexpected error when sending urgent card")
