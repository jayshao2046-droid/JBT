"""
健康监控 — TASK-0120 决策端通知体系 V1

提供 15 分钟健康快照和每日健康报告功能。
监控数据源、模型、策略、通知系统的健康状态。
"""

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from .dispatcher import DecisionEvent, NotifyLevel, get_dispatcher

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class ComponentHealth:
    """组件健康状态"""

    def __init__(self, name: str):
        self.name = name
        self.status = HealthStatus.HEALTHY
        self.message = ""
        self.last_check = datetime.now(_TZ_CST)
        self.metrics: Dict[str, Any] = {}

    def set_healthy(self, message: str = ""):
        """设置为健康"""
        self.status = HealthStatus.HEALTHY
        self.message = message
        self.last_check = datetime.now(_TZ_CST)

    def set_degraded(self, message: str):
        """设置为降级"""
        self.status = HealthStatus.DEGRADED
        self.message = message
        self.last_check = datetime.now(_TZ_CST)

    def set_critical(self, message: str):
        """设置为严重"""
        self.status = HealthStatus.CRITICAL
        self.message = message
        self.last_check = datetime.now(_TZ_CST)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
            "metrics": self.metrics,
        }


class HealthMonitor:
    """健康监控器"""

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {
            "data_source": ComponentHealth("数据源"),
            "model_service": ComponentHealth("模型服务"),
            "strategy_engine": ComponentHealth("策略引擎"),
            "notification": ComponentHealth("通知系统"),
            "gate_reviewer": ComponentHealth("门控审查器"),
        }

        self.snapshot_history: List[Dict[str, Any]] = []
        self.max_history = 96  # 保留 24 小时（15分钟 * 96）

    def check_data_source(self) -> ComponentHealth:
        """检查数据源健康状态"""
        comp = self.components["data_source"]

        try:
            # TODO: 实际检查逻辑
            # 1. 检查数据服务 API 可用性
            # 2. 检查最新数据时间戳
            # 3. 检查数据完整性

            # 示例逻辑
            comp.set_healthy("数据源正常")
            comp.metrics = {
                "last_update": datetime.now(_TZ_CST).isoformat(),
                "data_delay_seconds": 0,
            }

        except Exception as e:
            comp.set_critical(f"数据源异常: {e}")
            logger.error("Data source health check failed: %s", e)

        return comp

    def check_model_service(self) -> ComponentHealth:
        """检查模型服务健康状态"""
        comp = self.components["model_service"]

        try:
            # TODO: 实际检查逻辑
            # 1. 检查 Ollama 服务可用性
            # 2. 检查 qwen3:14b 模型加载状态
            # 3. 检查模型响应时间

            comp.set_healthy("模型服务正常")
            comp.metrics = {
                "model": "qwen3:14b",
                "avg_response_time_ms": 0,
            }

        except Exception as e:
            comp.set_critical(f"模型服务异常: {e}")
            logger.error("Model service health check failed: %s", e)

        return comp

    def check_strategy_engine(self) -> ComponentHealth:
        """检查策略引擎健康状态"""
        comp = self.components["strategy_engine"]

        try:
            # TODO: 实际检查逻辑
            # 1. 检查策略加载状态
            # 2. 检查信号生成频率
            # 3. 检查策略执行延迟

            comp.set_healthy("策略引擎正常")
            comp.metrics = {
                "active_strategies": 0,
                "signal_count_1h": 0,
            }

        except Exception as e:
            comp.set_critical(f"策略引擎异常: {e}")
            logger.error("Strategy engine health check failed: %s", e)

        return comp

    def check_notification(self) -> ComponentHealth:
        """检查通知系统健康状态"""
        comp = self.components["notification"]

        try:
            # 检查飞书和邮件配置
            feishu_enabled = os.getenv("FEISHU_ENABLED", "false").lower() == "true"
            email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

            if not feishu_enabled and not email_enabled:
                comp.set_degraded("飞书和邮件均未启用")
            elif not feishu_enabled:
                comp.set_degraded("飞书未启用，仅邮件可用")
            elif not email_enabled:
                comp.set_degraded("邮件未启用，仅飞书可用")
            else:
                comp.set_healthy("通知系统正常")

            comp.metrics = {
                "feishu_enabled": feishu_enabled,
                "email_enabled": email_enabled,
            }

        except Exception as e:
            comp.set_critical(f"通知系统异常: {e}")
            logger.error("Notification health check failed: %s", e)

        return comp

    def check_gate_reviewer(self) -> ComponentHealth:
        """检查门控审查器健康状态"""
        comp = self.components["gate_reviewer"]

        try:
            # TODO: 实际检查逻辑
            # 1. 检查 L1/L2 审查器可用性
            # 2. 检查审查延迟
            # 3. 检查拒绝率

            comp.set_healthy("门控审查器正常")
            comp.metrics = {
                "l1_avg_latency_ms": 0,
                "l2_avg_latency_ms": 0,
            }

        except Exception as e:
            comp.set_critical(f"门控审查器异常: {e}")
            logger.error("Gate reviewer health check failed: %s", e)

        return comp

    def check_all(self) -> Dict[str, ComponentHealth]:
        """检查所有组件"""
        self.check_data_source()
        self.check_model_service()
        self.check_strategy_engine()
        self.check_notification()
        self.check_gate_reviewer()

        return self.components

    def get_overall_status(self) -> HealthStatus:
        """获取整体健康状态"""
        statuses = [comp.status for comp in self.components.values()]

        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def take_snapshot(self) -> Dict[str, Any]:
        """生成健康快照"""
        self.check_all()

        snapshot = {
            "timestamp": datetime.now(_TZ_CST).isoformat(),
            "overall_status": self.get_overall_status().value,
            "components": {name: comp.to_dict() for name, comp in self.components.items()},
        }

        # 保存到历史
        self.snapshot_history.append(snapshot)
        if len(self.snapshot_history) > self.max_history:
            self.snapshot_history.pop(0)

        return snapshot

    def send_snapshot_notification(self, snapshot: Dict[str, Any]) -> None:
        """发送快照通知（仅在状态变化或严重时）"""
        overall_status = HealthStatus(snapshot["overall_status"])

        # 仅在 CRITICAL 或 DEGRADED 时发送通知
        if overall_status == HealthStatus.HEALTHY:
            return

        # 构建通知
        status_config = {
            HealthStatus.HEALTHY: {"emoji": "✅", "text": "健康", "color": "green"},
            HealthStatus.DEGRADED: {"emoji": "⚠️", "text": "降级", "color": "orange"},
            HealthStatus.CRITICAL: {"emoji": "🔴", "text": "严重", "color": "red"},
        }

        config = status_config[overall_status]
        title = f"决策服务健康快照"

        # 构建卡片内容
        body_parts = [f"**{config['emoji']} 整体状态: {config['text']}**", ""]

        # 组件状态
        healthy_comps = []
        problem_comps = []

        for name, comp_data in snapshot["components"].items():
            comp_status = HealthStatus(comp_data["status"])
            comp_config = status_config[comp_status]

            if comp_status == HealthStatus.HEALTHY:
                healthy_comps.append(f"{comp_config['emoji']} {comp_data['name']}")
            else:
                problem_comps.append(
                    f"{comp_config['emoji']} {comp_data['name']}: {comp_data['message']}"
                )

        if problem_comps:
            body_parts.append("异常组件:")
            body_parts.extend(problem_comps)
            body_parts.append("")

        if healthy_comps:
            body_parts.append("正常组件: " + " · ".join(healthy_comps))

        body = "\n".join(body_parts)

        level = NotifyLevel.P0 if overall_status == HealthStatus.CRITICAL else NotifyLevel.P1

        event = DecisionEvent(
            event_type="HEALTH",
            notify_level=level,
            event_code=f"HEALTH-SNAPSHOT-{datetime.now(_TZ_CST).strftime('%H%M')}",
            title=title,
            body=body,
        )

        dispatcher = get_dispatcher()
        dispatcher.dispatch(event)

        logger.info("Health snapshot notification sent: status=%s", overall_status.value)

    def generate_daily_report(self) -> str:
        """生成每日健康报告（Markdown格式）"""
        now = datetime.now(_TZ_CST)
        date = now.strftime("%Y-%m-%d")

        lines = [
            f"# {date} 决策服务健康报告",
            "",
            "## 📊 当前状态",
            "",
        ]

        # 当前状态
        self.check_all()
        overall_status = self.get_overall_status()

        status_text = {
            HealthStatus.HEALTHY: "✅ 健康",
            HealthStatus.DEGRADED: "⚠️ 降级",
            HealthStatus.CRITICAL: "🔴 严重",
        }

        lines.append(f"**整体状态**: {status_text[overall_status]}")
        lines.append("")

        for name, comp in self.components.items():
            lines.append(f"**{comp.name}**: {status_text[comp.status]}")
            if comp.message:
                lines.append(f"  - {comp.message}")

        lines.append("")

        # 24 小时趋势
        if self.snapshot_history:
            lines.extend([
                "## 📈 24 小时趋势",
                "",
            ])

            # 统计各状态出现次数
            status_counts = {
                HealthStatus.HEALTHY: 0,
                HealthStatus.DEGRADED: 0,
                HealthStatus.CRITICAL: 0,
            }

            for snapshot in self.snapshot_history:
                status = HealthStatus(snapshot["overall_status"])
                status_counts[status] += 1

            total = len(self.snapshot_history)
            lines.append(f"- 健康: {status_counts[HealthStatus.HEALTHY]}/{total} ({status_counts[HealthStatus.HEALTHY]/total*100:.1f}%)")
            lines.append(f"- 降级: {status_counts[HealthStatus.DEGRADED]}/{total} ({status_counts[HealthStatus.DEGRADED]/total*100:.1f}%)")
            lines.append(f"- 严重: {status_counts[HealthStatus.CRITICAL]}/{total} ({status_counts[HealthStatus.CRITICAL]/total*100:.1f}%)")
            lines.append("")

        return "\n".join(lines)

    def send_daily_report(self) -> None:
        """发送每日健康报告"""
        date = datetime.now(_TZ_CST).strftime("%Y-%m-%d")
        title = f"{date} 决策服务健康报告"
        body = self.generate_daily_report()

        event = DecisionEvent(
            event_type="DAILY",
            notify_level=NotifyLevel.NOTIFY,
            event_code=f"DAILY-HEALTH-{date}",
            title=title,
            body=body,
        )

        dispatcher = get_dispatcher()
        dispatcher.dispatch(event)

        logger.info("Daily health report sent: date=%s", date)


# 全局单例
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """获取健康监控器（单例）"""
    global _health_monitor

    if _health_monitor is None:
        _health_monitor = HealthMonitor()

    return _health_monitor
