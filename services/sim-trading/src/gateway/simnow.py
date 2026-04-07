"""
SimNow CTP 网关实现（openctp-ctp 6.7.7）
- MdApi: 行情订阅（DepthMarketData）
- TraderApi: 登录 + 结算单确认（实盘下单待 TASK-0016）
线程安全：回调在 CTP 内部线程，状态写入加锁后供 FastAPI 读取
"""
import logging
import threading
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
            self._api._md_api.ReqUserLogin(req, 0)

        def OnFrontDisconnected(self, nReason):
            logger.warning("[mdapi] disconnected reason=%d", nReason)
            self._on_status("md_disconnected")
            self._api._record_disconnect("md", nReason)

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
            self._on_tick({
                "symbol":        d.InstrumentID,
                "last":          d.LastPrice,
                "open":          d.OpenPrice,
                "high":          d.HighestPrice,
                "low":           d.LowestPrice,
                "bid":           d.BidPrice1,
                "ask":           d.AskPrice1,
                "bid_vol":       d.BidVolume1,
                "ask_vol":       d.AskVolume1,
                "bid2":          d.BidPrice2,  "ask2":  d.AskPrice2,
                "bid_vol2":      d.BidVolume2, "ask_vol2": d.AskVolume2,
                "bid3":          d.BidPrice3,  "ask3":  d.AskPrice3,
                "bid_vol3":      d.BidVolume3, "ask_vol3": d.AskVolume3,
                "bid4":          d.BidPrice4,  "ask4":  d.AskPrice4,
                "bid_vol4":      d.BidVolume4, "ask_vol4": d.AskVolume4,
                "bid5":          d.BidPrice5,  "ask5":  d.AskPrice5,
                "bid_vol5":      d.BidVolume5, "ask_vol5": d.AskVolume5,
                "volume":        d.Volume,
                "turnover":      d.Turnover,
                "open_interest": d.OpenInterest,
                "upper_limit":   d.UpperLimitPrice,
                "lower_limit":   d.LowerLimitPrice,
                "prev_close":    d.PreClosePrice,
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
            req.AppID = "simnow_client_test"
            req.AuthCode = "0000000000000000"
            self._api._td_api.ReqAuthenticate(req, self._nxt())

        def OnFrontDisconnected(self, nReason):
            logger.warning("[traderapi] disconnected reason=%d", nReason)
            self._on_status("td_disconnected")
            self._api._record_disconnect("td", nReason)

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
            self._api._td_api.ReqUserLogin(req, self._nxt())

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
                req = _tdmod.CThostFtdcSettlementInfoConfirmField()
                req.BrokerID = self._api._broker_id
                req.InvestorID = self._api._user_id
                self._api._td_api.ReqSettlementInfoConfirm(req, self._nxt())

        def OnRspSettlementInfoConfirm(self, p, pRspInfo, nRequestID, bIsLast):
            logger.info("[traderapi] settlement confirmed, ready")
            self._on_status("td_ready")

    return TdSpi


class SimNowGateway:
    def __init__(self, broker_id, user_id, password, md_front, td_front,
                 instruments=None):
        self._broker_id = broker_id
        self._user_id = user_id
        self._password = password
        self._md_front = md_front
        self._td_front = td_front
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

    def all_ticks(self):
        with self._lock:
            return dict(self._ticks)

    def _on_tick(self, tick):
        with self._lock:
            self._ticks[tick["symbol"]] = tick

    def _on_md_status(self, s):
        with self._lock:
            self._md_status = s
        logger.info("[gateway] md → %s", s)

    def _on_td_status(self, s):
        with self._lock:
            self._td_status = s
        logger.info("[gateway] td → %s", s)

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
        if not self._instruments or self._md_api is None:
            return
        instrs = [s.encode() for s in self._instruments]
        self._md_api.SubscribeMarketData(instrs, len(instrs))
        logger.info("[gateway] subscribed %d instruments", len(instrs))

    def connect(self):
        if not _CTP_AVAILABLE:
            raise RuntimeError("openctp-ctp not installed")
        self._connect_md()
        self._connect_td()

    def _connect_md(self):
        import tempfile
        d = tempfile.mkdtemp(prefix="ctp_md_")
        self._md_api = _mdmod.CThostFtdcMdApi.CreateFtdcMdApi(d + "/")
        self._md_spi = _make_md_spi_class()(self, self._on_tick, self._on_md_status)
        self._md_api.RegisterSpi(self._md_spi)
        self._md_api.RegisterFront(self._md_front)
        self._md_api.Init()
        logger.info("[gateway] md Init → %s", self._md_front)

    def _connect_td(self):
        import tempfile
        d = tempfile.mkdtemp(prefix="ctp_td_")
        self._td_api = _tdmod.CThostFtdcTraderApi.CreateFtdcTraderApi(d + "/")
        self._td_spi = _make_td_spi_class()(self, self._on_td_status)
        self._td_api.RegisterSpi(self._td_spi)
        self._td_api.RegisterFront(self._td_front)
        self._td_api.SubscribePublicTopic(_tdmod.THOST_TERT_QUICK)
        self._td_api.SubscribePrivateTopic(_tdmod.THOST_TERT_QUICK)
        self._td_api.Init()
        logger.info("[gateway] td Init → %s", self._td_front)

    def disconnect(self):
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
