"""爬虫引擎"""
import requests
from bs4 import BeautifulSoup

class CrawlerEngine:
    def __init__(self, mode: str = "code"):
        self.mode = mode

    def fetch(self, url: str) -> str:
        """抓取网页"""
        resp = requests.get(url, timeout=10)
        return resp.text

    def parse(self, html: str) -> list:
        """解析网页"""
        soup = BeautifulSoup(html, "html.parser")
        return []
