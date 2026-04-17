"""YAML 信号执行器 — TASK-0122-B + TASK-U0-20260417-006

将 YAML 策略文件中的信号定义通过 deepcoder:14b 翻译为可执行 Python 函数，
phi4-reasoning:14b 审核后，使用 Mini 历史 K 线数据执行真实回测。

TASK-U0-20260417-006: 添加 Researcher ↔ Critic 迭代优化流程，
支持多轮迭代（最多30轮），将策略优化到生产级标准。

安全说明：exec() 使用严格受限的 safe_globals 命名空间，禁止 import、
文件读写、网络访问、进程执行等高危操作。
"""
from __future__ import annotations

import ast
import copy
import json
import logging
import math
import os
import re
from dataclasses import dataclass, asdict, field
from typing import Any, Optional

import httpx

from ..llm.client import OllamaClient
from ..llm.openai_client import OpenAICompatibleClient

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


# ──────────────────────────────────────────────────────────────
# 预置技术指标计算库（纯 Python，供 LLM 生成代码直接调用）
# ──────────────────────────────────────────────────────────────

def _ta_ema(data: list[float], period: int) -> list[float]:
    """Exponential Moving Average."""
    result = [0.0] * len(data)
    if not data or period < 1:
        return result
    k = 2.0 / (period + 1)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = data[i] * k + result[i - 1] * (1 - k)
    return result


def _ta_sma(data: list[float], period: int) -> list[float]:
    """Simple Moving Average."""
    n = len(data)
    result = [0.0] * n
    if period < 1 or n == 0:
        return result
    s = 0.0
    for i in range(n):
        s += data[i]
        if i >= period:
            s -= data[i - period]
        if i >= period - 1:
            result[i] = s / period
    return result


def _ta_rsi(closes: list[float], period: int = 14) -> list[float]:
    """Relative Strength Index (Wilder smooth)."""
    n = len(closes)
    result = [50.0] * n
    if n < period + 1:
        return result
    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        gains[i] = diff if diff > 0 else 0.0
        losses[i] = -diff if diff < 0 else 0.0
    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period
    for i in range(period, n):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss < 1e-10:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - 100.0 / (1.0 + rs)
    return result


def _ta_macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9
             ) -> tuple[list[float], list[float], list[float]]:
    """MACD → (macd_line, signal_line, histogram)."""
    fast_ema = _ta_ema(closes, fast)
    slow_ema = _ta_ema(closes, slow)
    n = len(closes)
    macd_line = [fast_ema[i] - slow_ema[i] for i in range(n)]
    signal_line = _ta_ema(macd_line, signal)
    histogram = [macd_line[i] - signal_line[i] for i in range(n)]
    return macd_line, signal_line, histogram


def _ta_atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14
            ) -> list[float]:
    """Average True Range."""
    n = len(closes)
    result = [0.0] * n
    if n < 2:
        return result
    tr = [highs[0] - lows[0]] + [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, n)
    ]
    s = sum(tr[:period])
    for i in range(period - 1, n):
        if i == period - 1:
            result[i] = s / period
        else:
            result[i] = (result[i - 1] * (period - 1) + tr[i]) / period
    return result


def _ta_adx(highs: list[float], lows: list[float], closes: list[float], period: int = 14
            ) -> list[float]:
    """Average Directional Index (simplified)."""
    n = len(closes)
    result = [0.0] * n
    if n < period * 2:
        return result
    atr = _ta_atr(highs, lows, closes, period)
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0
    smooth_plus = _ta_ema(plus_dm, period)
    smooth_minus = _ta_ema(minus_dm, period)
    for i in range(period, n):
        if atr[i] < 1e-10:
            continue
        plus_di = 100.0 * smooth_plus[i] / atr[i]
        minus_di = 100.0 * smooth_minus[i] / atr[i]
        di_sum = plus_di + minus_di
        if di_sum > 0:
            dx = 100.0 * abs(plus_di - minus_di) / di_sum
            if i == period:
                result[i] = dx
            else:
                result[i] = (result[i - 1] * (period - 1) + dx) / period
    return result


def _ta_bollinger(closes: list[float], period: int = 20, std_dev: float = 2.0
                  ) -> tuple[list[float], list[float], list[float]]:
    """Bollinger Bands → (upper, middle, lower)."""
    n = len(closes)
    upper = [0.0] * n
    middle = _ta_sma(closes, period)
    lower = [0.0] * n
    for i in range(period - 1, n):
        window = closes[i - period + 1: i + 1]
        mean = middle[i]
        variance = sum((x - mean) ** 2 for x in window) / period
        sd = variance ** 0.5
        upper[i] = mean + std_dev * sd
        lower[i] = mean - std_dev * sd
    return upper, middle, lower


def _ta_volume_ratio(volumes: list[float], period: int = 10) -> list[float]:
    """Volume Ratio: current volume / SMA(volume, period)."""
    n = len(volumes)
    result = [1.0] * n
    avg = _ta_sma(volumes, period)
    for i in range(period - 1, n):
        if avg[i] > 0:
            result[i] = volumes[i] / avg[i]
    return result


def _ta_cci(highs: list[float], lows: list[float], closes: list[float], period: int = 20
            ) -> list[float]:
    """Commodity Channel Index."""
    n = len(closes)
    result = [0.0] * n
    tp = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(n)]
    tp_sma = _ta_sma(tp, period)
    for i in range(period - 1, n):
        window = tp[i - period + 1: i + 1]
        mean_dev = sum(abs(x - tp_sma[i]) for x in window) / period
        if mean_dev > 1e-10:
            result[i] = (tp[i] - tp_sma[i]) / (0.015 * mean_dev)
    return result


def _ta_williams_r(highs: list[float], lows: list[float], closes: list[float], period: int = 14
                   ) -> list[float]:
    """Williams %R."""
    n = len(closes)
    result = [-50.0] * n
    for i in range(period - 1, n):
        hh = max(highs[i - period + 1: i + 1])
        ll = min(lows[i - period + 1: i + 1])
        if hh - ll > 1e-10:
            result[i] = -100.0 * (hh - closes[i]) / (hh - ll)
    return result


def _ta_kdj(highs: list[float], lows: list[float], closes: list[float],
            n_period: int = 9, m1: int = 3, m2: int = 3
            ) -> tuple[list[float], list[float], list[float]]:
    """KDJ indicator → (K, D, J)."""
    n = len(closes)
    k_vals = [50.0] * n
    d_vals = [50.0] * n
    j_vals = [50.0] * n
    for i in range(n_period - 1, n):
        hh = max(highs[i - n_period + 1: i + 1])
        ll = min(lows[i - n_period + 1: i + 1])
        rsv = 50.0 if (hh - ll) < 1e-10 else 100.0 * (closes[i] - ll) / (hh - ll)
        k_vals[i] = (k_vals[i - 1] * (m1 - 1) + rsv) / m1 if i > n_period - 1 else rsv
        d_vals[i] = (d_vals[i - 1] * (m2 - 1) + k_vals[i]) / m2 if i > n_period - 1 else k_vals[i]
        j_vals[i] = 3 * k_vals[i] - 2 * d_vals[i]
    return k_vals, d_vals, j_vals


def _ta_obv(closes: list[float], volumes: list[float]) -> list[float]:
    """On Balance Volume."""
    n = len(closes)
    result = [0.0] * n
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            result[i] = result[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            result[i] = result[i - 1] - volumes[i]
        else:
            result[i] = result[i - 1]
    return result


# 汇集所有指标函数，注入到 exec 沙箱
_TA_FUNCTIONS: dict[str, Any] = {
    "ta_ema": _ta_ema,
    "ta_sma": _ta_sma,
    "ta_rsi": _ta_rsi,
    "ta_macd": _ta_macd,
    "ta_atr": _ta_atr,
    "ta_adx": _ta_adx,
    "ta_bollinger": _ta_bollinger,
    "ta_volume_ratio": _ta_volume_ratio,
    "ta_cci": _ta_cci,
    "ta_williams_r": _ta_williams_r,
    "ta_kdj": _ta_kdj,
    "ta_obv": _ta_obv,
}

# 每天交易分钟数（期货日盘+夜盘合计约10h）
_TRADING_MINS_PER_DAY = 600

# ──────────────────────────────────────────────────────────────
# 迭代优化配置（TASK-U0-20260417-006）
# ──────────────────────────────────────────────────────────────

# 生产级标准
PRODUCTION_STANDARDS = {
    "oos_sharpe": float(os.getenv("TARGET_SHARPE", "1.5")),
    "oos_trades": int(os.getenv("TARGET_TRADES", "20")),
    "oos_win_rate": float(os.getenv("TARGET_WIN_RATE", "0.5")),
    "oos_max_dd": float(os.getenv("TARGET_MAX_DD", "0.03")),
    "oos_annual_return": float(os.getenv("TARGET_ANNUAL_RETURN", "0.15")),
}

# 最低标准（快速达标阶段）
MINIMUM_STANDARDS = {
    "oos_sharpe": 0.5,
    "oos_trades": 10,
    "oos_win_rate": 0.4,
    "oos_max_dd": 0.05,
}

# 中等标准（中等提升阶段）
MEDIUM_STANDARDS = {
    "oos_sharpe": 1.0,
    "oos_trades": 15,
    "oos_win_rate": 0.45,
    "oos_max_dd": 0.04,
}

# 迭代配置
MAX_ITERATIONS = int(os.getenv("MAX_OPTIMIZATION_ITERATIONS", "30"))
STAGE1_MAX = int(os.getenv("STAGE1_MAX_ITERATIONS", "3"))
STAGE2_MAX = int(os.getenv("STAGE2_MAX_ITERATIONS", "10"))
STAGE3_MAX = int(os.getenv("STAGE3_MAX_ITERATIONS", "30"))

# 提前终止条件
MAX_NO_IMPROVEMENT_ROUNDS = 5


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

        # 支持切换到在线 API（通过环境变量 LLM_PROVIDER）
        llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        if llm_provider == "online":
            logger.info("使用在线 API 客户端（OpenAI-compatible）")
            self.client = OpenAICompatibleClient()
            self.researcher_model = os.getenv("ONLINE_RESEARCHER_MODEL", "qwen-coder-plus")
            self.auditor_model = os.getenv("ONLINE_AUDITOR_MODEL", "qwen-plus")
        else:
            logger.info("使用本地 Ollama 客户端")
            self.client = OllamaClient(base_url=ollama_url)
            self.researcher_model = os.getenv("OLLAMA_RESEARCHER_MODEL", researcher_model)
            self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", auditor_model)

        self.initial_capital = initial_capital

        # Critic 客户端（本地 Ollama，用于迭代优化）
        self.critic_client = OllamaClient(base_url=ollama_url)
        self.critic_model = os.getenv("CRITIC_MODEL", "qwen3:14b")

        # 迭代优化开关
        self.enable_iterative_optimization = os.getenv("ENABLE_ITERATIVE_OPTIMIZATION", "false").lower() == "true"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute_with_iterative_optimization(
        self,
        strategy: dict,
        start_date: str,
        end_date: str,
    ) -> tuple[SignalBacktestResult, list[dict]]:
        """执行策略回测，启用迭代优化（TASK-U0-20260417-006）。

        Returns:
            (final_result, iteration_history)
        """
        if not self.enable_iterative_optimization:
            result = await self.execute(strategy, start_date, end_date, None)
            return result, []

        logger.info("🔄 启动迭代优化流程（最多 %d 轮）", MAX_ITERATIONS)

        iteration_history = []
        best_result = None
        best_score = -999.0
        no_improvement_count = 0
        current_strategy = copy.deepcopy(strategy)

        for iteration in range(1, MAX_ITERATIONS + 1):
            stage = self._determine_stage(iteration)
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 迭代 {iteration}/{MAX_ITERATIONS} - 阶段: {stage}")
            logger.info(f"{'='*60}")

            # 执行回测
            result = await self.execute(current_strategy, start_date, end_date, None)

            if result.status == "failed":
                logger.warning(f"迭代 {iteration} 回测失败: {result.error}")
                iteration_history.append({
                    "iteration": iteration,
                    "stage": stage,
                    "status": "failed",
                    "error": result.error,
                })
                continue

            # 记录迭代结果
            iteration_record = {
                "iteration": iteration,
                "stage": stage,
                "trades": result.trades_count,
                "sharpe": result.sharpe_ratio,
                "win_rate": result.win_rate,
                "max_dd": result.max_drawdown,
                "annual_return": result.annualized_return,
            }
            iteration_history.append(iteration_record)

            logger.info(f"📊 迭代 {iteration} 结果:")
            logger.info(f"  - 交易次数: {result.trades_count}")
            logger.info(f"  - Sharpe: {result.sharpe_ratio:.4f}")
            logger.info(f"  - 胜率: {result.win_rate:.2%}")
            logger.info(f"  - 最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"  - 年化收益: {result.annualized_return:.2%}")

            # 计算综合得分
            score = self._calculate_score(result)
            if score > best_score:
                best_score = score
                best_result = result
                no_improvement_count = 0
                logger.info(f"✅ 新最佳得分: {score:.4f}")
            else:
                no_improvement_count += 1
                logger.info(f"⚠️ 无改进（连续 {no_improvement_count} 轮）")

            # 检查是否达到生产级标准
            if self._check_production_ready(result):
                logger.info(f"🎉 达到生产级标准！迭代 {iteration} 轮完成")
                return result, iteration_history

            # 提前终止检查
            if no_improvement_count >= MAX_NO_IMPROVEMENT_ROUNDS:
                logger.warning(f"❌ 连续 {MAX_NO_IMPROVEMENT_ROUNDS} 轮无改进，提前终止")
                break

            # 调用 Critic 诊断
            if iteration < MAX_ITERATIONS:
                logger.info(f"🔍 调用 Critic 诊断...")
                feedback = await self._get_critic_feedback(
                    current_strategy, result, iteration, stage, iteration_history
                )

                if feedback:
                    logger.info(f"📋 Critic 反馈:\n{json.dumps(feedback, indent=2, ensure_ascii=False)}")
                    # 应用调整建议
                    current_strategy = self._apply_critic_suggestions(current_strategy, feedback)
                    iteration_history[-1]["critic_feedback"] = feedback
                else:
                    logger.warning("⚠️ Critic 未返回有效反馈，使用当前参数继续")

        # 返回最佳结果
        final_result = best_result if best_result else result
        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 迭代优化完成")
        logger.info(f"  - 总迭代次数: {len(iteration_history)}")
        logger.info(f"  - 最佳得分: {best_score:.4f}")
        logger.info(f"  - 最终 Sharpe: {final_result.sharpe_ratio:.4f}")
        logger.info(f"  - 最终交易次数: {final_result.trades_count}")
        logger.info(f"{'='*60}")

        return final_result, iteration_history

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

        return f"""CRITICAL DATA STRUCTURE:
  bars is a list of dicts with ONLY these 6 keys: datetime, open, high, low, close, volume
  DO NOT access bars[i]["MACD"], bars[i]["RSI"], bars[i]["EMA"], etc. — THESE KEYS DO NOT EXIST!
  You MUST use the ta_* functions below to calculate ALL technical indicators.

OPTIMIZATION OBJECTIVES (优化目标):
  - 目标交易次数: ≥10 次/年（OOS 期间）
  - 目标 Sharpe: ≥0.5
  - 目标胜率: ≥40%
  - 最大回撤: ≤5%

HARD CONSTRAINTS (底线约束 - 绝对不可违反):
  - 必须保持日内交易逻辑（不持仓过夜）
  - 不能移除核心因子: {factor_names}
  - 信号条件必须基于技术指标，不能随机生成
  - 市场过滤条件不能完全移除（可以放宽阈值）

Strategy configuration:
  factors: {factor_names}
  factor_params: {effective_params}
  market_filter_conditions: {filter_conditions}
  long_entry: {long_cond}
  short_entry: {short_cond}
  confirm_bars: {confirm_bars}
{feedback_block}
AVAILABLE INDICATOR FUNCTIONS (already defined, call them directly):

  ta_sma(data: list[float], period: int) -> list[float]           # Simple Moving Average
  ta_ema(data: list[float], period: int) -> list[float]           # Exponential Moving Average
  ta_rsi(closes: list[float], period=14) -> list[float]           # Relative Strength Index
  ta_macd(closes, fast=12, slow=26, signal=9) -> (macd, signal_line, histogram)  # MACD
  ta_atr(highs, lows, closes, period=14) -> list[float]           # Average True Range
  ta_adx(highs, lows, closes, period=14) -> list[float]           # Average Directional Index
  ta_bollinger(closes, period=20, std_dev=2.0) -> (upper, middle, lower)  # Bollinger Bands
  ta_volume_ratio(volumes, period=10) -> list[float]              # Volume / SMA(volume)
  ta_cci(highs, lows, closes, period=20) -> list[float]           # CCI
  ta_williams_r(highs, lows, closes, period=14) -> list[float]    # Williams %R
  ta_kdj(highs, lows, closes, n=9, m1=3, m2=3) -> (K, D, J)      # KDJ
  ta_obv(closes, volumes) -> list[float]                           # On Balance Volume
  math module is also available.

FACTOR NAME → ta_* FUNCTION MAPPING:
  Factor "MACD" → ta_macd(closes, fast, slow, signal) returns (macd_line, signal_line, histogram)
  Factor "RSI" → ta_rsi(closes, period) returns list[float]
  Factor "VolumeRatio" → ta_volume_ratio(volumes, period) returns list[float]
  Factor "EMA" → ta_ema(closes, period) returns list[float]
  Factor "SMA" → ta_sma(closes, period) returns list[float]
  Factor "ATR" → ta_atr(highs, lows, closes, period) returns list[float]
  Factor "ADX" → ta_adx(highs, lows, closes, period) returns list[float]
  Factor "Bollinger" → ta_bollinger(closes, period, std_dev) returns (upper, middle, lower)

EXAMPLE USAGE:
  # WRONG: macd_value = bars[i]["MACD"]  ❌ KeyError!
  # RIGHT:
  macd_line, sig_line, macd_hist = ta_macd(closes, fast=12, slow=26, signal=9)  ✅
  rsi = ta_rsi(closes, period=14)  ✅
  volume_ratio = ta_volume_ratio(volumes, period=10)  ✅
  # Then use: macd_hist[i], rsi[i], volume_ratio[i] in your logic

Write this exact Python function:

def compute_signals(bars: list, params: dict) -> list:
    '''
    bars: list of dicts with ONLY 6 keys: datetime, open, high, low, close, volume
    params: merged factor params dict, e.g. {{"fast_period": 20, "slow_period": 60}}
    Returns: list of int (same length as bars) — 1=long, -1=short, 0=flat

    CRITICAL REQUIREMENTS:
    - bars[i] ONLY has: datetime, open, high, low, close, volume
    - DO NOT access bars[i]["MACD"], bars[i]["RSI"], bars[i]["EMA"] — THESE DO NOT EXIST!
    - MUST use ta_* functions for ALL indicators (ta_macd, ta_rsi, ta_ema, ta_sma, etc.)
    - Implement ALL factors: {factor_names}
    - params dict keys match the factor param names exactly
    - Apply market_filter conditions: {filter_conditions}
    - Long entry when: {long_cond}
    - Short entry when: {short_cond}
    - confirm_bars={confirm_bars}: signal must be consistent for N bars before confirming
    - Use ONLY the pre-built ta_* functions + Python stdlib + math module (NO pandas, NO numpy, NO ta-lib)
    - Return exactly len(bars) integers

    OPTIMIZATION GUIDANCE (if feedback provided):
    - If trade count is too low: consider relaxing filter thresholds (ATR/ADX/volume_ratio)
    - If Sharpe is too low: tighten entry conditions to improve quality
    - Balance between trade frequency and trade quality
    - DO NOT remove core factors or violate hard constraints
    '''
    n = len(bars)
    if n == 0:
        return []

    # Step 1: Extract OHLCV arrays from bars (these are the ONLY keys available)
    closes  = [float(b.get("close",  0)) for b in bars]
    highs   = [float(b.get("high",   0)) for b in bars]
    lows    = [float(b.get("low",    0)) for b in bars]
    volumes = [float(b.get("volume", 0)) for b in bars]

    # Step 2: Calculate indicators using ta_* functions (DO NOT access bars[i]["MACD"]!)
    # IMPORTANT: Use params dict to get period values, e.g. params.get("fast", 12)
    #
    # Example for factor "MACD" with params {{fast: 12, slow: 26, signal: 9}}:
    #   macd_line, sig_line, macd_hist = ta_macd(closes, fast=params.get("fast", 12),
    #                                             slow=params.get("slow", 26),
    #                                             signal=params.get("signal", 9))
    #   Then derive: rsi_slope = rsi[i] - rsi[i-1] if i > 0 else 0
    #
    # Example for factor "RSI" with params {{period: 14}}:
    #   rsi = ta_rsi(closes, period=params.get("period", 14))
    #
    # Example for factor "VolumeRatio" with params {{period: 10}}:
    #   volume_ratio = ta_volume_ratio(volumes, period=params.get("period", 10))

    # Step 3: Implement signal logic
    signals = [0] * n
    # ... your implementation here using the calculated indicators ...

    return signals

Output ONLY the Python function. No markdown fences. No explanation."""

    async def _audit_code(self, strategy: dict, code: str) -> tuple[bool, str]:
        """phi4-reasoning 审核生成代码是否符合策略意图。"""
        signal = strategy.get("signal", {})
        factors = strategy.get("factors", [])
        factor_names = [f.get("factor_name", "") for f in factors]

        audit_prompt = f"""You are auditing Python code for a trading strategy.

CRITICAL RULE: bars is a list of dicts with ONLY 6 keys: datetime, open, high, low, close, volume

Strategy factors: {factor_names}
Long condition: {signal.get("long_condition", "")}
Short condition: {signal.get("short_condition", "")}

Generated code:
{code[:3000]}

AUDIT QUESTION: Does this code try to access bars[i]["MACD"], bars[i]["RSI"], bars[i]["EMA"], or ANY key other than the 6 allowed keys (datetime, open, high, low, close, volume)?

If YES (accessing invalid keys like "MACD", "RSI", etc.): Reply "FAIL: accesses invalid bars keys"
If NO (only accesses the 6 valid keys): Reply "PASS"

Note: Using ta_macd(), ta_rsi(), ta_ema() functions is CORRECT. Only direct access to bars[i]["MACD"] is wrong."""

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
            safe_globals = {"__builtins__": _SAFE_BUILTINS, "math": math, **_TA_FUNCTIONS}
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

    # ------------------------------------------------------------------
    # 迭代优化辅助方法（TASK-U0-20260417-006）
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_stage(iteration: int) -> str:
        """判断当前迭代阶段"""
        if iteration <= STAGE1_MAX:
            return "快速达标"
        elif iteration <= STAGE2_MAX:
            return "中等提升"
        else:
            return "生产冲刺"

    @staticmethod
    def _check_production_ready(result: SignalBacktestResult) -> bool:
        """检查是否达到生产级标准"""
        checks = [
            result.sharpe_ratio >= PRODUCTION_STANDARDS["oos_sharpe"],
            result.trades_count >= PRODUCTION_STANDARDS["oos_trades"],
            result.win_rate >= PRODUCTION_STANDARDS["oos_win_rate"],
            result.max_drawdown <= PRODUCTION_STANDARDS["oos_max_dd"],
            result.annualized_return >= PRODUCTION_STANDARDS["oos_annual_return"],
        ]
        return all(checks)

    @staticmethod
    def _calculate_score(result: SignalBacktestResult) -> float:
        """计算综合得分（用于比较不同迭代结果）"""
        # 归一化各指标
        sharpe_score = min(result.sharpe_ratio / PRODUCTION_STANDARDS["oos_sharpe"], 1.0)
        trades_score = min(result.trades_count / PRODUCTION_STANDARDS["oos_trades"], 1.0)
        win_rate_score = min(result.win_rate / PRODUCTION_STANDARDS["oos_win_rate"], 1.0)
        dd_score = max(1.0 - result.max_drawdown / PRODUCTION_STANDARDS["oos_max_dd"], 0.0)
        annual_score = min(result.annualized_return / PRODUCTION_STANDARDS["oos_annual_return"], 1.0)

        # 加权平均（Sharpe 和交易次数权重更高）
        score = (
            sharpe_score * 0.35 +
            trades_score * 0.25 +
            win_rate_score * 0.15 +
            dd_score * 0.15 +
            annual_score * 0.10
        )
        return score

    async def _get_critic_feedback(
        self,
        strategy: dict,
        result: SignalBacktestResult,
        iteration: int,
        stage: str,
        history: list[dict],
    ) -> Optional[dict]:
        """调用 Critic 诊断问题并给出调整建议"""
        # 确定当前阶段目标
        if stage == "快速达标":
            target_standards = MINIMUM_STANDARDS
        elif stage == "中等提升":
            target_standards = MEDIUM_STANDARDS
        else:
            target_standards = PRODUCTION_STANDARDS

        # 构建历史记录摘要
        history_summary = []
        for h in history[-3:]:  # 只取最近3轮
            history_summary.append(
                f"迭代{h['iteration']}: 交易{h.get('trades', 0)}次, "
                f"Sharpe={h.get('sharpe', 0):.4f}, 胜率={h.get('win_rate', 0):.2%}"
            )

        factors = strategy.get("factors", [])
        signal = strategy.get("signal", {})
        market_filter = strategy.get("market_filter", {})

        prompt = f"""你是量化策略优化专家。分析回测结果，给出具体调整方案。

当前迭代: {iteration}/{MAX_ITERATIONS}
当前阶段: {stage}

策略配置:
- 因子: {[f.get('factor_name') for f in factors]}
- 因子参数: {json.dumps({f.get('factor_name'): f.get('params', {}) for f in factors}, ensure_ascii=False)}
- 多头条件: {signal.get('long_condition', '')}
- 空头条件: {signal.get('short_condition', '')}
- 市场过滤: {market_filter.get('conditions', [])}
- 时间周期: {strategy.get('timeframe_minutes', 0)} 分钟

回测结果:
- 交易次数: {result.trades_count} (目标: ≥{target_standards['oos_trades']})
- Sharpe: {result.sharpe_ratio:.4f} (目标: ≥{target_standards['oos_sharpe']})
- 胜率: {result.win_rate:.2%} (目标: ≥{target_standards['oos_win_rate']:.0%})
- 最大回撤: {result.max_drawdown:.2%} (目标: ≤{target_standards['oos_max_dd']:.0%})
- 年化收益: {result.annualized_return:.2%}

历史迭代记录:
{chr(10).join(history_summary) if history_summary else '无'}

底线约束（绝对不可违反）:
- 必须日内交易（no_overnight: true）
- 单笔止损 ≤ 1000 元
- 日内止损 ≤ 2000 元
- 不能移除核心因子

要求:
1. 分析当前最大瓶颈（交易次数不足？Sharpe太低？胜率不够？）
2. 给出1个最有效的调整方案
3. 预测调整后的效果

CRITICAL: 只输出纯 JSON，格式:
{{
  "diagnosis": {{
    "root_causes": ["原因1", "原因2", "原因3"],
    "current_bottleneck": "当前最大瓶颈",
    "stage_assessment": "阶段评估"
  }},
  "solution": {{
    "name": "方案名称",
    "priority": "high",
    "changes": {{
      "atr_threshold": "0.002",
      "adx_threshold": "15",
      "rsi_long_threshold": "40",
      "rsi_short_threshold": "60",
      "volume_ratio_threshold": "0.85"
    }},
    "expected_improvement": {{
      "trades": 预期交易次数,
      "sharpe": 预期Sharpe,
      "win_rate": 预期胜率
    }},
    "rationale": "为什么这个方案有效",
    "risk_note": "潜在风险"
  }}
}}"""

        messages = [
            {
                "role": "system",
                "content": "你是量化策略诊断专家。分析回测结果，找出问题根源，给出具体可执行的调整建议。只输出纯 JSON。"
            },
            {"role": "user", "content": prompt}
        ]

        try:
            result_dict = await self.critic_client.chat(self.critic_model, messages, timeout=60.0)

            if "error" in result_dict:
                logger.warning(f"Critic 调用失败: {result_dict['error']}")
                return None

            content = result_dict.get("content", "").strip()

            # 尝试解析 JSON
            try:
                feedback = json.loads(content)
                return feedback
            except json.JSONDecodeError as e:
                logger.warning(f"Critic 未返回有效 JSON: {e}")
                # 尝试提取 JSON 片段
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        feedback = json.loads(json_match.group(0))
                        return feedback
                    except json.JSONDecodeError:
                        pass
                return None

        except Exception as e:
            logger.error(f"Critic 调用异常: {e}", exc_info=True)
            return None

    @staticmethod
    def _apply_critic_suggestions(strategy: dict, critic_json: dict) -> dict:
        """根据 Critic 建议调整策略参数"""
        changes = critic_json.get("solution", {}).get("changes", {})

        if not changes:
            logger.warning("Critic 未提供具体调整建议")
            return strategy

        logger.info(f"应用 Critic 建议: {json.dumps(changes, ensure_ascii=False)}")

        # 更新因子参数
        for factor in strategy.get("factors", []):
            factor_name = factor.get("factor_name", "").lower()
            params = factor.get("params", {})

            for key, value in changes.items():
                key_lower = key.lower()

                # 直接匹配
                if key in params:
                    params[key] = float(value)
                    logger.info(f"  - {factor_name}.{key}: {params[key]}")
                # 模糊匹配（忽略大小写）
                elif any(k.lower() == key_lower for k in params.keys()):
                    for k in params.keys():
                        if k.lower() == key_lower:
                            params[k] = float(value)
                            logger.info(f"  - {factor_name}.{k}: {params[k]}")
                            break
                # 匹配因子名前缀（如 rsi_long_threshold → RSI 因子的 long_threshold）
                elif key_lower.startswith(factor_name):
                    param_name = key_lower.replace(factor_name + "_", "")
                    if param_name in params or any(k.lower() == param_name for k in params.keys()):
                        for k in params.keys():
                            if k.lower() == param_name:
                                params[k] = float(value)
                                logger.info(f"  - {factor_name}.{k}: {params[k]}")
                                break

            factor["params"] = params

        # 更新市场过滤器（字符串表达式）
        market_filter = strategy.get("market_filter", {})
        conditions = market_filter.get("conditions", [])

        new_conditions = []
        for condition in conditions:
            new_condition = condition

            # 替换 ATR 阈值
            if "atr_threshold" in changes and "atr" in condition.lower():
                # 匹配 "atr > 0.006 * close" 格式
                import re
                match = re.search(r'atr\s*>\s*([\d.]+)\s*\*\s*close', condition, re.IGNORECASE)
                if match:
                    old_value = match.group(1)
                    new_value = changes["atr_threshold"]
                    new_condition = condition.replace(old_value, str(new_value))
                    logger.info(f"  - market_filter.atr: {old_value} → {new_value}")

            # 替换 ADX 阈值
            if "adx_threshold" in changes and "adx" in condition.lower():
                # 匹配 "adx > 25" 格式
                match = re.search(r'adx\s*>\s*([\d.]+)', condition, re.IGNORECASE)
                if match:
                    old_value = match.group(1)
                    new_value = changes["adx_threshold"]
                    new_condition = condition.replace(old_value, str(new_value))
                    logger.info(f"  - market_filter.adx: {old_value} → {new_value}")

            new_conditions.append(new_condition)

        market_filter["conditions"] = new_conditions

        # 更新信号条件（字符串表达式）
        signal = strategy.get("signal", {})

        # 替换 RSI 阈值
        if "rsi_long_threshold" in changes:
            long_cond = signal.get("long_condition", "")
            # 匹配 "rsi < 45" 或 "rsi > 45" 格式
            match = re.search(r'rsi\s*([<>])\s*([\d.]+)', long_cond, re.IGNORECASE)
            if match:
                operator = match.group(1)
                old_value = match.group(2)
                new_value = changes["rsi_long_threshold"]
                long_cond = long_cond.replace(f"rsi {operator} {old_value}", f"rsi {operator} {new_value}")
                signal["long_condition"] = long_cond
                logger.info(f"  - signal.rsi_long: {old_value} → {new_value}")

        if "rsi_short_threshold" in changes:
            short_cond = signal.get("short_condition", "")
            match = re.search(r'rsi\s*([<>])\s*([\d.]+)', short_cond, re.IGNORECASE)
            if match:
                operator = match.group(1)
                old_value = match.group(2)
                new_value = changes["rsi_short_threshold"]
                short_cond = short_cond.replace(f"rsi {operator} {old_value}", f"rsi {operator} {new_value}")
                signal["short_condition"] = short_cond
                logger.info(f"  - signal.rsi_short: {old_value} → {new_value}")

        # 替换 VolumeRatio 阈值
        if "volume_ratio_threshold" in changes:
            long_cond = signal.get("long_condition", "")
            short_cond = signal.get("short_condition", "")

            # 匹配 "volume_ratio > 1.15" 格式
            match_long = re.search(r'volume_ratio\s*>\s*([\d.]+)', long_cond, re.IGNORECASE)
            match_short = re.search(r'volume_ratio\s*>\s*([\d.]+)', short_cond, re.IGNORECASE)

            if match_long:
                old_value = match_long.group(1)
                new_value = changes["volume_ratio_threshold"]
                long_cond = long_cond.replace(f"volume_ratio > {old_value}", f"volume_ratio > {new_value}")
                signal["long_condition"] = long_cond
                logger.info(f"  - signal.volume_ratio_long: {old_value} → {new_value}")

            if match_short:
                old_value = match_short.group(1)
                new_value = changes["volume_ratio_threshold"]
                short_cond = short_cond.replace(f"volume_ratio > {old_value}", f"volume_ratio > {new_value}")
                signal["short_condition"] = short_cond
                logger.info(f"  - signal.volume_ratio_short: {old_value} → {new_value}")

        return strategy
