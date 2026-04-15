"""
L1/L2/L3 门控通知模板 — TASK-0120 决策端通知体系 V1

提供 L1 快速门控、L2 深审、L3 在线确认的标准化通知模板。
包含去重机制、二次升级、追踪信息等完整功能。
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from collections import OrderedDict

from .dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))

# 去重缓存：{signal_id}_{stage} -> timestamp
_dedup_cache: OrderedDict[str, float] = OrderedDict()
_DEDUP_WINDOW = 60.0  # 60秒去重窗口
_MAX_CACHE_SIZE = 10000


def _should_send(signal_id: str, stage: str) -> bool:
    """
    检查是否应该发送通知（60秒去重）

    Args:
        signal_id: 信号ID
        stage: 阶段标识（L1/L2/L3）

    Returns:
        True 表示应该发送，False 表示重复
    """
    key = f"{signal_id}_{stage}"
    now = time.time()

    # FIFO 淘汰
    if len(_dedup_cache) >= _MAX_CACHE_SIZE:
        _dedup_cache.popitem(last=False)

    # 检查去重
    if key in _dedup_cache:
        last_sent = _dedup_cache[key]
        if now - last_sent < _DEDUP_WINDOW:
            logger.debug("Dedup: skip %s (sent %.1fs ago)", key, now - last_sent)
            return False

    # 记录发送时间
    _dedup_cache[key] = now
    return True


def notify_l1_result(
    signal_id: str,
    strategy_id: str,
    model_id: str,
    symbol: str,
    signal_direction: int,
    passed: bool,
    risk_flag: str,
    confidence: float,
    reasoning: str,
    trace_id: Optional[str] = None,
    degraded: bool = False,
) -> None:
    """
    L1 快速门控结果通知

    Args:
        signal_id: 信号ID
        strategy_id: 策略ID
        model_id: 模型ID
        symbol: 交易标的
        signal_direction: 信号方向 (1=多, -1=空, 0=观望)
        passed: 是否通过
        risk_flag: 风险标记
        confidence: 置信度
        reasoning: 推理过程
        trace_id: 追踪ID
        degraded: 是否降级模式
    """
    # 去重检查
    if not _should_send(signal_id, "L1"):
        return

    # 构建通知
    direction_text = {1: "做多", -1: "做空", 0: "观望"}.get(signal_direction, "未知")
    status = "✅ 通过" if passed else "🚫 拒绝"
    level = NotifyLevel.SIGNAL if passed else NotifyLevel.P1

    title = f"L1 快速门控 {status}"

    body_parts = [
        f"### {symbol} · {direction_text}",
        "",
        f"**风险标记** {risk_flag} · **置信度** {confidence:.2f}",
    ]

    if degraded:
        body_parts.append("⚠️ 降级模式：数据缺失，已降级继续")

    body_parts.extend(["", "**推理过程**", reasoning[:200]])

    body = "\n".join(body_parts)

    event = DecisionEvent(
        event_type="SIGNAL",
        notify_level=level,
        event_code=f"L1-{signal_id[:8]}",
        title=title,
        body=body,
        strategy_id=strategy_id,
        model_id=model_id,
        signal_id=signal_id,
        trace_id=trace_id or "",
    )

    dispatcher = get_dispatcher()
    dispatcher.dispatch(event)

    logger.info("L1 notification sent: signal=%s passed=%s", signal_id, passed)


def notify_l2_result(
    signal_id: str,
    strategy_id: str,
    model_id: str,
    symbol: str,
    signal_direction: int,
    passed: bool,
    risk_level: str,
    confidence: float,
    reasoning: str,
    trace_id: Optional[str] = None,
    degraded: bool = False,
) -> None:
    """
    L2 深审结果通知

    Args:
        signal_id: 信号ID
        strategy_id: 策略ID
        model_id: 模型ID
        symbol: 交易标的
        signal_direction: 信号方向
        passed: 是否通过
        risk_level: 风险等级
        confidence: 置信度
        reasoning: 推理过程
        trace_id: 追踪ID
        degraded: 是否降级模式
    """
    # 去重检查
    if not _should_send(signal_id, "L2"):
        return

    direction_text = {1: "做多", -1: "做空", 0: "观望"}.get(signal_direction, "未知")
    status = "✅ 通过" if passed else "🚫 拒绝"
    level = NotifyLevel.SIGNAL if passed else NotifyLevel.P1

    title = f"L2 深度审查 {status}"

    body_parts = [
        f"### {symbol} · {direction_text}",
        "",
        f"**风险等级** {risk_level} · **置信度** {confidence:.2f}",
    ]

    if degraded:
        body_parts.append("⚠️ 降级模式：数据缺失，已降级继续")

    body_parts.extend(["", "**深度分析**", reasoning[:300]])

    body = "\n".join(body_parts)

    event = DecisionEvent(
        event_type="SIGNAL",
        notify_level=level,
        event_code=f"L2-{signal_id[:8]}",
        title=title,
        body=body,
        strategy_id=strategy_id,
        model_id=model_id,
        signal_id=signal_id,
        trace_id=trace_id or "",
    )

    dispatcher = get_dispatcher()
    dispatcher.dispatch(event)

    logger.info("L2 notification sent: signal=%s passed=%s", signal_id, passed)


def notify_l3_result(
    signal_id: str,
    strategy_id: str,
    model_id: str,
    symbol: str,
    signal_direction: int,
    status: str,  # "confirmed" | "rejected" | "timeout"
    reason: str,
    trace_id: Optional[str] = None,
) -> None:
    """
    L3 在线确认结果通知

    Args:
        signal_id: 信号ID
        strategy_id: 策略ID
        model_id: 模型ID
        symbol: 交易标的
        signal_direction: 信号方向
        status: 确认状态 (confirmed/rejected/timeout)
        reason: 原因说明
        trace_id: 追踪ID
    """
    # 去重检查
    if not _should_send(signal_id, "L3"):
        return

    direction_text = {1: "做多", -1: "做空", 0: "观望"}.get(signal_direction, "未知")

    # 状态映射
    status_map = {
        "confirmed": ("✅ 确认", NotifyLevel.SIGNAL),
        "rejected": ("🚫 拒绝", NotifyLevel.P1),
        "timeout": ("⏱️ 超时", NotifyLevel.P1),
    }

    status_text, level = status_map.get(status, ("❓ 未知", NotifyLevel.P2))

    title = f"L3 在线确认 {status_text}"

    body = "\n".join([
        f"### {symbol} · {direction_text}",
        "",
        f"**确认状态** {status_text}",
        f"**原因** {reason}",
    ])

    event = DecisionEvent(
        event_type="SIGNAL",
        notify_level=level,
        event_code=f"L3-{signal_id[:8]}",
        title=title,
        body=body,
        strategy_id=strategy_id,
        model_id=model_id,
        signal_id=signal_id,
        trace_id=trace_id or "",
    )

    dispatcher = get_dispatcher()
    dispatcher.dispatch(event)

    logger.info("L3 notification sent: signal=%s status=%s", signal_id, status)


def notify_strategy_tune(
    strategy_id: str,
    model_id: str,
    success: bool,
    metrics: Dict[str, Any],
    message: str,
    rollback_point: Optional[str] = None,
    next_steps: Optional[str] = None,
) -> None:
    """
    策略调优完成通知

    Args:
        strategy_id: 策略ID
        model_id: 模型ID
        success: 是否成功
        metrics: 性能指标
        message: 说明信息
        rollback_point: 回滚点（失败时）
        next_steps: 建议下一步（失败时）
    """
    status = "✅ 成功" if success else "❌ 失败"
    level = NotifyLevel.NOTIFY if success else NotifyLevel.P1

    title = f"策略调优 {status}"

    body_parts = [f"### {strategy_id}", ""]

    if success:
        # 成功：展示性能指标
        metrics_parts = []
        if "sharpe" in metrics:
            metrics_parts.append(f"Sharpe {metrics['sharpe']:.2f}")
        if "max_drawdown" in metrics:
            metrics_parts.append(f"回撤 {metrics['max_drawdown']:.2%}")
        if "win_rate" in metrics:
            metrics_parts.append(f"胜率 {metrics['win_rate']:.2%}")

        if metrics_parts:
            body_parts.append(" · ".join(metrics_parts))
            body_parts.append("")
    else:
        # 失败：展示回滚点和建议
        if rollback_point:
            body_parts.append(f"**回滚点** {rollback_point}")
        if next_steps:
            body_parts.append(f"**建议** {next_steps}")
        body_parts.append("")

    body_parts.append(message)

    body = "\n".join(body_parts)

    event = DecisionEvent(
        event_type="STRATEGY",
        notify_level=level,
        event_code=f"STRATEGY-TUNE-{strategy_id}",
        title=title,
        body=body,
        strategy_id=strategy_id,
        model_id=model_id,
    )

    dispatcher = get_dispatcher()
    dispatcher.dispatch(event)

    logger.info("Strategy tune notification sent: strategy=%s success=%s", strategy_id, success)
