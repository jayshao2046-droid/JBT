"""暂存区管理 — 增量标记、水位追踪、数据拉取"""

import os
import json
import sqlite3
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx

from .config import ResearcherConfig
from .models import StagingRecord

logger = logging.getLogger(__name__)


class StagingManager:
    """暂存区管理器"""

    def __init__(self):
        ResearcherConfig.ensure_dirs()
        self.db_path = ResearcherConfig.STAGING_DB
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        # P1-1 修复：使用 with 语句确保连接自动关闭
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staging_records (
                    symbol TEXT PRIMARY KEY,
                    last_read_ts TEXT NOT NULL,
                    data_count INTEGER DEFAULT 0,
                    data_hash TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_last_read_ts(self, symbol: str) -> Optional[datetime]:
        """获取品种最后读取时间戳"""
        # P1-1 修复：使用 with 语句确保连接自动关闭
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_read_ts FROM staging_records WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()

        if row:
            return datetime.fromisoformat(row[0])
        return None

    def update_record(self, record: StagingRecord):
        """更新暂存区记录"""
        # P1-1 修复：使用 with 语句确保连接自动关闭
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO staging_records (symbol, last_read_ts, data_count, data_hash, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record.symbol,
                record.last_read_ts.isoformat(),
                record.data_count,
                record.data_hash,
                record.updated_at.isoformat()
            ))
            conn.commit()

    def get_incremental(self, symbols: List[str], lookback_hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """
        增量拉取数据

        Args:
            symbols: 品种列表
            lookback_hours: 回溯小时数（默认 24h）

        Returns:
            {symbol: [bar_data, ...]}
        """
        result = {}

        for symbol in symbols:
            last_ts = self.get_last_read_ts(symbol)
            if last_ts is None:
                # 首次读取，回溯 lookback_hours
                since = datetime.now() - timedelta(hours=lookback_hours)
            else:
                since = last_ts

            # 从 Mini data API 拉取数据
            data = self._fetch_from_data_api(symbol, since)

            if data:
                # 计算数据哈希
                data_hash = self._compute_hash(data)

                # 更新暂存区记录
                record = StagingRecord(
                    symbol=symbol,
                    last_read_ts=datetime.now(),
                    data_count=len(data),
                    data_hash=data_hash,
                    updated_at=datetime.now()
                )
                self.update_record(record)

                result[symbol] = data

        return result

    def _fetch_from_data_api(self, symbol: str, since: datetime) -> List[Dict[str, Any]]:
        """从 Mini data API 拉取期货 bars（使用 start/end 参数）"""
        try:
            url = f"{ResearcherConfig.DATA_API_URL}/api/v1/bars"
            now = datetime.now()

            # symbol 格式保持原始格式（如 KQ.m@SHFE.rb），由 API 侧处理
            params = {
                "symbol": symbol,
                "start": since.isoformat(),
                "end": now.isoformat(),
                "limit": 1000
            }

            resp = httpx.get(url, params=params, timeout=ResearcherConfig.HTTP_TIMEOUT_LONG)
            if resp.status_code == 200:
                return resp.json().get("bars", [])
            else:
                logger.warning(f"Mini API 返回错误 {resp.status_code} for {symbol}: {resp.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"拉取 {symbol} 数据失败: {e}")
            return []

    def _compute_hash(self, data: List[Dict[str, Any]]) -> str:
        """计算数据哈希（用于去重）"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def get_previous_summary(self, segment: str, date: str) -> Optional[Dict[str, Any]]:
        """
        获取上期摘要（用于变化对比）

        Args:
            segment: 当前时段
            date: 当前日期 YYYY-MM-DD

        Returns:
            上期报告的 futures_summary 或 None
        """
        # 根据时段推算上期报告
        segment_order = ["盘前", "午间", "盘后", "夜盘"]
        current_idx = segment_order.index(segment)

        if current_idx == 0:
            # 盘前 → 上期是前一天的夜盘
            prev_date = (datetime.fromisoformat(date) - timedelta(days=1)).strftime("%Y-%m-%d")
            prev_segment = "夜盘"
        else:
            # 其他时段 → 上期是当天的前一个时段
            prev_date = date
            prev_segment = segment_order[current_idx - 1]

        # 安全修复：P0-3 + P1-4 - 验证 prev_date 格式防止路径遍历
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', prev_date):
            raise ValueError(f"Invalid date format: {prev_date}")

        # P1-4 修复：验证 prev_segment 在白名单内
        valid_segments = ["盘前", "早盘", "午盘", "夜盘"]
        if prev_segment not in valid_segments:
            raise ValueError(f"Invalid segment: {prev_segment}")

        # 读取上期报告
        report_path = os.path.join(
            ResearcherConfig.REPORTS_DIR,
            prev_date,
            f"{prev_segment}.json"
        )

        # 安全修复：P0-3 - 验证路径在允许的目录内（在构建之前验证）
        from pathlib import Path
        reports_dir_resolved = Path(ResearcherConfig.REPORTS_DIR).resolve()
        report_path_resolved = Path(report_path).resolve()
        if not str(report_path_resolved).startswith(str(reports_dir_resolved)):
            raise ValueError(f"Path traversal detected: {report_path}")

        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                prev_report = json.load(f)
                return prev_report.get("futures_summary")

        return None
