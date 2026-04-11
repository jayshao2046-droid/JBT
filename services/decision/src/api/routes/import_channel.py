"""导入通道路由 — TASK-0063 CF2"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ...publish.email_importer import EmailImporter, ImportResult

router = APIRouter(prefix="/api/v1/import", tags=["import"])

# 全局单例
_importer = EmailImporter()


# ── Pydantic 模型 ──────────────────────────────────────────────
class EmailImportRequest(BaseModel):
    subject: str = Field(..., min_length=1, description="邮件主题")
    body: str = Field(..., min_length=1, description="邮件正文")
    sender: str = Field(..., min_length=1, description="发件人")


class DashboardImportRequest(BaseModel):
    yaml_content: str = Field(..., min_length=1, description="YAML 策略内容")


class ImportResultResponse(BaseModel):
    import_id: str
    channel: str
    status: str
    created_at: str
    strategy_ids: list[str]
    errors: list[str]
    raw_yaml_count: int


def _to_response(r: ImportResult) -> ImportResultResponse:
    return ImportResultResponse(
        import_id=r.import_id,
        channel=r.channel,
        status=r.status,
        created_at=r.created_at,
        strategy_ids=r.strategy_ids,
        errors=r.errors,
        raw_yaml_count=r.raw_yaml_count,
    )


# ── 路由 ───────────────────────────────────────────────────────
@router.post("/email", response_model=ImportResultResponse)
def import_from_email(req: EmailImportRequest):
    """邮件 YAML 策略导入。"""
    result = _importer.import_from_email(req.subject, req.body, req.sender)
    return _to_response(result)


@router.post("/dashboard", response_model=ImportResultResponse)
def import_from_dashboard(req: DashboardImportRequest):
    """看板 YAML 文件导入。"""
    result = _importer.import_from_dashboard(req.yaml_content)
    return _to_response(result)


@router.get("/history", response_model=list[ImportResultResponse])
def list_import_history(channel: Optional[str] = None):
    """导入历史列表，可按 channel 过滤。"""
    results = _importer.list_results(channel=channel)
    return [_to_response(r) for r in results]


@router.get("/history/{import_id}", response_model=ImportResultResponse)
def get_import_result(import_id: str):
    """查询单个导入结果。"""
    result = _importer.get_result(import_id)
    if result is None:
        raise HTTPException(status_code=404, detail="导入记录不存在")
    return _to_response(result)
