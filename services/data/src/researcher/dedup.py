"""文章去重管理器 — SQLite + hash 去重"""

import hashlib
import sqlite3
import logging
from datetime import datetime
from typing import Optional

from .config import ResearcherConfig

logger = logging.getLogger(__name__)


class ArticleDedup:
    """文章去重器：基于 title+source_id 哈希判重"""

    def __init__(self):
        self.db_path = ResearcherConfig.STAGING_DB
        self._init_table()

    def _init_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS crawled_articles (
                    article_hash TEXT PRIMARY KEY,
                    source_id    TEXT NOT NULL,
                    title        TEXT NOT NULL,
                    url          TEXT,
                    first_seen   TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_article_source ON crawled_articles(source_id, first_seen)"
            )

    @staticmethod
    def _hash(source_id: str, title: str) -> str:
        raw = f"{source_id}||{title.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def is_new(self, source_id: str, title: str) -> bool:
        """判断是否为新文章"""
        h = self._hash(source_id, title)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM crawled_articles WHERE article_hash = ?", (h,)
            ).fetchone()
        return row is None

    def mark_seen(self, source_id: str, title: str, url: str = ""):
        """标记为已处理"""
        h = self._hash(source_id, title)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO crawled_articles (article_hash, source_id, title, url, first_seen) "
                "VALUES (?, ?, ?, ?, ?)",
                (h, source_id, title, url, datetime.now().isoformat()),
            )

    def count_today(self, source_id: Optional[str] = None) -> int:
        """统计今日已处理文章数"""
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            if source_id:
                row = conn.execute(
                    "SELECT COUNT(*) FROM crawled_articles WHERE source_id = ? AND first_seen LIKE ?",
                    (source_id, f"{today}%"),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM crawled_articles WHERE first_seen LIKE ?",
                    (f"{today}%",),
                ).fetchone()
        return row[0] if row else 0
