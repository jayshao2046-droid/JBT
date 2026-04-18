"""反检测增强版 — UA 轮换、Referer/Accept 伪装、Cookie 管理、重试退避、Playwright 指纹"""

import random
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AntiDetect:
    """反检测工具 v2 — 增强反爬能力"""

    # User-Agent 轮换池（30+ 个，覆盖主流浏览器 2024-2026）
    USER_AGENTS = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Safari Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Firefox Mac/Linux
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        # Chrome Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Mobile (偶尔伪装移动端)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    ]

    # Referer 轮换池（按源域名分组）
    REFERER_MAP: Dict[str, List[str]] = {
        "default": [
            "https://www.google.com/",
            "https://www.google.com.hk/",
            "https://www.bing.com/",
            "https://cn.bing.com/",
        ],
        "domestic": [
            "https://www.baidu.com/",
            "https://www.sogou.com/",
            "https://www.so.com/",
        ],
        "international": [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
        ],
    }

    # Accept-Language 轮换
    ACCEPT_LANGUAGES = [
        "zh-CN,zh;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "en-US,en;q=0.9",
        "zh-CN,zh;q=0.9",
    ]

    def __init__(self):
        self._last_request_time: Dict[str, float] = {}  # source_id → last_time
        self._fail_count: Dict[str, int] = {}  # source_id → consecutive_fails

    def get_random_ua(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(self.USER_AGENTS)

    def get_headers(self, market: str = "default", source_url: str = "") -> Dict[str, str]:
        """获取完整的伪装请求头"""
        ua = self.get_random_ua()
        referer_pool = self.REFERER_MAP.get(market, self.REFERER_MAP["default"])
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice(self.ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Referer": random.choice(referer_pool),
        }
        # 特定源追加 DNT
        if random.random() > 0.5:
            headers["DNT"] = "1"
        return headers

    def get_random_interval(self, base: float) -> float:
        """获取随机请求间隔（base ± 30%）"""
        return base * random.uniform(0.7, 1.3)

    def should_throttle(self, source_id: str, min_interval: float = 3.0) -> float:
        """
        检查是否需要限速，返回需等待秒数（0 = 不需等待）

        自动对连续失败的源增加间隔（退避）
        """
        now = time.time()
        last = self._last_request_time.get(source_id, 0)
        fails = self._fail_count.get(source_id, 0)
        # 连续失败时增加间隔：min_interval * 2^fails (最大 60s)
        effective_interval = min(min_interval * (2 ** fails), 60.0)
        elapsed = now - last
        if elapsed < effective_interval:
            return effective_interval - elapsed
        return 0.0

    def record_request(self, source_id: str, success: bool):
        """记录请求结果（用于退避计算）"""
        self._last_request_time[source_id] = time.time()
        if success:
            self._fail_count[source_id] = 0
        else:
            self._fail_count[source_id] = self._fail_count.get(source_id, 0) + 1

    def get_fail_count(self, source_id: str) -> int:
        return self._fail_count.get(source_id, 0)

    def get_playwright_args(self) -> List[str]:
        """获取 Playwright 启动参数（去除 webdriver 标记）"""
        return [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
        ]

    def get_playwright_context_options(self) -> Dict:
        """Playwright 浏览器上下文选项"""
        ua = self.get_random_ua()
        return {
            "user_agent": ua,
            "viewport": random.choice([
                {"width": 1920, "height": 1080},
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
            ]),
            "locale": random.choice(["zh-CN", "en-US"]),
            "timezone_id": random.choice(["Asia/Shanghai", "America/New_York", "Europe/London"]),
        }

    def handle_rate_limit(self, attempt: int, max_attempts: int = 3) -> float:
        """处理速率限制（指数退避+抖动）"""
        if attempt > max_attempts:
            return -1
        base = 2 ** attempt
        jitter = random.uniform(0, base * 0.3)
        return base + jitter
