"""回测报告路由 — TASK-0060 CA3"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ...research.report_builder import ReportBuilder
from ...research.sandbox_engine import SandboxEngine, SandboxResult
from ...core.settings import get_settings

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

_builder = ReportBuilder()


def _get_engine() -> SandboxEngine:
    settings = get_settings()
    return SandboxEngine(data_service_url=settings.data_service_url)


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------

class BuildReportRequest(BaseModel):
    backtest_id: str
    strategy_id: str
    asset_type: str = "futures"


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.post("/build")
async def build_report(req: BuildReportRequest) -> dict:
    """从 sandbox backtest_id 构建报告。"""
    # 尝试从 sandbox 引擎缓存获取结果（同进程内 mock 场景）
    engine = _get_engine()
    result: SandboxResult | None = getattr(engine, "_results", {}).get(req.backtest_id)
    if result is None:
        # 检查 module-level 缓存（供测试或外部注入）
        result = _sandbox_results_cache.get(req.backtest_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"backtest_id '{req.backtest_id}' not found in sandbox cache",
        )
    report = _builder.build_from_sandbox(result, req.strategy_id, req.asset_type)
    return report.to_dict()


@router.get("/")
async def list_reports(strategy_id: Optional[str] = None) -> list[dict]:
    """列出报告，可按 strategy_id 过滤。"""
    reports = _builder.list_reports(strategy_id=strategy_id)
    return [r.to_dict() for r in reports]


@router.get("/{report_id}")
async def get_report(report_id: str) -> dict:
    """获取单个报告。"""
    report = _builder.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"report '{report_id}' not found",
        )
    return report.to_dict()


@router.get("/{report_id}/export/json")
async def export_json(report_id: str) -> dict:
    """导出 JSON 格式报告。"""
    data = _builder.export_json(report_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"report '{report_id}' not found",
        )
    return data


@router.get("/{report_id}/export/html")
async def export_html(report_id: str) -> HTMLResponse:
    """导出 HTML 格式报告。"""
    html = _builder.export_html(report_id)
    if html is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"report '{report_id}' not found",
        )
    return HTMLResponse(content=html)


# ------------------------------------------------------------------
# Module-level sandbox result cache (for injection / testing)
# ------------------------------------------------------------------

_sandbox_results_cache: dict[str, SandboxResult] = {}
