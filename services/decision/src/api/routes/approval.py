import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/approvals", tags=["approval"])

_approvals: dict[str, dict] = {}


class ApprovalSubmitRequest(BaseModel):
    strategy_id: str
    target: str
    requester: Optional[str] = None
    notes: Optional[str] = None


class ApprovalCompleteRequest(BaseModel):
    result: str
    notes: Optional[str] = None


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_approval(req: ApprovalSubmitRequest) -> dict:
    approval_id = f"ap-{uuid.uuid4().hex[:12]}"
    approval = {
        "approval_id": approval_id,
        "strategy_id": req.strategy_id,
        "target": req.target,
        "requester": req.requester,
        "notes": req.notes,
        "approval_status": "pending",
        "result": None,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    _approvals[approval_id] = approval
    return approval


@router.get("/{approval_id}")
def get_approval(approval_id: str) -> dict:
    approval = _approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval {approval_id} not found")
    return approval


@router.post("/{approval_id}/complete")
def complete_approval(approval_id: str, req: ApprovalCompleteRequest) -> dict:
    approval = _approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval {approval_id} not found")
    if req.result not in ("approve", "reject"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="result must be 'approve' or 'reject'",
        )
    approval["approval_status"] = "completed"
    approval["result"] = req.result
    approval["completed_at"] = datetime.now(timezone.utc).isoformat()
    if req.notes:
        approval["notes"] = req.notes
    return approval
