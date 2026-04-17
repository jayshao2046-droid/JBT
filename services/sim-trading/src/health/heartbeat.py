"""
心跳健康报告生成器
每 2 小时整点推送 sim-trading 系统健康状态到飞书
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_heartbeat_report() -> Dict[str, Any]:
    """生成心跳健康报告"""
    from src.api.router import _get_gateway, _system_state
    from src.ledger.service import get_ledger

    report = {
        "timestamp": datetime.now().isoformat(),
        "service": "sim-trading",
        "status": "unknown",
        "ctp": {},
        "account": {},
        "system": {},
        "uptime": {},
    }

    # 1. CTP 连接状态
    try:
        gw = _get_gateway()
        if gw is None:
            report["ctp"] = {
                "status": "not_initialized",
                "md_connected": False,
                "td_connected": False,
            }
        else:
            status = gw.status
            report["ctp"] = {
                "status": "connected" if (status.get("md_connected") and status.get("td_connected")) else "disconnected",
                "md_connected": status.get("md_connected", False),
                "td_connected": status.get("td_connected", False),
                "md_status": status.get("md", "unknown"),
                "td_status": status.get("td", "unknown"),
                "last_md_disconnect_time": status.get("last_md_disconnect_time"),
                "last_td_disconnect_time": status.get("last_td_disconnect_time"),
            }
    except Exception as exc:
        logger.error("[heartbeat] failed to get CTP status: %s", exc)
        report["ctp"] = {"status": "error", "error": str(exc)}

    # 2. 账户状态
    try:
        ledger = get_ledger()
        summary = ledger.get_account_summary()
        report["account"] = {
            "balance": summary.get("balance"),
            "available": summary.get("available"),
            "margin": summary.get("margin"),
            "floating_pnl": summary.get("floating_pnl"),
            "today_pnl": summary.get("today_pnl"),
            "trade_count": summary.get("trade_count", 0),
        }
    except Exception as exc:
        logger.error("[heartbeat] failed to get account status: %s", exc)
        report["account"] = {"status": "error", "error": str(exc)}

    # 3. 系统状态
    try:
        report["system"] = {
            "ctp_md_connected": _system_state.get("ctp_md_connected", False),
            "ctp_td_connected": _system_state.get("ctp_td_connected", False),
            "last_disconnect_reason": _system_state.get("last_disconnect_reason"),
            "last_disconnect_time": _system_state.get("last_disconnect_time"),
        }
    except Exception as exc:
        logger.error("[heartbeat] failed to get system state: %s", exc)
        report["system"] = {"status": "error", "error": str(exc)}

    # 4. 运行时长
    try:
        import time
        uptime_seconds = time.time() - _system_state.get("start_time", time.time())
        report["uptime"] = {
            "seconds": int(uptime_seconds),
            "human": _format_uptime(uptime_seconds),
        }
    except Exception as exc:
        logger.error("[heartbeat] failed to get uptime: %s", exc)
        report["uptime"] = {"status": "error", "error": str(exc)}

    # 5. 综合健康状态
    ctp_ok = report["ctp"].get("status") == "connected"
    account_ok = report["account"].get("balance") is not None

    if ctp_ok and account_ok:
        report["status"] = "healthy"
    elif ctp_ok or account_ok:
        report["status"] = "degraded"
    else:
        report["status"] = "unhealthy"

    return report


def _format_uptime(seconds: float) -> str:
    """格式化运行时长"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days > 0:
        return f"{days}天{hours}小时{minutes}分钟"
    elif hours > 0:
        return f"{hours}小时{minutes}分钟"
    else:
        return f"{minutes}分钟"


def format_heartbeat_message(report: Dict[str, Any]) -> str:
    """格式化心跳报告为飞书消息"""
    status = report.get("status", "unknown")
    timestamp = report.get("timestamp", "")

    # 状态图标
    status_icon = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "🔴",
        "unknown": "❓",
    }.get(status, "❓")

    # CTP 状态
    ctp = report.get("ctp", {})
    ctp_status = ctp.get("status", "unknown")
    md_icon = "✅" if ctp.get("md_connected") else "❌"
    td_icon = "✅" if ctp.get("td_connected") else "❌"

    # 账户状态
    account = report.get("account", {})
    balance = account.get("balance")
    available = account.get("available")
    floating_pnl = account.get("floating_pnl")
    today_pnl = account.get("today_pnl")
    trade_count = account.get("trade_count", 0)

    # 运行时长
    uptime = report.get("uptime", {})
    uptime_human = uptime.get("human", "未知")

    # 构造消息
    lines = [
        f"{status_icon} **系统状态**: {status.upper()}",
        "",
        f"**CTP 连接**",
        f"  行情通道: {md_icon} {ctp.get('md_status', 'unknown')}",
        f"  交易通道: {td_icon} {ctp.get('td_status', 'unknown')}",
        "",
    ]

    if balance is not None:
        lines.extend([
            f"**账户信息**",
            f"  权益: ¥{balance:,.2f}",
            f"  可用: ¥{available:,.2f}" if available is not None else "  可用: N/A",
            f"  持仓盈亏: {floating_pnl:+,.2f}" if floating_pnl is not None else "  持仓盈亏: N/A",
            f"  今日盈亏: {today_pnl:+,.2f}" if today_pnl is not None else "  今日盈亏: N/A",
            f"  今日成交: {trade_count} 笔",
            "",
        ])
    else:
        lines.extend([
            f"**账户信息**",
            f"  ⚠️ 账户数据未就绪",
            "",
        ])

    lines.extend([
        f"**运行状态**",
        f"  运行时长: {uptime_human}",
        f"  报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ])

    return "\n".join(lines)


def send_heartbeat_to_feishu(report: Dict[str, Any]) -> bool:
    """发送心跳报告到飞书"""
    try:
        from src.notifier.dispatcher import get_dispatcher, RiskEvent

        dispatcher = get_dispatcher()
        if dispatcher is None:
            logger.warning("[heartbeat] dispatcher not initialized")
            return False

        # 根据健康状态选择级别
        status = report.get("status", "unknown")
        risk_level = {
            "healthy": "P2",
            "degraded": "P1",
            "unhealthy": "P0",
            "unknown": "P1",
        }.get(status, "P1")

        message = format_heartbeat_message(report)

        event = RiskEvent(
            task_id="HEARTBEAT",
            stage_preset="sim",
            risk_level=risk_level,
            account_id=report.get("account", {}).get("account_id", ""),
            strategy_id="",
            symbol="",
            signal_id="",
            trace_id="",
            event_code="HEARTBEAT_REPORT",
            reason=message,
            source="heartbeat",
            category="SYSTEM",
            message=f"Sim-Trading 心跳报告 ({status.upper()})",
        )

        dispatcher.dispatch(event)
        logger.info("[heartbeat] report sent to feishu: status=%s", status)
        return True

    except Exception as exc:
        logger.error("[heartbeat] failed to send to feishu: %s", exc)
        return False
