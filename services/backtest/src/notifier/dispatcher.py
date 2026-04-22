"""
回测通知调度器 — 带静默窗口的轻量级调度。
通知类型：
- 完成（INFO → 资讯群，静默窗口适用）
- 失败（ALERT → 报警群，P1 bypass 静默窗口）
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone, timedelta

from .feishu import send_backtest_card

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


def _is_quiet_hours(now: datetime | None = None) -> bool:
    """静默时段：00:11–07:59，推送窗口 08:00–24:10。"""
    now = now or datetime.now(_TZ_CST)
    minutes = now.hour * 60 + now.minute
    return 11 <= minutes < 480


def notify_backtest_done(
    run_id: str,
    strategy_id: str,
    metrics: dict,
    elapsed_sec: float = 0.0,
) -> None:
    """
    回测完成通知 → INFO 群（静默窗口适用）。

    Args:
        run_id: 回测任务 ID
        strategy_id: 策略 ID
        metrics: 回测指标字典
        elapsed_sec: 耗时（秒）
    """
    if _is_quiet_hours():
        logger.debug("backtest done notify skipped (quiet hours) run_id=%s", run_id)
        return

    try:
        ok = send_backtest_card(
            status="done",
            run_id=run_id,
            strategy_id=strategy_id,
            elapsed_sec=elapsed_sec,
            metrics=metrics,
        )
        if ok:
            logger.info("回测完成通知已发送: run_id=%s strategy=%s", run_id, strategy_id)
        else:
            logger.debug("回测完成通知未发送 (webhook 未配置): run_id=%s", run_id)
    except Exception as exc:
        logger.warning("回测完成通知发送失败: %s", exc)


def notify_backtest_failed(
    run_id: str,
    strategy_id: str,
    error: str,
    elapsed_sec: float = 0.0,
) -> None:
    """
    回测失败通知 → ALERT 群（P1 bypass 静默窗口）。

    Args:
        run_id: 回测任务 ID
        strategy_id: 策略 ID
        error: 错误信息
        elapsed_sec: 耗时（秒）
    """
    # 失败通知 bypass 静默窗口（P1 级别）
    try:
        ok = send_backtest_card(
            status="failed",
            run_id=run_id,
            strategy_id=strategy_id,
            elapsed_sec=elapsed_sec,
            metrics={"error": error},
        )
        if ok:
            logger.info("回测失败通知已发送: run_id=%s strategy=%s", run_id, strategy_id)
        else:
            logger.debug("回测失败通知未发送 (webhook 未配置): run_id=%s", run_id)
    except Exception as exc:
        logger.warning("回测失败通知发送失败: %s", exc)
