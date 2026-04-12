"""LLM API routes."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..llm.client import OllamaClient
from ..llm.pipeline import LLMPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])

# Global pipeline instance
_pipeline: Optional[LLMPipeline] = None


def get_pipeline() -> LLMPipeline:
    """Get or create global pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = LLMPipeline()
    return _pipeline


# Request/Response models
class ResearchRequest(BaseModel):
    """Request for strategy research."""

    intent: str


class ResearchResponse(BaseModel):
    """Response from strategy research."""

    code: str
    model: str
    duration_seconds: float
    error: Optional[str] = None


class AuditRequest(BaseModel):
    """Request for strategy audit."""

    code: str


class AuditResponse(BaseModel):
    """Response from strategy audit."""

    passed: bool
    issues: list
    risk_level: str
    summary: str
    model: str
    duration_seconds: float
    error: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """Request for performance analysis."""

    performance_data: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    """Response from performance analysis."""

    analysis: str
    model: str
    duration_seconds: float
    error: Optional[str] = None


class PipelineRequest(BaseModel):
    """Request for full pipeline execution."""

    intent: str
    performance_data: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    """Response from full pipeline execution."""

    research_result: Dict[str, Any]
    audit_result: Dict[str, Any]
    analysis_result: Optional[Dict[str, Any]] = None
    total_duration_seconds: float
    error: Optional[str] = None


@router.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest) -> ResearchResponse:
    """
    Generate strategy code from intent description.

    Args:
        req: Research request with intent

    Returns:
        Generated strategy code and metadata
    """
    pipeline = get_pipeline()
    result = await pipeline.research(req.intent)
    return ResearchResponse(**result)


@router.post("/audit", response_model=AuditResponse)
async def audit(req: AuditRequest) -> AuditResponse:
    """
    Audit strategy code for correctness and risk.

    Args:
        req: Audit request with code

    Returns:
        Audit results with pass/fail status
    """
    pipeline = get_pipeline()
    result = await pipeline.audit(req.code)
    return AuditResponse(**result)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze strategy performance data.

    Args:
        req: Analysis request with performance data

    Returns:
        Analysis report with insights
    """
    pipeline = get_pipeline()
    result = await pipeline.analyze(req.performance_data)
    return AnalyzeResponse(**result)


@router.post("/pipeline", response_model=PipelineResponse)
async def pipeline(req: PipelineRequest) -> PipelineResponse:
    """
    Execute full pipeline: research → audit → analyze.

    Args:
        req: Pipeline request with intent and optional performance data

    Returns:
        Results from all pipeline steps
    """
    pipeline_instance = get_pipeline()
    result = await pipeline_instance.full_pipeline(req.intent, req.performance_data)
    return PipelineResponse(**result)
