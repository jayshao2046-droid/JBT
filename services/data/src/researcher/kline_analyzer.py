"""K线技术分析模块 — 盘后从 tushare 拉取日 K 线数据，通过 LLM 生成技术分析研报

触发时机：
- 盘后 16:00 由 scheduler 触发一次（交易日）

功能：
1. 从 tushare fut_daily 拉取主力连续合约日 K 数据（60根）
2. 计算技术指标（MA/RSI/ATR/MACD）
3. 调用 Ollama LLM 生成中文盘后技术分析
4. 返回 KlineAnalysisReport 对象
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import httpx

from .config import ResearcherConfig

logger = logging.getLogger(__name__)

# 品种中文名映射
SYMBOL_CN_NAMES = {
    "rb": "螺纹钢", "hc": "热卷", "cu": "沪铜", "al": "沪铝", "zn": "沪锌",
    "au": "沪金", "ag": "沪银", "ru": "橡胶", "ss": "不锈钢", "sp": "纸浆",
    "i": "铁矿石", "m": "豆粕", "pp": "PP", "v": "PVC", "l": "LLDPE",
    "c": "玉米", "jd": "鸡蛋", "y": "豆油", "p": "棕榈油", "a": "豆一",
    "jm": "焦煤", "j": "焦炭", "eb": "苯乙烯", "pg": "LPG", "lh": "生猪",
    "TA": "PTA", "MA": "甲醇", "CF": "棉花", "SR": "白糖", "OI": "菜油",
    "RM": "菜粕", "FG": "玻璃", "SA": "纯碱", "PF": "涤纶短纤", "UR": "尿素",
}

# 交易所板块分组
SECTOR_MAP = {
    "黑色系": ["rb", "hc", "i", "jm", "j", "ss", "FG", "SA"],
    "有色金属": ["cu", "al", "zn", "au", "ag"],
    "能源化工": ["ru", "sp", "TA", "MA", "v", "l", "pp", "eb", "pg", "PF", "UR"],
    "农产品": ["m", "y", "p", "a", "c", "jd", "CF", "SR", "OI", "RM", "lh"],
}


def _extract_short_symbol(full_symbol: str) -> str:
    """从 KQ.m@SHFE.rb 提取 rb"""
    return full_symbol.rsplit(".", 1)[-1] if "." in full_symbol else full_symbol


def _convert_to_tushare_code(symbol: str) -> Optional[str]:
    """
    KQ.m@SHFE.rb → RB9999.SHF （主力连续合约）
    KQ.m@DCE.i   → I9999.DCE
    KQ.m@CZCE.TA → TA9999.ZCE
    """
    EXCHANGE_MAP = {
        "SHFE": "SHF", "DCE": "DCE", "CZCE": "ZCE",
        "CFFEX": "CFX", "INE": "INE", "GFEX": "GFE",
    }
    try:
        exchange_part, code_part = symbol.split("@")[-1].split(".")
        exchange = EXCHANGE_MAP.get(exchange_part.upper(), exchange_part)
        return f"{code_part.upper()}9999.{exchange}"
    except Exception:
        return None


def _get_sector(short_symbol: str) -> str:
    """获取品种所属板块"""
    for sector, symbols in SECTOR_MAP.items():
        if short_symbol in symbols:
            return sector
    return "其他"


def is_trading_hours() -> bool:
    """判断当前是否在交易时段"""
    now = datetime.now()
    h, m = now.hour, now.minute
    t = h * 60 + m
    # 日盘: 09:00-11:30
    if 540 <= t <= 690:
        return True
    # 日盘: 13:00-15:00
    if 780 <= t <= 900:
        return True
    # 夜盘: 21:00-23:30
    if 1260 <= t <= 1410:
        return True
    return False


def get_trading_session() -> str:
    """获取当前交易时段名称"""
    now = datetime.now()
    h, m = now.hour, now.minute
    t = h * 60 + m
    if 540 <= t <= 690:
        return "morning"
    if 780 <= t <= 900:
        return "afternoon"
    if 1260 <= t <= 1410:
        return "night"
    return "off"


class KlineAnalyzer:
    """K线技术分析引擎"""

    def __init__(self):
        self.data_api = ResearcherConfig.DATA_API_URL
        self.ollama_url = ResearcherConfig.OLLAMA_URL
        self.ollama_model = ResearcherConfig.OLLAMA_MODEL
        self._http: Optional[httpx.AsyncClient] = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    def fetch_daily_kline(self, symbol: str, count: int = 60) -> Optional[List[Dict]]:
        """
        从 tushare 拉取日 K 数据（主力连续合约，盘后使用）

        Args:
            symbol: KQ.m@SHFE.rb 格式
            count: 拉取条数（默认60，约3个月）

        Returns:
            K 线列表 [{datetime, open, high, low, close, volume, open_oi}, ...]
        """
        import tushare as ts
        import time as time_mod

        token = ResearcherConfig.TUSHARE_TOKEN
        if not token:
            logger.warning("[DAILY-KLINE] TUSHARE_TOKEN 未配置")
            return None

        ts_code = _convert_to_tushare_code(symbol)
        if not ts_code:
            logger.warning(f"[DAILY-KLINE] 无法解析 symbol: {symbol}")
            return None

        try:
            from datetime import datetime as dt, timedelta
            pro = ts.pro_api(token)
            end_date = dt.now().strftime("%Y%m%d")
            start_date = (dt.now() - timedelta(days=count * 2)).strftime("%Y%m%d")
            df = pro.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            time_mod.sleep(0.3)  # rate limit
            if df is None or df.empty:
                logger.warning(f"[DAILY-KLINE] {ts_code} tushare 返回空")
                return None
            df = df.sort_values("trade_date").tail(count)
            bars = []
            for _, row in df.iterrows():
                bars.append({
                    "datetime": str(row["trade_date"]),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("vol", 0)),
                    "open_oi": float(row.get("oi", 0)),
                })
            logger.info(f"[DAILY-KLINE] {ts_code} 获取 {len(bars)} 条日K")
            return bars
        except Exception as e:
            logger.warning(f"[DAILY-KLINE] {ts_code} tushare 拉取失败: {e}")
            return None

    def calculate_indicators(self, bars: List[Dict]) -> Dict[str, Any]:
        """计算技术指标"""
        if not bars or len(bars) < 5:
            return {}

        closes = [float(b.get("close", 0)) for b in bars if b.get("close")]
        volumes = [float(b.get("volume", 0)) for b in bars if b.get("volume") is not None]
        highs = [float(b.get("high", 0)) for b in bars if b.get("high")]
        lows = [float(b.get("low", 0)) for b in bars if b.get("low")]

        if len(closes) < 5:
            return {}

        latest = closes[-1]
        prev = closes[-2] if len(closes) >= 2 else latest
        change_pct = ((latest - prev) / prev * 100) if prev != 0 else 0

        # MA
        ma5 = sum(closes[-5:]) / min(5, len(closes)) if len(closes) >= 5 else latest
        ma10 = sum(closes[-10:]) / min(10, len(closes)) if len(closes) >= 10 else latest
        ma20 = sum(closes[-20:]) / min(20, len(closes)) if len(closes) >= 20 else latest

        # RSI (14)
        rsi = self._calc_rsi(closes, 14)

        # ATR (14)
        atr = self._calc_atr(highs, lows, closes, 14)

        # MACD (12, 26, 9)
        macd_line, signal_line, histogram = self._calc_macd(closes)

        # 成交量均值
        vol_avg = sum(volumes[-20:]) / min(20, len(volumes)) if volumes else 0
        vol_latest = volumes[-1] if volumes else 0
        vol_ratio = vol_latest / vol_avg if vol_avg > 0 else 1.0

        # 简单支撑/压力（近期高低点）
        recent_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        recent_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)

        return {
            "latest_price": latest,
            "price_change_pct": round(change_pct, 3),
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "rsi14": round(rsi, 1),
            "atr14": round(atr, 2),
            "macd_line": round(macd_line, 2),
            "macd_signal": round(signal_line, 2),
            "macd_histogram": round(histogram, 2),
            "volume_latest": vol_latest,
            "volume_ratio": round(vol_ratio, 2),
            "recent_high": recent_high,
            "recent_low": recent_low,
            "bars_count": len(closes),
        }

    @staticmethod
    def _calc_rsi(closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _calc_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if len(highs) < period + 1:
            return 0.0
        trs = []
        for i in range(1, len(highs)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
            trs.append(tr)
        return sum(trs[-period:]) / min(period, len(trs))

    @staticmethod
    def _calc_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        if len(closes) < slow:
            return 0.0, 0.0, 0.0

        def ema(data, n):
            k = 2 / (n + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append(data[i] * k + result[-1] * (1 - k))
            return result

        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = ema(macd_line, signal)
        hist = macd_line[-1] - signal_line[-1]
        return macd_line[-1], signal_line[-1], hist

    async def analyze_symbol(self, symbol: str, related_news: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        分析单个品种：拉取 K 线 → 计算指标 → LLM 生成分析

        Returns:
            KlineAnalysisReport 风格的字典
        """
        short = _extract_short_symbol(symbol)
        cn_name = SYMBOL_CN_NAMES.get(short, short)
        sector = _get_sector(short)

        # 拉取日 K（tushare，同步方法用 executor 避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        bars = await loop.run_in_executor(None, self.fetch_daily_kline, symbol, ResearcherConfig.DAILY_KLINE_COUNT)

        if not bars:
            logger.info(f"[KLINE] {symbol} ({cn_name}) 无K线数据，跳过")
            return None

        # 计算指标
        indicators = self.calculate_indicators(bars)
        if not indicators:
            return None

        # 构建 LLM prompt
        news_context = ""
        if related_news:
            news_items = "\n".join([f"- {n}" for n in related_news[:5]])
            news_context = f"\n相关新闻：\n{news_items}"

        prompt = f"""你是期货技术分析师。请对 {cn_name}({short}) 进行盘后日线技术面分析，板块：{sector}，基于近{ResearcherConfig.DAILY_KLINE_COUNT}根日K数据。

技术指标：
- 最新价：{indicators['latest_price']}，涨跌幅：{indicators['price_change_pct']}%
- MA5={indicators['ma5']}，MA10={indicators['ma10']}，MA20={indicators['ma20']}
- RSI(14)={indicators['rsi14']}
- ATR(14)={indicators['atr14']}
- MACD线={indicators['macd_line']}，信号线={indicators['macd_signal']}，柱={indicators['macd_histogram']}
- 量比={indicators['volume_ratio']}
- 近期高点={indicators['recent_high']}，低点={indicators['recent_low']}
{news_context}

请用JSON格式回复：
{{"trend":"偏多/偏空/震荡/观望","confidence":0.0-1.0,"analysis":"技术分析(100字内)","support":[价位],"resistance":[价位],"risk":"风险提示(50字内)"}}"""

        # 调用 Ollama
        analysis = await self._call_ollama(prompt)
        if not analysis:
            analysis = {
                "trend": "观望",
                "confidence": 0.3,
                "analysis": f"{cn_name}数据不足，暂无明确方向",
                "support": [indicators.get("recent_low", 0)],
                "resistance": [indicators.get("recent_high", 0)],
                "risk": "LLM分析超时，仅供参考",
            }

        now = datetime.now()
        return {
            "report_id": f"KLINE-{now.strftime('%Y%m%d-%H%M')}-{short}",
            "symbol": symbol,
            "symbol_name": cn_name,
            "sector": sector,
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.isoformat(),
            "timeframe": "1d",
            "bars_count": indicators.get("bars_count", 0),
            "latest_price": indicators["latest_price"],
            "price_change_pct": indicators["price_change_pct"],
            "volume": indicators.get("volume_latest", 0),
            "ma5": indicators["ma5"],
            "ma10": indicators.get("ma10", 0),
            "ma20": indicators["ma20"],
            "rsi14": indicators["rsi14"],
            "atr14": indicators["atr14"],
            "macd": {
                "line": indicators["macd_line"],
                "signal": indicators["macd_signal"],
                "histogram": indicators["macd_histogram"],
            },
            "volume_ratio": indicators["volume_ratio"],
            "trend": analysis.get("trend", "观望"),
            "confidence": analysis.get("confidence", 0.3),
            "analysis": analysis.get("analysis", ""),
            "support_levels": analysis.get("support", []),
            "resistance_levels": analysis.get("resistance", []),
            "risk_note": analysis.get("risk", ""),
            "related_news": related_news[:5] if related_news else [],
        }

    async def analyze_batch(self, symbols: List[str], related_news_map: Dict[str, List[str]] = None) -> List[Dict]:
        """批量分析多个品种（串行，避免 LLM 过载）"""
        results = []
        total = len(symbols)
        for idx, symbol in enumerate(symbols, 1):
            short = _extract_short_symbol(symbol)
            news = (related_news_map or {}).get(short, [])
            logger.info(f"[KLINE] 分析 {idx}/{total}: {short}")
            try:
                result = await self.analyze_symbol(symbol, related_news=news)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"[KLINE] {symbol} 分析异常: {e}")
            # 避免 LLM 过载
            await asyncio.sleep(1)
        return results

    async def _call_ollama(self, prompt: str) -> Optional[Dict]:
        """调用 Ollama LLM"""
        try:
            http = await self._get_http()
            resp = await http.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": 4096,
                    },
                },
                timeout=90.0,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                # 移除 <think>...</think> 块
                if "<think>" in text and "</think>" in text:
                    text = text[text.index("</think>") + len("</think>"):]
                text = text.strip()
                # 尝试提取 JSON
                if "{" in text:
                    json_str = text[text.index("{"):text.rindex("}") + 1]
                    return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("[KLINE] LLM 返回无法解析为 JSON")
        except Exception as e:
            logger.warning(f"[KLINE] Ollama 调用失败: {e}")
        return None

    async def generate_sector_summary(self, reports: List[Dict]) -> Dict[str, str]:
        """按板块汇总分析结果"""
        sector_groups: Dict[str, List[Dict]] = {}
        for r in reports:
            sector = r.get("sector", "其他")
            sector_groups.setdefault(sector, []).append(r)

        summaries = {}
        for sector, items in sector_groups.items():
            bullish = sum(1 for i in items if i.get("trend") == "偏多")
            bearish = sum(1 for i in items if i.get("trend") == "偏空")
            neutral = len(items) - bullish - bearish
            symbols_str = ", ".join([f"{i['symbol_name']}({i['trend']})" for i in items])
            summaries[sector] = (
                f"{sector}板块：共{len(items)}个品种，"
                f"偏多{bullish}、偏空{bearish}、震荡/观望{neutral}。"
                f"详情：{symbols_str}"
            )
        return summaries
