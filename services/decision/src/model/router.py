from typing import Optional

from ..core.settings import get_settings
from ..gating.backtest_gate import get_backtest_gate
from ..gating.research_gate import get_research_gate
from ..strategy.repository import get_repository


def _reject(reason: str) -> dict:
    return {
        "allowed": False,
        "reason": reason,
    }


def route(
    strategy_id: str,
    backtest_certificate_id: Optional[str],
    research_snapshot_id: Optional[str],
) -> dict:
    settings = get_settings()
    strategy_pkg = get_repository().get(strategy_id)

    if (
        strategy_pkg is not None
        and strategy_pkg.backtest_certificate_id
        and backtest_certificate_id
        and strategy_pkg.backtest_certificate_id != backtest_certificate_id
    ):
        return _reject("requested backtest certificate does not match strategy package")

    if (
        strategy_pkg is not None
        and strategy_pkg.research_snapshot_id
        and research_snapshot_id
        and strategy_pkg.research_snapshot_id != research_snapshot_id
    ):
        return _reject("requested research snapshot does not match strategy package")

    backtest_cert = None
    expected_backtest_id = backtest_certificate_id or (
        strategy_pkg.backtest_certificate_id if strategy_pkg is not None else None
    )
    if settings.model_router_require_backtest_cert or expected_backtest_id:
        backtest_cert = get_backtest_gate().get_cert(strategy_id)
        if backtest_cert is None or backtest_cert.review_status != "approved":
            return _reject("no valid backtest certificate found for strategy")
        if expected_backtest_id and backtest_cert.certificate_id != expected_backtest_id:
            return _reject("backtest certificate does not match active eligibility")
        if (
            strategy_pkg is not None
            and strategy_pkg.factor_version_hash
            and backtest_cert.factor_version_hash
            and strategy_pkg.factor_version_hash != backtest_cert.factor_version_hash
        ):
            return _reject("backtest certificate factor version hash mismatch")

    research_snapshot = None
    expected_research_id = research_snapshot_id or (
        strategy_pkg.research_snapshot_id if strategy_pkg is not None else None
    )
    if settings.model_router_require_research_snapshot or expected_research_id:
        research_snapshot = get_research_gate().get_snapshot(strategy_id)
        if research_snapshot is None or research_snapshot.research_status != "completed":
            return _reject("no completed research snapshot found for strategy")
        if expected_research_id and research_snapshot.research_snapshot_id != expected_research_id:
            return _reject("research snapshot does not match active eligibility")
        if (
            strategy_pkg is not None
            and strategy_pkg.factor_version_hash
            and research_snapshot.factor_version_hash
            and strategy_pkg.factor_version_hash != research_snapshot.factor_version_hash
        ):
            return _reject("research snapshot factor version hash mismatch")

    if (
        backtest_cert is not None
        and research_snapshot is not None
        and backtest_cert.factor_version_hash
        and research_snapshot.factor_version_hash
        and backtest_cert.factor_version_hash != research_snapshot.factor_version_hash
    ):
        return _reject("backtest and research eligibility factor version hash mismatch")

    return {
        "allowed": True,
        "reason": "all gate checks passed",
    }
