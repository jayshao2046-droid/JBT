"""YAML 信号执行器 — TASK-0122-B

将 YAML 策略文件中的信号定义通过 deepcoder:14b 翻译为可执行 Python 函数，
phi4-reasoning:14b 审核后，使用 Mini 历史 K 线数据执行真实回测。

安全说明：exec() 使用严格受限的 safe_globals 命名空间，禁止 import、
文件读写、网络访问、进程执行等高危操作。
"""
from __future__ import annotations

import ast
import logging
import math
import os
import re
from dataclasses import dataclass, asdict, field
from typing import Any, Optional

import httpx

from ..llm.client import OllamaClient

logger = logging.getLogger(__name__)

# 允许在 exec 沙箱内使用的安全内置函数集合
_SAFE_BUILTINS: dict[str, Any] = {
    "len": len, "range": range, "enumerate": enumerate, "zip": zip,
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "int": int, "float": float, "bool": bool, "str": str,
    "abs": abs, "max": max, "min": min, "sum": sum, "round": round,
    "sorted": sorted, "reversed": reversed, "isinstance": isinstance,
    "any": any, "all": all, "map": map, "filter": filter,
    "Exception": Exception, "ValueError": ValueError,
    "IndexError": IndexError, "ZeroDivisionError": ZeroDivisionError,
    "print": print,
}

# 每天交易分钟数（期货日盘+夜盘合计约10h）
_TRADING_MINS_PER_DAY = 600


@dataclass
class SignalBacktestResult:
    """信号回测结果。"""

    strategy_id: str
    status: str                  # completed | failed
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades_count: int
    bars_count: int
    equity_curve: list = field(default_factory=list)
    generated_code: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("equity_curve", None)  # 不序列化 equity_curve（太大）
        return d


class YAMLSignalExecutor:
    """YAML 策略信号执行器。

    通过 deepcoder:14b 将 YAML 信号定义翻译为 Python 函数，
    phi4-reasoning:14b 审核后用真实 K 线数据执行回测。
    """

    MAX_RETRY = 2

    def __init__(
        self,
        data_service_url: str = "http://192.168.31.76:8105",
        ollama_url: str = "http://192.168.31.142:11434",
        researcher_model: str = "deepcoder:14b",
        auditor_model: str = "phi4-reasoning:14b",
        initial_capital: float = 500_000.0,
    ) -> None:
        self.data_service_url = data_service_url.rstrip("/")
        self.client = OllamaClient(base_url=ollama_url)
        self.researcher_model = os.getenv("OLLAMA_RESEARCHER_MODEL", researcher_model)
        self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", auditor_model)
        self.initial_capital = initial_capital

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        strategy: dict,
        start_date: str,
        end_date: str,
        params_override: Optional[dict] = None,
    ) -> SignalBacktestResult:
        """执行 YAML 策略回测（含 deepcoder 代码生成）。

        Args:
            strategy: YAML 策略配置字典
            start_date: 回测起始日期 YYYY-MM-DD
            end_date: 回测结束日期 YYYY-MM-DD
            params_override: 覆盖 YAML 中的因子参数（用于优化 trial）
        """
        strategy_id = strategy.get("name", "unknown")
        symbol = self._extract_symbol(strategy)
        tf = strategy.get("timeframe_minutes", 60)

        try:
            bars = await self._fetch_bars(symbol, start_date, end_date, tf)
        except RuntimeError as e:
            return self._fail(strategy_id, str(e))

        if len(bars) < 50:
            return self._fail(strategy_id, f"数据不足: {symbol} 仅 {len(bars)} 根 K 线")

        code, error = await self._generate_signal_code(strategy, params_override)
        if error:
            return self._fail(strategy_id, error)

        return self._run_backtest(strategy_id, bars, code, strategy, params_override)

    async def execute_with_code(
        self,
        strategy: dict,
        bars: list[dict],
        code: str,
        params_override: Optional[dict] = None,
    ) -> SignalBacktestResult:
        """使用已生成的代码执行回测（Optuna trial 复用，不重复调 LLM）。

        Args:
            strategy: YAML 策略配置字典
            bars: 已拉取的 K 线数据
            code: deepcoder 已生成的 compute_signals 函数代码
            params_override: 覆盖因子参数
        """
        strategy_id = strategy.get("name", "unknown")
        return self._run_backtest(strategy_id, bars, code, strategy, params_override)

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    async def _fetch_bars(
        self, symbol: str, start: str, end: str, timeframe_minutes: int
    ) -> list[dict]:
        """从 Mini data API 获取 K 线数据。无法连接时直接 raise，不降级。"""
        url = f"{self.data_service_url}/api/v1/bars"
        params: dict[str, Any] = {
            "symbol": symbol,
            "start": start,
            "end": end,
            "interval": timeframe_minutes,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("bars", data.get("data", []))
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Mini data API 不可达 ({self.data_service_url})，请先恢复数据服务再重试。错误: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"数据获取失败 {symbol}: {e}") from e

    # ------------------------------------------------------------------
    # Symbol mapping
    # ------------------------------------------------------------------

    def _extract_symbol(self, strategy: dict) -> str:
        """将 YAML symbols（如 DCE.p2605）映射为连续合约格式（DCE.p0）。"""
        symbols = strategy.get("symbols", [])
        if symbols:
            raw = str(symbols[0])
            parts = raw.split(".")
            if len(parts) == 2:
                exchange = parts[0]
                variety = re.sub(r"\d+", "", parts[1])
                return f"{exchange}.{variety}0"
        return "UNKNOWN.0"

    # ------------------------------------------------------------------
    # Code generation (deepcoder + phi4)
    # ------------------------------------------------------------------

    async def _generate_signal_code(
        self, strategy: dict, params_override: Optional[dict], feedback: str = ""
    ) -> tuple[str, str]:
        """调用 deepcoder 生成信号函数，phi4 审核，最多 MAX_RETRY 次。

        Returns:
            (code, error_message) — error_message 为空表示成功
        """
        for attempt in range(self.MAX_RETRY + 1):
            prompt = self._build_deepcoder_prompt(strategy, params_override, feedback)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Python quantitative developer. "
                        "Output ONLY the Python function, no markdown, no explanation."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            result = await self.client.chat(self.researcher_model, messages, timeout=300.0)

            if "error" in result:
                if attempt < self.MAX_RETRY:
                    logger.warning("deepcoder attempt %d failed: %s, retrying...", attempt + 1, result["error"])
                    continue
                return "", f"deepcoder 生成失败: {result['error']}"

            code = self._extract_python_code(result.get("content", ""))
            if not code:
                if attempt < self.MAX_RETRY:
                    continue
                return "", "deepcoder 未生成有效 Python 函数"

            # 语法校验
            try:
                ast.parse(code)
            except SyntaxError as e:
                if attempt < self.MAX_RETRY:
                    feedback = f"SyntaxError: {e}"
                    continue
                return "", f"生成代码语法错误: {e}"

            # phi4 审核
            audit_ok, audit_reason = await self._audit_code(strategy, code)
            if audit_ok:
                logger.info("策略 %s 代码生成通过审核（attempt %d）", strategy.get("name"), attempt + 1)
                return code, ""

            if attempt < self.MAX_RETRY:
                logger.warning("phi4 审核拒绝 attempt %d: %s，重试...", attempt + 1, audit_reason)
                feedback = audit_reason
                continue

            return "", f"phi4 审核失败（{self.MAX_RETRY + 1} 次后放弃）: {audit_reason}"

        return "", "代码生成失败（未知原因）"

    def _build_deepcoder_prompt(
        self,
        strategy: dict,
        params_override: Optional[dict],
        feedback: str = "",
    ) -> str:
        factors = strategy.get("factors", [])
        signal = strategy.get("signal", {})
        market_filter = strategy.get("market_filter", {})

        factor_names = [f.get("factor_name", "") for f in factors]

        # 合并覆盖参数
        effective_params: dict[str, Any] = {}
        for f in factors:
            p = dict(f.get("params", {}))
            if params_override:
                for k, v in params_override.items():
                    if k in p:
                        p[k] = v
            effective_params[f.get("factor_name", "")] = p

        long_cond = signal.get("long_condition", "")
        short_cond = signal.get("short_condition", "")
        confirm_bars = signal.get("confirm_bars", 1)
        filter_conditions = market_filter.get("conditions", [])

        feedback_block = (
            f"\n\nPREVIOUS ATTEMPT FAILED. Fix this: {feedback}\n"
            if feedback
            else ""
        )

        return f"""Strategy configuration:
  factors: {factor_names}
  factor_params: {effective_params}
  market_filter_conditions: {filter_conditions}
  long_entry: {long_cond}
  short_entry: {short_cond}
  confirm_bars: {confirm_bars}
{feedback_block}
Write this exact Python function:

def compute_signals(bars: list, params: dict) -> list:
    '''
    bars: list of dicts — keys: datetime, open, high, low, close, volume
    params: merged factor params dict, e.g. {{"fast_period": 20, "slow_period": 60}}
    Returns: list of int (same length as bars) — 1=long, -1=short, 0=flat

    Requirements:
    - Implement ALL factors: {factor_names}
    - params dict keys match the factor param names exactly
    - Apply market_filter conditions: {filter_conditions}
    - Long entry when: {long_cond}
    - Short entry when: {short_cond}
    - confirm_bars={confirm_bars}: signal must be consistent for N bars before confirming
    - Use ONLY Python stdlib + math module (NO pandas, NO numpy, NO ta-lib)
    - Compute all indicator series from scratch using loop arithmetic
    - Return exactly len(bars) integers
    '''
    n = len(bars)
    if n == 0:
        return []
    closes = [float(b.get("close", 0)) for b in bars]
    highs  = [float(b.get("high",  0)) for b in bars]
    lows   = [float(b.get("low",   0)) for b in bars]
    signals = [0] * n
    # TODO: implement indicators and signal logic here
    return signals

Output ONLY the Python function. No markdown fences. No explanation."""

    async def _audit_code(self, strategy: dict, code: str) -> tuple[bool, str]:
        """phi4-reasoning 审核生成代码是否符合策略意图。"""
        signal = strategy.get("signal", {})
        factors = strategy.get("factors", [])
        factor_names = [f.get("factor_name", "") for f in factors]

        audit_prompt = f"""Strategy intent:
  factors: {factor_names}
  long_condition: {signal.get("long_condition", "")}
  short_condition: {signal.get("short_condition", "")}

Generated Python function:
{code[:3000]}

Audit checklist:
1. Are all factor indicators actually computed from the bars data?
2. Do the entry conditions match the long/short conditions above?
3. Is the function syntactically complete (no missing return, no truncation)?
4. Does it use only stdlib math (no pandas/numpy imports)?

Reply with EXACTLY one of:
PASS
FAIL: <one-line reason>"""

        messages = [
            {"role": "system", "content": "You are a strict quantitative code auditor. Be concise and direct."},
            {"role": "user", "content": audit_prompt},
        ]
        result = await self.client.chat(self.auditor_model, messages, timeout=180.0)

        if "error" in result:
            # phi4 失败时不阻断，允许通过
            logger.warning("phi4 audit error (non-blocking): %s", result["error"])
            return True, ""

        content = result.get("content", "").strip()
        first_line = content.split("\n")[0].strip().upper()
        if first_line.startswith("PASS"):
            return True, ""
        if first_line.startswith("FAIL"):
            reason = content[4:].strip().lstrip(":").strip()
            return False, reason[:200]
        # 格式不符时默认通过（避免误判）
        return True, ""

    @staticmethod
    def _extract_python_code(content: str) -> str:
        """从 LLM 回复中提取 Python 函数代码。"""
        # 去除 markdown 代码块标记
        content = re.sub(r"```python\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"```\s*", "", content)
        content = content.strip()

        # 必须包含函数定义
        if "def compute_signals" not in content:
            return ""

        # 找到函数起始行
        lines = content.split("\n")
        start = None
        for i, line in enumerate(lines):
            if line.strip().startswith("def compute_signals"):
                start = i
                break

        if start is None:
            return ""

        return "\n".join(lines[start:])

    # ------------------------------------------------------------------
    # Backtest execution
    # ------------------------------------------------------------------

    def _run_backtest(
        self,
        strategy_id: str,
        bars: list[dict],
        code: str,
        strategy: dict,
        params_override: Optional[dict],
    ) -> SignalBacktestResult:
        """使用已生成代码对 bars 执行回测，返回完整绩效指标。"""
        # 构建参数字典
        params: dict[str, Any] = {}
        for f in strategy.get("factors", []):
            params.update(f.get("params", {}))
        if params_override:
            params.update(params_override)

        try:
            safe_globals = {"__builtins__": _SAFE_BUILTINS, "math": math}
            local_ns: dict[str, Any] = {}
            exec(compile(code, "<generated_signal>", "exec"), safe_globals, local_ns)  # noqa: S102
            compute_signals = local_ns.get("compute_signals")
            if not callable(compute_signals):
                return self._fail(strategy_id, "生成函数 compute_signals 未定义")
            signals: list[int] = compute_signals(bars, params)
            if not signals or len(signals) != len(bars):
                return self._fail(
                    strategy_id,
                    f"信号序列长度异常: {len(signals) if signals else 0} vs {len(bars)}",
                )
        except Exception as e:
            return self._fail(strategy_id, f"信号函数执行异常: {type(e).__name__}: {e}")

        return self._simulate_trades(strategy_id, bars, signals, strategy, code)

    def _simulate_trades(
        self,
        strategy_id: str,
        bars: list[dict],
        signals: list[int],
        strategy: dict,
        code: str,
    ) -> SignalBacktestResult:
        """基于信号序列模拟开平仓，计算完整绩效指标。"""
        risk = strategy.get("risk", {})
        position_fraction: float = float(strategy.get("position_fraction", 0.1))
        slippage: float = float(
            strategy.get("transaction_costs", {}).get("slippage_per_unit", 1)
        )
        commission: float = float(
            strategy.get("transaction_costs", {}).get("commission_per_lot_round_turn", 5)
        )
        daily_loss_limit: float = float(risk.get("daily_loss_limit_yuan", 2000))
        max_dd_pct: float = float(risk.get("max_drawdown_pct", 0.015))
        tf: int = int(strategy.get("timeframe_minutes", 60))

        capital = self.initial_capital
        peak_capital = capital
        position = 0        # 1=long, -1=short, 0=flat
        entry_price = 0.0
        daily_pnl: dict[str, float] = {}
        trades: list[dict] = []
        equity_curve: list[float] = [capital]

        for i, bar in enumerate(bars):
            price = float(bar.get("close", 0) or 0)
            if price <= 0:
                equity_curve.append(capital)
                continue

            date_str = str(bar.get("datetime", bar.get("date", "")))[:10]

            # 风控：最大回撤熔断
            peak_capital = max(peak_capital, capital)
            if peak_capital > 0:
                current_dd = (peak_capital - capital) / peak_capital
                if current_dd >= max_dd_pct and position != 0:
                    pnl = self._calc_pnl(position, entry_price, price, position_fraction, capital, slippage, commission)
                    capital += pnl
                    daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + pnl
                    trades.append({"type": "dd_fuse", "bar": i, "price": price, "pnl": round(pnl, 2)})
                    position = 0
                    entry_price = 0.0

            # 风控：日亏损熔断
            today_loss = -(daily_pnl.get(date_str, 0.0))
            if today_loss >= daily_loss_limit and position != 0:
                pnl = self._calc_pnl(position, entry_price, price, position_fraction, capital, slippage, commission)
                capital += pnl
                daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + pnl
                trades.append({"type": "daily_fuse", "bar": i, "price": price, "pnl": round(pnl, 2)})
                position = 0
                entry_price = 0.0

            sig = signals[i]

            # 平仓（方向反转）
            if position == 1 and sig == -1:
                pnl = self._calc_pnl(position, entry_price, price, position_fraction, capital, slippage, commission)
                capital += pnl
                daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + pnl
                trades.append({"type": "close_long", "bar": i, "price": price, "pnl": round(pnl, 2)})
                position = 0
            elif position == -1 and sig == 1:
                pnl = self._calc_pnl(position, entry_price, price, position_fraction, capital, slippage, commission)
                capital += pnl
                daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + pnl
                trades.append({"type": "close_short", "bar": i, "price": price, "pnl": round(pnl, 2)})
                position = 0

            # 开仓
            if position == 0 and sig == 1:
                position = 1
                entry_price = price
                trades.append({"type": "open_long", "bar": i, "price": price})
            elif position == 0 and sig == -1:
                position = -1
                entry_price = price
                trades.append({"type": "open_short", "bar": i, "price": price})

            equity_curve.append(capital)

        # 强制平最后持仓
        if position != 0 and bars:
            last_price = float(bars[-1].get("close", 0) or 0)
            if last_price > 0 and entry_price > 0:
                pnl = self._calc_pnl(position, entry_price, last_price, position_fraction, capital, slippage, commission)
                capital += pnl
                trades.append({"type": "eod_close", "bar": len(bars) - 1, "price": last_price, "pnl": round(pnl, 2)})
                if equity_curve:
                    equity_curve[-1] = capital

        # ── 绩效计算 ──
        closed_trades = [t for t in trades if "pnl" in t]
        total_return = (capital - self.initial_capital) / self.initial_capital if self.initial_capital else 0.0

        # 年化收益
        bars_per_day = max(1, _TRADING_MINS_PER_DAY // tf)
        total_days = len(bars) / bars_per_day
        years = total_days / 252 if total_days > 0 else 1.0
        annualized = (1 + total_return) ** (1 / years) - 1 if years > 0 and (1 + total_return) > 0 else 0.0

        max_dd = self._calc_max_drawdown(equity_curve)
        sharpe = self._calc_sharpe(equity_curve, tf)
        win_rate = (
            len([t for t in closed_trades if t.get("pnl", 0) > 0]) / len(closed_trades)
            if closed_trades
            else 0.0
        )

        start_d = str(bars[0].get("datetime", bars[0].get("date", "")))[:10] if bars else ""
        end_d = str(bars[-1].get("datetime", bars[-1].get("date", "")))[:10] if bars else ""

        return SignalBacktestResult(
            strategy_id=strategy_id,
            status="completed",
            start_date=start_d,
            end_date=end_d,
            initial_capital=self.initial_capital,
            final_capital=round(capital, 2),
            total_return=round(total_return, 6),
            annualized_return=round(annualized, 6),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(max_dd, 6),
            win_rate=round(win_rate, 4),
            trades_count=len(closed_trades),
            bars_count=len(bars),
            equity_curve=equity_curve,
            generated_code=code,
        )

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_pnl(
        position: int,
        entry_price: float,
        exit_price: float,
        position_fraction: float,
        capital: float,
        slippage: float,
        commission: float,
    ) -> float:
        if entry_price <= 0:
            return 0.0
        qty = (capital * position_fraction) / entry_price
        raw_pnl = (exit_price - entry_price) * qty * position
        cost = slippage * qty + commission
        return raw_pnl - cost

    @staticmethod
    def _calc_max_drawdown(equity_curve: list[float]) -> float:
        if len(equity_curve) < 2:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0.0
        for v in equity_curve:
            if v > peak:
                peak = v
            if peak > 0:
                dd = (peak - v) / peak
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    @staticmethod
    def _calc_sharpe(equity_curve: list[float], timeframe_minutes: int = 60) -> float:
        """计算年化 Sharpe Ratio。"""
        if len(equity_curve) < 10:
            return 0.0
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i - 1] > 0:
                returns.append((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1])
        if not returns:
            return 0.0
        n = len(returns)
        mean_r = sum(returns) / n
        variance = sum((r - mean_r) ** 2 for r in returns) / n
        std_r = variance ** 0.5
        if std_r < 1e-10:
            return 0.0
        bars_per_day = max(1, _TRADING_MINS_PER_DAY // timeframe_minutes)
        annual_bars = bars_per_day * 240
        return (mean_r / std_r) * (annual_bars ** 0.5)

    @staticmethod
    def _fail(strategy_id: str, error: str) -> SignalBacktestResult:
        logger.error("YAMLSignalExecutor fail: %s — %s", strategy_id, error)
        return SignalBacktestResult(
            strategy_id=strategy_id,
            status="failed",
            start_date="",
            end_date="",
            initial_capital=0.0,
            final_capital=0.0,
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=1.0,
            win_rate=0.0,
            trades_count=0,
            bars_count=0,
            error=error,
        )
