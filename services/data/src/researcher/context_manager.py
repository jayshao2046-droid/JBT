"""
上下文管理器 - 管理连贯写作的上下文

职责：
1. 存储历史分析结果
2. 提供上下文查询接口
3. 支持连贯写作
"""
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器"""

    def __init__(self, db_path: str = "/data/researcher/context.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        # 安全修复：P0-4 - 使用 with 语句防止资源泄漏
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 分析历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    analysis_type TEXT,
                    content TEXT,
                    timestamp TEXT,
                    segment TEXT
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp
                ON analysis_history(symbol, timestamp DESC)
            """)

            conn.commit()

    def add_analysis(self, symbol: str, analysis_type: str, content: str, segment: str = ""):
        """添加分析记录"""
        # 安全修复：P0-4 - 使用 with 语句防止资源泄漏
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO analysis_history (symbol, analysis_type, content, timestamp, segment)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, analysis_type, content, now, segment))

            conn.commit()

    def get_recent_analysis(self, symbol: str, hours: int = 24, limit: int = 10) -> List[Dict]:
        """获取最近的分析记录"""
        # 安全修复：P0-4 - 使用 with 语句防止资源泄漏
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor.execute("""
                SELECT analysis_type, content, timestamp, segment
                FROM analysis_history
                WHERE symbol = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (symbol, cutoff, limit))

            rows = cursor.fetchall()

        return [
            {
                "analysis_type": row[0],
                "content": row[1],
                "timestamp": row[2],
                "segment": row[3]
            }
            for row in rows
        ]

    def get_segment_summary(self, segment: str) -> List[Dict]:
        """获取某个时段的所有分析"""
        # 安全修复：P0-4 - 使用 with 语句防止资源泄漏
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT symbol, analysis_type, content, timestamp
                FROM analysis_history
                WHERE segment = ?
                ORDER BY timestamp DESC
            """, (segment,))

            rows = cursor.fetchall()

        return [
            {
                "symbol": row[0],
                "analysis_type": row[1],
                "content": row[2],
                "timestamp": row[3]
            }
            for row in rows
        ]

    def cleanup_old_records(self, days: int = 7):
        """清理旧记录"""
        # 安全修复：P0-4 - 使用 with 语句防止资源泄漏
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("DELETE FROM analysis_history WHERE timestamp < ?", (cutoff,))

            conn.commit()

        logger.info(f"Cleaned up context records older than {days} days")
