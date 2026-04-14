"""JBT 数据端通知调度器 — 双通道 + 三群路由 + 告警状态机。

职责：
1. 三群路由：按 notify_type 投递到报警/交易/资讯群
2. 双通道调度：飞书 + 邮件，跟踪通道健康状态
3. 告警升级：P2 → P1 → P0 按时间自动升级
4. 渠道降级：飞书失败 → 自动邮件补发；双通道失败 → 本地 alarm.log
5. 告警去重冷却：同一事件 5 分钟内不重复推送
6. 夜间静默：默认 22:00-08:00；NEWS 单独延后到 08:30
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import os
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CN_TZ = timezone(timedelta(hours=8))

# ── 环境变量键 ──────────────────────────────────────────────
FEISHU_ALERT_URL_KEY = "FEISHU_ALERT_WEBHOOK_URL"
FEISHU_TRADE_URL_KEY = "FEISHU_TRADE_WEBHOOK_URL"
FEISHU_TRADING_URL_KEY = "FEISHU_TRADING_WEBHOOK_URL"
FEISHU_INFO_URL_KEY = "FEISHU_INFO_WEBHOOK_URL"
FEISHU_NEWS_URL_KEY = "FEISHU_NEWS_WEBHOOK_URL"


def _first_nonempty_env(*keys: str) -> str:
    for key in keys:
        value = os.environ.get(key, "")
        if value:
            return value
    return ""


class ChannelState(enum.Enum):
    NORMAL = "NORMAL"
    FEISHU_FAILED = "FEISHU_FAILED"
    EMAIL_FAILED = "EMAIL_FAILED"
    ALL_FAILED = "ALL_FAILED"


class NotifyType(enum.Enum):
    """通知类型 → 三群路由。"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    TRADE = "TRADE"
    INFO = "INFO"
    NEWS = "NEWS"
    NOTIFY = "NOTIFY"
    FACTOR = "FACTOR"
    WATCHLIST = "WATCHLIST"
    PREREAD_DONE = "PREREAD_DONE"
    PREREAD_FAIL = "PREREAD_FAIL"


@dataclass
class AlertState:
    """告警升级状态跟踪。"""
    event_key: str
    first_seen: float
    current_level: str  # P2 / P1 / P0
    last_push_ts: float = 0.0
    acknowledged: bool = False


@dataclass
class DataEvent:
    """数据端通知事件。"""
    event_code: str
    notify_type: NotifyType
    title: str
    body_md: str  # Feishu lark_md
    body_rows: list[tuple[str, str]] = field(default_factory=list)  # Email KV rows
    trace_md: str = ""
    trace_rows: list[tuple[str, str]] = field(default_factory=list)
    source_name: str = ""
    # 通道路由: {"feishu", "email"}; 默认双通道。
    channels: set[str] = field(default_factory=lambda: {"feishu", "email"})
    # 是否绕过 22:00-08:00 静默窗口（用于必须送达类通知）。
    bypass_quiet_hours: bool = False
    # 飞书操作按钮 (P0 用)
    action_buttons: list[dict[str, Any]] = field(default_factory=list)

    @property
    def dedup_key(self) -> str:
        raw = f"{self.event_code}|{self.source_name}|{self.notify_type.value}"
        return hashlib.md5(raw.encode()).hexdigest()


@dataclass
class CollectionWindowItem:
    """采集完成结果的窗口缓冲项。"""

    collector_name: str
    status: str
    record_count: int
    elapsed_sec: float
    error_msg: str = ""
    finished_at: datetime = field(default_factory=lambda: datetime.now(CN_TZ))


def _webhook_for_type(notify_type: NotifyType) -> str:
    """根据通知类型返回对应 Webhook URL（含降级兜底链）。"""
    if notify_type in (NotifyType.P0, NotifyType.P1, NotifyType.P2):
        return _first_nonempty_env(
            FEISHU_ALERT_URL_KEY, FEISHU_TRADE_URL_KEY, FEISHU_TRADING_URL_KEY, FEISHU_NEWS_URL_KEY,
        )
    if notify_type == NotifyType.TRADE:
        return _first_nonempty_env(FEISHU_TRADE_URL_KEY, FEISHU_TRADING_URL_KEY, FEISHU_ALERT_URL_KEY)
    if notify_type == NotifyType.NEWS:
        return _first_nonempty_env(FEISHU_NEWS_URL_KEY, FEISHU_INFO_URL_KEY, FEISHU_ALERT_URL_KEY)
    if notify_type == NotifyType.FACTOR:
        return _first_nonempty_env(FEISHU_TRADE_URL_KEY, FEISHU_TRADING_URL_KEY, FEISHU_INFO_URL_KEY, FEISHU_ALERT_URL_KEY)
    if notify_type == NotifyType.WATCHLIST:
        return _first_nonempty_env(FEISHU_INFO_URL_KEY, FEISHU_NEWS_URL_KEY, FEISHU_ALERT_URL_KEY)
    if notify_type in (NotifyType.PREREAD_DONE, NotifyType.PREREAD_FAIL):
        return _first_nonempty_env(FEISHU_TRADE_URL_KEY, FEISHU_TRADING_URL_KEY, FEISHU_ALERT_URL_KEY)
    return _first_nonempty_env(FEISHU_INFO_URL_KEY, FEISHU_NEWS_URL_KEY, FEISHU_ALERT_URL_KEY)


def _is_quiet_hours(now: datetime | None = None) -> bool:
    """默认 22:00-08:00 静默时段。"""
    now = now or datetime.now(CN_TZ)
    return now.hour >= 22 or now.hour < 8


def _is_news_quiet_hours(now: datetime | None = None) -> bool:
    """NEWS 专用静默时段：22:00-08:30。"""
    now = now or datetime.now(CN_TZ)
    minutes = now.hour * 60 + now.minute
    return minutes >= 22 * 60 or minutes < 8 * 60 + 30


def _is_quiet_hours_for_type(notify_type: NotifyType, now: datetime | None = None) -> bool:
    """按通知类型判断静默窗口。"""
    if notify_type == NotifyType.NEWS:
        return _is_news_quiet_hours(now)
    return _is_quiet_hours(now)


class NotifierDispatcher:
    """双通道通知调度器。"""

    COOLDOWN_SEC = 300  # 5 分钟去重冷却
    UPGRADE_P2_TO_P1_SEC = 1800  # 30 分钟
    UPGRADE_P1_TO_P0_SEC = 3600  # 60 分钟
    P0_REPEAT_SEC = 900  # P0 每 15 分钟重复
    COLLECTION_WINDOW_SEC = 60.0

    def __init__(
        self,
        *,
        feishu_sender: Any | None = None,
        email_sender: Any | None = None,
        collector_window_sec: float | None = None,
    ) -> None:
        from src.notify.feishu import FeishuSender
        from src.notify.email_notify import EmailSender

        self._feishu = feishu_sender or FeishuSender()
        self._email = email_sender or EmailSender()
        self._state = ChannelState.NORMAL
        self._lock = threading.Lock()
        self._collector_window_sec = max(
            0.0,
            float(
                self.COLLECTION_WINDOW_SEC if collector_window_sec is None else collector_window_sec,
            ),
        )

        # 去重：dedup_key → last_push_ts
        self._dedup_cache: dict[str, float] = {}
        # 告警升级：event_key → AlertState
        self._alert_states: dict[str, AlertState] = {}
        # 采集完成窗口聚合
        self._collection_window: list[CollectionWindowItem] = []
        self._collection_window_started_at: float | None = None
        self._collection_timer: threading.Timer | None = None
        # 告警日志
        self._alarm_log = Path(os.environ.get("JBT_DATA_LOG_DIR", "/runtime/logs")) / "alarm.log"

    @property
    def channel_state(self) -> ChannelState:
        return self._state

    def dispatch(self, event: DataEvent) -> bool:
        """调度通知事件到双通道。

        Returns True if at least one channel succeeded.
        """
        now = time.time()

        # 夜间静默：仅 P0 或显式 bypass 通过
        if _is_quiet_hours_for_type(event.notify_type) and (not event.bypass_quiet_hours) and event.notify_type not in (NotifyType.P0,):
            logger.debug("quiet hours, skipping: %s", event.event_code)
            return True

        # 去重冷却
        with self._lock:
            last = self._dedup_cache.get(event.dedup_key, 0)
            if now - last < self.COOLDOWN_SEC:
                logger.debug("cooldown active for %s, skipping", event.event_code)
                return True
            self._dedup_cache[event.dedup_key] = now

        channels = event.channels or {"feishu", "email"}
        feishu_attempted = False
        email_attempted = False

        # 发送飞书（按 channels 路由）
        feishu_ok = True
        if "feishu" in channels:
            feishu_attempted = True
            webhook_url = _webhook_for_type(event.notify_type)
            feishu_ok = self._feishu.send(
                webhook_url=webhook_url,
                event=event,
            )

        # 发送邮件（按 channels 路由）
        email_ok = True
        if "email" in channels:
            # 默认策略：P0/P1 总是发；其他仅在飞书失败时降级发
            if event.notify_type in (NotifyType.P0, NotifyType.P1):
                email_attempted = True
                email_ok = self._email.send(event=event)
            elif "feishu" in channels:
                if not feishu_ok:
                    logger.warning("feishu failed for %s, degrading to email", event.event_code)
                    email_attempted = True
                    email_ok = self._email.send(event=event)
            else:
                # 仅邮件模式时直接发送
                email_attempted = True
                email_ok = self._email.send(event=event)

        # 更新通道状态
        if feishu_attempted and not feishu_ok and email_attempted and not email_ok:
            self._state = ChannelState.ALL_FAILED
            self._write_alarm_log(event)
        elif feishu_attempted and not feishu_ok:
            self._state = ChannelState.FEISHU_FAILED
        elif email_attempted and not email_ok:
            self._state = ChannelState.EMAIL_FAILED
        else:
            self._state = ChannelState.NORMAL

        return (feishu_attempted and feishu_ok) or (email_attempted and email_ok) or (not feishu_attempted and not email_attempted)

    def record_collection_result(
        self,
        *,
        collector_name: str,
        record_count: int,
        elapsed_sec: float,
        status: str,
        error_msg: str = "",
        finished_at: datetime | None = None,
    ) -> int:
        """缓冲采集完成结果，并在同窗内合并成单条飞书摘要。"""
        item = CollectionWindowItem(
            collector_name=collector_name,
            status=status,
            record_count=max(0, int(record_count)),
            elapsed_sec=max(0.0, float(elapsed_sec)),
            error_msg=error_msg,
            finished_at=finished_at or datetime.now(CN_TZ),
        )

        timer_to_start: threading.Timer | None = None
        with self._lock:
            if self._collection_window_started_at is None:
                self._collection_window_started_at = item.finished_at.timestamp()
            self._collection_window.append(item)
            pending_count = len(self._collection_window)
            if self._collection_timer is None and self._collector_window_sec > 0:
                timer_to_start = threading.Timer(self._collector_window_sec, self.flush_collection_window)
                timer_to_start.daemon = True
                self._collection_timer = timer_to_start

        if timer_to_start is not None:
            timer_to_start.start()

        return pending_count

    def flush_collection_window(self) -> bool:
        """立刻发送当前采集完成窗口摘要。"""
        timer_to_cancel: threading.Timer | None = None
        with self._lock:
            if not self._collection_window:
                self._collection_timer = None
                self._collection_window_started_at = None
                return True

            items = list(self._collection_window)
            started_at = self._collection_window_started_at or time.time()
            self._collection_window.clear()
            self._collection_window_started_at = None
            timer_to_cancel = self._collection_timer
            self._collection_timer = None

        if timer_to_cancel is not None and timer_to_cancel is not threading.current_thread():
            timer_to_cancel.cancel()

        event = self._build_collection_summary_event(items=items, started_at=started_at)
        return self.dispatch(event)

    @staticmethod
    def _collection_status_icon(status: str) -> str:
        return {
            "success": "🟢",
            "zero_output": "🟡",
            "failed": "🔴",
        }.get(status, "🟢")

    @staticmethod
    def _collection_status_label(status: str) -> str:
        return {
            "success": "完成",
            "zero_output": "0产出",
            "failed": "异常",
        }.get(status, "完成")

    def _build_collection_summary_event(
        self,
        *,
        items: list[CollectionWindowItem],
        started_at: float,
    ) -> DataEvent:
        started_dt = datetime.fromtimestamp(started_at, CN_TZ)
        finished_dt = max((item.finished_at for item in items), default=started_dt)
        success_count = sum(1 for item in items if item.status == "success")
        zero_count = sum(1 for item in items if item.status == "zero_output")
        failed_count = sum(1 for item in items if item.status == "failed")

        lines: list[str] = []
        for item in items:
            prefix = self._collection_status_icon(item.status)
            if item.status == "failed":
                detail = " ".join(str(item.error_msg or "未提供错误信息").split())[:120]
                lines.append(f"{prefix} **{item.collector_name}** 异常 | {detail}")
            elif item.status == "zero_output":
                lines.append(
                    f"{prefix} **{item.collector_name}** 0产出 | {item.record_count:,} 条 | {item.elapsed_sec:.1f}s",
                )
            else:
                lines.append(
                    f"{prefix} **{item.collector_name}** 完成 | {item.record_count:,} 条 | {item.elapsed_sec:.1f}s",
                )

        if len(items) == 1:
            single = items[0]
            title = f"{single.collector_name} {self._collection_status_label(single.status)}"
        else:
            parts: list[str] = []
            if success_count:
                parts.append(f"成功 {success_count}")
            if zero_count:
                parts.append(f"0产出 {zero_count}")
            if failed_count:
                parts.append(f"异常 {failed_count}")
            suffix = f"（{' / '.join(parts)}）" if parts else ""
            title = f"采集摘要 {started_dt.strftime('%H:%M')}{suffix}"

        batch_hash = hashlib.md5(
            "|".join(
                f"{item.collector_name}:{item.status}:{item.record_count}:{item.finished_at.isoformat()}"
                for item in items
            ).encode("utf-8"),
        ).hexdigest()

        return DataEvent(
            event_code="collector_window_summary",
            notify_type=NotifyType.NOTIFY,
            title=title,
            body_md="\n".join(lines),
            body_rows=[
                ("采集器数", str(len(items))),
                ("成功", str(success_count)),
                ("0产出", str(zero_count)),
                ("异常", str(failed_count)),
            ],
            trace_rows=[
                ("窗口开始", started_dt.strftime("%Y-%m-%d %H:%M:%S")),
                ("窗口结束", finished_dt.strftime("%Y-%m-%d %H:%M:%S")),
            ],
            source_name=f"collector_window:{started_dt.strftime('%Y%m%d%H%M%S')}:{batch_hash}",
            channels={"feishu"},
            bypass_quiet_hours=True,
        )

    def check_alert_escalation(self, event_key: str, current_level: str) -> str:
        """检查告警升级。

        Returns the (possibly upgraded) level.
        """
        now = time.time()
        with self._lock:
            state = self._alert_states.get(event_key)
            if state is None:
                self._alert_states[event_key] = AlertState(
                    event_key=event_key,
                    first_seen=now,
                    current_level=current_level,
                    last_push_ts=now,
                )
                return current_level

            if state.acknowledged:
                return state.current_level

            elapsed = now - state.first_seen
            if state.current_level == "P2" and elapsed >= self.UPGRADE_P2_TO_P1_SEC:
                state.current_level = "P1"
                logger.warning("alert escalated P2→P1: %s (%.0fs)", event_key, elapsed)
            if state.current_level == "P1" and elapsed >= self.UPGRADE_P1_TO_P0_SEC:
                state.current_level = "P0"
                logger.warning("alert escalated P1→P0: %s (%.0fs)", event_key, elapsed)

            return state.current_level

    def acknowledge_alert(self, event_key: str) -> None:
        """人工确认告警，停止升级。"""
        with self._lock:
            state = self._alert_states.get(event_key)
            if state:
                state.acknowledged = True

    def resolve_alert(self, event_key: str) -> None:
        """告警恢复，清除升级状态。"""
        with self._lock:
            self._alert_states.pop(event_key, None)

    def cleanup_dedup_cache(self) -> None:
        """清理过期的去重缓存条目。"""
        cutoff = time.time() - self.COOLDOWN_SEC * 2
        with self._lock:
            expired = [k for k, v in self._dedup_cache.items() if v < cutoff]
            for k in expired:
                del self._dedup_cache[k]

    def check_webhooks_health(self) -> dict[str, bool]:
        """启动时检测 3 个 Webhook 是否可达。"""
        results = {}
        for name, key in [
            ("alert", FEISHU_ALERT_URL_KEY),
            ("trade", FEISHU_TRADE_URL_KEY),
            ("info", FEISHU_INFO_URL_KEY),
        ]:
            url = os.environ.get(key, "")
            results[name] = bool(url)
            if not url:
                logger.warning("webhook %s not configured (%s)", name, key)
        return results

    def _write_alarm_log(self, event: DataEvent) -> None:
        """双通道全部失败时写本地 alarm.log。"""
        try:
            self._alarm_log.parent.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
            entry = {
                "timestamp": ts,
                "event_code": event.event_code,
                "notify_type": event.notify_type.value,
                "title": event.title,
                "channel_state": self._state.value,
            }
            with open(self._alarm_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("alarm.log write failed: %s", exc)


# ── 全局单例 ──────────────────────────────────────────────
_dispatcher: NotifierDispatcher | None = None


def get_dispatcher() -> NotifierDispatcher:
    """获取全局 dispatcher 单例。"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = NotifierDispatcher()
    return _dispatcher
