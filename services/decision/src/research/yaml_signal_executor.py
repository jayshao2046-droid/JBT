"""YAML 信号执行器 — TASK-0122-B + TASK-U0-20260417-006

将 YAML 策略文件中的信号定义通过 qwen3:14b 翻译为可执行 Python 函数，
qwen3:14b 审核后，使用 Mini 历史 K 线数据执行真实回测。

TASK-U0-20260417-006: 添加 Researcher ↔ Critic 迭代优化流程，
支持多轮迭代（最多30轮），将策略优化到生产级标准。

安全说明：exec() 使用严格受限的 safe_globals 命名空间，禁止 import、
文件读写、网络访问、进程执行等高危操作。
"""
from __future__ import annotations

import ast
import concurrent.futures
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
    "hasattr": hasattr, "type": type,
    "Exception": Exception, "ValueError": ValueError,
    "IndexError": IndexError, "ZeroDivisionError": ZeroDivisionError,
    "print": print,
}

# P0-1 安全修复：AST 白名单检查 + 执行超时（防止 LLM 代码注入）
_DANGEROUS_CALL_NAMES = frozenset({
    "eval", "exec", "compile", "__import__", "open", "getattr", "setattr",
    "delattr", "vars", "dir", "globals", "locals", "breakpoint",
})
_EXEC_TIMEOUT = 10.0  # 信号函数执行超时（秒），防止死循环


def _ast_whitelist_check(code: str) -> None:
    """对 LLM 生成的代码执行 AST 节点白名单检查。

    Raises:
        ValueError: 当代码包含危险语法结构时
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"代码语法错误: {e}") from e

    for node in ast.walk(tree):
        # 禁止 import 语句
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("安全限制：不允许 import 语句")
        # 禁止 global/nonlocal
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError("安全限制：不允许 global/nonlocal 语句")
        # 禁止 dunder 属性访问（防止 __class__.__mro__ 等沙箱逃逸）
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("__") and node.attr.endswith("__")
        ):
            raise ValueError(f"安全限制：不允许访问双下划线属性 '{node.attr}'")
        # 禁止危险内置函数调用
        if isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name and name in _DANGEROUS_CALL_NAMES:
                raise ValueError(f"安全限制：不允许调用 '{name}'")


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
    trades: list = field(default_factory=list)  # 原始交易记录（含 features），供 XGBoost 训练

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("equity_curve", None)  # 不序列化 equity_curve（太大）
        d.pop("trades", None)        # 不序列化 trades（太大），通过 .trades 直接访问
        return d


class YAMLSignalExecutor:
    """YAML 策略信号执行器。

    通过 qwen3:14b 将 YAML 信号定义翻译为 Python 函数，
    qwen3:14b 审核后用真实 K 线数据执行回测。
    """

    MAX_RETRY = 2

    def __init__(
        self,
        data_service_url: str = "http://192.168.31.74:8105",
        ollama_url: str = "http://192.168.31.142:11434",
        researcher_model: str = "qwen3:14b-q4_K_M",
        auditor_model: str = "qwen3:14b-q4_K_M",
        initial_capital: float = 500_000.0,
    ) -> None:
        self.data_service_url = data_service_url.rstrip("/")

        # 支持切换到在线 API（通过环境变量 LLM_PROVIDER）
        llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        if llm_provider == "online":
            logger.info("使用在线 API 客户端（OpenAI-compatible）")
            self.client = OpenAICompatibleClient(component="yaml_executor")
            self.researcher_model = os.getenv("ONLINE_RESEARCHER_MODEL", "qwen-coder-plus")
            self.auditor_model = os.getenv("ONLINE_AUDITOR_MODEL", "qwen-plus")
        else:
            logger.info("使用本地 Ollama 客户端")
            self.client = OllamaClient(base_url=ollama_url, component="yaml_executor")
            self.researcher_model = os.getenv("OLLAMA_RESEARCHER_MODEL", researcher_model)
            self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", auditor_model)

        self.initial_capital = initial_capital

        # Critic 客户端走 HybridClient：Ollama 优先，超时降级在线
        from ..llm.client import HybridClient
        critic_provider = os.getenv("CRITIC_LLM_PROVIDER", "hybrid").lower()
        if critic_provider == "online":
            self.critic_client = OpenAICompatibleClient(component="critic")
            self.critic_model = os.getenv("ONLINE_AUDITOR_MODEL", "gpt-5.4")
        elif critic_provider == "ollama":
            self.critic_client = OllamaClient(base_url=ollama_url, component="critic")
            self.critic_model = os.getenv("CRITIC_MODEL", "qwen3:14b")
        else:
            self.critic_client = HybridClient(
                ollama_client=OllamaClient(base_url=ollama_url),
                component="critic",
            )
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
        cached_code: Optional[str] = None,
    ) -> SignalBacktestResult:
        """执行 YAML 策略回测（含 qwen3 代码生成）。

        Args:
            strategy: YAML 策略配置字典
            start_date: 回测起始日期 YYYY-MM-DD
            end_date: 回测结束日期 YYYY-MM-DD
            params_override: 覆盖 YAML 中的因子参数（用于优化 trial）
            cached_code: Optuna 已验证的代码（若提供则跳过 LLM 生成）
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

        if cached_code:
            logger.info("使用 Optuna 缓存代码（跳过 LLM 生成）: %s", strategy_id)
            code = cached_code
        else:
            code, error = await self._generate_signal_code(strategy, params_override)
            if error:
                return self._fail(strategy_id, error)

        # 信号可行性校验：先跑一次全量数据，信号全 0 则重新生成
        feasible, signals_preview = self._validate_signal_feasibility(
            strategy_id, bars, code, strategy, params_override
        )
        if not feasible:
            logger.warning("信号可行性校验失败，尝试重新生成代码...")
            code, error = await self._generate_signal_code(
                strategy, params_override,
                feedback="前一次生成的代码对整个数据集产生 0 笔交易（信号全为 0）。"
                         "请放宽条件：减少 AND 条件数量、降低阈值、"
                         "确保 market_filter 和 signal 条件不矛盾。"
            )
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
            code: qwen3 已生成的 compute_signals 函数代码
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
            "timeframe_minutes": timeframe_minutes,
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
        """从 YAML 提取 symbol（支持 symbol 或 symbols 字段）。"""
        # 优先从 strategy.symbol 读取
        if "strategy" in strategy and "symbol" in strategy["strategy"]:
            return strategy["strategy"]["symbol"]

        # 兼容旧格式 symbols 列表
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
    # Code generation (qwen3 + qwen3)
    # ------------------------------------------------------------------

    async def _generate_signal_code(
        self, strategy: dict, params_override: Optional[dict], feedback: str = ""
    ) -> tuple[str, str]:
        """调用 qwen3 生成信号函数，qwen3 审核，最多 MAX_RETRY 次。

        Returns:
            (code, error_message) — error_message 为空表示成功
        """
        for attempt in range(self.MAX_RETRY + 1):
            prompt = self._build_qwen3_prompt(strategy, params_override, feedback)
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
                    logger.warning("qwen3 attempt %d failed: %s, retrying...", attempt + 1, result["error"])
                    continue
                return "", f"qwen3 生成失败: {result['error']}"

            code = self._extract_python_code(result.get("content", ""))
            if not code:
                if attempt < self.MAX_RETRY:
                    continue
                return "", "qwen3 未生成有效 Python 函数"

            # 语法校验
            try:
                ast.parse(code)
            except SyntaxError as e:
                if attempt < self.MAX_RETRY:
                    feedback = f"SyntaxError: {e}"
                    continue
                return "", f"生成代码语法错误: {e}"

            # qwen3 审核
            audit_ok, audit_reason = await self._audit_code(strategy, code)
            if not audit_ok:
                if attempt < self.MAX_RETRY:
                    logger.warning("qwen3 审核拒绝 attempt %d: %s，重试...", attempt + 1, audit_reason)
                    feedback = audit_reason
                    continue
                return "", f"qwen3 审核失败（{self.MAX_RETRY + 1} 次后放弃）: {audit_reason}"

            return code, ""

        return "", "代码生成失败（未知原因）"

    def _build_qwen3_prompt(
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

DERIVED VARIABLE MAPPING (派生变量计算公式 — 重要!):
  YAML 信号条件中的变量名必须按以下公式计算：
  - bollinger_upper, bollinger_mid, bollinger_lower = ta_bollinger(closes, period, std_dev)
  - bb_bandwidth = (bollinger_upper[i] - bollinger_lower[i]) / bollinger_mid[i]  if bollinger_mid[i] > 0 else 0
  - bb_position = (close[i] - bollinger_lower[i]) / (bollinger_upper[i] - bollinger_lower[i])  if (bollinger_upper[i] - bollinger_lower[i]) > 0 else 0.5
  - rsi = ta_rsi(closes, period)  # rsi[i] is the RSI value at bar i
  - atr = ta_atr(highs, lows, closes, period)  # atr[i] is ATR at bar i
  - volume_ratio = ta_volume_ratio(volumes, period)  # volume_ratio[i] is ratio at bar i
  - macd_line, signal_line, macd_hist = ta_macd(closes, fast, slow, signal)
  - adx = ta_adx(highs, lows, closes, period)
  - k_vals, d_vals, j_vals = ta_kdj(highs, lows, closes)
  - cci = ta_cci(highs, lows, closes, period)

SIGNAL CONSISTENCY RULE (信号一致性规则):
  market_filter 和 signal 条件必须逻辑一致，不能自相矛盾。例如：
  - ❌ 错误: filter 要求 bb_position 在 0.4~0.6（中间），但 signal 要求 close > bollinger_upper（顶部）
  - ✅ 正确: breakout 策略的 filter 应该检查波动率（如 atr），signal 检查突破（close > upper）
  - ✅ 正确: mean_reversion 策略的 filter 检查非极端行情，signal 检查偏离回归

OPTIMIZATION OBJECTIVES (优化目标 — 激进探索优先):
  - 首要目标: 产生足够多的交易（≥50 次），有亏有赚都可以
  - 次要目标: 在大量交易中提升胜率和 Sharpe
  - 条件不要太严格，宁可多开仓再收敛，也不要 0 笔交易

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
    - DO NOT use any import statements! math and all ta_* functions are pre-injected into scope.
    - Return exactly len(bars) integers

    NUMERIC PRECISION RULE (数值精度 — 极其重要!):
    - market_filter conditions 中的数值必须与 YAML 完全一致，禁止自行换算或四舍五入
    - 例如 YAML 写 'atr > 0.0006 * close'，代码必须写 atr_i > 0.0006 * close_i
    - 绝对禁止将 0.0006 写成 0.006 或 0.06 — 这会导致零交易!
    - 所有阈值直接从 market_filter conditions 字符串中提取，不做任何数量级变换

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

    # IMPORTANT: confirm_bars implementation
    # If confirm_bars > 1, signal must be consistent for N consecutive bars
    # CORRECT implementation:
    #   long_count = 0
    #   short_count = 0
    #   for i in range(n):
    #       # Check raw signal conditions
    #       long_signal = (your_long_condition)
    #       short_signal = (your_short_condition)
    #
    #       # Count consecutive bars
    #       if long_signal:
    #           long_count += 1
    #           short_count = 0
    #       elif short_signal:
    #           short_count += 1
    #           long_count = 0
    #       else:
    #           long_count = 0
    #           short_count = 0
    #
    #       # Confirm signal after N consecutive bars
    #       if long_count >= confirm_bars:
    #           signals[i] = 1
    #       elif short_count >= confirm_bars:
    #           signals[i] = -1

    # ... your implementation here using the calculated indicators ...

    return signals

Output ONLY the Python function. No markdown fences. No explanation."""

    async def _audit_code(self, strategy: dict, code: str) -> tuple[bool, str]:
        """qwen3:14b 审核生成代码是否符合策略意图。"""
        signal = strategy.get("signal", {})
        factors = strategy.get("factors", [])
        factor_names = [f.get("factor_name", "") for f in factors]

        audit_prompt = f"""You are auditing Python code for a trading strategy.

CRITICAL RULE: bars is a list of dicts with ONLY 6 keys: datetime, open, high, low, close, volume

Strategy factors: {factor_names}
Long condition: {signal.get("long_condition", "")}
Short condition: {signal.get("short_condition", "")}

Generated code:
{code}

AUDIT CHECKLIST (check ALL items, FAIL on ANY violation):
1. Does the code access bars[i]["MACD"], bars[i]["RSI"], bars[i]["EMA"], bars[i]["EMA_Cross"],
   bars[i]["ADX"], bars[i]["ATR"], or ANY key other than the 6 allowed keys
   (datetime, open, high, low, close, volume)?
   → If YES: FAIL
2. Does the code reference column names like 'EMA_Cross', 'MACD_hist', 'RSI' as if
   they are pre-existing DataFrame columns or dict keys in bars?
   → If YES: FAIL
3. Are ALL technical indicators (MACD, RSI, EMA, SMA, ATR, ADX, etc.) computed using
   ta_* functions (ta_macd, ta_rsi, ta_ema, ta_sma, ta_atr, ta_adx, etc.)?
   → If NOT all computed via ta_*: FAIL

If ALL checks pass: Reply "PASS"
If ANY check fails: Reply "FAIL: <specific reason>"

Note: Using ta_macd(), ta_rsi(), ta_ema() etc. is CORRECT. Only direct access to bars[i]["MACD"] or assuming bars has pre-computed indicator columns is wrong."""

        messages = [
            {"role": "system", "content": "You are a strict quantitative code auditor. Be concise and direct."},
            {"role": "user", "content": audit_prompt},
        ]
        result = await self.client.chat(self.auditor_model, messages, timeout=180.0)

        if "error" in result:
            # qwen3 失败时不阻断，允许通过
            logger.warning("qwen3 audit error (non-blocking): %s", result["error"])
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
    # Signal feasibility validation (#9, #24)
    # ------------------------------------------------------------------

    def _validate_signal_feasibility(
        self,
        strategy_id: str,
        bars: list[dict],
        code: str,
        strategy: dict,
        params_override: Optional[dict],
    ) -> tuple[bool, list[int]]:
        """校验生成的信号代码是否能产生非零信号。

        用全量 bars 跑一次 compute_signals，如果信号全为 0（无任何开仓），
        说明条件自相矛盾或过于严格，需要重新生成。

        Returns:
            (feasible, signals) — feasible=True 表示至少有 1 个非零信号
        """
        params: dict[str, Any] = {}
        for f in strategy.get("factors", []):
            params.update(f.get("params", {}))
        if params_override:
            params.update(params_override)

        try:
            _ast_whitelist_check(code)
        except ValueError:
            return False, []

        try:
            def _run():
                _safe_globals = {"__builtins__": _SAFE_BUILTINS, "math": math, **_TA_FUNCTIONS}
                _local_ns: dict[str, Any] = {}
                exec(compile(code, "<feasibility_check>", "exec"), _safe_globals, _local_ns)  # noqa: S102
                _compute = _local_ns.get("compute_signals")
                if not callable(_compute):
                    return []
                return _compute(bars, params)

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_run)
                signals = fut.result(timeout=_EXEC_TIMEOUT)

            if not signals or len(signals) != len(bars):
                return False, []

            non_zero = sum(1 for s in signals if s != 0)
            if non_zero == 0:
                logger.warning(
                    "信号可行性校验: %s — %d 根 K 线全部信号为 0，条件过严或自相矛盾",
                    strategy_id, len(bars),
                )
                return False, signals

            logger.info(
                "信号可行性校验通过: %s — %d/%d 根有信号 (%.1f%%)",
                strategy_id, non_zero, len(bars), non_zero / len(bars) * 100,
            )
            return True, signals

        except Exception as e:
            logger.warning("信号可行性校验异常: %s — %s", strategy_id, e)
            return False, []

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

        # P0-1 修复：AST 白名单安全检查
        # 自动剥离安全的 import 语句（math 已在沙箱中预注入）
        import re as _re
        code = _re.sub(r'^\s*import\s+math\s*$', '', code, flags=_re.MULTILINE)
        code = _re.sub(r'^\s*from\s+math\s+import\s+.*$', '', code, flags=_re.MULTILINE)
        try:
            _ast_whitelist_check(code)
        except ValueError as _ast_err:
            logger.warning("AST 安全检查拒绝生成代码: %s", _ast_err)
            return self._fail(strategy_id, f"生成代码安全拒绝: {_ast_err}")

        # 执行沙箱（含超时保护，防止死循环）
        def _run_exec() -> list[int]:
            """在受限沙箱中执行生成代码并运行信号计算。"""
            _safe_globals = {"__builtins__": _SAFE_BUILTINS, "math": math, **_TA_FUNCTIONS}
            _local_ns: dict[str, Any] = {}
            exec(compile(code, "<generated_signal>", "exec"), _safe_globals, _local_ns)  # noqa: S102
            _compute = _local_ns.get("compute_signals")
            if not callable(_compute):
                raise ValueError("生成函数 compute_signals 未定义")
            return _compute(bars, params)

        try:
            logger.debug("生成的信号函数代码:\n%s...", code[:500])
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _pool:
                _fut = _pool.submit(_run_exec)
                try:
                    signals: list[int] = _fut.result(timeout=_EXEC_TIMEOUT)
                except concurrent.futures.TimeoutError:
                    return self._fail(strategy_id, f"信号函数执行超时（>{_EXEC_TIMEOUT}s），疑似死循环")
            if not signals or len(signals) != len(bars):
                return self._fail(
                    strategy_id,
                    f"信号序列长度异常: {len(signals) if signals else 0} vs {len(bars)}",
                )
        except ValueError as e:
            return self._fail(strategy_id, f"信号函数执行错误: {e}")
        except Exception as e:
            import traceback
            logger.error("信号函数执行异常详情:\n%s", traceback.format_exc())
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

        # 读取止盈止损配置
        stop_loss_config = strategy.get("stop_loss", {})
        take_profit_config = strategy.get("take_profit", {})

        # 计算ATR（如果需要）
        atr_values = {}
        if (stop_loss_config.get("type") == "atr" or
            take_profit_config.get("type") == "atr"):
            atr_period = stop_loss_config.get("atr_period", 14)
            atr_values = self._calculate_atr(bars, atr_period)

        capital = self.initial_capital
        peak_capital = capital
        position = 0        # 1=long, -1=short, 0=flat
        entry_price = 0.0
        entry_bar = 0
        daily_pnl: dict[str, float] = {}
        trades: list[dict] = []
        equity_curve: list[float] = [capital]

        # 预计算技术指标用于交易特征快照（供 XGBoost 训练）
        closes = [float(b.get("close", 0)) for b in bars]
        highs = [float(b.get("high", 0)) for b in bars]
        lows = [float(b.get("low", 0)) for b in bars]
        volumes = [float(b.get("volume", 0)) for b in bars]
        _feat_rsi = _ta_rsi(closes, 14)
        _feat_atr = _ta_atr(highs, lows, closes, 14)
        _feat_adx = _ta_adx(highs, lows, closes, 14)
        _feat_vol_ratio = _ta_volume_ratio(volumes, 10)
        _feat_bb_upper, _feat_bb_mid, _feat_bb_lower = _ta_bollinger(closes, 20, 2.0)
        _feat_macd, _feat_macd_sig, _feat_macd_hist = _ta_macd(closes)

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

            # 风控：止损检查
            current_atr = atr_values.get(i, 0.0)
            if position != 0 and self._should_stop_loss(
                position, entry_price, price, stop_loss_config, current_atr
            ):
                pnl = self._calc_pnl(position, entry_price, price, position_fraction, capital, slippage, commission)
                capital += pnl
                daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + pnl
                trades.append({"type": "stop_loss", "bar": i, "price": price, "pnl": round(pnl, 2)})
                position = 0
                entry_price = 0.0
                equity_curve.append(capital)
                continue

            # 风控：止盈检查
            if position != 0 and self._should_take_profit(
                position, entry_price, price, take_profit_config, current_atr
            ):
                pnl = self._calc_pnl(position, entry_price, price, position_fraction, capital, slippage, commission)
                capital += pnl
                daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + pnl
                trades.append({"type": "take_profit", "bar": i, "price": price, "pnl": round(pnl, 2)})
                position = 0
                entry_price = 0.0
                equity_curve.append(capital)
                continue

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
                entry_bar = i
                # 特征快照（供 XGBoost 训练）
                feat_snapshot = self._capture_trade_features(
                    i, closes, _feat_rsi, _feat_atr, _feat_adx,
                    _feat_vol_ratio, _feat_bb_upper, _feat_bb_mid, _feat_bb_lower,
                    _feat_macd_hist, bar,
                )
                trades.append({"type": "open_long", "bar": i, "price": price, "features": feat_snapshot})
            elif position == 0 and sig == -1:
                position = -1
                entry_price = price
                entry_bar = i
                feat_snapshot = self._capture_trade_features(
                    i, closes, _feat_rsi, _feat_atr, _feat_adx,
                    _feat_vol_ratio, _feat_bb_upper, _feat_bb_mid, _feat_bb_lower,
                    _feat_macd_hist, bar,
                )
                trades.append({"type": "open_short", "bar": i, "price": price, "features": feat_snapshot})

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
            trades=trades,  # 含 features 字段，供 XGBoost 训练
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
    def _capture_trade_features(
        idx: int,
        closes: list[float],
        rsi: list[float],
        atr: list[float],
        adx: list[float],
        vol_ratio: list[float],
        bb_upper: list[float],
        bb_mid: list[float],
        bb_lower: list[float],
        macd_hist: list[float],
        bar: dict,
    ) -> dict:
        """捕获开仓时刻的技术指标特征快照（供 XGBoost 训练）。"""
        close = closes[idx] if idx < len(closes) else 0.0
        bb_width = (
            (bb_upper[idx] - bb_lower[idx]) / bb_mid[idx]
            if idx < len(bb_mid) and bb_mid[idx] > 0
            else 0.0
        )
        bb_pos = (
            (close - bb_lower[idx]) / (bb_upper[idx] - bb_lower[idx])
            if idx < len(bb_upper) and (bb_upper[idx] - bb_lower[idx]) > 0
            else 0.5
        )
        # 提取小时（日内时段特征）
        dt_str = str(bar.get("datetime", bar.get("date", "")))
        hour = -1
        try:
            if len(dt_str) >= 13:
                hour = int(dt_str[11:13])
        except (ValueError, IndexError):
            pass

        return {
            "rsi": round(rsi[idx], 4) if idx < len(rsi) else 50.0,
            "atr": round(atr[idx], 6) if idx < len(atr) else 0.0,
            "atr_pct": round(atr[idx] / close, 6) if idx < len(atr) and close > 0 else 0.0,
            "adx": round(adx[idx], 4) if idx < len(adx) else 0.0,
            "volume_ratio": round(vol_ratio[idx], 4) if idx < len(vol_ratio) else 1.0,
            "bb_width": round(bb_width, 6),
            "bb_position": round(bb_pos, 4),
            "macd_hist": round(macd_hist[idx], 6) if idx < len(macd_hist) else 0.0,
            "hour": hour,
            "close": round(close, 2),
        }

    @staticmethod
    def _calculate_atr(bars: list[dict], period: int = 14) -> dict[int, float]:
        """计算每个K线的ATR值（简单移动平均）"""
        atr_values = {}
        tr_list = []

        for i in range(1, len(bars)):
            high = float(bars[i].get("high", 0))
            low = float(bars[i].get("low", 0))
            prev_close = float(bars[i-1].get("close", 0))

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_list.append(tr)

            if len(tr_list) >= period:
                atr_values[i] = sum(tr_list[-period:]) / period

        return atr_values

    @staticmethod
    def _should_stop_loss(
        position: int,
        entry_price: float,
        current_price: float,
        stop_loss_config: dict,
        atr: float = 0.0
    ) -> bool:
        """检查是否触发止损"""
        if not stop_loss_config:
            return False

        stop_type = stop_loss_config.get("type", "atr")

        if stop_type == "atr" and atr > 0:
            multiplier = float(stop_loss_config.get("atr_multiplier", 1.5))
            stop_distance = atr * multiplier

            if position == 1:  # 多头
                return current_price <= entry_price - stop_distance
            else:  # 空头
                return current_price >= entry_price + stop_distance

        return False

    @staticmethod
    def _should_take_profit(
        position: int,
        entry_price: float,
        current_price: float,
        take_profit_config: dict,
        atr: float = 0.0
    ) -> bool:
        """检查是否触发止盈"""
        if not take_profit_config:
            return False

        profit_type = take_profit_config.get("type", "atr")

        if profit_type == "atr" and atr > 0:
            multiplier = float(take_profit_config.get("atr_multiplier", 2.5))
            profit_distance = atr * multiplier

            if position == 1:  # 多头
                return current_price >= entry_price + profit_distance
            else:  # 空头
                return current_price <= entry_price - profit_distance

        return False

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

        if "confirm_bars" in changes:
            try:
                new_confirm_bars = max(1, int(float(changes["confirm_bars"])))
                old_confirm_bars = int(signal.get("confirm_bars", 1) or 1)
                signal["confirm_bars"] = new_confirm_bars
                logger.info(f"  - signal.confirm_bars: {old_confirm_bars} → {new_confirm_bars}")
            except (TypeError, ValueError):
                logger.warning("  - signal.confirm_bars 调整失败: %s", changes["confirm_bars"])

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

        if "reduce_and_conditions" in changes:
            for signal_key in ("long_condition", "short_condition"):
                condition = signal.get(signal_key, "")
                parts = [part.strip() for part in condition.split(" and ") if part.strip()]
                if len(parts) <= 1:
                    continue
                removed = parts.pop()
                signal[signal_key] = " and ".join(parts)
                logger.info(f"  - signal.{signal_key}: 移除末尾 AND 条件 '{removed}'")

        if "drop_market_filter_tail" in changes:
            market_conditions = market_filter.get("conditions", [])
            if len(market_conditions) > 1:
                removed = market_conditions.pop()
                market_filter["conditions"] = market_conditions
                logger.info(f"  - market_filter.conditions: 移除末尾条件 '{removed}'")

        return strategy
