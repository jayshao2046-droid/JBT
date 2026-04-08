import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["sim-trading"])

# ---------- SimNow Gateway 单例 ----------
_gateway = None   # type: Any   # SimNowGateway | None

def _get_gateway():
    return _gateway

# ---------- 内存状态（从环境变量初始化，重启后 CTP 凭证自动恢复）----------
_system_state: Dict[str, Any] = {
    "trading_enabled": True,
    "active_preset": "sim_50w",
    "paused_reason": None,
    "ctp_md_connected": False,
    "ctp_td_connected": False,
    "last_disconnect_reason": None,
    "last_disconnect_time": None,
    "ctp_broker_id": os.getenv("SIMNOW_BROKER_ID", "9999"),
    "ctp_user_id": os.getenv("SIMNOW_USER_ID", ""),
    "ctp_password": os.getenv("SIMNOW_PASSWORD", ""),
    "ctp_md_front": os.getenv("SIMNOW_MD_FRONT", "tcp://180.168.146.187:10131"),
    "ctp_td_front": os.getenv("SIMNOW_TRADE_FRONT", "tcp://180.168.146.187:10130"),
}

_LOCAL_VIRTUAL_PRINCIPAL = 500000.0

_risk_presets: Dict[str, Any] = {
    # ── SHFE 上期所 ────────────────────────────────────────
    "RB":  {"name": "螺纹钢",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": True,  "commission": 1.0,  "slippage_ticks": 1},
    "HC":  {"name": "热卷",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": True,  "commission": 1.0,  "slippage_ticks": 1},
    "SS":  {"name": "不锈钢",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 5.0,  "slippage_ticks": 1},
    "SP":  {"name": "纸浆",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "CU":  {"name": "沪铜",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": True,  "commission": 5.0,  "slippage_ticks": 1},
    "AL":  {"name": "沪铝",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "ZN":  {"name": "沪锌",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "PB":  {"name": "沪铅",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "NI":  {"name": "沪镍",      "max_lots": 3,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False, "commission": 6.0,  "slippage_ticks": 1},
    "SN":  {"name": "沪锡",      "max_lots": 3,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False, "commission": 10.0, "slippage_ticks": 1},
    "BC":  {"name": "国际铜",    "max_lots": 3,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False, "commission": 8.0,  "slippage_ticks": 1},
    "AU":  {"name": "沪金",      "max_lots": 5,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False, "commission": 10.0, "slippage_ticks": 1},
    "AG":  {"name": "沪银",      "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 5.0,  "slippage_ticks": 1},
    "FU":  {"name": "燃料油",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 5.0,  "slippage_ticks": 1},
    "BU":  {"name": "沥青",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "RU":  {"name": "天然橡胶",  "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "NR":  {"name": "20号胶",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    # ── DCE 大商所 ─────────────────────────────────────────
    "I":   {"name": "铁矿石",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.0,  "slippage_ticks": 1},
    "J":   {"name": "焦炭",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 1.0,  "slippage_ticks": 1},
    "JM":  {"name": "焦煤",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 1.0,  "slippage_ticks": 1},
    "A":   {"name": "大豆一号",  "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 2.0,  "slippage_ticks": 1},
    "B":   {"name": "大豆二号",  "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 1.0,  "slippage_ticks": 1},
    "M":   {"name": "豆粕",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "Y":   {"name": "豆油",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 2.5,  "slippage_ticks": 1},
    "P":   {"name": "棕榈油",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 2.5,  "slippage_ticks": 1},
    "C":   {"name": "玉米",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.2,  "slippage_ticks": 1},
    "CS":  {"name": "玉米淀粉",  "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "RR":  {"name": "粳米",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "LH":  {"name": "生猪",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 5.0,  "slippage_ticks": 1},
    "V":   {"name": "PVC",       "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "L":   {"name": "聚乙烯",    "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "PP":  {"name": "聚丙烯",    "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "EG":  {"name": "乙二醇",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "EB":  {"name": "苯乙烯",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "PG":  {"name": "液化气",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    # ── CZCE 郑商所 ────────────────────────────────────────
    "CF":  {"name": "棉花",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "CY":  {"name": "棉纱",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "SR":  {"name": "白糖",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 2.5,  "slippage_ticks": 1},
    "AP":  {"name": "苹果",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "CJ":  {"name": "红枣",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "OI":  {"name": "菜油",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 2.5,  "slippage_ticks": 1},
    "RM":  {"name": "菜粕",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "RS":  {"name": "油菜籽",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 2.0,  "slippage_ticks": 1},
    "PK":  {"name": "花生",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "SM":  {"name": "锰硅",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "SF":  {"name": "硅铁",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "TA":  {"name": "PTA",       "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "MA":  {"name": "甲醇",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "FG":  {"name": "玻璃",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "SA":  {"name": "纯碱",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "UR":  {"name": "尿素",      "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "PF":  {"name": "短纤",      "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "PX":  {"name": "对二甲苯",  "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    # ── CFFEX 中金所 ───────────────────────────────────────
    "IF":  {"name": "沪深300",   "max_lots": 3,  "max_position": 5,  "daily_loss_pct": 1.0, "price_dev_pct": 0.3, "enabled": False, "commission": 23.0, "slippage_ticks": 1},
    "IC":  {"name": "中证500",   "max_lots": 3,  "max_position": 5,  "daily_loss_pct": 1.0, "price_dev_pct": 0.3, "enabled": False, "commission": 17.0, "slippage_ticks": 1},
    "IH":  {"name": "上证50",    "max_lots": 3,  "max_position": 5,  "daily_loss_pct": 1.0, "price_dev_pct": 0.3, "enabled": False, "commission": 12.0, "slippage_ticks": 1},
    "IM":  {"name": "中证1000",  "max_lots": 3,  "max_position": 5,  "daily_loss_pct": 1.0, "price_dev_pct": 0.3, "enabled": False, "commission": 10.0, "slippage_ticks": 1},
    "T":   {"name": "10年国债",  "max_lots": 5,  "max_position": 15, "daily_loss_pct": 0.5, "price_dev_pct": 0.2, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    "TF":  {"name": "5年国债",   "max_lots": 5,  "max_position": 15, "daily_loss_pct": 0.5, "price_dev_pct": 0.2, "enabled": False, "commission": 2.0,  "slippage_ticks": 1},
    "TS":  {"name": "2年国债",   "max_lots": 5,  "max_position": 15, "daily_loss_pct": 0.5, "price_dev_pct": 0.2, "enabled": False, "commission": 1.5,  "slippage_ticks": 1},
    "TL":  {"name": "30年国债",  "max_lots": 5,  "max_position": 15, "daily_loss_pct": 0.5, "price_dev_pct": 0.2, "enabled": False, "commission": 3.0,  "slippage_ticks": 1},
    # ── INE 上海能源 + GFEX 广期所 ────────────────────────
    "SC":  {"name": "原油",      "max_lots": 3,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False, "commission": 20.0, "slippage_ticks": 1},
    "LU":  {"name": "低硫燃料油","max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 5.0,  "slippage_ticks": 1},
    "SI":  {"name": "工业硅",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False, "commission": 5.0,  "slippage_ticks": 1},
    "LC":  {"name": "碳酸锂",    "max_lots": 3,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False, "commission": 10.0, "slippage_ticks": 1},
}

# ---------- 请求模型 ----------
class PauseRequest(BaseModel):
    reason: str = "手动暂停"

class CtpConfigRequest(BaseModel):
    broker_id: str
    user_id: str
    password: str
    md_front: str
    td_front: str

class RiskPresetUpdateRequest(BaseModel):
    symbol: str
    max_lots: int
    max_position: int
    daily_loss_pct: float
    price_dev_pct: float
    enabled: bool
    commission: float = 1.0
    slippage_ticks: int = 1


class StrategyPublishRequest(BaseModel):
    strategy_id: str
    strategy_version: str
    package_hash: str
    publish_target: str
    allowed_targets: list[str]
    lifecycle_status: str
    published_at: datetime
    live_visibility_mode: str


def _build_local_virtual_account() -> Dict[str, Any]:
    return {
        "label": "本地虚拟盘总本金",
        "principal": _LOCAL_VIRTUAL_PRINCIPAL,
        "currency": "CNY",
        "active_preset": _system_state.get("active_preset", "sim_50w"),
    }


def _build_ctp_snapshot(connected: bool, account: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    acct = account or {}
    balance = acct.get("balance") if connected else None
    available = acct.get("available") if connected else None
    margin = acct.get("margin") if connected else None
    floating_pnl = acct.get("floating_pnl") if connected else None
    close_pnl = acct.get("close_pnl") if connected else None
    commission = acct.get("commission") if connected else None
    initial_balance = acct.get("pre_balance") if connected else None
    margin_rate = round(margin / balance * 100, 2) if balance and margin else None
    if not connected:
        note = "CTP 未连接，账户快照不可用"
    elif balance is None:
        note = "CTP 已连接，账户快照刷新中"
    else:
        note = "CTP 账户快照"
    return {
        "connected": connected,
        "balance": balance,
        "available": available,
        "margin": margin,
        "margin_rate": margin_rate,
        "floating_pnl": floating_pnl,
        "close_pnl": close_pnl,
        "commission": commission,
        "initial_balance": initial_balance,
        "net_pnl": round((close_pnl or 0) + (floating_pnl or 0), 2)
        if close_pnl is not None or floating_pnl is not None
        else None,
        "note": note,
    }

# ---------- 基础状态 ----------
@router.get("/status")
def get_status():
    return {
        "status": "sim-trading running",
        "stage": "skeleton",
        "trading_enabled": _system_state["trading_enabled"],
        "active_preset": _system_state["active_preset"],
    }

@router.get("/positions")
def get_positions():
    return {"positions": [], "note": "not implemented yet"}

@router.get("/orders")
def get_orders():
    return {"orders": [], "note": "not implemented yet"}

@router.post("/orders")
def create_order():
    return {"result": "not implemented yet"}

# ---------- 系统状态控制 ----------
@router.get("/system/state")
def get_system_state():
    return _system_state

@router.post("/system/pause")
def pause_trading(req: PauseRequest):
    _system_state["trading_enabled"] = False
    _system_state["paused_reason"] = req.reason
    try:
        from src.risk.guards import emit_alert
        emit_alert("P1", req.reason, {"event_code": "TRADING_PAUSED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "paused", "state": _system_state}

@router.post("/system/resume")
def resume_trading():
    _system_state["trading_enabled"] = True
    _system_state["paused_reason"] = None
    try:
        from src.risk.guards import emit_alert
        emit_alert("P2", "手动恢复交易", {"event_code": "TRADING_RESUMED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "resumed", "state": _system_state}

@router.post("/system/preset")
def set_preset(body: dict):
    preset = body.get("preset", "sim_50w")
    _system_state["active_preset"] = preset
    return {"result": "preset updated", "active_preset": preset}

# ---------- CTP 配置 ----------
@router.get("/ctp/config")
def get_ctp_config():
    return {
        "broker_id": _system_state.get("ctp_broker_id", ""),
        "user_id": _system_state.get("ctp_user_id", ""),
        "password": "***" if _system_state.get("ctp_password") else "",
        "md_front": _system_state.get("ctp_md_front", ""),
        "td_front": _system_state.get("ctp_td_front", ""),
    }

@router.post("/ctp/config")
def save_ctp_config(req: CtpConfigRequest):
    _system_state["ctp_broker_id"] = req.broker_id
    _system_state["ctp_user_id"] = req.user_id
    _system_state["ctp_password"] = req.password
    _system_state["ctp_md_front"] = req.md_front
    _system_state["ctp_td_front"] = req.td_front
    return {"result": "ctp config saved"}

@router.post("/ctp/connect")
def ctp_connect():
    global _gateway
    import logging
    from src.gateway.simnow import SimNowGateway, _CTP_AVAILABLE

    if not _CTP_AVAILABLE:
        raise HTTPException(status_code=503, detail="openctp-ctp not installed")

    broker_id = _system_state.get("ctp_broker_id") or os.getenv("SIMNOW_BROKER_ID", "9999")
    user_id   = _system_state.get("ctp_user_id")   or os.getenv("SIMNOW_USER_ID", "")
    password  = _system_state.get("ctp_password")   or os.getenv("SIMNOW_PASSWORD", "")
    md_front  = _system_state.get("ctp_md_front")  or os.getenv("SIMNOW_MD_FRONT", "tcp://180.168.146.187:10131")
    td_front  = _system_state.get("ctp_td_front")  or os.getenv("SIMNOW_TRADE_FRONT", "tcp://180.168.146.187:10130")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id not configured")

    # 先断开旧连接
    if _gateway is not None:
        try:
            _gateway.disconnect()
        except Exception:
            pass

    # 全量合约列表（取 risk_presets key 作为订阅品种前缀，实际主连后缀由前端处理）
    instruments = list(_risk_presets.keys())

    _gateway = SimNowGateway(
        broker_id=broker_id,
        user_id=user_id,
        password=password,
        md_front=md_front,
        td_front=td_front,
        instruments=instruments,
    )
    _gateway.connect()

    # 等待最多 10 秒确认连接
    import time
    for _ in range(20):
        st = _gateway.status
        if st["md_connected"] or st["td_connected"]:
            break
        time.sleep(0.5)

    st = _gateway.status
    _system_state["ctp_md_connected"] = st["md_connected"]
    _system_state["ctp_td_connected"] = st["td_connected"]
    _system_state["last_disconnect_reason"] = st.get("last_md_disconnect_reason") or st.get("last_td_disconnect_reason")
    _system_state["last_disconnect_time"] = st.get("last_md_disconnect_time") or st.get("last_td_disconnect_time")

    try:
        from src.risk.guards import emit_alert
        if st["md_connected"] or st["td_connected"]:
            emit_alert("P2", "行情/交易接口连接成功", {"event_code": "CTP_CONNECTED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
        else:
            emit_alert("P1", "CTP 连接超时，行情与交易接口均未就绪", {"event_code": "CTP_CONNECT_FAILED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass

    return {
        "result": "connecting",
        "md": st["md"],
        "td": st["td"],
        "md_connected": st["md_connected"],
        "td_connected": st["td_connected"],
    }

@router.post("/ctp/disconnect")
def ctp_disconnect():
    global _gateway
    if _gateway is not None:
        try:
            _gateway.disconnect()
        except Exception:
            pass
        _gateway = None
    _system_state["ctp_md_connected"] = False
    _system_state["ctp_td_connected"] = False
    try:
        from src.risk.guards import emit_alert
        emit_alert("P2", "CTP 接口主动断开连接", {"event_code": "CTP_DISCONNECTED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "disconnected", "state": _system_state}


@router.get("/ctp/status")
def ctp_status():
    """实时 CTP 连接状态（md + td 独立状态）"""
    if _gateway is None:
        return {"md": "disconnected", "td": "disconnected",
                "md_connected": False, "td_connected": False,
                "last_disconnect_reason": _system_state.get("last_disconnect_reason"),
                "last_disconnect_time": _system_state.get("last_disconnect_time")}
    st = _gateway.status
    # 同步回 system_state
    _system_state["ctp_md_connected"] = st["md_connected"]
    _system_state["ctp_td_connected"] = st["td_connected"]
    _system_state["last_disconnect_reason"] = st.get("last_md_disconnect_reason") or st.get("last_td_disconnect_reason")
    _system_state["last_disconnect_time"] = st.get("last_md_disconnect_time") or st.get("last_td_disconnect_time")
    return st


@router.get("/ticks")
def get_ticks(symbols: str = ""):
    """
    获取最新 tick 数据。
    ?symbols=rb,cu,au  — 指定品种逗号分隔；不传返回全量
    """
    if _gateway is None:
        return {"ticks": {}, "source": "none"}
    all_t = _gateway.all_ticks()
    if symbols:
        wanted = {s.strip().upper() for s in symbols.split(",")}
        all_t = {k: v for k, v in all_t.items() if k.upper() in wanted}
    return {"ticks": all_t, "source": "ctp", "count": len(all_t)}

# ---------- 品种风控预设 ----------
@router.get("/risk-presets")
def get_risk_presets():
    return {"presets": _risk_presets}

@router.post("/risk-presets")
def update_risk_preset(req: RiskPresetUpdateRequest):
    if req.symbol not in _risk_presets:
        _risk_presets[req.symbol] = {"name": req.symbol}
    _risk_presets[req.symbol].update({
        "max_lots": req.max_lots,
        "max_position": req.max_position,
        "daily_loss_pct": req.daily_loss_pct,
        "price_dev_pct": req.price_dev_pct,
        "enabled": req.enabled,
    })
    return {"result": "updated", "symbol": req.symbol, "preset": _risk_presets[req.symbol]}


# ---------- 账户信息（CTP 连接后读取，否则返回空状态）----------
@router.get("/account")
def get_account():
    """
    账户主口径拆分为：
    1. 本地虚拟盘总本金（固定 50 万）
    2. CTP 账户快照（仅作次级展示）
    """
    if _gateway is None or not _gateway.status.get("td_connected"):
        return {
            "connected": False,
            "local_virtual": _build_local_virtual_account(),
            "ctp_snapshot": _build_ctp_snapshot(False),
        }
    acct = _gateway._account
    # 如果账户数据尚未回来，异步触发一次查询
    if acct.get("balance") is None:
        try:
            _gateway._query_account()
        except Exception:
            pass
    return {
        "connected": True,
        "local_virtual": _build_local_virtual_account(),
        "ctp_snapshot": _build_ctp_snapshot(True, acct),
    }


@router.post("/strategy/publish", status_code=202)
def receive_strategy_publish(req: StrategyPublishRequest):
    if req.publish_target != "sim-trading":
        raise HTTPException(status_code=400, detail="publish_target must be sim-trading")
    if "sim-trading" not in req.allowed_targets:
        raise HTTPException(status_code=400, detail="allowed_targets must include sim-trading")
    if req.lifecycle_status != "publish_pending":
        raise HTTPException(status_code=400, detail="lifecycle_status must be publish_pending")
    if req.live_visibility_mode != "locked_visible":
        raise HTTPException(status_code=400, detail="live_visibility_mode must be locked_visible")

    return {
        "accepted": True,
        "target": "sim-trading",
        "strategy_id": req.strategy_id,
        "strategy_version": req.strategy_version,
        "package_hash": req.package_hash,
        "received_at": datetime.utcnow().isoformat() + "Z",
        "message": "strategy package accepted",
    }
