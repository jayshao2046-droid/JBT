"""内存数据库 - SQLite 存储"""
import sqlite3
from pathlib import Path

class MemoryDB:
    def __init__(self, db_path: str = "/data/researcher/memory.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
