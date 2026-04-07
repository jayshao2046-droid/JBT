from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "decision", "port": 8104})


@router.get("/ready")
def readiness_check() -> JSONResponse:
    return JSONResponse({"ready": True})
