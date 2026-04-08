from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...core.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> JSONResponse:
    settings = get_settings()
    return JSONResponse({"status": "ok", "service": "decision", "port": settings.decision_port})


@router.get("/ready")
def readiness_check() -> JSONResponse:
    return JSONResponse({"ready": True})
