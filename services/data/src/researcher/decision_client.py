"""决策端客户端 - 推送报告到决策系统

职责：
1. 推送报告到 Mini API
2. 推送到飞书
3. 推送到邮件
"""
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)


class DecisionClient:
    """决策端客户端"""

    def __init__(self):
        self.mini_api = "http://192.168.31.74:8105/api/v1/researcher/reports"
        self.feishu_webhook = ""  # 需要配置
        self.email_to = "jay@example.com"  # 需要配置

    def push_report(self, report: Dict):
        """推送报告到所有渠道"""
        try:
            # 推送到 Mini
            self._push_to_mini(report)

            # 推送到飞书
            self._push_to_feishu(report)

            # 推送到邮件
            self._push_to_email(report)

            logger.info(f"Report pushed: {report.get('report_id')}")

        except Exception as e:
            logger.error(f"Error pushing report: {e}", exc_info=True)

    def _push_to_mini(self, report: Dict):
        """推送到 Mini API"""
        try:
            resp = requests.post(self.mini_api, json=report, timeout=10)
            if resp.status_code == 200:
                logger.info("Pushed to Mini successfully")
            else:
                logger.error(f"Mini push failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Mini push error: {e}")

    def _push_to_feishu(self, report: Dict):
        """推送到飞书"""
        if not self.feishu_webhook:
            return

        try:
            content = self._format_feishu_message(report)
            resp = requests.post(
                self.feishu_webhook,
                json={"msg_type": "text", "content": {"text": content}},
                timeout=5
            )
            logger.info(f"Pushed to Feishu: {resp.status_code}")
        except Exception as e:
            logger.error(f"Feishu push error: {e}")

    def _push_to_email(self, report: Dict):
        """推送到邮件"""
        try:
            from .email_sender import send_email
            subject = f"研究员报告 - {report.get('segment')}"
            body = self._format_email_body(report)
            send_email(self.email_to, subject, body)
        except Exception as e:
            logger.error(f"Email push error: {e}")

    def _format_feishu_message(self, report: Dict) -> str:
        """格式化飞书消息"""
        return f"""
【研究员报告】
时段：{report.get('segment')}
时间：{report.get('generated_at')}
期货品种：{report.get('futures_summary', {}).get('symbols_covered', 0)}
"""

    def _format_email_body(self, report: Dict) -> str:
        """格式化邮件正文"""
        return f"""
研究员报告

报告ID：{report.get('report_id')}
时段：{report.get('segment')}
生成时间：{report.get('generated_at')}

期货市场概述：
{report.get('futures_summary', {}).get('market_overview', '')}

爬虫统计：
采集源数量：{report.get('crawler_stats', {}).get('sources_crawled', 0)}
处理文章数：{report.get('crawler_stats', {}).get('articles_processed', 0)}
"""
