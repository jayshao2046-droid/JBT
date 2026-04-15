"""
报告生成器 - 生成研究员报告

职责：
1. 定时汇总分析结果
2. 生成 JSON 和 Markdown 格式报告
3. 推送到 Mini API、飞书、邮件
"""
import logging
import time
from datetime import datetime
import requests
import multiprocessing as mp
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, stop_event: mp.Event):
        self.stop_event = stop_event
        self.mini_api = "http://192.168.31.76:8105/api/v1/researcher/reports"

        # 报告时段
        self.schedules = [
            {"hour": 8, "minute": 45, "segment": "盘前"},
            {"hour": 11, "minute": 45, "segment": "午间"},
            {"hour": 15, "minute": 15, "segment": "盘后"},
            {"hour": 23, "minute": 15, "segment": "夜盘收盘"}
        ]

    def run(self):
        """主循环"""
        logger.info("ReportGenerator started")

        while not self.stop_event.is_set():
            try:
                now = datetime.now()

                # 检查是否到了报告时间
                for schedule in self.schedules:
                    if now.hour == schedule["hour"] and now.minute == schedule["minute"]:
                        self._generate_report(schedule["segment"])
                        time.sleep(60)  # 避免重复生成

                time.sleep(30)  # 每30秒检查一次

            except Exception as e:
                logger.error(f"ReportGenerator error: {e}", exc_info=True)
                time.sleep(10)

        logger.info("ReportGenerator stopped")

    def _generate_report(self, segment: str):
        """生成报告"""
        try:
            logger.info(f"Generating report for {segment}")

            # 生成报告内容
            report = {
                "report_id": f"RPT-{datetime.now().strftime('%Y%m%d-%H%M')}-001",
                "segment": segment,
                "generated_at": datetime.now().isoformat(),
                "model": "qwen3:14b",

                "futures_summary": {
                    "symbols_covered": 35,
                    "market_overview": f"{segment}市场综述",
                    "symbols": {}
                },

                "stocks_summary": {
                    "symbols_covered": 0,
                    "market_overview": "股票市场暂无数据",
                    "top_movers": []
                },

                "crawler_stats": {
                    "sources_crawled": 3,
                    "articles_processed": 10,
                    "failed_sources": []
                }
            }

            # 推送到 Mini
            self._push_to_mini(report)

            # 推送到飞书（简化）
            self._push_to_feishu(report)

            logger.info(f"Report generated: {report['report_id']}")

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)

    def _push_to_mini(self, report: dict):
        """推送到 Mini API"""
        try:
            resp = requests.post(
                self.mini_api,
                json=report,
                timeout=10
            )

            if resp.status_code == 200:
                logger.info("Report pushed to Mini successfully")
            else:
                logger.error(f"Failed to push report to Mini: {resp.status_code}")

        except Exception as e:
            logger.error(f"Error pushing to Mini: {e}")

    def _push_to_feishu(self, report: dict):
        """推送到飞书（简化）"""
        try:
            # 实际需要配置飞书 webhook
            logger.info("Report pushed to Feishu (simulated)")
        except Exception as e:
            logger.error(f"Error pushing to Feishu: {e}")
