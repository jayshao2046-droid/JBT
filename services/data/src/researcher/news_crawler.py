"""
新闻爬虫 - 采集期货相关新闻

职责：
1. 爬取新浪财经、东方财富、金十数据等新闻源
2. 过滤期货相关新闻
3. 推送到共享队列
"""
import logging
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import multiprocessing as mp

logger = logging.getLogger(__name__)


class NewsCrawler:
    """新闻爬虫"""

    def __init__(self, queue: mp.Queue, stop_event: mp.Event):
        self.queue = queue
        self.stop_event = stop_event

        # 新闻源配置
        self.sources = [
            {
                "name": "新浪财经-期货",
                "url": "https://finance.sina.com.cn/futuremarket/",
                "interval": 300  # 5分钟
            },
            {
                "name": "东方财富-期货",
                "url": "https://futures.eastmoney.com/news/",
                "interval": 300
            },
            {
                "name": "金十数据",
                "url": "https://www.jin10.com/",
                "interval": 180  # 3分钟
            }
        ]

        self.last_crawl_time = {}
        self.seen_urls = set()  # 去重

    def run(self):
        """主循环"""
        logger.info("NewsCrawler started")

        while not self.stop_event.is_set():
            try:
                self._crawl_all_sources()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"NewsCrawler error: {e}", exc_info=True)
                time.sleep(10)

        logger.info("NewsCrawler stopped")

    def _crawl_all_sources(self):
        """爬取所有新闻源"""
        now = time.time()

        for source in self.sources:
            if self.stop_event.is_set():
                break

            # 检查是否到了爬取时间
            last_time = self.last_crawl_time.get(source["name"], 0)
            if now - last_time < source["interval"]:
                continue

            try:
                self._crawl_source(source)
                self.last_crawl_time[source["name"]] = now
            except Exception as e:
                logger.error(f"Error crawling {source['name']}: {e}")

    def _crawl_source(self, source: dict):
        """爬取单个新闻源"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            resp = requests.get(source["url"], headers=headers, timeout=10)
            if resp.status_code != 200:
                return

            soup = BeautifulSoup(resp.text, "html.parser")

            # 简单提取标题和链接（实际需要针对每个网站定制）
            links = soup.find_all("a", href=True)

            for link in links[:20]:  # 只取前 20 条
                if self.stop_event.is_set():
                    break

                title = link.get_text(strip=True)
                url = link["href"]

                # 过滤：标题包含期货关键词
                if not self._is_futures_related(title):
                    continue

                # 去重
                if url in self.seen_urls:
                    continue

                self.seen_urls.add(url)

                # 推送到队列
                event = {
                    "type": "news",
                    "source": source["name"],
                    "title": title,
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                }

                try:
                    self.queue.put_nowait(event)
                    logger.info(f"News: {title[:50]}")
                except:
                    pass

        except Exception as e:
            logger.debug(f"Error crawling {source['name']}: {e}")

    def _is_futures_related(self, title: str) -> bool:
        """判断是否期货相关"""
        keywords = [
            "期货", "商品", "铜", "铝", "锌", "铅", "镍", "锡", "金", "银",
            "螺纹", "热卷", "铁矿", "焦炭", "焦煤", "动力煤", "原油", "沥青",
            "橡胶", "玉米", "豆粕", "菜粕", "白糖", "棉花", "PTA", "甲醇",
            "股指", "国债", "IF", "IC", "IH", "IM"
        ]

        return any(kw in title for kw in keywords)
