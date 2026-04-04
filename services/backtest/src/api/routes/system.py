"""
System routes — /api/system/status  /api/system/logs
"""
from __future__ import annotations

import os
import platform
import time
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])

_START_TIME = time.time()


@router.get("/status")
def get_status() -> Dict[str, Any]:
    return {
        "status": "running",
        "uptime": time.time() - _START_TIME,
        "platform": platform.system(),
        "pid": os.getpid(),
        "cpu_percent": 0.0,
        "memory_percent": 0.0,
    }


@router.get("/logs")
def get_logs() -> str:
    return "System logs not yet connected to log file in Phase 1."
