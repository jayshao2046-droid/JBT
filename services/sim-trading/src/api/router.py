import os
import secrets as _secrets
import uuid
from collections import deque
from datetime import datetime
from threading import Lock as _ThreadLock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel

# ---------- API Key 认证 ----------
# 配置方式：运行 .env 中添加 SIM_API_KEY=<随机强密钥>
# 未设置时跳过认证（仅限内网隔离部署使用）
_API_KEY: str = os.getenv("SIM_API_KEY", "")


def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """API Key 认证中间件。设置 SIM_API_KEY 环境变量后强制校验。"""
    if not _API_KEY:
        return  # 未配置则跳过（内网模式）
    if not x_api_key or not _secrets.compare_digest(x_api_key, _API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing X-Api-Key header")


router = APIRouter(prefix="/api/v1", tags=["sim-trading"], dependencies=[Depends(verify_api_key)])

# ---------- SimNow Gateway 单例 ----------
_gateway = None   # type: Any   # SimNowGateway | None

# ---------- ExecutionService 单例（激活后委托 Gateway 执行下单）----------
from src.execution.service import ExecutionService as _ExecutionService
_execution_service = _ExecutionService()   # 模块加载时创建，CTP 连接后通过 bind_gateway 绑定


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
    "ctp_broker_id": os.getenv("SIMNOW_BROKER_ID", "6000"),
    "ctp_user_id": os.getenv("SIMNOW_USER_ID", ""),
    "ctp_password": os.getenv("SIMNOW_PASSWORD", ""),
    "ctp_md_front": os.getenv("SIMNOW_MD_FRONT", "tcp://124.74.248.10:41213"),
    "ctp_td_front": os.getenv("SIMNOW_TRADE_FRONT", "tcp://124.74.248.10:41205"),
    "ctp_app_id": os.getenv("CTP_APP_ID", "client_jbtsim_1.0.0"),
    "ctp_auth_code": os.getenv("CTP_AUTH_CODE", "QN76PPIPR9EKM4QK"),
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
    app_id: str = "client_jbtsim_1.0.0"
    auth_code: str = ""  # 不设硬编码默认值，由调用方显式传入或从 env 读取

class RiskPresetUpdateRequest(BaseModel):
    symbol: str
    max_lots: int
    max_position: int
    daily_loss_pct: float
    price_dev_pct: float
    enabled: bool
    commission: float = 1.0
    slippage_ticks: int = 1


class OrderRequest(BaseModel):
    instrument_id: str
    direction: str   # "buy" / "sell"
    offset: str      # "open" / "close" / "close_today"
    price: float
    volume: int


class CancelOrderRequest(BaseModel):
    order_ref: str


class StrategyPublishRequest(BaseModel):
    strategy_id: str
    strategy_version: str
    package_hash: str
    publish_target: str
    allowed_targets: list[str]
    lifecycle_status: str
    published_at: datetime
    live_visibility_mode: str


# ---------- 信号接收模型与队列 ----------
_VALID_DIRECTIONS = {"buy", "sell", "long", "short"}

class SignalReceiveRequest(BaseModel):
    signal_id: str
    strategy_id: str
    symbol: str
    direction: str
    quantity: float
    price: Optional[float] = None
    order_type: str = "market"
    timestamp: Optional[str] = None
    valid_until: Optional[str] = None
    account_id: Optional[str] = None
    risk_level: str = "normal"
    meta_data: Optional[dict] = None

_signal_queue: deque = deque(maxlen=10000)
# 有界幂等去重表：最多保留 50k 条记录，FIFO 淘汰，防止内存无界增长
_MAX_SIGNAL_IDS = 50_000
_received_signal_ids: Dict[str, bool] = {}   # insertion-ordered (Python 3.7+)


def _has_seen_signal(signal_id: str) -> bool:
    return signal_id in _received_signal_ids


def _mark_signal_seen(signal_id: str) -> None:
    if len(_received_signal_ids) >= _MAX_SIGNAL_IDS:
        oldest = next(iter(_received_signal_ids))
        del _received_signal_ids[oldest]
    _received_signal_ids[signal_id] = True


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


def _sync_gateway_state() -> Optional[Dict[str, Any]]:
    gw = _get_gateway()
    if gw is None:
        return None

    st = gw.status
    _system_state["ctp_md_connected"] = st["md_connected"]
    _system_state["ctp_td_connected"] = st["td_connected"]
    _system_state["last_disconnect_reason"] = st.get("last_md_disconnect_reason") or st.get("last_td_disconnect_reason")
    _system_state["last_disconnect_time"] = st.get("last_md_disconnect_time") or st.get("last_td_disconnect_time")
    return st


def _safe_state() -> Dict[str, Any]:
    """返回脱敏后的 _system_state 副本，屏蔽密码与鉴权码明文。"""
    s = dict(_system_state)
    for key in ("ctp_password", "ctp_auth_code"):
        if s.get(key):
            s[key] = "***"
    return s

# ---------- 基础状态 ----------
@router.get("/status")
def get_status():
    return {
        "status": "sim-trading running",
        "stage": "1.0.0",
        "trading_enabled": _system_state["trading_enabled"],
        "active_preset": _system_state["active_preset"],
    }

@router.get("/positions")
def get_positions():
    gw = _get_gateway()
    if gw is None:
        return {"positions": [], "note": "CTP 未连接"}
    from src.ledger.service import get_ledger
    return {"positions": get_ledger().get_positions()}

@router.get("/orders")
def get_orders():
    gw = _get_gateway()
    if gw is None:
        return {"orders": {}, "note": "CTP 未连接"}
    return {"orders": gw.get_orders()}

@router.post("/orders")
def create_order(req: OrderRequest):
    """
    下单 API —— 含光大穿透式合规所需的全部前置校验：
    1. 交易暂停检查（暂停交易功能）
    2. CTP 连接检查
    3. 合约代码校验（程序端拦截，不报入交易系统）
    4. 最小变动价位校验（程序端拦截）
    5. 单笔最大委托手数校验（程序端拦截）
    6. 风控预设手数限制
    通过后发送到 CTP，交易所错误通过回调异步返回。
    """
    import math

    # ── 1. 暂停交易检查 ──
    if not _system_state.get("trading_enabled", True):
        reason = _system_state.get("paused_reason", "手动暂停")
        return {"rejected": True, "source": "program",
                "error": f"交易已暂停: {reason}", "code": "TRADING_PAUSED"}

    # ── 2. CTP 连接检查 ──
    gw = _get_gateway()
    if gw is None or gw._td_status not in ("td_ready", "td_logged_in"):
        return {"rejected": True, "source": "program",
                "error": "交易通道未连接", "code": "TD_NOT_CONNECTED"}

    instrument_id = req.instrument_id.strip()
    direction_map = {"buy": "0", "sell": "1"}
    offset_map = {"open": "0", "close": "1", "close_today": "3"}
    direction = direction_map.get(req.direction)
    offset = offset_map.get(req.offset)
    if direction is None or offset is None:
        return {"rejected": True, "source": "program",
                "error": f"无效的方向/开平: direction={req.direction}, offset={req.offset}",
                "code": "INVALID_DIRECTION_OFFSET"}

    # ── 3. 合约代码校验 ──
    spec = gw.get_instrument_spec(instrument_id)
    if spec is None:
        return {"rejected": True, "source": "program",
                "error": f"合约代码不存在: {instrument_id}",
                "code": "INVALID_INSTRUMENT"}

    # ── 4. 最小变动价位校验 ──
    price_tick = spec.get("price_tick", 0)
    if price_tick > 0:
        remainder = round(req.price % price_tick, 10)
        if remainder > 1e-9 and abs(remainder - price_tick) > 1e-9:
            return {"rejected": True, "source": "program",
                    "error": f"价格 {req.price} 不符合最小变动价位 {price_tick}",
                    "code": "INVALID_PRICE_TICK"}

    # ── 5. 单笔最大委托手数校验（交易所限制）──
    max_vol = spec.get("max_order_volume", 1000)
    if req.volume > max_vol:
        return {"rejected": True, "source": "program",
                "error": f"委托手数 {req.volume} 超出交易所单笔限制 {max_vol}",
                "code": "EXCEED_MAX_ORDER_VOLUME"}

    if req.volume <= 0:
        return {"rejected": True, "source": "program",
                "error": "委托手数必须大于 0", "code": "INVALID_VOLUME"}

    # ── 6. 风控预设手数限制 ──
    product_id = spec.get("product_id", "").upper()
    preset = _risk_presets.get(product_id, {})
    if preset:
        risk_max = preset.get("max_lots", 9999)
        if req.volume > risk_max:
            return {"rejected": True, "source": "risk_control",
                    "error": f"委托手数 {req.volume} 超出风控单笔限制 {risk_max} ({product_id})",
                    "code": "EXCEED_RISK_MAX_LOTS"}
        if not preset.get("enabled", True):
            return {"rejected": True, "source": "risk_control",
                    "error": f"品种 {product_id} 未启用交易", "code": "PRODUCT_DISABLED"}

    # ── 执行下单（通过 ExecutionService 委托 Gateway）──
    try:
        result = _execution_service.submit_order(instrument_id, direction, offset, req.price, req.volume)
        return {"rejected": False, "source": "ctp", **result}
    except Exception as exc:
        return {"rejected": True, "source": "program",
                "error": str(exc), "code": "ORDER_SUBMIT_ERROR"}


@router.post("/orders/cancel")
def cancel_order(req: CancelOrderRequest):
    """撤单 API"""
    gw = _get_gateway()
    if gw is None:
        raise HTTPException(status_code=503, detail="CTP 未连接")
    try:
        result = gw.cancel_order(req.order_ref)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/orders/errors")
def get_order_errors():
    """获取最近的订单错误（含 CTP 前置和交易所返回的错误）"""
    gw = _get_gateway()
    if gw is None:
        return {"errors": []}
    return {"errors": gw.get_order_errors()}


@router.get("/instruments")
def get_instruments(product: str = ""):
    """查询已缓存的合约规格（tick size、最大手数等）"""
    gw = _get_gateway()
    if gw is None:
        return {"instruments": {}, "count": 0}
    specs = gw.get_all_instrument_specs()
    if product:
        wanted = {p.strip().upper() for p in product.split(",")}
        specs = {k: v for k, v in specs.items() if v.get("product_id", "").upper() in wanted}
    return {"instruments": specs, "count": len(specs)}

# ---------- 系统状态控制 ----------
@router.get("/system/state")
def get_system_state():
    _sync_gateway_state()
    safe = {**_system_state}
    # 脱敏：永远不返回凭证明文
    for key in ("ctp_password", "ctp_auth_code"):
        if safe.get(key):
            safe[key] = "***"
    return safe

@router.post("/system/pause")
def pause_trading(req: PauseRequest):
    _system_state["trading_enabled"] = False
    _system_state["paused_reason"] = req.reason
    try:
        from src.risk.guards import emit_alert
        emit_alert("P1", req.reason, {"event_code": "TRADING_PAUSED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "paused", "state": _safe_state()}

@router.post("/system/resume")
def resume_trading():
    _system_state["trading_enabled"] = True
    _system_state["paused_reason"] = None
    try:
        from src.risk.guards import emit_alert
        emit_alert("P2", "手动恢复交易", {"event_code": "TRADING_RESUMED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "resumed", "state": _safe_state()}

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
        "app_id": _system_state.get("ctp_app_id", ""),
        "auth_code": "***" if _system_state.get("ctp_auth_code") else "",
    }

@router.post("/ctp/config")
def save_ctp_config(req: CtpConfigRequest):
    _system_state["ctp_broker_id"] = req.broker_id
    _system_state["ctp_user_id"] = req.user_id
    _system_state["ctp_password"] = req.password
    _system_state["ctp_md_front"] = req.md_front
    _system_state["ctp_td_front"] = req.td_front
    _system_state["ctp_app_id"] = req.app_id
    _system_state["ctp_auth_code"] = req.auth_code
    return {"result": "ctp config saved"}

@router.post("/ctp/connect")
def ctp_connect(silent: bool = False):
    global _gateway
    import logging
    from src.gateway.simnow import SimNowGateway, _CTP_AVAILABLE

    if not _CTP_AVAILABLE:
        raise HTTPException(status_code=503, detail="openctp-ctp not installed")

    broker_id = _system_state.get("ctp_broker_id") or os.getenv("SIMNOW_BROKER_ID", "6000")
    user_id   = _system_state.get("ctp_user_id")   or os.getenv("SIMNOW_USER_ID", "")
    password  = _system_state.get("ctp_password")   or os.getenv("SIMNOW_PASSWORD", "")
    md_front  = _system_state.get("ctp_md_front")  or os.getenv("SIMNOW_MD_FRONT", "tcp://124.74.248.10:41213")
    td_front  = _system_state.get("ctp_td_front")  or os.getenv("SIMNOW_TRADE_FRONT", "tcp://124.74.248.10:41205")
    app_id    = _system_state.get("ctp_app_id")    or os.getenv("CTP_APP_ID", "client_jbtsim_1.0.0")
    auth_code = _system_state.get("ctp_auth_code") or os.getenv("CTP_AUTH_CODE", "QN76PPIPR9EKM4QK")

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
        app_id=app_id,
        auth_code=auth_code,
    )
    _gateway.connect()
    # 绑定 ExecutionService，使其可通过独立模块提交订单
    _execution_service.bind_gateway(_gateway)

    # 等待最多 10 秒确认连接
    import time
    for _ in range(20):
        st = _gateway.status
        if st["md_connected"] or st["td_connected"]:
            break
        time.sleep(0.5)

    st = _sync_gateway_state() or _gateway.status

    if not silent:
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
    return {"result": "disconnected", "state": _safe_state()}


@router.get("/ctp/status")
def ctp_status():
    """实时 CTP 连接状态（md + td 独立状态）"""
    if _gateway is None:
        return {"md": "disconnected", "td": "disconnected",
                "md_connected": False, "td_connected": False,
                "last_disconnect_reason": _system_state.get("last_disconnect_reason"),
                "last_disconnect_time": _system_state.get("last_disconnect_time")}
    return _sync_gateway_state() or _gateway.status


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


# ---------- 信号接收端点 ----------
@router.post("/signals/receive")
def receive_signal(req: SignalReceiveRequest):
    """
    接收来自决策服务的交易信号。
    验证参数 → 幂等检查 → 生成 execution_id → 暂存队列 → 返回确认。
    """
    errors = []
    if not req.signal_id or not req.signal_id.strip():
        errors.append("signal_id is required")
    if not req.strategy_id or not req.strategy_id.strip():
        errors.append("strategy_id is required")
    if not req.symbol or not req.symbol.strip():
        errors.append("symbol is required")
    if req.quantity <= 0:
        errors.append("quantity must be > 0")
    if req.direction not in _VALID_DIRECTIONS:
        errors.append(f"direction must be one of {sorted(_VALID_DIRECTIONS)}")

    if errors:
        return {
            "status": "rejected",
            "signal_id": req.signal_id,
            "execution_id": None,
            "message": "; ".join(errors),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # 幂等：重复 signal_id 直接返回 received 但不再入队
    if _has_seen_signal(req.signal_id):
        return {
            "status": "received",
            "signal_id": req.signal_id,
            "execution_id": None,
            "message": "duplicate signal_id, already received",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    execution_id = f"exec-{uuid.uuid4().hex[:12]}"
    entry = {
        "signal_id": req.signal_id,
        "strategy_id": req.strategy_id,
        "symbol": req.symbol,
        "direction": req.direction,
        "quantity": req.quantity,
        "price": req.price,
        "order_type": req.order_type,
        "risk_level": req.risk_level,
        "execution_id": execution_id,
        "received_at": datetime.utcnow().isoformat() + "Z",
    }
    _signal_queue.append(entry)
    _mark_signal_seen(req.signal_id)

    return {
        "status": "received",
        "signal_id": req.signal_id,
        "execution_id": execution_id,
        "message": "signal accepted",
        "timestamp": datetime.utcnow().isoformat() + "Z",
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


# ---------- 报表 API ----------
@router.get("/report/daily")
def get_daily_report():
    """返回当日收盘报表数据。"""
    from src.ledger.service import get_ledger
    return get_ledger().generate_daily_report()


@router.get("/report/trades")
def get_report_trades():
    """返回当日成交列表。"""
    from src.ledger.service import get_ledger
    return {"trades": get_ledger().get_trades()}


@router.get("/report/positions")
def get_report_positions():
    """返回当前持仓列表。"""
    from src.ledger.service import get_ledger
    return {"positions": get_ledger().get_positions()}


# ---------- 只读日志查看 ----------
def _get_memory_log_records() -> List[Dict[str, Any]]:
    """从 main.py 的 MemoryLogHandler 获取日志记录列表。"""
    from src.main import memory_log_handler
    return list(memory_log_handler.records)


@router.get("/logs")
def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    level: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
):
    """返回最近 N 条日志，支持按级别和来源过滤。纯只读。"""
    records = _get_memory_log_records()
    if level:
        level_upper = level.upper()
        records = [r for r in records if r["level"] == level_upper]
    if source:
        records = [r for r in records if source in r["source"]]
    tail = records[-limit:]
    return {"logs": tail, "total": len(tail)}


@router.get("/logs/tail")
def get_logs_tail(
    limit: int = Query(default=100, ge=1, le=1000),
    level: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
):
    """返回最新 N 条日志（供轮询刷新），结构同 /logs。"""
    records = _get_memory_log_records()
    if level:
        level_upper = level.upper()
        records = [r for r in records if r["level"] == level_upper]
    if source:
        records = [r for r in records if source in r["source"]]
    tail = records[-limit:]
    return {"logs": tail, "total": len(tail)}
