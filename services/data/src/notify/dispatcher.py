"""JBT 数据端通知调度器 — 双通道 + 三群路由 + 告警状态机。

职责：
1. 三群路由：按 notify_type 投递到报警/交易/资讯群
2. 双通道调度：飞书 + 邮件，跟踪通道健康状态
3. 告警升级：P2 → P1 → P0 按时间自动升级
4. 渠道降级：飞书失败 → 自动邮件补发；双通道失败 → 本地 alarm.log
5. 告警去重冷却：同一事件 5 分钟内不重复推送
6. 夜间静默：22:00-08:00 仅 P0 和黑天鹅即时推送
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
FEISHU_INFO_URL_KEY = "FEISHU_INFO_WEBHOOK_URL"


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
    # 飞书操作按钮 (P0 用)
    action_buttons: list[dict[str, Any]] = field(default_factory=list)

    @property
    def dedup_key(self) -> str:
        raw = f"{self.event_code}|{self.source_name}|{self.notify_type.value}"
        return hashlib.md5(raw.encode()).hexdigest()


def _webhook_for_type(notify_type: NotifyType) -> str:
    """根据通知类型返回对应 Webhook URL。"""
    if notify_type in (NotifyType.P0, NotifyType.P1, NotifyType.P2):
        return os.environ.get(FEISHU_ALERT_URL_KEY, "")
    if notify_type == NotifyType.TRADE:
        return os.environ.get(FEISHU_TRADE_URL_KEY, "")
    return os.environ.get(FEISHU_INFO_URL_KEY, "")


def _is_quiet_hours() -> bool:
    """22:00-08:00 静默时段。"""
    now = datetime.now(CN_TZ)
    return now.hour >= 22 or now.hour < 8


class NotifierDispatcher:
    """双通道通知调度器。"""

    COOLDOWN_SEC = 300  # 5 分钟去重冷却
    UPGRADE_P2_TO_P1_SEC = 1800  # 30 分钟
    UPGRADE_P1_TO_P0_SEC = 3600  # 60 分钟
    P0_REPEAT_SEC = 900  # P0 每 15 分钟重复

    def __init__(self) -> None:
        from services.data.src.notify.feishu import FeishuSender
        from services.data.src.notify.email_notify import EmailSender

        self._feishu = FeishuSender()
        self._email = EmailSender()
        self._state = ChannelState.NORMAL
        self._lock = threading.Lock()

        # 去重：dedup_key → last_push_ts
        self._dedup_cache: dict[str, float] = {}
        # 告警升级：event_key → AlertState
        self._alert_states: dict[str, AlertState] = {}
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

        # 夜间静默：仅 P0 通过
        if _is_quiet_hours() and event.notify_type not in (NotifyType.P0,):
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

        # 发送飞书（按 channels 路由）
        feishu_ok = True
        if "feishu" in channels:
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
                email_ok = self._email.send(event=event)
            elif "feishu" in channels:
                if not feishu_ok:
                    logger.warning("feishu failed for %s, degrading to email", event.event_code)
                    email_ok = self._email.send(event=event)
            else:
                # 仅邮件模式时直接发送
                email_ok = self._email.send(event=event)

        # 更新通道状态
        if feishu_ok and email_ok:
            self._state = ChannelState.NORMAL
        elif not feishu_ok and email_ok:
            self._state = ChannelState.FEISHU_FAILED
        elif feishu_ok and not email_ok:
            self._state = ChannelState.EMAIL_FAILED
        else:
            self._state = ChannelState.ALL_FAILED
            self._write_alarm_log(event)

        return feishu_ok or email_ok

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
