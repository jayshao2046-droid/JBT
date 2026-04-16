"""Mini 侧研报存储 — SQLite 索引 + JSON 文件

路径约定（Mini 本地）：
  STORE_ROOT  = runtime/data/researcher/
  JSON 文件   = runtime/data/researcher/reports/YYYY-MM-DD/HH-MM.json
  SQLite      = runtime/data/researcher/researcher_reports.db
"""

from __future__ import annotations

import datetime
import json
import os
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 动态确定存储根目录（与 main.py 中 DEFAULT_STORAGE_ROOT 对齐）
_SERVICE_ROOT = Path(__file__).resolve().parents[2]  # services/data/
# 优先使用 DATA_STORAGE_ROOT 环境变量（Docker 容器内为 /data），
# 其次 RESEARCHER_STORE_ROOT 环境变量（测试覆盖用），
# 最后 fallback 到 _SERVICE_ROOT/runtime/data（开发环境）
_DATA_STORAGE_ROOT = Path(
    os.environ.get("DATA_STORAGE_ROOT", str(_SERVICE_ROOT / "runtime" / "data"))
)
STORE_ROOT = Path(
    os.environ.get(
        "RESEARCHER_STORE_ROOT",
        str(_DATA_STORAGE_ROOT / "researcher"),
    )
)
DB_PATH = STORE_ROOT / "researcher_reports.db"


def _ensure_dirs() -> None:
    # 动态读取 STORE_ROOT，支持测试时 monkeypatch
    import sys
    store_root = sys.modules[__name__].STORE_ROOT
    store_root.mkdir(parents=True, exist_ok=True)
    (store_root / "reports").mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db_connection():
    """
    P0-2 修复：使用上下文管理器强制连接关闭

    使用方式：
        with get_db_connection() as conn:
            conn.execute(...)
    """
    _ensure_dirs()
    # 动态读取 DB_PATH，支持测试时 monkeypatch
    import sys
    db_path = sys.modules[__name__].DB_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _init_db() -> None:
    """初始化数据库表结构"""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS researcher_reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id   TEXT UNIQUE NOT NULL,
                date        TEXT NOT NULL,
                hour        TEXT NOT NULL,
                symbol_count INTEGER DEFAULT 0,
                confidence  REAL DEFAULT 0.0,
                file_path   TEXT,
                stored_at   TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rr_date ON researcher_reports(date, hour)")
        conn.commit()


def save(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    保存研报到 Mini。

    Args:
        report: 研报字典（Alienware 推送的完整 JSON）

    Returns:
        {"report_id": ..., "stored_at": ..., "file_path": ...}
    """
    _ensure_dirs()
    _init_db()  # 确保数据库表已创建

    report_id = report.get("report_id", "")
    date      = report.get("date") or str(datetime.date.today())
    # segment 可能是 "12:00" 或 "12-00"，统一转为文件名安全格式
    segment   = report.get("segment") or report.get("hour", "00-00")
    hour      = segment.replace(":", "-")
    symbols   = report.get("symbols") or report.get("futures_summary", {}).get("symbols", {})
    confidence = float(report.get("confidence", 0.0))
    stored_at  = datetime.datetime.now().isoformat()

    # 写 JSON 文件
    import sys
    store_root = sys.modules[__name__].STORE_ROOT
    day_dir = store_root / "reports" / date
    day_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(day_dir / f"{hour}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # 写 SQLite 索引（INSERT OR REPLACE 幂等）
    with get_db_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO researcher_reports
               (report_id, date, hour, symbol_count, confidence, file_path, stored_at)
               VALUES (?,?,?,?,?,?,?)""",
            (report_id, date, hour, len(symbols), confidence, file_path, stored_at),
        )
        conn.commit()

    return {"report_id": report_id, "stored_at": stored_at, "file_path": file_path}


def get_latest(date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    返回最新一份完整研报 JSON。

    Args:
        date: YYYY-MM-DD，None 表示今天

    Returns:
        研报字典，无数据返回 None
    """
    _init_db()  # 确保数据库表已创建
    target = date or str(datetime.date.today())
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT file_path FROM researcher_reports WHERE date=? ORDER BY hour DESC LIMIT 1",
            (target,),
        ).fetchone()

    if not row:
        return None

    try:
        with open(row["file_path"], encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Report file not found: {row['file_path']}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in report file {row['file_path']}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load report from {row['file_path']}: {e}", exc_info=True)
        return None


def list_reports(date: Optional[str] = None, limit: int = 24) -> List[Dict[str, Any]]:
    """
    返回指定日期的研报摘要列表（不含完整 symbols 数据）。

    Args:
        date:  YYYY-MM-DD，None 表示今天
        limit: 最多返回条数

    Returns:
        摘要列表，按 hour 倒序
    """
    _init_db()  # 确保数据库表已创建
    target = date or str(datetime.date.today())
    with get_db_connection() as conn:
        rows = conn.execute(
            """SELECT report_id, date, hour, symbol_count, confidence, stored_at
               FROM researcher_reports
               WHERE date=? ORDER BY hour DESC LIMIT ?""",
            (target, limit),
        ).fetchall()

    return [
        {
            "report_id":    r["report_id"],
            "date":         r["date"],
            "hour":         r["hour"],
            "symbol_count": r["symbol_count"],
            "confidence":   r["confidence"],
            "stored_at":    r["stored_at"],
        }
        for r in rows
    ]


# P0-2 修复：模块加载时初始化数据库，确保表结构存在
_init_db()
