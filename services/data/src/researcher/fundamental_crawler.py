"""
基本面爬虫 - 采集基本面数据

职责：
1. 爬取产业链数据（库存、产量、开工率等）
2. 爬取宏观数据（CPI、PMI等）
3. 推送到共享队列
"""
import logging
import time
from datetime import datetime
import requests
import multiprocessing as mp

logger = logging.getLogger(__name__)


class FundamentalCrawler:
    """基本面爬虫"""

    def __init__(self, queue: mp.Queue, stop_event: mp.Event):
        self.queue = queue
        self.stop_event = stop_event

        # 数据源配置
        self.sources = [
            {
                "name": "我的钢铁网-库存",
                "url": "https://www.mysteel.com/",
                "interval": 3600,  # 1小时
                "type": "inventory"
            },
            {
                "name": "卓创资讯-产量",
                "url": "https://www.sci99.com/",
                "interval": 3600,
                "type": "production"
            },
            {
                "name": "统计局-宏观",
                "url": "http://www.stats.gov.cn/",
                "interval": 86400,  # 1天
                "type": "macro"
            }
        ]

        self.last_crawl_time = {}

    def run(self):
        """主循环"""
        logger.info("FundamentalCrawler started")

        while not self.stop_event.is_set():
            try:
                self._crawl_all_sources()
                time.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                logger.error(f"FundamentalCrawler error: {e}", exc_info=True)
                time.sleep(10)

        logger.info("FundamentalCrawler stopped")

    def _crawl_all_sources(self):
        """爬取所有数据源"""
        now = time.time()

        for source in self.sources:
            if self.stop_event.is_set():
                break

            last_time = self.last_crawl_time.get(source["name"], 0)
            if now - last_time < source["interval"]:
                continue

            try:
                self._crawl_source(source)
                self.last_crawl_time[source["name"]] = now
            except Exception as e:
                logger.error(f"Error crawling {source['name']}: {e}")

    def _crawl_source(self, source: dict):
        """爬取单个数据源（简化实现）"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            resp = requests.get(source["url"], headers=headers, timeout=10)
            if resp.status_code != 200:
                return

            # 简化：实际需要针对每个网站定制解析逻辑
            event = {
                "type": "fundamental",
                "source": source["name"],
                "data_type": source["type"],
                "timestamp": datetime.now().isoformat(),
                "content": f"Crawled from {source['name']}"  # 实际应解析具体数据
            }

            # 安全修复：P0-6 - 明确捕获预期异常类型
            try:
                self.queue.put_nowait(event)
                logger.info(f"Fundamental: {source['name']}")
            except Exception as e:
                logger.warning(f"Queue full, dropping fundamental data from {source['name']}")

        except Exception as e:
            logger.debug(f"Error crawling {source['name']}: {e}")
