import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["sim-trading"])

# ---------- SimNow Gateway 单例 ----------
_gateway = None   # type: Any   # SimNowGateway | None

def _get_gateway():
    return _gateway

# ---------- 内存状态（骨架阶段，重启重置）----------
_system_state: Dict[str, Any] = {
    "trading_enabled": True,
    "active_preset": "sim_50w",
    "paused_reason": None,
    "ctp_md_connected": False,
    "ctp_td_connected": False,
    "ctp_broker_id": "",
    "ctp_user_id": "",
    "ctp_md_front": "tcp://180.168.146.187:10131",
    "ctp_td_front": "tcp://180.168.146.187:10130",
}

_risk_presets: Dict[str, Any] = {
    "RB": {"name": "螺纹钢",  "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": True},
    "HC": {"name": "热卷",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": True},
    "CU": {"name": "沪铜",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": True},
    "AL": {"name": "沪铝",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": True},
    "ZN": {"name": "沪锌",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False},
    "AU": {"name": "黄金",    "max_lots": 5,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False},
    "AG": {"name": "白银",    "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "I":  {"name": "铁矿石",  "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "J":  {"name": "焦炭",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False},
    "JM": {"name": "焦煤",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False},
    "M":  {"name": "豆粕",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "Y":  {"name": "豆油",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "A":  {"name": "大豆",    "max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False},
    "C":  {"name": "玉米",    "max_lots": 10, "max_position": 30, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "L":  {"name": "聚乙烯",  "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "PP": {"name": "聚丙烯",  "max_lots": 10, "max_position": 20, "daily_loss_pct": 2.0, "price_dev_pct": 1.0, "enabled": False},
    "RU": {"name": "天然橡胶","max_lots": 5,  "max_position": 15, "daily_loss_pct": 1.5, "price_dev_pct": 0.8, "enabled": False},
    "SC": {"name": "原油",    "max_lots": 3,  "max_position": 10, "daily_loss_pct": 1.0, "price_dev_pct": 0.5, "enabled": False},
    "IF": {"name": "沪深300", "max_lots": 3,  "max_position": 5,  "daily_loss_pct": 1.0, "price_dev_pct": 0.3, "enabled": False},
    "IC": {"name": "中证500", "max_lots": 3,  "max_position": 5,  "daily_loss_pct": 1.0, "price_dev_pct": 0.3, "enabled": False},
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
    return {"result": "paused", "state": _system_state}

@router.post("/system/resume")
def resume_trading():
    _system_state["trading_enabled"] = True
    _system_state["paused_reason"] = None
    return {"result": "resumed", "state": _system_state}

@router.post("/system/preset")
def set_preset(body: dict):
    preset = body.get("preset", "sim_50w")
    _system_state["active_preset"] = preset
    return {"result": "preset updated", "active_preset": preset}

# ---------- CTP 配置 ----------
@router.get("/ctp/config")
def get_ctp_config():
    return {k: v for k, v in _system_state.items() if k.startswith("ctp_")}

@router.post("/ctp/config")
def save_ctp_config(req: CtpConfigRequest):
    _system_state["ctp_broker_id"] = req.broker_id
    _system_state["ctp_user_id"] = req.user_id
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
    password  = os.getenv("SIMNOW_PASSWORD", "")
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

    # 等待最多 5 秒确认连接
    import time
    for _ in range(10):
        st = _gateway.status
        if st["md_connected"] or st["td_connected"]:
            break
        time.sleep(0.5)

    st = _gateway.status
    _system_state["ctp_md_connected"] = st["md_connected"]
    _system_state["ctp_td_connected"] = st["td_connected"]

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
    return {"result": "disconnected", "state": _system_state}


@router.get("/ctp/status")
def ctp_status():
    """实时 CTP 连接状态（md + td 独立状态）"""
    if _gateway is None:
        return {"md": "disconnected", "td": "disconnected",
                "md_connected": False, "td_connected": False}
    st = _gateway.status
    # 同步回 system_state
    _system_state["ctp_md_connected"] = st["md_connected"]
    _system_state["ctp_td_connected"] = st["td_connected"]
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
    账户净值/可用资金/浮动盈亏。
    CTP 未连接时返回 connected=false，不返回任何假数据。
    """
    if _gateway is None or not _gateway.status.get("td_connected"):
        return {
            "connected": False,
            "equity": None,
            "available": None,
            "floating_pnl": None,
            "margin": None,
            "margin_rate": None,
            "note": "CTP 未连接，账户数据不可用",
        }
    # CTP 已连接时，从 gateway 获取（TASK-0016 实现订单/账户查询后扩展）
    return {
        "connected": True,
        "equity": None,
        "available": None,
        "floating_pnl": None,
        "margin": None,
        "margin_rate": None,
        "note": "CTP 已连接，账户查询 TASK-0016 实现",
    }
