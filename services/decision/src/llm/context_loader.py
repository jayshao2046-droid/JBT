"""Daily context loader for LLM pipeline.

TASK-0104-D2: 从 data 服务拉取夜间预读摘要，TTL 缓存 8 小时。
TASK-0112 Batch A: 扩展 L1/L2 门控上下文加载（K线 + 研报）。
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

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


# ============================================================================
# TASK-0112 Batch A: L1/L2 门控上下文加载
# ============================================================================

def _is_stock_symbol(symbol: str) -> bool:
    """判断是否为股票标的（根据前缀判断）。

    Args:
        symbol: 交易标的

    Returns:
        True if stock, False if futures
    """
    # 股票标的通常以数字开头（如 000001.SZ, 600000.SH）
    # 期货标的通常以字母开头（如 RB2505, AU2506）
    return symbol and symbol[0].isdigit()


async def get_l1_context(symbol: str) -> Tuple[str, List[str]]:
    """获取 L1 快审上下文：5日日线K线。

    Args:
        symbol: 交易标的

    Returns:
        Tuple of (context_string, missing_sources)
            - context_string: 格式化的上下文文本
            - missing_sources: 缺失的数据源列表
    """
    data_api_url = os.getenv("DATA_API_URL", "http://localhost:8105")
    missing_sources = []

    # 判断是股票还是期货，选择对应的 API 端点
    if _is_stock_symbol(symbol):
        endpoint = f"{data_api_url.rstrip('/')}/api/v1/stocks/bars"
    else:
        endpoint = f"{data_api_url.rstrip('/')}/api/v1/bars"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                endpoint,
                params={"symbol": symbol, "duration": "1d", "count": 5},
            )
            response.raise_for_status()
            data = response.json()
            bars = data.get("bars", [])

            if not bars:
                logger.warning(f"L1 上下文：{symbol} 5日K线为空")
                missing_sources.append("5日日线K线")
                return "[DATA_DEGRADED] 5日日线K线缺失", missing_sources

            # 格式化 K 线数据
            context_parts = ["[L1 上下文 - 5日日线K线]"]
            for bar in bars:
                context_parts.append(
                    f"  {bar.get('timestamp', 'N/A')}: "
                    f"开 {bar.get('open', 0):.2f} "
                    f"高 {bar.get('high', 0):.2f} "
                    f"低 {bar.get('low', 0):.2f} "
                    f"收 {bar.get('close', 0):.2f} "
                    f"量 {bar.get('volume', 0)}"
                )

            if len(bars) < 5:
                context_parts.append(f"[DATA_DEGRADED] 仅获取到 {len(bars)} 条K线，预期 5 条")
                missing_sources.append("5日日线K线（不足）")

            return "\n".join(context_parts), missing_sources

    except httpx.HTTPStatusError as exc:
        logger.error(f"L1 上下文拉取失败 (HTTP {exc.response.status_code}): {symbol}")
        missing_sources.append("5日日线K线")
        return f"[DATA_DEGRADED] K线拉取失败: HTTP {exc.response.status_code}", missing_sources
    except Exception as exc:
        logger.error(f"L1 上下文拉取异常: {symbol} - {exc}")
        missing_sources.append("5日日线K线")
        return f"[DATA_DEGRADED] K线拉取异常: {str(exc)}", missing_sources


async def get_l2_context(symbol: str) -> Tuple[str, List[str]]:
    """获取 L2 深审上下文：20日日线 + 60根分钟线 + 研报摘要。

    Args:
        symbol: 交易标的

    Returns:
        Tuple of (context_string, missing_sources)
            - context_string: 格式化的上下文文本
            - missing_sources: 缺失的数据源列表
    """
    data_api_url = os.getenv("DATA_API_URL", "http://localhost:8105")
    missing_sources = []
    context_parts = ["[L2 上下文]"]

    # 判断是股票还是期货
    is_stock = _is_stock_symbol(symbol)
    bars_endpoint = f"{data_api_url.rstrip('/')}/api/v1/stocks/bars" if is_stock else f"{data_api_url.rstrip('/')}/api/v1/bars"

    # 1. 拉取 20日日线
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                bars_endpoint,
                params={"symbol": symbol, "duration": "1d", "count": 20},
            )
            response.raise_for_status()
            data = response.json()
            daily_bars = data.get("bars", [])

            if not daily_bars:
                logger.warning(f"L2 上下文：{symbol} 20日日线为空")
                missing_sources.append("20日日线K线")
                context_parts.append("[DATA_DEGRADED] 20日日线K线缺失")
            else:
                context_parts.append(f"\n20日日线K线（最近5条）:")
                for bar in daily_bars[:5]:
                    context_parts.append(
                        f"  {bar.get('timestamp', 'N/A')}: "
                        f"收 {bar.get('close', 0):.2f} "
                        f"量 {bar.get('volume', 0)}"
                    )
                if len(daily_bars) < 20:
                    context_parts.append(f"[DATA_DEGRADED] 仅获取到 {len(daily_bars)} 条日线，预期 20 条")
                    missing_sources.append("20日日线K线（不足）")

    except Exception as exc:
        logger.error(f"L2 上下文 20日日线拉取失败: {symbol} - {exc}")
        missing_sources.append("20日日线K线")
        context_parts.append(f"[DATA_DEGRADED] 20日日线拉取失败: {str(exc)}")

    # 2. 拉取 60根分钟线
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                bars_endpoint,
                params={"symbol": symbol, "duration": "1m", "count": 60},
            )
            response.raise_for_status()
            data = response.json()
            minute_bars = data.get("bars", [])

            if not minute_bars:
                logger.warning(f"L2 上下文：{symbol} 60根分钟线为空")
                missing_sources.append("60根分钟线")
                context_parts.append("\n[DATA_DEGRADED] 60根分钟线缺失")
            else:
                context_parts.append(f"\n60根分钟线（最近5条）:")
                for bar in minute_bars[:5]:
                    context_parts.append(
                        f"  {bar.get('timestamp', 'N/A')}: "
                        f"收 {bar.get('close', 0):.2f}"
                    )
                if len(minute_bars) < 60:
                    context_parts.append(f"[DATA_DEGRADED] 仅获取到 {len(minute_bars)} 条分钟线，预期 60 条")
                    missing_sources.append("60根分钟线（不足）")

    except Exception as exc:
        logger.error(f"L2 上下文 60根分钟线拉取失败: {symbol} - {exc}")
        missing_sources.append("60根分钟线")
        context_parts.append(f"\n[DATA_DEGRADED] 60根分钟线拉取失败: {str(exc)}")

    # 3. 拉取研报摘要（TASK-0110 就绪前 graceful fallback）
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{data_api_url.rstrip('/')}/api/v1/researcher/report/latest",
                params={"symbol": symbol},
            )
            response.raise_for_status()
            data = response.json()
            report = data.get("report", {})

            if not report:
                logger.info(f"L2 上下文：{symbol} 研报为空（TASK-0110 未就绪或无数据）")
                missing_sources.append("研报摘要")
                context_parts.append("\n[DATA_DEGRADED] 研报摘要缺失（数据研究员未就绪）")
            else:
                summary = report.get("summary", "无摘要")
                context_parts.append(f"\n研报摘要:\n  {summary[:200]}")

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            logger.info(f"L2 上下文：研报 API 未就绪 (404)，TASK-0110 可能未部署")
            missing_sources.append("研报摘要")
            context_parts.append("\n[DATA_DEGRADED] 研报摘要缺失（API 未就绪）")
        else:
            logger.error(f"L2 上下文研报拉取失败 (HTTP {exc.response.status_code}): {symbol}")
            missing_sources.append("研报摘要")
            context_parts.append(f"\n[DATA_DEGRADED] 研报拉取失败: HTTP {exc.response.status_code}")
    except Exception as exc:
        logger.error(f"L2 上下文研报拉取异常: {symbol} - {exc}")
        missing_sources.append("研报摘要")
        context_parts.append(f"\n[DATA_DEGRADED] 研报拉取异常: {str(exc)}")

    return "\n".join(context_parts), missing_sources
