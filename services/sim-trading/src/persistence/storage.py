"""
数据持久化存储服务
使用 JSON 文件存储权益曲线、KPI 快照等历史数据
"""
import json
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from threading import Lock
from typing import List, Dict, Any, Optional


class PersistenceStorage:
    """数据持久化存储服务"""

    def __init__(self, runtime_dir: str = "./runtime"):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(exist_ok=True)
        self._lock = Lock()

    def append_equity_point(self, equity: float, floating_pnl: float, close_pnl: float) -> None:
        """追加权益曲线数据点"""
        today = date.today().isoformat()
        filepath = self.runtime_dir / "equity_curve.json"

        with self._lock:
            data = self._load_json(filepath, default={})
            if today not in data:
                data[today] = []

            data[today].append({
                "timestamp": datetime.now().isoformat(),
                "equity": round(equity, 2),
                "floating_pnl": round(floating_pnl, 2),
                "close_pnl": round(close_pnl, 2)
            })

            # 只保留最近 90 天
            cutoff = (date.today() - timedelta(days=90)).isoformat()
            data = {k: v for k, v in data.items() if k >= cutoff}

            self._save_json(filepath, data)

    def get_equity_curve(self, period: str = "day") -> List[Dict[str, Any]]:
        """获取权益曲线数据

        Args:
            period: day | week | month | year | all

        Returns:
            权益曲线数据点列表
        """
        filepath = self.runtime_dir / "equity_curve.json"
        data = self._load_json(filepath, default={})

        if period == "day":
            today = date.today().isoformat()
            return data.get(today, [])
        elif period == "week":
            start = (date.today() - timedelta(days=7)).isoformat()
            return self._flatten_range(data, start)
        elif period == "month":
            start = (date.today() - timedelta(days=30)).isoformat()
            return self._flatten_range(data, start)
        elif period == "year":
            start = (date.today() - timedelta(days=365)).isoformat()
            return self._flatten_range(data, start)
        else:  # all
            return self._flatten_range(data, "1970-01-01")

    def save_kpi_snapshot(
        self,
        snapshot_date: str,
        trading_kpis: Dict[str, float],
        execution_kpis: Dict[str, float]
    ) -> None:
        """保存 KPI 快照"""
        filepath = self.runtime_dir / "kpi_snapshots.json"

        with self._lock:
            data = self._load_json(filepath, default={})
            data[snapshot_date] = {
                "date": snapshot_date,
                "trading_kpis": trading_kpis,
                "execution_kpis": execution_kpis,
                "timestamp": datetime.now().isoformat()
            }

            # 只保留最近 90 天
            cutoff = (date.today() - timedelta(days=90)).isoformat()
            data = {k: v for k, v in data.items() if k >= cutoff}

            self._save_json(filepath, data)

    def get_kpi_snapshot(self, snapshot_date: str) -> Optional[Dict[str, Any]]:
        """获取 KPI 快照"""
        filepath = self.runtime_dir / "kpi_snapshots.json"
        data = self._load_json(filepath, default={})
        return data.get(snapshot_date)

    def save_trade(self, trade: Dict[str, Any]) -> None:
        """保存成交记录"""
        filepath = self.runtime_dir / "trades_history.json"

        with self._lock:
            data = self._load_json(filepath, default=[])
            trade["saved_at"] = datetime.now().isoformat()
            data.append(trade)

            # 只保留最近 30 天
            cutoff = (datetime.now() - timedelta(days=30)).isoformat()
            data = [t for t in data if t.get("saved_at", "") >= cutoff]

            self._save_json(filepath, data)

    def get_trades(self, days: int = 1) -> List[Dict[str, Any]]:
        """获取成交历史

        Args:
            days: 最近 N 天

        Returns:
            成交记录列表
        """
        filepath = self.runtime_dir / "trades_history.json"
        data = self._load_json(filepath, default=[])

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return [t for t in data if t.get("saved_at", "") >= cutoff]

    def _flatten_range(self, data: Dict, start_date: str) -> List[Dict]:
        """展平日期范围内的数据"""
        result = []
        for day, points in sorted(data.items()):
            if day >= start_date:
                result.extend(points)
        return result

    def _load_json(self, filepath: Path, default=None):
        """加载 JSON 文件"""
        if not filepath.exists():
            return default
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default

    def _save_json(self, filepath: Path, data):
        """保存 JSON 文件"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Failed to save {filepath}: {e}")


# 全局单例
_storage_instance: Optional[PersistenceStorage] = None
_storage_lock = Lock()


def get_storage() -> PersistenceStorage:
    """获取全局 PersistenceStorage 单例"""
    global _storage_instance
    if _storage_instance is None:
        with _storage_lock:
            if _storage_instance is None:
                runtime_dir = os.getenv("RUNTIME_DIR", "./runtime")
                _storage_instance = PersistenceStorage(runtime_dir)
    return _storage_instance
