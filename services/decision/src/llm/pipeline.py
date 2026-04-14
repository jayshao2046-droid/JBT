"""LLM Pipeline for serial model execution.

TASK-0083: 集成数据和研究中心，支持自动拉取 K 线、沙箱回测。
TASK-0104-D2: 注入夜间预读上下文到三个角色 prompt。
"""

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from .client import OllamaClient
from .context_loader import get_daily_context
from .prompts import ANALYST_SYSTEM, AUDITOR_SYSTEM, RESEARCHER_SYSTEM

logger = logging.getLogger(__name__)


class LLMPipeline:
    """Three-model serial pipeline for strategy research, audit, and analysis."""

    def __init__(self, client: Optional[OllamaClient] = None):
        """
        Initialize LLM pipeline.

        Args:
            client: OllamaClient instance. If None, creates a new one.
        """
        self.client = client or OllamaClient()
        self.researcher_model = os.getenv("OLLAMA_RESEARCHER_MODEL", "deepcoder:14b")
        self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", "phi4-reasoning:14b")
        self.analyst_model = os.getenv("OLLAMA_ANALYST_MODEL", "phi4-reasoning:14b")

    async def research(self, intent: str) -> Dict[str, Any]:
        """
        Call deepcoder to generate strategy code.

        TASK-0104-D2: 注入 researcher_context 到 user message 前。

        Args:
            intent: Strategy intent description

        Returns:
            Dict containing:
                - code: Generated strategy code
                - model: Model name
                - duration_seconds: Execution time
                - error: Error message if failed
        """
        start_time = time.time()

        # TASK-0104-D2: 尝试加载今日预读上下文
        ctx = get_daily_context()
        context_block = ""
        if ctx:
            researcher_ctx = ctx.get("researcher_context", {})
            if researcher_ctx:
                # 格式化研究员上下文为可读文本
                watchlist = researcher_ctx.get("watchlist", [])
                daily_summary = researcher_ctx.get("daily_summary", [])
                macro_snapshot = researcher_ctx.get("macro_snapshot", {})

                context_parts = ["[今日市场预读]"]
                if watchlist:
                    context_parts.append(f"当前可交易标的池: {', '.join(watchlist[:10])}")
                if daily_summary:
                    context_parts.append("近5日市场概况:")
                    for item in daily_summary[:3]:
                        context_parts.append(f"  {item.get('symbol')}: 平均涨跌 {item.get('avg_change_pct')}%")
                if macro_snapshot:
                    context_parts.append(f"宏观环境: {', '.join([f'{k}={v}' for k, v in list(macro_snapshot.items())[:5]])}")

                context_block = "\n".join(context_parts) + "\n\n"
                logger.info("已注入研究员上下文到 research() prompt")

        # 将上下文拼接到 intent 前
        user_content = context_block + intent

        messages = [
            {"role": "system", "content": RESEARCHER_SYSTEM},
            {"role": "user", "content": user_content},
        ]

        result = await self.client.chat(self.researcher_model, messages)
        duration = time.time() - start_time

        if "error" in result:
            logger.error(f"Research failed: {result['error']}")
            return {
                "error": result["error"],
                "code": "",
                "model": self.researcher_model,
                "duration_seconds": duration,
            }

        return {
            "code": result.get("content", ""),
            "model": result.get("model", self.researcher_model),
            "duration_seconds": duration,
        }

    async def audit(self, code: str) -> Dict[str, Any]:
        """
        Call qwen3 to audit strategy code.

        TASK-0104-D2: 注入 l2_audit_context + l1_briefing 到 user message 前。

        Args:
            code: Strategy code to audit

        Returns:
            Dict containing:
                - passed: Whether audit passed
                - issues: List of issues found
                - risk_level: Risk level (low/medium/high)
                - summary: Audit summary
                - model: Model name
                - duration_seconds: Execution time
                - error: Error message if failed
        """
        start_time = time.time()

        # TASK-0104-D2: 尝试加载今日预读上下文
        ctx = get_daily_context()
        context_block = ""
        if ctx:
            l1_brief = ctx.get("l1_briefing", {})
            audit_ctx = ctx.get("l2_audit_context", {})

            if l1_brief or audit_ctx:
                context_parts = ["[今日审核参考]"]

                # L1 速报
                if l1_brief:
                    sentiment = l1_brief.get("sentiment_summary", {})
                    volatility = l1_brief.get("volatility_snapshot", {})
                    news_count = len(l1_brief.get("news_titles", []))
                    context_parts.append(f"L1速报: 市场情绪 {sentiment}, 波动率 {volatility}, 重大新闻 {news_count} 条")

                # L2 上下文
                if audit_ctx:
                    minute_stats = audit_ctx.get("minute_stats", [])
                    iv_snapshot = audit_ctx.get("iv_snapshot", {})
                    if minute_stats:
                        context_parts.append(f"L2上下文: 近20日分钟K统计 {len(minute_stats)} 只标的")
                    if iv_snapshot:
                        context_parts.append(f"期权IV: {', '.join([f'{k}={v}' for k, v in list(iv_snapshot.items())[:3]])}")

                context_block = "\n".join(context_parts) + "\n\n"
                logger.info("已注入审核上下文到 audit() prompt")

        # 将上下文拼接到 code 前
        user_content = context_block + code

        messages = [
            {"role": "system", "content": AUDITOR_SYSTEM},
            {"role": "user", "content": user_content},
        ]

        result = await self.client.chat(self.auditor_model, messages)
        duration = time.time() - start_time

        if "error" in result:
            logger.error(f"Audit failed: {result['error']}")
            return {
                "error": result["error"],
                "passed": False,
                "issues": [],
                "risk_level": "unknown",
                "summary": "",
                "model": self.auditor_model,
                "duration_seconds": duration,
            }

        # Try to parse JSON response
        content = result.get("content", "")
        try:
            import json

            audit_result = json.loads(content)
            return {
                "passed": audit_result.get("passed", False),
                "issues": audit_result.get("issues", []),
                "risk_level": audit_result.get("risk_level", "unknown"),
                "summary": audit_result.get("summary", ""),
                "model": result.get("model", self.auditor_model),
                "duration_seconds": duration,
            }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse audit result as JSON: {content}")
            return {
                "passed": False,
                "issues": ["Failed to parse audit result"],
                "risk_level": "unknown",
                "summary": content,
                "model": result.get("model", self.auditor_model),
                "duration_seconds": duration,
            }

    async def analyze(self, performance_data: Dict[str, Any], symbol: Optional[str] = None, timeframe: Optional[str] = None) -> Dict[str, Any]:
        """
        Call phi4-reasoning to analyze performance data.

        TASK-0083: 增加自动从 data 服务拉取 K 线数据能力。
        TASK-0104-D2: 注入 analyst_dataset 到 user message 前。

        Args:
            performance_data: Strategy performance metrics
            symbol: Optional symbol for fetching K-line data
            timeframe: Optional timeframe (e.g., "1m", "5m", "1d")

        Returns:
            Dict containing:
                - analysis: Analysis report
                - model: Model name
                - duration_seconds: Execution time
                - error: Error message if failed
        """
        start_time = time.time()

        # TASK-0083: 如果提供了 symbol 和 timeframe，自动拉取 K 线数据
        kline_data = None
        if symbol and timeframe:
            try:
                data_service_url = os.getenv("DATA_SERVICE_URL", "http://localhost:8105")
                kline_data = await self._fetch_kline_data(data_service_url, symbol, timeframe)
                logger.info(f"已从 data 服务拉取 {symbol} {timeframe} K 线数据: {len(kline_data)} 条")
            except Exception as exc:
                logger.warning(f"拉取 K 线数据失败: {exc}")

        # TASK-0104-D2: 尝试加载今日预读上下文
        ctx = get_daily_context()
        context_block = ""
        if ctx:
            analyst_data = ctx.get("analyst_dataset", {})
            if analyst_data:
                context_parts = ["[今日分析师数据集]"]

                # 波动率序列
                vol_series = analyst_data.get("volatility_series", [])
                if vol_series:
                    context_parts.append(f"波动率序列: {len(vol_series)} 条记录")

                # 北向资金
                north_flow = analyst_data.get("north_flow_series", [])
                if north_flow:
                    context_parts.append(f"北向资金: {len(north_flow)} 条记录")

                # 融资融券
                margin_series = analyst_data.get("margin_series", [])
                if margin_series:
                    context_parts.append(f"融资融券: {len(margin_series)} 条记录")

                context_block = "\n".join(context_parts) + "\n\n"
                logger.info("已注入分析师数据集到 analyze() prompt")

        # Format performance data as text
        perf_text = context_block + "\n".join([f"{k}: {v}" for k, v in performance_data.items()])
        if kline_data:
            perf_text += f"\n\nK 线数据样本（最近 5 条）:\n{kline_data[:5]}"

        messages = [
            {"role": "system", "content": ANALYST_SYSTEM},
            {"role": "user", "content": perf_text},
        ]

        result = await self.client.chat(self.analyst_model, messages)
        duration = time.time() - start_time

        if "error" in result:
            logger.error(f"Analysis failed: {result['error']}")
            return {
                "error": result["error"],
                "analysis": "",
                "model": self.analyst_model,
                "duration_seconds": duration,
            }

        return {
            "analysis": result.get("content", ""),
            "model": result.get("model", self.analyst_model),
            "duration_seconds": duration,
        }

    async def full_pipeline(
        self,
        intent: str,
        performance_data: Optional[Dict[str, Any]] = None,
        auto_backtest: bool = False,
        optuna_X_y: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Execute full pipeline: research → audit → [optuna → backtest] → analyze.

        TASK-0083: 增加可选的自动沙箱回测步骤。
        TASK-0112-C: 审核通过后先做 Optuna 参数优化，再用最优参数运行沙箱回测。

        Args:
            intent: Strategy intent description
            performance_data: Optional performance data for analysis step
            auto_backtest: If True, automatically run sandbox backtest after audit passes
            optuna_X_y: Optional (X, y) numpy arrays for Optuna hyperparameter search.
                        If None, Optuna step is skipped even when auto_backtest=True.

        Returns:
            Dict containing:
                - research_result: Research step result
                - audit_result: Audit step result
                - optuna_params: Best params from Optuna (if optuna_X_y provided)
                - backtest_result: Backtest result (if auto_backtest=True and audit passed)
                - analysis_result: Analysis step result (if audit passed)
                - total_duration_seconds: Total execution time
                - error: Error message if any step failed
        """
        total_start = time.time()
        result: Dict[str, Any] = {}

        # Step 1: Research
        logger.info("Starting research step")
        research_result = await self.research(intent)
        result["research_result"] = research_result

        if "error" in research_result:
            result["error"] = f"Research failed: {research_result['error']}"
            result["total_duration_seconds"] = time.time() - total_start
            return result

        # Step 2: Audit
        logger.info("Starting audit step")
        audit_result = await self.audit(research_result["code"])
        result["audit_result"] = audit_result

        if "error" in audit_result:
            result["error"] = f"Audit failed: {audit_result['error']}"
            result["total_duration_seconds"] = time.time() - total_start
            return result

        # Step 2.5: Optuna + Auto backtest (TASK-0083 / TASK-0112-C)
        if auto_backtest and audit_result.get("passed", False):
            best_params: Dict[str, Any] = {}

            # 2.5a: Optuna 参数优化（audit 通过后，有训练数据时执行）
            if optuna_X_y is not None:
                logger.info("Starting Optuna hyperparameter search")
                try:
                    import numpy as _np  # noqa: PLC0415

                    from ..research.optuna_search import OptunaSearch  # noqa: PLC0415
                    from ..research.trainer import XGBoostTrainer  # noqa: PLC0415

                    X_opt, y_opt = optuna_X_y
                    if not isinstance(X_opt, _np.ndarray) or not isinstance(y_opt, _np.ndarray):
                        raise TypeError("optuna_X_y must be a tuple of (np.ndarray, np.ndarray)")

                    searcher = OptunaSearch()
                    trainer_instance = XGBoostTrainer()
                    optuna_summary = searcher.schedule_nightly(
                        trainer=trainer_instance,
                        X=X_opt,
                        y=y_opt,
                        symbol="pipeline",
                        n_trials=30,  # pipeline 内快速搜索（完整夜间调优用 schedule_nightly 直调）
                        timeout=120,
                    )
                    best_params = optuna_summary.get("best_params", {})
                    result["optuna_params"] = optuna_summary
                    logger.info(f"Optuna search done: best_sharpe={optuna_summary.get('best_sharpe'):.3f}")
                except Exception as exc:
                    logger.warning(f"Optuna step skipped due to error: {exc}")
                    result["optuna_params"] = {"error": str(exc), "skipped": True}
            else:
                result["optuna_params"] = {"skipped": True, "reason": "No optuna_X_y provided"}

            # 2.5b: 沙箱回测（用最优参数）
            logger.info("Starting auto backtest step")
            try:
                backtest_result = await self._run_sandbox_backtest(
                    research_result["code"], params=best_params
                )
                result["backtest_result"] = backtest_result
            except Exception as exc:
                logger.error(f"Auto backtest failed: {exc}")
                result["backtest_result"] = {"error": str(exc)}

        # Step 3: Analyze (only if audit passed and performance data provided)
        if audit_result.get("passed", False) and performance_data:
            logger.info("Starting analysis step")
            analysis_result = await self.analyze(performance_data)
            result["analysis_result"] = analysis_result

            if "error" in analysis_result:
                result["error"] = f"Analysis failed: {analysis_result['error']}"
        elif not audit_result.get("passed", False):
            logger.info("Skipping analysis step: audit did not pass")
            result["analysis_result"] = {"skipped": True, "reason": "Audit did not pass"}
        else:
            logger.info("Skipping analysis step: no performance data provided")
            result["analysis_result"] = {"skipped": True, "reason": "No performance data provided"}

        result["total_duration_seconds"] = time.time() - total_start
        return result

    async def research_with_data(self, intent: str, symbol: str, timeframe: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        TASK-0083: 先从 data API 拉取标的 K 线，再传给 deepcoder 做策略研究。

        Args:
            intent: Strategy intent description
            symbol: Trading symbol (e.g., "000001.SZ", "RB2505")
            timeframe: Timeframe (e.g., "1m", "5m", "1d")
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Dict containing:
                - code: Generated strategy code
                - kline_data: Fetched K-line data
                - model: Model name
                - duration_seconds: Execution time
                - error: Error message if failed
        """
        start_time = time.time()

        # Step 1: Fetch K-line data
        try:
            data_service_url = os.getenv("DATA_SERVICE_URL", "http://localhost:8105")
            kline_data = await self._fetch_kline_data(data_service_url, symbol, timeframe, start_date, end_date)
            logger.info(f"已拉取 {symbol} {timeframe} K 线数据: {len(kline_data)} 条")
        except Exception as exc:
            logger.error(f"拉取 K 线数据失败: {exc}")
            return {
                "error": f"Failed to fetch K-line data: {exc}",
                "code": "",
                "kline_data": [],
                "model": self.researcher_model,
                "duration_seconds": time.time() - start_time,
            }

        # Step 2: Research with K-line context
        enhanced_intent = f"{intent}\n\n标的: {symbol}\n时间周期: {timeframe}\nK 线数据样本（最近 5 条）:\n{kline_data[:5]}"
        research_result = await self.research(enhanced_intent)
        research_result["kline_data"] = kline_data
        research_result["duration_seconds"] = time.time() - start_time

        return research_result

    async def _fetch_kline_data(
        self,
        data_service_url: str,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        """从 data 服务拉取 K 线数据。"""
        url = f"{data_service_url.rstrip('/')}/api/v1/bars"
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
        }
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("bars", [])

    async def _run_sandbox_backtest(self, code: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """运行沙箱回测（调用 SandboxEngine）。TASK-0112-C: 支持传入 Optuna 最优参数。"""
        # TODO: 实现沙箱回测调用逻辑
        # 这里返回一个占位结果
        logger.warning("沙箱回测功能尚未完全实现，返回占位结果")
        return {
            "status": "not_implemented",
            "message": "Sandbox backtest feature is under development",
            "params_used": params or {},
        }
