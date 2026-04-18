"""
SimNow CTP 网关实现（openctp-ctp 6.7.7）
- MdApi: 行情订阅（DepthMarketData）
- TraderApi: 登录 + 结算单确认（实盘下单待 TASK-0016）
线程安全：回调在 CTP 内部线程，状态写入加锁后供 FastAPI 读取
"""
import logging
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("simnow-gateway")

# ---------- 安全导入 ----------
try:
    from openctp_ctp import thostmduserapi as _mdmod
    from openctp_ctp import thosttraderapi as _tdmod
    _CTP_AVAILABLE = True
except ImportError:
    _mdmod = None
    _tdmod = None
    _CTP_AVAILABLE = False
    logger.warning("openctp-ctp not installed, SimNow gateway unavailable")


_FUTURES_PRODUCT_CLASS = getattr(_tdmod, "THOST_FTDC_PC_Futures", "1") if _CTP_AVAILABLE else "1"


def _expand_czce_delivery_year(year_digit: int) -> int:
    from datetime import datetime

    current_yy = datetime.now().year % 100
    base_decade = (current_yy // 10) * 10
    candidates = [
        base_decade - 10 + year_digit,
        base_decade + year_digit,
        base_decade + 10 + year_digit,
    ]
    futureish = [candidate for candidate in candidates if candidate >= current_yy - 1]
    pool = futureish or candidates
    return min(pool, key=lambda candidate: abs(candidate - current_yy))


def _resolve_futures_expiry(
    instrument_id: str,
    delivery_year: Optional[int] = None,
    delivery_month: Optional[int] = None,
) -> Optional[int]:
    try:
        year = int(delivery_year or 0)
        month = int(delivery_month or 0)
    except (TypeError, ValueError):
        year = 0
        month = 0

    if year > 0 and 1 <= month <= 12:
        return (year % 100) * 100 + month

    match = re.fullmatch(r"[A-Za-z]{1,3}(\d{4})", instrument_id)
    if match:
        expiry = int(match.group(1))
        return expiry if 1 <= expiry % 100 <= 12 else None

    match = re.fullmatch(r"[A-Za-z]{1,3}(\d{3})", instrument_id)
    if not match:
        return None

    digits = match.group(1)
    year_digit = int(digits[0])
    month = int(digits[1:])
    if not 1 <= month <= 12:
        return None
    return _expand_czce_delivery_year(year_digit) * 100 + month


def _select_tradeable_contract(
    contracts: List[tuple[str, int]],
    current_yymm: int,
) -> Optional[tuple[str, int]]:
    """优先跳过当前月，避免把近月/交割合约误当作主力交易合约。"""
    if not contracts:
        return None

    ordered = sorted(contracts, key=lambda item: item[1])
    next_month = [item for item in ordered if item[1] > current_yymm]
    if next_month:
        return next_month[0]

    same_or_future = [item for item in ordered if item[1] >= current_yymm]
    if same_or_future:
        return same_or_future[0]

    return ordered[-1]


def is_trading_session(current_dt=None) -> bool:
    """返回当前是否处于交易时段。

    周末完全返回 False；工作日覆盖（SimNow 实际交易时间）：
    - 上午盘：09:00 - 11:30
    - 下午盘：13:00 - 15:00（部分品种 13:30，取最早）
    - 夜盘：  21:00 - 23:00
    """
    from datetime import datetime, time as dtime

    now = current_dt or datetime.now()
    weekday = now.weekday()  # 0=Mon ... 6=Sun
    current_time = now.time()

    # 周末完全静默
    if weekday >= 5:
        return False

    sessions = (
        (dtime(9, 0), dtime(11, 30)),
        (dtime(13, 0), dtime(15, 0)),
        (dtime(21, 0), dtime(23, 0)),
    )
    return any(start <= current_time < end for start, end in sessions)


def _make_md_spi_class():
    base = _mdmod.CThostFtdcMdSpi

    class MdSpi(base):
        def __init__(self, api, on_tick, on_status):
            super().__init__()
            self._api = api
            self._on_tick = on_tick
            self._on_status = on_status

        def OnFrontConnected(self):
            logger.info("[mdapi] connected, login")
            self._on_status("md_connected")
            req = _mdmod.CThostFtdcReqUserLoginField()
            req.BrokerID = self._api._broker_id
            req.UserID = self._api._user_id
            req.Password = self._api._password
            try:
                self._api._md_api.ReqUserLogin(req, 0, 0, "")
            except TypeError:
                self._api._md_api.ReqUserLogin(req, 0)

        def OnFrontDisconnected(self, nReason):
            logger.warning("[mdapi] disconnected reason=%d", nReason)
            self._on_status("md_disconnected")
            self._api._record_disconnect("md", nReason)
            if is_trading_session():
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"CTP 行情前置断开 reason={nReason}", {"event_code": "CTP_FRONT_DISCONNECTED", "source": "simnow_md"})
                except Exception:
                    pass
            else:
                logger.info("[mdapi] suppress disconnect alert outside trading session")
            self._api._schedule_reconnect("md")

        def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
            if pRspInfo and pRspInfo.ErrorID != 0:
                logger.error("[mdapi] login failed: %s", pRspInfo.ErrorMsg)
                self._on_status("md_login_failed")
            else:
                logger.info("[mdapi] login ok day=%s",
                            pRspUserLogin.TradingDay if pRspUserLogin else "?")
                self._on_status("md_logged_in")
                self._api._subscribe_all()

        def OnRtnDepthMarketData(self, d):
            if not d:
                return
            # CTP 对无效字段返回 DBL_MAX，过滤掉避庍显示科学计数法
            _DBLMAX = 1.7976931348623157e+308
            def _safe(v): return None if v is None or v >= _DBLMAX * 0.9 else v
            self._on_tick({
                "symbol":        d.InstrumentID,
                "last":          _safe(d.LastPrice),
                "open":          _safe(d.OpenPrice),
                "high":          _safe(d.HighestPrice),
                "low":           _safe(d.LowestPrice),
                "bid":           _safe(d.BidPrice1),
                "ask":           _safe(d.AskPrice1),
                "bid_vol":       d.BidVolume1,
                "ask_vol":       d.AskVolume1,
                "bid2":          _safe(d.BidPrice2),  "ask2":  _safe(d.AskPrice2),
                "bid_vol2":      d.BidVolume2, "ask_vol2": d.AskVolume2,
                "bid3":          _safe(d.BidPrice3),  "ask3":  _safe(d.AskPrice3),
                "bid_vol3":      d.BidVolume3, "ask_vol3": d.AskVolume3,
                "bid4":          _safe(d.BidPrice4),  "ask4":  _safe(d.AskPrice4),
                "bid_vol4":      d.BidVolume4, "ask_vol4": d.AskVolume4,
                "bid5":          _safe(d.BidPrice5),  "ask5":  _safe(d.AskPrice5),
                "bid_vol5":      d.BidVolume5, "ask_vol5": d.AskVolume5,
                "volume":        d.Volume,
                "turnover":      d.Turnover,
                "open_interest": d.OpenInterest,
                "upper_limit":   _safe(d.UpperLimitPrice),
                "lower_limit":   _safe(d.LowerLimitPrice),
                "prev_close":    _safe(d.PreClosePrice),
                "update_time":   d.UpdateTime,
                "update_ms":     d.UpdateMillisec,
            })

    return MdSpi


def _make_td_spi_class():
    base = _tdmod.CThostFtdcTraderSpi

    class TdSpi(base):
        def __init__(self, api, on_status):
            super().__init__()
            self._api = api
            self._on_status = on_status
            self._req = 0

        def _nxt(self):
            self._req += 1
            return self._req

        def OnFrontConnected(self):
            logger.info("[traderapi] connected, auth")
            self._on_status("td_connected")
            req = _tdmod.CThostFtdcReqAuthenticateField()
            req.BrokerID = self._api._broker_id
            req.UserID = self._api._user_id
            req.AppID = self._api._app_id
            req.AuthCode = self._api._auth_code
            self._api._td_api.ReqAuthenticate(req, self._nxt())

        def OnFrontDisconnected(self, nReason):
            logger.warning("[traderapi] disconnected reason=%d", nReason)
            self._on_status("td_disconnected")
            self._api._record_disconnect("td", nReason)
            if is_trading_session():
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"CTP 交易前置断开 reason={nReason}", {"event_code": "CTP_FRONT_DISCONNECTED", "source": "simnow_td"})
                except Exception:
                    pass
            else:
                logger.info("[traderapi] suppress disconnect alert outside trading session")
            self._api._schedule_reconnect("td")

        def OnRspAuthenticate(self, p, pRspInfo, nRequestID, bIsLast):
            if pRspInfo and pRspInfo.ErrorID != 0:
                logger.error("[traderapi] auth failed: %s", pRspInfo.ErrorMsg)
                self._on_status("td_auth_failed")
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"交易认证失败 {pRspInfo.ErrorMsg}", {"event_code": "CTP_TD_AUTH_FAILED", "stage_preset": "sim"})
                except Exception:
                    pass
                return
            req = _tdmod.CThostFtdcReqUserLoginField()
            req.BrokerID = self._api._broker_id
            req.UserID = self._api._user_id
            req.Password = self._api._password
            nxt = self._nxt()
            try:
                self._api._td_api.ReqUserLogin(req, nxt, 0, "")
            except TypeError:
                self._api._td_api.ReqUserLogin(req, nxt)

        def OnRspUserLogin(self, p, pRspInfo, nRequestID, bIsLast):
            if pRspInfo and pRspInfo.ErrorID != 0:
                logger.error("[traderapi] login failed: %s", pRspInfo.ErrorMsg)
                self._on_status("td_login_failed")
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"交易登录失败 {pRspInfo.ErrorMsg}", {"event_code": "CTP_TD_LOGIN_FAILED", "stage_preset": "sim"})
                except Exception:
                    pass
            else:
                logger.info("[traderapi] login ok")
                self._on_status("td_logged_in")
                # 保存 FrontID/SessionID 用于撤单
                self._api._front_id = getattr(p, "FrontID", 0)
                self._api._session_id = getattr(p, "SessionID", 0)
                req = _tdmod.CThostFtdcSettlementInfoConfirmField()
                req.BrokerID = self._api._broker_id
                req.InvestorID = self._api._user_id
                self._api._td_api.ReqSettlementInfoConfirm(req, self._nxt())

        def OnRspSettlementInfoConfirm(self, p, pRspInfo, nRequestID, bIsLast):
            logger.info("[traderapi] settlement confirmed, ready")
            self._on_status("td_ready")
            # 结算确认后：查账户 + 查可用合约 + 查持仓
            # P1-3 修复：保存 Timer 引用以便后续清理
            import threading
            t1 = threading.Timer(1.0, self._api._query_account)
            t2 = threading.Timer(2.0, self._api._query_instruments)
            t3 = threading.Timer(3.0, self._api._query_positions)
            # 将 Timer 保存到 API 实例以便在 disconnect 时清理
            if not hasattr(self._api, '_active_timers'):
                self._api._active_timers = []
            self._api._active_timers.extend([t1, t2, t3])
            t1.start()
            t2.start()
            t3.start()

        def OnRspQryInstrument(self, p, pRspInfo, nRequestID, bIsLast):
            if p:
                self._api._on_instrument(
                    instrument_id=p.InstrumentID,
                    product_id=p.ProductID.upper(),
                    product_class=getattr(p, "ProductClass", None),
                    delivery_year=getattr(p, "DeliveryYear", None),
                    delivery_month=getattr(p, "DeliveryMonth", None),
                    price_tick=getattr(p, "PriceTick", None),
                    max_order_volume=getattr(p, "MaxLimitOrderVolume", None),
                    volume_multiple=getattr(p, "VolumeMultiple", None),
                    exchange_id=getattr(p, "ExchangeID", None),
                )
            if bIsLast:
                self._api._subscribe_discovered_contracts()
                count = len(self._api._product_to_contract)
                logger.info("[traderapi] instrument query done, %d futures products mapped", count)

        def OnRspQryTradingAccount(self, p, pRspInfo, nRequestID, bIsLast):
            if not p:
                return
            if pRspInfo and pRspInfo.ErrorID != 0:
                logger.error("[traderapi] account query error: %s", pRspInfo.ErrorMsg)
                return
            self._api._on_account({
                "balance":        p.Balance,       # 动态权益
                "available":      p.Available,     # 可用资金
                "margin":         p.CurrMargin,    # 占用保证金
                "floating_pnl":   p.PositionProfit,# 持仓盈亏
                "close_pnl":      p.CloseProfit,   # 平仓盈亏
                "commission":     p.Commission,    # 手续费
                "pre_balance":    p.PreBalance,    # 上次结算准备金（静态权益）
                "deposit":        p.Deposit,       # 入金
                "withdraw":       p.Withdraw,      # 出金
            })
            logger.info("[traderapi] account balance=%.2f pre_balance=%.2f available=%.2f",
                        p.Balance, p.PreBalance, p.Available)

        def OnRtnTrade(self, pTrade):
            if not pTrade:
                return
            trade_data = {
                "instrument_id": pTrade.InstrumentID,
                "order_ref": pTrade.OrderRef,
                "direction": getattr(pTrade, "Direction", ""),
                "offset": getattr(pTrade, "OffsetFlag", ""),
                "price": pTrade.Price,
                "volume": pTrade.Volume,
                "trade_id": pTrade.TradeID.strip(),
                "trade_time": pTrade.TradeTime,
                "exchange_id": pTrade.ExchangeID,
            }
            try:
                from src.ledger.service import get_ledger
                get_ledger().add_trade(trade_data)
            except Exception:
                pass
            logger.info("[traderapi] trade: %s %s@%.2f vol=%d",
                        pTrade.InstrumentID, pTrade.TradeID.strip(), pTrade.Price, pTrade.Volume)
            # 成交通知（交易时段内）
            if is_trading_session():
                direction_str = "买" if getattr(pTrade, "Direction", "") == "0" else "卖"
                offset_str = {"0": "开仓", "1": "平仓", "3": "平今", "4": "平昨"}.get(
                    getattr(pTrade, "OffsetFlag", ""), "未知")
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P2", f"{direction_str}{offset_str} {pTrade.InstrumentID} {pTrade.Volume}手@{pTrade.Price:.2f}",
                               {"event_code": "TRADE_EXECUTED", "source": "simnow_td",
                                "instrument": pTrade.InstrumentID, "trade_id": pTrade.TradeID.strip(),
                                "category": "交易"})
                except Exception:
                    pass

        def OnRtnOrder(self, pOrder):
            if not pOrder:
                return
            order_ref = pOrder.OrderRef.strip()
            status_char = getattr(pOrder, "OrderStatus", "?")
            status_msg = getattr(pOrder, "StatusMsg", "").strip()
            order_info = {
                "instrument_id": pOrder.InstrumentID,
                "order_ref": order_ref,
                "direction": getattr(pOrder, "Direction", ""),
                "offset": getattr(pOrder, "CombOffsetFlag", "")[0:1],
                "price": getattr(pOrder, "LimitPrice", 0),
                "volume_total": getattr(pOrder, "VolumeTotalOriginal", 0),
                "volume_traded": getattr(pOrder, "VolumeTraded", 0),
                "volume_remaining": getattr(pOrder, "VolumeTotal", 0),
                "status": status_char,
                "status_msg": status_msg,
                "order_sys_id": getattr(pOrder, "OrderSysID", "").strip(),
                "exchange_id": getattr(pOrder, "ExchangeID", "").strip(),
                "insert_time": getattr(pOrder, "InsertTime", ""),
                "cancel_time": getattr(pOrder, "CancelTime", ""),
                "front_id": getattr(pOrder, "FrontID", 0),
                "session_id": getattr(pOrder, "SessionID", 0),
            }
            with self._api._lock:
                self._api._orders[order_ref] = order_info
                if status_char == "5" and "拒绝" in status_msg:
                    err = {
                        "source": "exchange_status",
                        "error_id": None,
                        "error_msg": status_msg,
                        "instrument_id": pOrder.InstrumentID,
                        "order_ref": order_ref,
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                    }
                    latest = self._api._order_errors[-1] if self._api._order_errors else None
                    if latest != err:
                        self._api._order_errors.append(err)
                        if len(self._api._order_errors) > 200:
                            self._api._order_errors = self._api._order_errors[-200:]
            logger.info("[traderapi] order update: %s status=%s(%s) ref=%s traded=%d/%d",
                        pOrder.InstrumentID, status_char, status_msg,
                        order_ref, order_info["volume_traded"], order_info["volume_total"])

        def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
            """CTP 前置拒绝下单（资金不足、仓位不足等）"""
            if pRspInfo and pRspInfo.ErrorID != 0:
                err = {
                    "source": "ctp_front",
                    "error_id": pRspInfo.ErrorID,
                    "error_msg": pRspInfo.ErrorMsg,
                    "instrument_id": pInputOrder.InstrumentID if pInputOrder else "",
                    "order_ref": pInputOrder.OrderRef.strip() if pInputOrder else "",
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
                with self._api._lock:
                    self._api._order_errors.append(err)
                    if len(self._api._order_errors) > 200:
                        self._api._order_errors = self._api._order_errors[-200:]
                logger.error("[traderapi] order insert rejected: [%d] %s  instrument=%s",
                             pRspInfo.ErrorID, pRspInfo.ErrorMsg,
                             pInputOrder.InstrumentID if pInputOrder else "?")
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"下单被拒 [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}",
                               {"event_code": "ORDER_REJECTED", "source": "ctp_front",
                                "instrument": pInputOrder.InstrumentID if pInputOrder else ""})
                except Exception:
                    pass

        def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
            """交易所拒绝下单"""
            if pRspInfo and pRspInfo.ErrorID != 0:
                err = {
                    "source": "exchange",
                    "error_id": pRspInfo.ErrorID,
                    "error_msg": pRspInfo.ErrorMsg,
                    "instrument_id": pInputOrder.InstrumentID if pInputOrder else "",
                    "order_ref": pInputOrder.OrderRef.strip() if pInputOrder else "",
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
                with self._api._lock:
                    self._api._order_errors.append(err)
                    if len(self._api._order_errors) > 200:
                        self._api._order_errors = self._api._order_errors[-200:]
                logger.error("[traderapi] exchange rejected order: [%d] %s  instrument=%s",
                             pRspInfo.ErrorID, pRspInfo.ErrorMsg,
                             pInputOrder.InstrumentID if pInputOrder else "?")
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"交易所拒单 [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}",
                               {"event_code": "ORDER_EXCHANGE_REJECTED", "source": "exchange",
                                "instrument": pInputOrder.InstrumentID if pInputOrder else ""})
                except Exception:
                    pass

        def OnRspOrderAction(self, pInputOrderAction, pRspInfo, nRequestID, bIsLast):
            """撤单被拒"""
            if pRspInfo and pRspInfo.ErrorID != 0:
                err = {
                    "source": "ctp_cancel",
                    "error_id": pRspInfo.ErrorID,
                    "error_msg": pRspInfo.ErrorMsg,
                    "instrument_id": pInputOrderAction.InstrumentID if pInputOrderAction else "",
                    "order_ref": getattr(pInputOrderAction, "OrderRef", "").strip() if pInputOrderAction else "",
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
                with self._api._lock:
                    self._api._order_errors.append(err)
                    if len(self._api._order_errors) > 200:
                        self._api._order_errors = self._api._order_errors[-200:]
                logger.error("[traderapi] cancel rejected: [%d] %s", pRspInfo.ErrorID, pRspInfo.ErrorMsg)

        def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
            """交易所拒绝撤单"""
            if pRspInfo and pRspInfo.ErrorID != 0:
                err = {
                    "source": "exchange_cancel",
                    "error_id": pRspInfo.ErrorID,
                    "error_msg": pRspInfo.ErrorMsg,
                    "instrument_id": pOrderAction.InstrumentID if pOrderAction else "",
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                }
                with self._api._lock:
                    self._api._order_errors.append(err)
                    if len(self._api._order_errors) > 200:
                        self._api._order_errors = self._api._order_errors[-200:]
                logger.error("[traderapi] exchange cancel rejected: [%d] %s", pRspInfo.ErrorID, pRspInfo.ErrorMsg)

        def OnRspQryInvestorPosition(self, p, pRspInfo, nRequestID, bIsLast):
            if p and p.InstrumentID:
                self._api._on_position({
                    "instrument_id": p.InstrumentID,
                    "direction": getattr(p, "PosiDirection", ""),
                    "position": p.Position,
                    "today_position": getattr(p, "TodayPosition", 0),
                    "open_cost": getattr(p, "OpenCost", 0),
                    "position_cost": getattr(p, "PositionCost", 0),
                    "floating_pnl": getattr(p, "PositionProfit", 0),
                    "margin": getattr(p, "UseMargin", 0),
                })
            if bIsLast:
                self._api._flush_positions()

        def OnRspError(self, pRspInfo, nRequestID, bIsLast):
            if pRspInfo and pRspInfo.ErrorID != 0:
                logger.error("[traderapi] error: %d %s", pRspInfo.ErrorID, pRspInfo.ErrorMsg)
                try:
                    from src.risk.guards import emit_alert
                    emit_alert("P1", f"CTP 通用错误 [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}",
                               {"event_code": "CTP_RSP_ERROR", "source": "simnow_td"})
                except Exception:
                    pass

    return TdSpi


class SimNowGateway:
    def __init__(self, broker_id, user_id, password, md_front, td_front,
                 instruments=None, app_id="client_jbtsim_1.0.0",
                 auth_code=None):
        # P0-4 修复：移除硬编码的 auth_code，改为必须从环境变量或配置传入
        if auth_code is None:
            raise ValueError("auth_code must be provided (not hardcoded)")

        self._broker_id = broker_id
        self._user_id = user_id
        self._password = password
        self._md_front = md_front
        self._td_front = td_front
        self._app_id = app_id
        self._auth_code = auth_code
        self._instruments = instruments or []
        self._lock = threading.Lock()
        self._ticks: Dict[str, Dict] = {}
        self._md_status = "disconnected"
        self._td_status = "disconnected"
        self._md_api = None
        self._td_api = None
        self._md_spi = None
        self._td_spi = None
        self._last_md_disconnect_reason = None
        self._last_md_disconnect_time = None
        self._last_td_disconnect_reason = None
        self._last_td_disconnect_time = None
        self._account: Dict = {}
        # ── 合约规格缓存（OnRspQryInstrument 填充）──
        # InstrumentID → {price_tick, max_order_volume, volume_multiple, exchange_id, product_id}
        self._instrument_specs: Dict[str, Dict] = {}
        # ── 订单管理 ──
        self._orders: Dict[str, Dict] = {}        # OrderRef → order state
        self._order_errors: List[Dict] = []        # 最近的订单错误（含交易所返回）
        self._order_ref_counter: int = 0
        self._front_id: int = 0
        self._session_id: int = 0
        # product_id.upper() → list of (InstrumentID, expiry_int)
        # e.g. "RB" → [("rb2506", 2506), ("rb2507", 2507), ...]
        self._product_to_contracts: Dict[str, list] = {}
        # product_id.upper() → near-month InstrumentID
        self._product_to_contract: Dict[str, str] = {}
        # actual InstrumentID → product_id.upper() 用于 tick 聚合
        self._contract_to_product: Dict[str, str] = {}
        # 合约发现完成后待订阅列表（在 MD 就绪前缓冲）
        self._pending_subscribe: list = []
        # 持仓查询中间缓冲（CTP 逐条回调，bIsLast 时 flush）
        self._pending_positions: list = []
        self._shutdown = False
        self._reconnect_threads: Dict[str, Optional[threading.Thread]] = {"md": None, "td": None}
        self._announce_order_trace()

    def _order_trace_log_path(self) -> str:
        import sys

        return "C:/temp/order_trace.jsonl" if sys.platform == "win32" else "/tmp/order_trace.jsonl"

    def _announce_order_trace(self) -> None:
        """服务启动时明确记录订单追踪已启用及输出位置。"""
        try:
            import os

            log_file = self._order_trace_log_path()
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            logger.info("[ORDER TRACE] integrated tracing enabled, output=%s", log_file)
        except Exception as exc:
            logger.warning("[ORDER TRACE] tracer bootstrap failed: %s", exc)

    @property
    def status(self):
        with self._lock:
            return {
                "md": self._md_status,
                "td": self._td_status,
                "md_connected": self._md_status == "md_logged_in",
                "td_connected": self._td_status in ("td_ready", "td_logged_in"),
                "last_md_disconnect_reason": self._last_md_disconnect_reason,
                "last_md_disconnect_time": self._last_md_disconnect_time,
                "last_td_disconnect_reason": self._last_td_disconnect_reason,
                "last_td_disconnect_time": self._last_td_disconnect_time,
            }

    def latest_tick(self, symbol):
        with self._lock:
            return self._ticks.get(symbol)

    def _channel_status(self, channel: str) -> str:
        if channel == "md":
            return self._md_status
        return self._td_status

    def _release_channel_api(self, channel: str):
        api_attr = "_md_api" if channel == "md" else "_td_api"
        spi_attr = "_md_spi" if channel == "md" else "_td_spi"
        api = getattr(self, api_attr, None)
        if api is not None:
            try:
                api.Release()
            except Exception as exc:
                logger.warning("[gateway] release %s api failed: %s", channel, exc)
        setattr(self, api_attr, None)
        setattr(self, spi_attr, None)

    def _reconnect_loop(self, channel: str, delay_seconds: float):
        delay = max(delay_seconds, 1.0)
        disconnected_status = f"{channel}_disconnected"
        connect_fn = self._connect_md if channel == "md" else self._connect_td

        try:
            while True:
                time.sleep(delay)
                with self._lock:
                    if self._shutdown:
                        logger.info("[gateway] %s reconnect worker exits: shutdown", channel)
                        return
                    current_status = self._channel_status(channel)

                if current_status != disconnected_status:
                    logger.info("[gateway] %s reconnect worker exits: status=%s", channel, current_status)
                    return

                logger.info("[gateway] %s still disconnected after %.1fs, reconnecting", channel, delay)
                self._release_channel_api(channel)
                try:
                    connect_fn()
                except Exception as exc:
                    logger.warning("[gateway] %s reconnect attempt failed: %s", channel, exc)
                delay = min(delay * 2, 60.0)
        finally:
            with self._lock:
                current = self._reconnect_threads.get(channel)
                if current is threading.current_thread():
                    self._reconnect_threads[channel] = None

    def _schedule_reconnect(self, channel: str, delay_seconds: float = 5.0) -> bool:
        disconnected_status = f"{channel}_disconnected"
        with self._lock:
            if self._shutdown:
                return False
            if self._channel_status(channel) != disconnected_status:
                return False
            worker = self._reconnect_threads.get(channel)
            if worker is not None and worker.is_alive():
                return False
            worker = threading.Thread(
                target=self._reconnect_loop,
                args=(channel, delay_seconds),
                daemon=True,
                name=f"ctp-{channel}-reconnect",
            )
            self._reconnect_threads[channel] = worker
        worker.start()
        return True

    def all_ticks(self):
        with self._lock:
            return dict(self._ticks)

    def _on_tick(self, tick):
        with self._lock:
            instr_id = tick["symbol"]
            self._ticks[instr_id] = tick
            # 同时用产品代码索引，方便前端用 RB/HC 等查询
            product_id = self._contract_to_product.get(instr_id)
            if product_id:
                self._ticks[product_id] = dict(tick, symbol=product_id)

    def _on_md_status(self, s):
        with self._lock:
            self._md_status = s
        logger.info("[gateway] md → %s", s)

    def _on_td_status(self, s):
        with self._lock:
            self._td_status = s
        logger.info("[gateway] td → %s", s)

    def _on_account(self, data: dict):
        with self._lock:
            self._account = data
        try:
            from src.ledger.service import get_ledger
            get_ledger().update_account(data)
        except Exception:
            pass

    def _on_instrument(
        self,
        instrument_id: str,
        product_id: str,
        product_class: Optional[str] = None,
        delivery_year: Optional[int] = None,
        delivery_month: Optional[int] = None,
        price_tick: Optional[float] = None,
        max_order_volume: Optional[int] = None,
        volume_multiple: Optional[int] = None,
        exchange_id: Optional[str] = None,
    ):
        """处理单条合约信息，只保留 futures，并支持郑商所 3 位月份编码。"""
        if product_class != _FUTURES_PRODUCT_CLASS:
            return
        expiry = _resolve_futures_expiry(instrument_id, delivery_year, delivery_month)
        if expiry is None:
            return
        with self._lock:
            lst = self._product_to_contracts.setdefault(product_id, [])
            if any(existing_id == instrument_id for existing_id, _ in lst):
                return
            lst.append((instrument_id, expiry))
            # 存储合约规格
            if price_tick is not None:
                self._instrument_specs[instrument_id] = {
                    "price_tick": float(price_tick),
                    "max_order_volume": int(max_order_volume or 1000),
                    "volume_multiple": int(volume_multiple or 1),
                    "exchange_id": str(exchange_id or ""),
                    "product_id": product_id,
                }

    def _subscribe_discovered_contracts(self):
        """从 _product_to_contracts 中选出可交易合约并订阅 MD。"""
        import datetime
        now = datetime.datetime.now()
        # 当前年月：YYMM格式
        cur_yymm = (now.year % 100) * 100 + now.month

        with self._lock:
            for product_id, contracts in self._product_to_contracts.items():
                preferred = _select_tradeable_contract(contracts, cur_yymm)
                if preferred is None:
                    continue
                self._product_to_contract[product_id] = preferred[0]
                self._contract_to_product[preferred[0]] = product_id

        # 用实际 instruments 过滤出需要的品种
        subscribed_products = set(p.upper() for p in self._instruments)
        to_subscribe = [
            iid for prod, iid in self._product_to_contract.items()
            if prod in subscribed_products
        ]
        to_subscribe = list(dict.fromkeys(to_subscribe))
        # 如果没有发现任何合约（可能非交易时间），fallback 直接用产品代码
        if not to_subscribe:
            logger.warning("[gateway] no contracts discovered, subscribing raw product codes")
            to_subscribe = list(self._instruments)

        if to_subscribe and self._md_api is not None and self._md_status == "md_logged_in":
            instrs = [s.encode() for s in to_subscribe]
            self._md_api.SubscribeMarketData(instrs, len(instrs))
            logger.info("[gateway] subscribed %d tradeable contracts: %s",
                        len(to_subscribe), to_subscribe[:5])
        else:
            logger.info("[gateway] will subscribe %d contracts when MD ready", len(to_subscribe))
            # 存起来，等 MD 登录后触发
            with self._lock:
                self._pending_subscribe = to_subscribe

    def _query_instruments(self):
        """查询 CTP 可用合约列表（td_ready 后调用）。"""
        if self._td_api is None or self._td_status not in ("td_ready", "td_logged_in"):
            return
        try:
            req = _tdmod.CThostFtdcQryInstrumentField()
            self._td_api.ReqQryInstrument(req, 0)
            logger.info("[gateway] querying instruments...")
        except Exception as exc:
            logger.warning("[gateway] _query_instruments failed: %s", exc)

    def _query_account(self):
        """主动查询 CTP 账户余额（td_ready 后 1s 调用，guardian 可重复调用）。"""
        if self._td_api is None or self._td_status not in ("td_ready", "td_logged_in"):
            return
        try:
            req = _tdmod.CThostFtdcQryTradingAccountField()
            req.BrokerID = self._broker_id
            req.InvestorID = self._user_id
            self._td_api.ReqQryTradingAccount(req, 0)
        except Exception as exc:
            logger.warning("[gateway] _query_account failed: %s", exc)

    def query_account(self):
        self._query_account()

    def _on_position(self, data: dict):
        with self._lock:
            self._pending_positions.append(data)

    def _flush_positions(self):
        with self._lock:
            positions = list(self._pending_positions)
            self._pending_positions.clear()
        try:
            from src.ledger.service import get_ledger
            get_ledger().update_positions(positions)
        except Exception:
            pass
        logger.info("[gateway] positions flushed: %d records", len(positions))

    def _query_positions(self):
        if self._td_api is None or self._td_status not in ("td_ready", "td_logged_in"):
            return
        try:
            with self._lock:
                self._pending_positions.clear()
            req = _tdmod.CThostFtdcQryInvestorPositionField()
            req.BrokerID = self._broker_id
            req.InvestorID = self._user_id
            self._td_api.ReqQryInvestorPosition(req, 0)
            logger.info("[gateway] querying positions...")
        except Exception as exc:
            logger.warning("[gateway] _query_positions failed: %s", exc)

    def _record_disconnect(self, channel, reason):
        import time as _time
        with self._lock:
            if channel == "md":
                self._last_md_disconnect_reason = reason
                self._last_md_disconnect_time = _time.time()
            else:
                self._last_td_disconnect_reason = reason
                self._last_td_disconnect_time = _time.time()

    def _subscribe_all(self):
        """MD 登录成功后调用：优先用 _pending_subscribe（已发现近月合约），
        否则 fallback 用 _product_to_contract，再否则用原始品种代码列表。"""
        with self._lock:
            pending = list(getattr(self, '_pending_subscribe', []))
            self._pending_subscribe = []
            discovered = list(self._product_to_contract.values())

        if pending:
            to_sub = pending
        elif discovered:
            to_sub = discovered
        else:
            to_sub = list(self._instruments)  # fallback：原始产品代码

        if not to_sub or self._md_api is None:
            return
        instrs = [s.encode() for s in to_sub]
        self._md_api.SubscribeMarketData(instrs, len(instrs))
        logger.info("[gateway] subscribed %d instruments (near-month=%s)", len(instrs), bool(pending or discovered))

    def connect(self):
        if not _CTP_AVAILABLE:
            raise RuntimeError("openctp-ctp not installed")
        self._connect_md()
        self._connect_td()

    def _connect_md(self):
        with self._lock:
            self._shutdown = False
        import tempfile
        d = tempfile.mkdtemp(prefix="ctp_md_")
        self._md_api = _mdmod.CThostFtdcMdApi.CreateFtdcMdApi(d + "/", False, False, False)
        self._md_spi = _make_md_spi_class()(self, self._on_tick, self._on_md_status)
        self._md_api.RegisterSpi(self._md_spi)
        self._md_api.RegisterFront(self._md_front)
        self._md_api.Init()
        logger.info("[gateway] md Init → %s", self._md_front)

    def _connect_td(self):
        with self._lock:
            self._shutdown = False
        import tempfile
        d = tempfile.mkdtemp(prefix="ctp_td_")
        self._td_api = _tdmod.CThostFtdcTraderApi.CreateFtdcTraderApi(d + "/", False)
        self._td_spi = _make_td_spi_class()(self, self._on_td_status)
        self._td_api.RegisterSpi(self._td_spi)
        self._td_api.RegisterFront(self._td_front)
        self._td_api.SubscribePublicTopic(_tdmod.THOST_TERT_QUICK)
        self._td_api.SubscribePrivateTopic(_tdmod.THOST_TERT_QUICK)
        self._td_api.Init()
        logger.info("[gateway] td Init → %s", self._td_front)

    # ── 下单/撤单核心方法 ──

    def _next_order_ref(self) -> str:
        with self._lock:
            self._order_ref_counter += 1
            return str(self._order_ref_counter)

    def get_instrument_spec(self, instrument_id: str) -> Optional[Dict]:
        """查询合约规格（tick size, max volume 等）"""
        with self._lock:
            return self._instrument_specs.get(instrument_id)

    def get_all_instrument_specs(self) -> Dict[str, Dict]:
        with self._lock:
            return dict(self._instrument_specs)

    def get_orders(self) -> Dict[str, Dict]:
        with self._lock:
            return dict(self._orders)

    def get_order_errors(self) -> List[Dict]:
        with self._lock:
            return list(self._order_errors)

    def _trace_order_source(self, instrument_id: str, direction: str, offset: str,
                            price: float, volume: int):
        """订单追踪：记录调用栈和上下文到日志文件"""
        try:
            import traceback
            import json
            import inspect
            from datetime import datetime

            # 获取调用栈
            stack = traceback.extract_stack()[:-1]  # 排除当前帧

            # 获取调用者的局部变量
            caller_frame = inspect.currentframe().f_back.f_back  # 跳过 insert_order
            caller_locals = {}
            caller_globals = {}

            if caller_frame:
                try:
                    caller_locals = {
                        k: str(v)[:200]
                        for k, v in caller_frame.f_locals.items()
                        if not k.startswith("_") and k not in ["self", "cls"]
                    }
                    caller_globals = {
                        k: str(v)[:200]
                        for k, v in caller_frame.f_globals.items()
                        if k in ["strategy_id", "signal_id", "task_id", "account_id"]
                    }
                except Exception:
                    pass

            # 方向和开平转换
            direction_str = "买" if direction == "0" else "卖"
            offset_str = {"0": "开仓", "1": "平仓", "3": "平今", "4": "平昨"}.get(offset, offset)

            # 构造追踪记录
            trace_record = {
                "timestamp": datetime.now().isoformat(),
                "order": {
                    "instrument_id": instrument_id,
                    "direction": direction,
                    "direction_str": direction_str,
                    "offset": offset,
                    "offset_str": offset_str,
                    "price": price,
                    "volume": volume,
                },
                "caller_context": {
                    "locals": caller_locals,
                    "globals": caller_globals,
                },
                "call_stack": [
                    {
                        "file": frame.filename,
                        "line": frame.lineno,
                        "function": frame.name,
                        "code": frame.line,
                    }
                    for frame in stack
                ],
            }

            # 写入追踪日志
            log_file = self._order_trace_log_path()
            with open(log_file, "a") as f:
                f.write(json.dumps(trace_record, ensure_ascii=False) + "\n")

            # 打印到日志
            logger.info("[ORDER TRACE] %s%s %s %d手@%.2f | 调用栈深度: %d",
                       direction_str, offset_str, instrument_id, volume, price, len(stack))

        except Exception as e:
            logger.warning("[ORDER TRACE] 追踪失败: %s", e)

    def insert_order(self, instrument_id: str, direction: str, offset: str,
                     price: float, volume: int) -> Dict:
        """
        发送限价单到 CTP。
        direction: '0'=买, '1'=卖
        offset: '0'=开仓, '1'=平仓, '3'=平今
        返回 {"order_ref": str, "status": "submitted"} 或 raise
        """
        # 订单追踪：记录调用栈和上下文
        self._trace_order_source(instrument_id, direction, offset, price, volume)

        if self._td_api is None or self._td_status not in ("td_ready", "td_logged_in"):
            raise RuntimeError("交易通道未就绪")

        order_ref = self._next_order_ref()
        req = _tdmod.CThostFtdcInputOrderField()
        req.BrokerID = self._broker_id
        req.InvestorID = self._user_id
        req.InstrumentID = instrument_id
        req.OrderRef = order_ref
        req.UserID = self._user_id
        req.OrderPriceType = _tdmod.THOST_FTDC_OPT_LimitPrice
        req.Direction = direction
        req.CombOffsetFlag = offset
        req.CombHedgeFlag = "1"  # 投机
        req.LimitPrice = price
        req.VolumeTotalOriginal = volume
        req.TimeCondition = _tdmod.THOST_FTDC_TC_GFD
        req.VolumeCondition = _tdmod.THOST_FTDC_VC_AV
        req.MinVolume = 1
        req.ContingentCondition = _tdmod.THOST_FTDC_CC_Immediately
        req.StopPrice = 0.0
        req.ForceCloseReason = _tdmod.THOST_FTDC_FCC_NotForceClose
        req.IsAutoSuspend = 0
        req.IsSwapOrder = 0

        # 初始订单记录
        with self._lock:
            self._orders[order_ref] = {
                "instrument_id": instrument_id,
                "order_ref": order_ref,
                "direction": direction,
                "offset": offset,
                "price": price,
                "volume_total": volume,
                "volume_traded": 0,
                "volume_remaining": volume,
                "status": "submitting",
                "status_msg": "提交中",
                "order_sys_id": "",
                "exchange_id": "",
                "insert_time": "",
                "cancel_time": "",
                "front_id": self._front_id,
                "session_id": self._session_id,
            }

        self._td_api.ReqOrderInsert(req, int(order_ref))
        logger.info("[gateway] order insert: %s %s%s@%.2f vol=%d ref=%s",
                    instrument_id, "买" if direction == "0" else "卖",
                    {"0": "开", "1": "平", "3": "平今"}.get(offset, offset),
                    price, volume, order_ref)
        return {"order_ref": order_ref, "status": "submitted"}

    def cancel_order(self, order_ref: str) -> Dict:
        """撤单。根据 order_ref 查找订单信息后发送撤单请求。"""
        if self._td_api is None or self._td_status not in ("td_ready", "td_logged_in"):
            raise RuntimeError("交易通道未就绪")

        with self._lock:
            order = self._orders.get(order_ref)
        if not order:
            raise ValueError(f"订单 {order_ref} 不存在")

        req = _tdmod.CThostFtdcInputOrderActionField()
        req.BrokerID = self._broker_id
        req.InvestorID = self._user_id
        req.OrderRef = order_ref
        req.FrontID = order.get("front_id", self._front_id)
        req.SessionID = order.get("session_id", self._session_id)
        req.ActionFlag = _tdmod.THOST_FTDC_AF_Delete
        req.InstrumentID = order["instrument_id"]
        if order.get("exchange_id"):
            req.ExchangeID = order["exchange_id"]
        if order.get("order_sys_id"):
            req.OrderSysID = order["order_sys_id"]

        self._td_api.ReqOrderAction(req, int(order_ref))
        logger.info("[gateway] cancel order: ref=%s instrument=%s", order_ref, order["instrument_id"])
        return {"order_ref": order_ref, "status": "cancel_submitted"}

    def disconnect(self):
        with self._lock:
            self._shutdown = True
        # P1-3 修复：取消所有活跃的 Timer 以防止资源泄漏
        if hasattr(self, '_active_timers'):
            for timer in self._active_timers:
                try:
                    timer.cancel()
                except Exception:
                    pass
            self._active_timers.clear()
        for attr in ("_md_api", "_td_api"):
            api = getattr(self, attr, None)
            if api:
                try:
                    api.Release()
                except Exception:
                    pass
                setattr(self, attr, None)
        with self._lock:
            self._md_status = "disconnected"
            self._td_status = "disconnected"
        logger.info("[gateway] disconnected")

    def update_instruments(self, instruments):
        self._instruments = instruments
        if self._md_status == "md_logged_in":
            self._subscribe_all()
