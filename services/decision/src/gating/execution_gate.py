from ..core.settings import get_settings


def check_execution_eligibility(strategy_id: str, target: str) -> dict:
    settings = get_settings()

    if target == "live-trading":
        if settings.live_trading_gate_locked:
            return {
                "eligible": False,
                "target": target,
                "reason": "live-trading gate locked",
            }
        return {
            "eligible": False,
            "target": target,
            "reason": "live-trading not permitted in current phase",
        }

    if target == "sim-trading":
        if not settings.execution_gate_enabled:
            return {
                "eligible": False,
                "target": target,
                "reason": "execution gate disabled",
            }
        return {
            "eligible": True,
            "target": target,
            "reason": "sim-trading gate open",
        }

    return {
        "eligible": False,
        "target": target,
        "reason": f"unknown target: {target}",
    }
