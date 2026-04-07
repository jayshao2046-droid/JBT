from typing import Optional

from ..core.settings import get_settings


def route(strategy_id: str, backtest_certificate_id: Optional[str], research_snapshot_id: Optional[str]) -> dict:
    settings = get_settings()

    if settings.model_router_require_backtest_cert and not backtest_certificate_id:
        return {
            "allowed": False,
            "reason": "backtest certificate required but not provided",
        }

    if settings.model_router_require_research_snapshot and not research_snapshot_id:
        return {
            "allowed": False,
            "reason": "research snapshot required but not provided",
        }

    return {
        "allowed": True,
        "reason": "all gate checks passed",
    }
