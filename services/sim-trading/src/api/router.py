from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["sim-trading"])

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
    # 骨架阶段：模拟连接成功
    _system_state["ctp_md_connected"] = True
    _system_state["ctp_td_connected"] = True
    return {"result": "connected (skeleton mock)", "state": _system_state}

@router.post("/ctp/disconnect")
def ctp_disconnect():
    _system_state["ctp_md_connected"] = False
    _system_state["ctp_td_connected"] = False
    return {"result": "disconnected", "state": _system_state}

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
