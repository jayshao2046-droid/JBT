"""LLM Pipeline for serial model execution."""

import logging
import os
import time
from typing import Any, Dict, Optional

from .client import OllamaClient
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
        self.auditor_model = os.getenv("OLLAMA_AUDITOR_MODEL", "qwen3:14b")
        self.analyst_model = os.getenv("OLLAMA_ANALYST_MODEL", "phi4-reasoning:14b")

    async def research(self, intent: str) -> Dict[str, Any]:
        """
        Call deepcoder to generate strategy code.

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
        messages = [
            {"role": "system", "content": RESEARCHER_SYSTEM},
            {"role": "user", "content": intent},
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
        messages = [
            {"role": "system", "content": AUDITOR_SYSTEM},
            {"role": "user", "content": code},
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

    async def analyze(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call phi4-reasoning to analyze performance data.

        Args:
            performance_data: Strategy performance metrics

        Returns:
            Dict containing:
                - analysis: Analysis report
                - model: Model name
                - duration_seconds: Execution time
                - error: Error message if failed
        """
        start_time = time.time()

        # Format performance data as text
        perf_text = "\n".join([f"{k}: {v}" for k, v in performance_data.items()])

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

    async def full_pipeline(self, intent: str, performance_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute full pipeline: research → audit → analyze.

        Args:
            intent: Strategy intent description
            performance_data: Optional performance data for analysis step

        Returns:
            Dict containing:
                - research_result: Research step result
                - audit_result: Audit step result
                - analysis_result: Analysis step result (if audit passed)
                - total_duration_seconds: Total execution time
                - error: Error message if any step failed
        """
        total_start = time.time()
        result = {}

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
