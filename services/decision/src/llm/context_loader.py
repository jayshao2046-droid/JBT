"""Daily context loader for LLM pipeline.

TASK-0104-D2: 从 data 服务拉取夜间预读摘要，TTL 缓存 8 小时。
"""

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class DailyContextLoader:
    """Load daily preread context from data service with TTL cache."""

    TTL_SECONDS = 8 * 3600  # 8 小时缓存
    DATA_API_URL = os.getenv("DATA_API_URL", "http://localhost:8105")

    def __init__(self):
        """Initialize context loader with empty cache."""
        self._cache: Optional[Dict[str, Any]] = None
        self._loaded_at: float = 0.0

    def get(self) -> Optional[Dict[str, Any]]:
        """返回今日预读上下文，TTL 内走内存缓存；不可用时返回 None（降级）。

        Returns:
            Dict containing:
                - researcher_context: 研究员上下文
                - l1_briefing: L1 快速简报
                - l2_audit_context: L2 审核上下文
                - analyst_dataset: 数据分析师数据集
                - ready_flag: 是否就绪
                - generated_at: 生成时间
                - errors: 错误列表
            Or None if data service is unavailable (graceful degradation)
        """
        # Check cache validity
        if self._cache and (time.time() - self._loaded_at) < self.TTL_SECONDS:
            logger.debug("返回缓存的预读上下文 (TTL 内)")
            return self._cache

        # Refresh cache
        return self._refresh()

    def _refresh(self) -> Optional[Dict[str, Any]]:
        """从 data 服务刷新预读上下文。

        Returns:
            Dict or None if failed (graceful degradation)
        """
        try:
            url = f"{self.DATA_API_URL.rstrip('/')}/api/v1/context/daily"
            logger.debug(f"正在从 data 服务拉取预读上下文: {url}")

            response = httpx.get(url, timeout=5.0)

            if response.status_code == 200:
                self._cache = response.json()
                self._loaded_at = time.time()
                logger.info(
                    "预读上下文已刷新: ready_flag=%s errors=%d",
                    self._cache.get("ready_flag", False),
                    len(self._cache.get("errors", [])),
                )
                return self._cache
            else:
                logger.warning(
                    "data 服务返回非 200 状态码: %d, 降级为无上下文模式",
                    response.status_code,
                )
                return None

        except httpx.ConnectError:
            logger.warning("无法连接到 data 服务 (%s), 降级为无上下文模式", self.DATA_API_URL)
            return None
        except httpx.TimeoutException:
            logger.warning("data 服务请求超时, 降级为无上下文模式")
            return None
        except Exception as exc:
            logger.warning("拉取预读上下文失败: %s, 降级为无上下文模式", exc)
            return None


# Module-level singleton
_loader = DailyContextLoader()


def get_daily_context() -> Optional[Dict[str, Any]]:
    """模块级单例访问入口。

    Returns:
        Dict or None if data service is unavailable
    """
    return _loader.get()
