"""LLM Pipeline for serial model execution.

TASK-0083: 集成数据和研究中心，支持自动拉取 K 线、沙箱回测。
TASK-0104-D2: 注入夜间预读上下文到三个角色 prompt。
TASK-0121-D1: 集成研究员报告到决策流程。
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from .client import OllamaClient, HybridClient
from .openai_client import OpenAICompatibleClient
from .context_loader import get_daily_context
from .prompts import ANALYST_SYSTEM, AUDITOR_SYSTEM, RESEARCHER_SYSTEM
from .researcher_loader import ResearcherLoader
from .researcher_scorer import ResearcherScorer
from .researcher_phi4_scorer import ResearcherPhi4Scorer

logger = logging.getLogger(__name__)

# 研报消费审计日志
_RESEARCH_AUDIT_LOG: list[dict] = []


def _resolve_timeframe_minutes(timeframe: str) -> int:
    mapping = {
        "1m": 1,
        "1min": 1,
        "5m": 5,
        "5min": 5,
        "15m": 15,
        "15min": 15,
        "30m": 30,
        "30min": 30,
        "60m": 60,
        "60min": 60,
        "1h": 60,
        "1d": 1440,
        "1day": 1440,
    }
    return mapping.get(timeframe.strip().lower(), 1)


def _default_window_for_timeframe(timeframe: str) -> tuple[str, str]:
    window_days = {
        "1m": 3,
        "1min": 3,
        "5m": 7,
        "5min": 7,
        "15m": 14,
        "15min": 14,
        "30m": 21,
        "30min": 21,
        "60m": 30,
        "60min": 30,
        "1h": 30,
        "1d": 120,
        "1day": 120,
    }
    end = datetime.utcnow().replace(microsecond=0)
    start = end - timedelta(days=window_days.get(timeframe.strip().lower(), 3))
    return start.isoformat(), end.isoformat()


class LLMPipeline:
    """Three-model serial pipeline for strategy research, audit, and analysis."""

    def __init__(self, client=None):
        """
        Initialize LLM pipeline.

        Args:
            client: OllamaClient or OpenAICompatibleClient instance.
                   If None, auto-selects based on LLM_PROVIDER env var.
        """
        # 高频组件走 HybridClient：本地 Ollama 优先，超时自动降级到在线 API
        llm_provider = os.getenv("PIPELINE_LLM_PROVIDER", "hybrid").lower()

        if client is not None:
            self.client = client
        elif llm_provider == "online":
            logger.info("LLMPipeline: 强制使用在线 API")
            self.client = OpenAICompatibleClient(component="pipeline")
        elif llm_provider == "ollama":
            logger.info("LLMPipeline: 强制使用本地 Ollama（无降级）")
            self.client = OllamaClient(component="pipeline")
        else:
            logger.info("LLMPipeline: 混合模式（Ollama 优先，超时降级在线）")
            self.client = HybridClient(component="pipeline")

        if llm_provider == "online":
            self.researcher_model = os.getenv("ONLINE_RESEARCHER_MODEL", "gpt-5.4")
            self.auditor_model = os.getenv("ONLINE_AUDITOR_MODEL", "gpt-5.4")
            self.analyst_model = os.getenv("ONLINE_RESEARCHER_MODEL", "gpt-5.4")
        else:
            self.researcher_model = os.getenv("OLLAMA_RESEARCHER_MODEL", "qwen3:14b-q4_K_M")
            self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", "qwen3:14b-q4_K_M")
            self.analyst_model = os.getenv("OLLAMA_ANALYST_MODEL", "qwen3:14b-q4_K_M")

        # TASK-0121-D1: 初始化研究员报告加载器和评分器
        data_service_url = os.getenv("DATA_SERVICE_URL", "http://192.168.31.76:8105")
        self.researcher_loader = ResearcherLoader(data_service_url)
        self.researcher_scorer = ResearcherScorer()
        self.researcher_phi4_scorer = ResearcherPhi4Scorer(client=self.client)

    async def research(self, intent: str) -> Dict[str, Any]:
        """
        Call qwen3 to generate strategy code.

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

        # 注入 ResearchStore 最新宏观判断
        try:
            from ..research.research_store import ResearchStore
            macro = ResearchStore().get_macro_summary()
            if macro.get("available"):
                macro_block = (
                    f"[最新宏观评级]\n"
                    f"  趋势: {macro.get('macro_trend', 'N/A')}\n"
                    f"  风险等级: {macro.get('risk_level', 'N/A')}\n"
                    f"  关键驱动: {', '.join(macro.get('key_drivers', []))}\n"
                    f"  推荐板块: {', '.join(macro.get('recommended_sectors', []))}\n"
                    f"  评分: {macro.get('score', 'N/A')}\n\n"
                )
                context_block += macro_block
                # 审计日志：记录宏观判断被消费
                _RESEARCH_AUDIT_LOG.append({
                    "consumer": "pipeline.research",
                    "report_type": "macro",
                    "action": "inject_to_prompt",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "macro_trend": macro.get("macro_trend"),
                    "risk_level": macro.get("risk_level"),
                })
                logger.info("已注入 ResearchStore 宏观判断到 research() prompt")
        except Exception as e:
            logger.warning(f"注入宏观判断失败（非致命）: {e}")

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
        Call qwen3 to analyze performance data.

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
        TASK-0083: 先从 data API 拉取标的 K 线，再传给 qwen3 做策略研究。

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
        """拉取 K 线数据：tqsdk 实时主路，Mini API 降为 fallback。"""
        # 1. 尝试 tqsdk 实时分钟线
        try:
            bars = await self._fetch_kline_via_tqsdk(symbol, timeframe)
            if bars:
                return bars
        except Exception as e:
            logger.warning(f"[KLINE] tqsdk 主路失败: {e}")

        # 2. fallback: Mini API
        try:
            url = f"{data_service_url.rstrip('/')}/api/v1/bars"
            timeframe_minutes = _resolve_timeframe_minutes(timeframe)
            default_start, default_end = _default_window_for_timeframe(timeframe)
            params: Dict[str, Any] = {
                "symbol": symbol,
                "timeframe_minutes": timeframe_minutes,
                "start": start_date or default_start,
                "end": end_date or default_end,
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return data
                return data.get("bars", data.get("data", []))
        except Exception as e:
            logger.warning(f"[KLINE] Mini API fallback 失败: {e}")
            return []

    async def _fetch_kline_via_tqsdk(self, symbol: str, timeframe: str) -> list:
        """通过 tqsdk 拉取实时分钟 K 线（在 executor 中运行，避免阻塞事件循环）。"""
        import os
        username = os.getenv("TQSDK_AUTH_USERNAME", "")
        password = os.getenv("TQSDK_AUTH_PASSWORD", "")
        if not username or not password:
            logger.debug("[KLINE] TQSDK 账号未配置，跳过")
            return []

        duration_map = {
            "1m": 60,
            "1min": 60,
            "5m": 300,
            "5min": 300,
            "15m": 900,
            "15min": 900,
            "30m": 1800,
            "30min": 1800,
            "60m": 3600,
            "60min": 3600,
            "1h": 3600,
            "1d": 86400,
            "1day": 86400,
        }
        duration_seconds = duration_map.get(timeframe.strip().lower(), 60)

        import asyncio
        loop = asyncio.get_event_loop()
        bars = await loop.run_in_executor(
            None,
            self._sync_fetch_tqsdk,
            symbol, duration_seconds, username, password,
        )
        return bars or []

    @staticmethod
    def _sync_fetch_tqsdk(symbol: str, duration_seconds: int, username: str, password: str) -> list:
        """同步 tqsdk 拉取（在 executor 中运行）。"""
        api = None
        try:
            from tqsdk import TqApi, TqAuth
            api = TqApi(auth=TqAuth(username, password))
            klines = api.get_kline_serial(symbol, duration_seconds, data_length=120)
            api.wait_update()
            bars = []
            for _, row in klines.iterrows():
                if float(row.get("close", 0)) > 0:
                    bars.append({
                        "datetime": str(row.get("datetime", "")),
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", 0)),
                        "open_oi": float(row.get("open_oi", 0)),
                    })
            return bars
        except ImportError:
            logger.warning("[KLINE] tqsdk 未安装，跳过")
            return []
        except Exception as e:
            logger.warning(f"[KLINE] tqsdk sync fetch 失败: {e}")
            return []
        finally:
            if api:
                try:
                    api.close()
                except Exception:
                    pass

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

    async def evaluate_researcher_report(self, segment: Optional[str] = None) -> Dict[str, Any]:
        """
        评估研究员报告并发送飞书通知。

        Args:
            segment: 可选的时段过滤（如 "15:00"）

        Returns:
            Dict containing:
                - report: 原始报告数据
                - score: qwen3 评分 (0.0-1.0)
                - confidence: 置信度 (high/medium/low)
                - reasoning: 评级理由
                - key_insights: 关键洞察列表
                - notification_sent: 是否成功发送飞书通知
                - error: 错误信息（如果有）
        """
        start_time = time.time()
        result = {}

        try:
            # 1. 从 Alienware 加载最新报告
            logger.info(f"从 Alienware 加载研究员报告 (segment={segment})")
            report = self.researcher_loader.get_latest_report(segment=segment)

            if not report:
                return {
                    "error": "未找到研究员报告",
                    "duration_seconds": time.time() - start_time
                }

            result["report"] = report
            logger.info(f"已加载报告: {report.get('report_id', 'unknown')}")

            # 2. 使用 qwen3 进行评级
            logger.info("使用 qwen3 评估报告")
            scoring_result = await self.researcher_phi4_scorer.score_report(
                report=report,
                context={}  # 可以传入持仓、市场上下文等
            )

            result.update(scoring_result)
            logger.info(f"qwen3 评分: {scoring_result.get('score')}, 置信度: {scoring_result.get('confidence')}")

            # 3. 发送飞书通知
            logger.info("发送飞书通知")
            notification_result = await self._send_feishu_notification(report, scoring_result)
            result["notification_sent"] = notification_result.get("success", False)

            if not notification_result.get("success"):
                logger.warning(f"飞书通知发送失败: {notification_result.get('error')}")

            result["duration_seconds"] = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"评估研究员报告失败: {e}", exc_info=True)
            return {
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }

    async def _send_feishu_notification(self, report: Dict, scoring_result: Dict) -> Dict[str, Any]:
        """发送飞书通知（使用卡片模式）"""
        try:
            import re

            # 构建通知内容
            report_id = report.get("report_id", "unknown")
            score = scoring_result.get("score", 0.0)
            reasoning = scoring_result.get("reasoning", "")
            improvements = scoring_result.get("improvements", [])

            # 清理 reasoning 中的 <think> 标签
            reasoning = re.sub(r'<think>.*?</think>', '', reasoning, flags=re.DOTALL).strip()

            # 格式化改进建议
            improvements_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(improvements)]) if improvements else "无"

            # 评分颜色
            if score >= 80:
                score_color = "green"
            elif score >= 60:
                score_color = "blue"
            elif score >= 40:
                score_color = "orange"
            else:
                score_color = "red"

            # 构建飞书卡片消息
            card_content = {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📊 研究员报告评级"
                    },
                    "template": score_color
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**报告ID**\n{report_id}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**评分**\n{score:.0f}/100"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**评级理由**\n{reasoning}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**改进建议**\n{improvements_text}"
                        }
                    }
                ]
            }

            # 调用飞书 API（需要从 decision 服务获取飞书配置）
            feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL")
            if not feishu_webhook:
                logger.warning("未配置 FEISHU_WEBHOOK_URL，跳过飞书通知")
                return {"success": False, "error": "未配置飞书 webhook"}

            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    feishu_webhook,
                    json={
                        "msg_type": "interactive",
                        "card": card_content
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info("飞书通知发送成功")
                    return {"success": True}
                else:
                    logger.error(f"飞书通知发送失败: {response.status_code} {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"发送飞书通知异常: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
