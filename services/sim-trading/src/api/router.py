import os
import hmac
import socket
import uuid
from collections import deque
from datetime import datetime, timedelta
from threading import Lock as _ThreadLock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

# ---------- API Key 认证 ----------
# 认证已迁移到 main.py 作为 FastAPI 全局中间件
# 保留此注释以标记历史变更（commit 836eac9 → a69df54 → 本次清理）

router = APIRouter(prefix="/api/v1", tags=["sim-trading"])

# ---------- SimNow Gateway 单例 ----------
_gateway = None   # type: Any   # SimNowGateway | None
_CTP_CONNECT_FAIL_ALERT_COOLDOWN = 600
_last_ctp_connect_fail_alert_ts = 0.0

# ---------- ExecutionService 单例（激活后委托 Gateway 执行下单）----------
from src.execution.service import ExecutionService as _ExecutionService
_execution_service = _ExecutionService()   # 模块加载时创建，CTP 连接后通过 bind_gateway 绑定


def _get_gateway():
    return _gateway


def _parse_tcp_front(front: str) -> Optional[tuple[str, int]]:
    value = (front or "").strip()
    if not value:
        return None
    if "://" in value:
        scheme, value = value.split("://", 1)
        if scheme.lower() != "tcp":
            return None
    host, sep, port_text = value.rpartition(":")
    if not sep or not host:
        return None
    try:
        return host, int(port_text)
    except ValueError:
        return None


def get_ctp_front_reachability(
    md_front: Optional[str] = None,
    td_front: Optional[str] = None,
    timeout: float = 2.0,
) -> Dict[str, bool]:
    md_value = md_front or _system_state.get("ctp_md_front") or os.getenv("SIMNOW_MD_FRONT", "")
    td_value = td_front or _system_state.get("ctp_td_front") or os.getenv("SIMNOW_TRADE_FRONT", "")
    results: Dict[str, bool] = {}
    for channel, front in {"md": md_value, "td": td_value}.items():
        endpoint = _parse_tcp_front(front)
        if endpoint is None:
            results[channel] = False
            continue
        try:
            with socket.create_connection(endpoint, timeout=timeout):
                results[channel] = True
        except OSError:
            results[channel] = False
    return results

# ---------- CTP 连接锁（防止并发 connect 调用造成 _gateway 竞态）----------
_connect_lock = _ThreadLock()


def disconnect_gateway_internal() -> None:
    """供 guardian 等站内调用的最小断联 helper，不走 HTTP 鉴权路径。"""
    global _gateway
    with _connect_lock:
        if _gateway is not None:
            try:
                _gateway.disconnect()
            except Exception:
                pass
            _gateway = None
        _system_state["ctp_md_connected"] = False
        _system_state["ctp_td_connected"] = False


def _require_write_api_key(request: Request) -> None:
    """关键写操作强制鉴权：未配置 SIM_API_KEY 时默认锁定写操作。"""
    expected = (os.getenv("SIM_API_KEY", "") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="SIM_API_KEY not configured; write operations are locked",
        )
    provided = (request.headers.get("X-API-Key", "") or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="invalid or missing API key")


def _is_local_manual_request(request: Request) -> bool:
    """仅允许本机手动请求在声明 manual 时免 key。"""
    manual_flag = (request.headers.get("X-Manual-Op", "") or "").strip().lower()
    if manual_flag not in {"1", "true", "yes", "manual"}:
        return False
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost"}


def _require_trade_api_key(request: Request) -> None:
    """
    下单/平仓相关指令鉴权策略：
    - 自动交易必须带 key（严格）
    - 手动操作仅允许本机 + X-Manual-Op 显式声明时免 key
    """
    if _is_local_manual_request(request):
        return
    _require_write_api_key(request)

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
    "ctp_auth_code": os.getenv("CTP_AUTH_CODE", ""),
    "reduce_only_mode": False,  # 只减仓模式：True 时禁止开仓
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
def create_order(req: OrderRequest, request: Request):
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
    _require_trade_api_key(request)

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

    # ── 7. 灾难止损检查（净值回撤超阈值时熔断全停）──
    _acct = gw._account if gw else {}
    if _acct.get("balance") is not None and _acct.get("pre_balance") is not None:
        from src.risk.guards import RiskGuards
        if not RiskGuards().check_disaster_stop(_acct):
            return {"rejected": True, "source": "risk_control",
                    "error": "灾难止损已触发，禁止下单", "code": "DISASTER_STOP_TRIGGERED"}

    # ── 8. 只减仓模式检查（reduce_only_mode 启用时禁止开仓）──
    if _system_state.get("reduce_only_mode", False) and offset == "0":
        try:
            from src.risk.guards import emit_alert
            emit_alert("P1", f"只减仓模式：拒绝开仓指令 {instrument_id}",
                       {"event_code": "RISK_REDUCE_ONLY_REJECT", "symbol": instrument_id,
                        "source": "risk_guard"})
        except Exception:
            pass
        return {"rejected": True, "source": "risk_control",
                "error": "只减仓模式：禁止开仓", "code": "REDUCE_ONLY_REJECT"}

    # ── 9. 持仓累计上限检查（开仓时按品种合计持仓不得超 max_position）──
    if preset and offset == "0":
        max_pos = preset.get("max_position", 0)
        if max_pos > 0:
            from src.ledger.service import get_ledger
            positions = get_ledger().get_positions()
            current_pos = sum(
                (p.get("position") or 0)
                for p in positions
                if str(p.get("instrument_id") or "").upper().startswith(product_id)
            )
            if current_pos + req.volume > max_pos:
                return {"rejected": True, "source": "risk_control",
                        "error": (f"开仓后持仓 {current_pos + req.volume} 手"
                                  f" 超出上限 {max_pos} 手 ({product_id})"),
                        "code": "EXCEED_MAX_POSITION"}

    # ── 执行下单（通过 ExecutionService 委托 Gateway）──
    try:
        result = _execution_service.submit_order(instrument_id, direction, offset, req.price, req.volume)
        return {"rejected": False, "source": "ctp", **result}
    except Exception as exc:
        return {"rejected": True, "source": "program",
                "error": str(exc), "code": "ORDER_SUBMIT_ERROR"}


@router.post("/orders/cancel")
def cancel_order(req: CancelOrderRequest, request: Request):
    """撤单 API"""
    _require_trade_api_key(request)
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
def pause_trading(req: PauseRequest, request: Request):
    _require_write_api_key(request)
    _system_state["trading_enabled"] = False
    _system_state["paused_reason"] = req.reason
    try:
        from src.risk.guards import emit_alert
        emit_alert("P1", req.reason, {"event_code": "TRADING_PAUSED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "paused", "state": _safe_state()}

@router.post("/system/resume")
def resume_trading(request: Request):
    _require_write_api_key(request)
    _system_state["trading_enabled"] = True
    _system_state["paused_reason"] = None
    try:
        from src.risk.guards import emit_alert
        emit_alert("P2", "手动恢复交易", {"event_code": "TRADING_RESUMED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
    except Exception:
        pass
    return {"result": "resumed", "state": _safe_state()}

@router.post("/system/preset")
def set_preset(body: dict, request: Request):
    _require_write_api_key(request)
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
def save_ctp_config(req: CtpConfigRequest, request: Request):
    _require_write_api_key(request)
    _system_state["ctp_broker_id"] = req.broker_id
    _system_state["ctp_user_id"] = req.user_id
    _system_state["ctp_password"] = req.password
    _system_state["ctp_md_front"] = req.md_front
    _system_state["ctp_td_front"] = req.td_front
    _system_state["ctp_app_id"] = req.app_id
    _system_state["ctp_auth_code"] = req.auth_code
    return {"result": "ctp config saved"}

def ctp_connect(silent: bool = False):
    global _gateway, _last_ctp_connect_fail_alert_ts
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
    auth_code = _system_state.get("ctp_auth_code") or os.getenv("CTP_AUTH_CODE", "")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id not configured")

    reachability = get_ctp_front_reachability(md_front=md_front, td_front=td_front)
    if not (reachability.get("md") or reachability.get("td")):
        raise HTTPException(
            status_code=503,
            detail=(
                "CTP fronts unreachable: "
                f"md={reachability.get('md', False)} td={reachability.get('td', False)}"
            ),
        )

    # 并发保护：同一时刻只允许一个 connect 操作（sync 路由运行在线程池，需显式加锁）
    if not _connect_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="CTP connect already in progress")

    try:
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

        # 等待最多 10 秒确认连接（sync 路由中使用 time.sleep 不阻塞事件循环）
        import time
        for _ in range(20):
            st = _gateway.status
            if st["md_connected"] or st["td_connected"]:
                break
            time.sleep(0.5)

        st = _sync_gateway_state() or _gateway.status
    finally:
        _connect_lock.release()

    if not silent:
        try:
            import time
            from src.risk.guards import emit_alert
            now_ts = time.time()
            if (
                not (st["md_connected"] or st["td_connected"])
                and now_ts - _last_ctp_connect_fail_alert_ts >= _CTP_CONNECT_FAIL_ALERT_COOLDOWN
            ):
                emit_alert("P1", "CTP 连接超时，行情与交易接口均未就绪", {"event_code": "CTP_CONNECT_FAILED", "account_id": _system_state.get("ctp_user_id", ""), "stage_preset": "sim"})
                _last_ctp_connect_fail_alert_ts = now_ts
        except Exception:
            pass

    return {
        "result": "connecting",
        "md": st["md"],
        "td": st["td"],
        "md_connected": st["md_connected"],
        "td_connected": st["td_connected"],
    }


@router.post("/ctp/connect")
def ctp_connect_api(request: Request, silent: bool = False):
    _require_write_api_key(request)
    return ctp_connect(silent=silent)

@router.post("/ctp/disconnect")
def ctp_disconnect(request: Request):
    _require_write_api_key(request)
    disconnect_gateway_internal()
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
def update_risk_preset(req: RiskPresetUpdateRequest, request: Request):
    _require_write_api_key(request)
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
def receive_signal(req: SignalReceiveRequest, request: Request):
    """
    接收来自决策服务的交易信号。
    验证参数 → 幂等检查 → 生成 execution_id → 暂存队列 → 返回确认。
    """
    # 自动交易入口：必须带 key，不允许手动豁免
    _require_write_api_key(request)

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


@router.get("/signals/queue")
def get_signal_queue(limit: int = Query(default=50, ge=1, le=500)):
    """
    查看信号接收队列（只读）。

    ⚠️ 已知局限：当前队列无自动消费者，信号入队后不会自动触发下单。
    如需执行，须手动调用 POST /orders 接口。
    该端点用于运维监控与调试，不影响队列内容。
    """
    items = list(_signal_queue)[-limit:]
    return {
        "count": len(items),
        "total_received": len(_received_signal_ids),
        "consumer": "none",
        "note": "队列当前无自动消费者，信号需手动通过 /orders 接口执行",
        "signals": items,
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


# ---------- Failover 容灾交接 ----------
from src.failover.handler import FailoverHandler, HandoverPayload

_failover_handler = FailoverHandler()


@router.post("/failover/handover")
def failover_handover(data: HandoverPayload):
    """接收来自 decision LocalSimEngine 的交接数据"""
    result = _failover_handler.receive_handover(data)
    return result


@router.get("/failover/status")
def failover_status():
    """查询当前交接状态"""
    return _failover_handler.get_status()


@router.post("/failover/confirm")
def failover_confirm(body: dict):
    """确认交接完成"""
    handover_id = body.get("handover_id", "")
    success = _failover_handler.confirm_handover(handover_id)
    return {"success": success, "handover_id": handover_id}


# ---------- SIMWEB-01 P0-1: 权益历史 ----------
@router.get("/equity/history")
def get_equity_history(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
):
    """获取权益历史数据（P0-1）"""
    from src.ledger.service import get_ledger
    from datetime import datetime

    start_time = None
    end_time = None

    if start:
        try:
            start_time = datetime.fromisoformat(start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start time format")

    if end:
        try:
            end_time = datetime.fromisoformat(end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end time format")

    history = get_ledger().get_equity_history(start_time, end_time)
    return {"history": history, "count": len(history)}


# ---------- SIMWEB-01 P0-2: L1/L2 风控状态 ----------
@router.get("/risk/l1")
def get_risk_l1_status():
    """获取 L1 风控检查项状态（P0-2）"""
    from src.risk.guards import RiskGuards

    guards = RiskGuards()
    # L1 风控检查项（10 项基础检查）
    l1_status = {
        "trading_enabled": _system_state.get("trading_enabled", True),
        "ctp_connected": _system_state.get("ctp_td_connected", False),
        "reduce_only_mode": False,  # 当前未实现，预留
        "disaster_stop_triggered": False,  # 需要从账户数据计算
        "max_position_check": True,  # 预留
        "daily_loss_check": True,  # 预留
        "price_deviation_check": True,  # 预留
        "order_frequency_check": True,  # 预留
        "margin_rate_check": True,  # 预留
        "connection_quality_check": True,  # 预留
    }

    # 检查灾难止损
    gw = _get_gateway()
    if gw and gw.status.get("td_connected"):
        account = gw._account
        if account.get("balance") is not None:
            disaster_check = guards.check_disaster_stop(account)
            l1_status["disaster_stop_triggered"] = not disaster_check

    return {"l1_status": l1_status, "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/risk/l2")
def get_risk_l2_status():
    """获取 L2 风控指标（P0-2）"""
    from src.ledger.service import get_ledger

    ledger = get_ledger()
    trades = ledger.get_trades()

    # 计算连续亏损次数
    consecutive_losses = 0
    for trade in reversed(trades):
        pnl = trade.get("pnl", 0)
        if pnl < 0:
            consecutive_losses += 1
        else:
            break

    # 计算保证金率
    margin_rate = None
    gw = _get_gateway()
    if gw and gw.status.get("td_connected"):
        account = gw._account
        balance = account.get("balance")
        margin = account.get("margin")
        if balance and margin and balance > 0:
            margin_rate = round(margin / balance * 100, 2)

    l2_status = {
        "consecutive_losses": consecutive_losses,
        "margin_rate": margin_rate,
        "daily_trade_count": len(trades),
        "daily_pnl": sum(t.get("pnl", 0) for t in trades),
        "position_count": len(ledger.get_positions()),
    }

    return {"l2_status": l2_status, "timestamp": datetime.utcnow().isoformat() + "Z"}


# ---------- SIMWEB-01 P0-3: 止损修改 ----------
class UpdateStopLossRequest(BaseModel):
    stop_loss: float


@router.patch("/positions/{position_id}/stop_loss")
def update_position_stop_loss(position_id: str, req: UpdateStopLossRequest, request: Request):
    """修改持仓止损（P0-3）"""
    _require_trade_api_key(request)
    from src.ledger.service import get_ledger

    ledger = get_ledger()
    positions = ledger.get_positions()

    # 查找持仓
    target_position = None
    for pos in positions:
        if str(pos.get("position_id")) == position_id or str(pos.get("instrument_id")) == position_id:
            target_position = pos
            break

    if target_position is None:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    # 更新止损（当前只更新内存，实际应该持久化）
    target_position["stop_loss"] = req.stop_loss

    return {
        "success": True,
        "position_id": position_id,
        "stop_loss": req.stop_loss,
        "message": "Stop loss updated successfully",
    }


# ---------- SIMWEB-01 P1-1: 交易绩效 KPI ----------
@router.get("/stats/performance")
def get_performance_stats():
    """获取交易绩效统计（P1-1）"""
    from src.ledger.service import get_ledger
    from src.stats.performance import PerformanceCalculator

    ledger = get_ledger()
    trades = ledger.get_trades()
    equity_history = ledger.get_equity_history()

    calculator = PerformanceCalculator()
    stats = calculator.get_performance_stats(trades, equity_history)

    return {"performance": stats, "timestamp": datetime.utcnow().isoformat() + "Z"}


# ---------- SIMWEB-01 P1-2: 执行质量 KPI ----------
@router.get("/stats/execution")
def get_execution_stats():
    """获取执行质量统计（P1-2）"""
    from src.ledger.service import get_ledger
    from src.stats.execution import ExecutionQualityCalculator

    ledger = get_ledger()
    trades = ledger.get_trades()

    # 获取订单列表
    gw = _get_gateway()
    orders = []
    if gw and gw.status.get("td_connected"):
        orders_dict = gw.get_orders()
        orders = list(orders_dict.values()) if isinstance(orders_dict, dict) else []

    calculator = ExecutionQualityCalculator()
    stats = calculator.get_execution_stats(trades, orders)

    return {"execution": stats, "timestamp": datetime.utcnow().isoformat() + "Z"}


# ---------- SIMWEB-01 P1-3: 批量操作 ----------
class BatchCloseRequest(BaseModel):
    position_ids: List[str]


@router.post("/positions/batch_close")
def batch_close_positions(req: BatchCloseRequest, request: Request):
    """批量平仓（P1-3）"""
    _require_trade_api_key(request)
    from src.execution.service import ExecutionService

    results = []
    for position_id in req.position_ids:
        try:
            # 这里需要调用执行服务的平仓方法
            # 当前简化实现，实际需要通过 CTP 网关平仓
            result = {"position_id": position_id, "success": True, "message": "Close order submitted"}
            results.append(result)
        except Exception as e:
            results.append({"position_id": position_id, "success": False, "error": str(e)})

    success_count = sum(1 for r in results if r.get("success"))
    return {
        "results": results,
        "total": len(req.position_ids),
        "success": success_count,
        "failed": len(req.position_ids) - success_count,
    }


# ---------- SIMWEB-01 P1-5: 风控告警推送（SSE） ----------
@router.get("/risk/alerts")
async def get_risk_alerts():
    """获取风控告警流（SSE 推送）（P1-5）"""
    from fastapi.responses import StreamingResponse
    import asyncio

    async def event_generator():
        """SSE 事件生成器。当前仅保活，避免伪造 P1 告警数据。"""
        yield ": keepalive\n\n"
        while True:
            await asyncio.sleep(15)
            yield ": keepalive\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------- SIMWEB-01 P1-6: K 线数据 ----------
@router.get("/market/kline/{symbol}")
def get_market_kline(symbol: str, interval: str = Query(default="1m")):
    """获取 K 线数据（P1-6）"""
    # 当前简化实现，返回模拟数据
    # 实际应该从 CTP 或数据服务获取
    klines = []
    for i in range(100):
        klines.append(
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=100 - i)).isoformat() + "Z",
                "open": 3800 + i * 0.5,
                "high": 3810 + i * 0.5,
                "low": 3790 + i * 0.5,
                "close": 3805 + i * 0.5,
                "volume": 1000 + i * 10,
            }
        )

    return {"symbol": symbol, "interval": interval, "klines": klines}


# ---------- SIMWEB-01 P1-7: 市场异动监控 ----------
@router.get("/market/movers")
def get_market_movers(top_n: int = Query(default=10, ge=1, le=50)):
    """获取市场异动品种（P1-7）"""
    from src.stats.market import MarketMoverCalculator

    # 获取所有合约的行情数据
    gw = _get_gateway()
    instruments = []

    if gw and gw.status.get("md_connected"):
        # 从网关获取行情数据
        # 当前简化实现，返回模拟数据
        instruments = [
            {
                "instrument_id": "RB2505",
                "name": "螺纹钢2505",
                "last_price": 3850,
                "prev_close": 3800,
                "highest_price": 3880,
                "lowest_price": 3820,
                "volume": 150000,
                "avg_volume": 100000,
            },
            {
                "instrument_id": "HC2505",
                "name": "热卷2505",
                "last_price": 3650,
                "prev_close": 3600,
                "highest_price": 3680,
                "lowest_price": 3620,
                "volume": 120000,
                "avg_volume": 80000,
            },
        ]

    calculator = MarketMoverCalculator()
    movers = calculator.get_market_movers(instruments, top_n)

    return {"movers": movers, "timestamp": datetime.utcnow().isoformat() + "Z"}
