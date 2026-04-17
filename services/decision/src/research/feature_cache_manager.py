"""品种特征缓存管理器 - 支持增量更新"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FeatureCacheManager:
    """管理品种特征的缓存和增量更新"""

    def __init__(self, cache_dir: str = "runtime/symbol_profiles"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, symbol: str) -> Path:
        """获取品种缓存文件路径"""
        safe_symbol = symbol.replace(".", "_").replace("/", "_")
        return self.cache_dir / f"{safe_symbol}.json"

    def load_cache(self, symbol: str) -> Optional[dict[str, Any]]:
        """加载品种特征缓存

        Returns:
            缓存数据，如果不存在或已损坏则返回 None
        """
        cache_path = self.get_cache_path(symbol)
        if not cache_path.exists():
            logger.info(f"缓存不存在: {symbol}")
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info(f"加载缓存成功: {symbol}, 最后更新={cache.get('last_update')}")
            return cache
        except Exception as e:
            logger.error(f"加载缓存失败: {symbol}, 错误={e}")
            return None

    def save_cache(self, symbol: str, cache_data: dict[str, Any]) -> None:
        """保存品种特征缓存"""
        cache_path = self.get_cache_path(symbol)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.info(f"保存缓存成功: {symbol}")
        except Exception as e:
            logger.error(f"保存缓存失败: {symbol}, 错误={e}")
            raise

    def is_cache_valid(self, cache: dict[str, Any], max_age_days: int = 1) -> bool:
        """检查缓存是否有效（未过期）

        Args:
            cache: 缓存数据
            max_age_days: 最大缓存天数

        Returns:
            True 如果缓存有效，False 如果已过期
        """
        if not cache or "last_update" not in cache:
            return False

        try:
            last_update = datetime.fromisoformat(cache["last_update"])
            age = datetime.now() - last_update
            is_valid = age.days < max_age_days

            if not is_valid:
                logger.info(f"缓存已过期: 最后更新={last_update}, 已过去{age.days}天")

            return is_valid
        except Exception as e:
            logger.error(f"检查缓存有效性失败: {e}")
            return False

    def get_incremental_date_range(self, cache: dict[str, Any]) -> tuple[str, str]:
        """获取增量更新的日期范围

        Args:
            cache: 缓存数据

        Returns:
            (start_date, end_date) 元组，格式 "YYYY-MM-DD"
        """
        if not cache or "data_range" not in cache:
            # 没有缓存，返回默认5年范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

        # 从上次更新的下一天开始
        last_end = cache["data_range"]["end"]
        start_date = datetime.strptime(last_end, "%Y-%m-%d") + timedelta(days=1)
        end_date = datetime.now()

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def merge_rolling_state(
        self,
        old_state: dict[str, list[float]],
        new_data: dict[str, list[float]],
        window_sizes: dict[str, int]
    ) -> dict[str, list[float]]:
        """合并滚动状态（删除最旧数据，追加最新数据）

        Args:
            old_state: 旧的滚动状态
            new_data: 新增的数据
            window_sizes: 各窗口的大小限制

        Returns:
            更新后的滚动状态
        """
        merged = {}

        for key, window_size in window_sizes.items():
            old_values = old_state.get(key, [])
            new_values = new_data.get(key, [])

            # 合并并保留最新的 window_size 个数据点
            combined = old_values + new_values
            merged[key] = combined[-window_size:] if len(combined) > window_size else combined

        return merged

    def list_all_cached_symbols(self) -> list[str]:
        """列出所有已缓存的品种"""
        symbols = []
        for cache_file in self.cache_dir.glob("*.json"):
            # 从文件名恢复品种代码
            symbol = cache_file.stem.replace("_", ".")
            symbols.append(symbol)
        return sorted(symbols)

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        symbols = self.list_all_cached_symbols()

        valid_count = 0
        expired_count = 0

        for symbol in symbols:
            cache = self.load_cache(symbol)
            if cache and self.is_cache_valid(cache):
                valid_count += 1
            else:
                expired_count += 1

        return {
            "total_symbols": len(symbols),
            "valid_caches": valid_count,
            "expired_caches": expired_count,
            "cache_dir": str(self.cache_dir),
        }
