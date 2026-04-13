"""
FailoverManager — TASK-0025
SimNow 备用方案管理器：健康探测 + 状态机 + 仅平仓执行。
"""
from __future__ import annotations

import enum
import logging
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FailoverState(str, enum.Enum):
    """备用模式状态。"""
    NORMAL = "NORMAL"           # 正常模式，使用 sim-trading 服务
    FAILOVER = "FAILOVER"       # 备用模式，使用 SimNow 直连
    RECOVERING = "RECOVERING"   # 恢复中，sim-trading 已恢复但需验证稳定性


class FailoverManager:
    """
    SimNow 备用方案管理器。

    功能：
    1. 定期健康探测 sim-trading 服务
    2. 状态机管理：NORMAL ↔ FAILOVER ↔ RECOVERING
    3. 备用模式下仅允许平仓操作
    4. 状态变更时发送飞书通知
    """

    def __init__(
        self,
        sim_trading_url: Optional[str] = None,
        probe_interval: Optional[int] = None,
        fail_threshold: Optional[int] = None,
        recover_threshold: Optional[int] = None,
    ) -> None:
        """
        Args:
            sim_trading_url: sim-trading 服务 URL
            probe_interval: 探测间隔（秒）
            fail_threshold: 连续失败阈值
            recover_threshold: 连续成功阈值
        """
        self._sim_trading_url = (
            sim_trading_url or os.environ.get("SIM_TRADING_SERVICE_URL", "http://localhost:8101")
        ).rstrip("/")
        self._probe_interval = probe_interval or int(os.environ.get("FAILOVER_PROBE_INTERVAL", "30"))
        self._fail_threshold = fail_threshold or int(os.environ.get("FAILOVER_FAIL_THRESHOLD", "3"))
        self._recover_threshold = recover_threshold or int(os.environ.get("FAILOVER_RECOVER_THRESHOLD", "2"))

        # SimNow 凭证（从环境变量读取）
        self._simnow_broker_id = os.environ.get("SIMNOW_BROKER_ID", "")
        self._simnow_user_id = os.environ.get("SIMNOW_USER_ID", "")
        self._simnow_password = os.environ.get("SIMNOW_PASSWORD", "")
        self._simnow_td_front = os.environ.get("SIMNOW_TD_FRONT", "")

        # 状态机
        self._state = FailoverState.NORMAL
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_probe_time = 0.0
        self._state_changed_at = datetime.now(timezone.utc)

    def get_state(self) -> FailoverState:
        """获取当前状态。"""
        return self._state

    def check_health(self) -> bool:
        """
        健康检查 sim-trading 服务。

        Returns:
            True if healthy, False otherwise
        """
        url = f"{self._sim_trading_url}/health"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.getcode() == 200
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            logger.debug(f"Health check failed: {exc}")
            return False

    def probe_and_update_state(self) -> None:
        """
        执行健康探测并更新状态机。

        状态转换：
        - NORMAL → 连续 N 次失败 → FAILOVER
        - FAILOVER → 健康检查恢复 → RECOVERING
        - RECOVERING → 连续 M 次成功 → NORMAL
        """
        now = time.time()
        if now - self._last_probe_time < self._probe_interval:
            return  # 未到探测间隔

        self._last_probe_time = now
        is_healthy = self.check_health()

        if self._state == FailoverState.NORMAL:
            if is_healthy:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
                logger.warning(
                    f"sim-trading 健康检查失败 ({self._consecutive_failures}/{self._fail_threshold})"
                )
                if self._consecutive_failures >= self._fail_threshold:
                    self._transition_to(FailoverState.FAILOVER)

        elif self._state == FailoverState.FAILOVER:
            if is_healthy:
                logger.info("sim-trading 健康检查恢复，进入 RECOVERING 状态")
                self._transition_to(FailoverState.RECOVERING)
                self._consecutive_successes = 1
            else:
                logger.debug("sim-trading 仍不可用，维持 FAILOVER 状态")

        elif self._state == FailoverState.RECOVERING:
            if is_healthy:
                self._consecutive_successes += 1
                logger.info(
                    f"sim-trading 健康检查成功 ({self._consecutive_successes}/{self._recover_threshold})"
                )
                if self._consecutive_successes >= self._recover_threshold:
                    self._transition_to(FailoverState.NORMAL)
            else:
                logger.warning("sim-trading 健康检查再次失败，回退到 FAILOVER 状态")
                self._transition_to(FailoverState.FAILOVER)
                self._consecutive_successes = 0

    def _transition_to(self, new_state: FailoverState) -> None:
        """状态转换并发送通知。"""
        old_state = self._state
        self._state = new_state
        self._state_changed_at = datetime.now(timezone.utc)
        self._consecutive_failures = 0

        logger.warning(f"FailoverManager 状态转换: {old_state} → {new_state}")

        # 发送飞书通知
        if new_state == FailoverState.FAILOVER:
            self._send_failover_alert()
        elif new_state == FailoverState.NORMAL:
            self._send_recovery_notification()

    def _send_failover_alert(self) -> None:
        """发送 FAILOVER 模式激活告警（P1）。"""
        try:
            from ..notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher
            dispatcher = get_dispatcher()

            event = DecisionEvent(
                event_type="SYSTEM",
                event_code="failover_activated",
                notify_level=NotifyLevel.P1,
                title="⚠️ [DECISION-P1] SimNow 备用模式已激活",
                body=(
                    f"## SimNow 备用模式已激活\n\n"
                    f"**原因**: sim-trading 服务连续 {self._fail_threshold} 次健康检查失败\n\n"
                    f"**当前状态**: FAILOVER\n\n"
                    f"**限制**: 仅允许平仓操作，禁止开仓\n\n"
                    f"**时间**: {self._state_changed_at.isoformat()}\n"
                ),
                trace_id="failover_manager",
            )
            dispatcher.dispatch(event)
            logger.info("已发送 FAILOVER 激活告警")
        except Exception as exc:
            logger.error(f"发送 FAILOVER 告警失败: {exc}")

    def _send_recovery_notification(self) -> None:
        """发送 NORMAL 模式恢复通知。"""
        try:
            from ..notifier.dispatcher import DecisionEvent, NotifyLevel, get_dispatcher
            dispatcher = get_dispatcher()

            event = DecisionEvent(
                event_type="SYSTEM",
                event_code="failover_recovered",
                notify_level=NotifyLevel.NOTIFY,
                title="📣 [DECISION-NOTIFY] SimNow 备用模式已退出",
                body=(
                    f"## SimNow 备用模式已退出\n\n"
                    f"**原因**: sim-trading 服务已恢复正常\n\n"
                    f"**当前状态**: NORMAL\n\n"
                    f"**恢复时间**: {self._state_changed_at.isoformat()}\n"
                ),
                trace_id="failover_manager",
            )
            dispatcher.dispatch(event)
            logger.info("已发送 NORMAL 恢复通知")
        except Exception as exc:
            logger.error(f"发送恢复通知失败: {exc}")

    def close_position(
        self,
        symbol: str,
        volume: int,
        direction: str,
    ) -> Dict[str, any]:
        """
        备用模式下执行平仓操作（仅平仓，禁止开仓）。

        Args:
            symbol: 合约代码
            volume: 平仓手数
            direction: 平仓方向（CLOSE_TODAY / CLOSE_YESTERDAY）

        Returns:
            Dict 包含 success, reason, order_id 等
        """
        if self._state != FailoverState.FAILOVER:
            return {
                "success": False,
                "reason": "not_in_failover_mode",
                "message": f"当前状态为 {self._state}，不需要使用备用模式",
            }

        # 验证是平仓操作
        if direction not in ("CLOSE_TODAY", "CLOSE_YESTERDAY", "CLOSE"):
            logger.error(f"备用模式拒绝开仓请求: symbol={symbol}, direction={direction}")
            return {
                "success": False,
                "reason": "failover_mode_open_rejected",
                "message": "备用模式下禁止开仓操作",
            }

        # 验证 SimNow 凭证
        if not all([self._simnow_broker_id, self._simnow_user_id, self._simnow_password, self._simnow_td_front]):
            logger.error("SimNow 凭证不完整，无法执行平仓")
            return {
                "success": False,
                "reason": "simnow_credentials_missing",
                "message": "SimNow 凭证未配置",
            }

        # TASK-0025: 仅实现 Python 层面的请求构造，不实际调用 CTP C++ API
        logger.warning(
            f"[FAILOVER] 平仓请求: symbol={symbol}, volume={volume}, direction={direction}, "
            f"broker={self._simnow_broker_id}, user={self._simnow_user_id}"
        )

        # 返回模拟结果（真实 CTP 绑定留后续）
        return {
            "success": True,
            "reason": "failover_close_submitted",
            "message": f"平仓请求已提交（模拟）: {symbol} {volume}手 {direction}",
            "order_id": f"FAILOVER_{int(time.time())}",
            "symbol": symbol,
            "volume": volume,
            "direction": direction,
        }
