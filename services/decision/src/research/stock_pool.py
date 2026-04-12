"""
股票池管理器 (CB4)
管理常驻股票池，支持添加、删除、轮换操作
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .stock_screener import StockScreener


class StockPool:
    """股票池管理器，维护固定大小的股票池"""

    def __init__(
        self,
        max_size: int = 30,
        data_service_url: str = "http://localhost:8105",
        screener: StockScreener | None = None
    ):
        self.max_size = max_size
        self.data_service_url = data_service_url
        self.pool_id = f"pool-{uuid.uuid4().hex[:12]}"
        self._pool: dict[str, str] = {}  # symbol -> added_at (ISO string)
        self._screener = screener
        self._updated_at = datetime.now().isoformat()

    def add(self, symbol: str) -> bool:
        """添加股票到池中，如果已存在返回 False"""
        if symbol in self._pool:
            return False
        if len(self._pool) >= self.max_size:
            return False
        self._pool[symbol] = datetime.now().isoformat()
        self._updated_at = datetime.now().isoformat()
        return True

    def remove(self, symbol: str) -> bool:
        """从池中移除股票，如果不存在返回 False"""
        if symbol not in self._pool:
            return False
        del self._pool[symbol]
        self._updated_at = datetime.now().isoformat()
        return True

    def rotate(self, to_add: list[str], to_remove: list[str]) -> dict:
        """批量轮换：先移除 to_remove，再添加 to_add"""
        removed_count = 0
        added_count = 0
        failed_add = []

        # 先移除
        for symbol in to_remove:
            if self.remove(symbol):
                removed_count += 1

        # 再添加
        for symbol in to_add:
            if self.add(symbol):
                added_count += 1
            else:
                failed_add.append(symbol)

        return {
            "pool_id": self.pool_id,
            "removed_count": removed_count,
            "added_count": added_count,
            "failed_add": failed_add,
            "current_size": len(self._pool),
            "max_size": self.max_size,
            "rotated_at": datetime.now().isoformat()
        }

    def get_pool(self) -> list[str]:
        """返回当前股票代码列表"""
        return list(self._pool.keys())

    def contains(self, symbol: str) -> bool:
        """检查股票是否在池中"""
        return symbol in self._pool

    def size(self) -> int:
        """返回当前池大小"""
        return len(self._pool)

    def to_dict(self) -> dict:
        """返回股票池完整信息"""
        return {
            "pool_id": self.pool_id,
            "symbols": list(self._pool.keys()),
            "max_size": self.max_size,
            "updated_at": self._updated_at
        }
