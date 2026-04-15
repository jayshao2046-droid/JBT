"""
去重管理器 - 防止重复处理数据

职责：
1. 记录已处理的新闻/文章
2. 记录已分析的 K 线时间点
3. 提供去重查询接口
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DeduplicationManager:
    """去重管理器"""

    def __init__(self, db_path: str = "/data/researcher/dedup.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 新闻去重表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_dedup (
                url TEXT PRIMARY KEY,
                title TEXT,
                source TEXT,
                first_seen_at TEXT,
                last_seen_at TEXT
            )
        """)

        # K 线分析去重表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kline_dedup (
                symbol TEXT,
                timestamp TEXT,
                analyzed_at TEXT,
                PRIMARY KEY (symbol, timestamp)
            )
        """)

        # 基本面数据去重表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_dedup (
                source TEXT,
                data_type TEXT,
                data_date TEXT,
                fetched_at TEXT,
                PRIMARY KEY (source, data_type, data_date)
            )
        """)

        conn.commit()
        conn.close()

    def is_news_seen(self, url: str) -> bool:
        """检查新闻是否已处理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM news_dedup WHERE url = ?", (url,))
        result = cursor.fetchone()

        conn.close()
        return result is not None

    def mark_news_seen(self, url: str, title: str, source: str):
        """标记新闻已处理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO news_dedup (url, title, source, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, COALESCE((SELECT first_seen_at FROM news_dedup WHERE url = ?), ?), ?)
        """, (url, title, source, url, now, now))

        conn.commit()
        conn.close()

    def is_kline_analyzed(self, symbol: str, timestamp: str) -> bool:
        """检查 K 线是否已分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM kline_dedup WHERE symbol = ? AND timestamp = ?", (symbol, timestamp))
        result = cursor.fetchone()

        conn.close()
        return result is not None

    def mark_kline_analyzed(self, symbol: str, timestamp: str):
        """标记 K 线已分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR IGNORE INTO kline_dedup (symbol, timestamp, analyzed_at)
            VALUES (?, ?, ?)
        """, (symbol, timestamp, now))

        conn.commit()
        conn.close()

    def is_fundamental_fetched(self, source: str, data_type: str, data_date: str) -> bool:
        """检查基本面数据是否已获取"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM fundamental_dedup WHERE source = ? AND data_type = ? AND data_date = ?",
            (source, data_type, data_date)
        )
        result = cursor.fetchone()

        conn.close()
        return result is not None

    def mark_fundamental_fetched(self, source: str, data_type: str, data_date: str):
        """标记基本面数据已获取"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR IGNORE INTO fundamental_dedup (source, data_type, data_date, fetched_at)
            VALUES (?, ?, ?, ?)
        """, (source, data_type, data_date, now))

        conn.commit()
        conn.close()

    def cleanup_old_records(self, days: int = 30):
        """清理旧记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("DELETE FROM news_dedup WHERE last_seen_at < ?", (cutoff,))
        cursor.execute("DELETE FROM kline_dedup WHERE analyzed_at < ?", (cutoff,))
        cursor.execute("DELETE FROM fundamental_dedup WHERE fetched_at < ?", (cutoff,))

        conn.commit()
        conn.close()

        logger.info(f"Cleaned up records older than {days} days")
