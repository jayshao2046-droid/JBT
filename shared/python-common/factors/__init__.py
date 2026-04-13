"""JBT 因子共享包 — 统一因子注册表与双地同步工具。

TASK-0083 / Token: tok-e166b118
TASK-0084 / Token: tok-966162da
"""

from .registry import (
    FactorRegistry,
    get_factor_hash,
    list_factors,
    check_coverage,
    get_global_registry,
    register_global,
    get_jbt_factors,
)
from .sync import (
    compare_registries,
    check_factor_hash,
    get_missing_factors,
    generate_sync_report,
)

__all__ = [
    "FactorRegistry",
    "get_factor_hash",
    "list_factors",
    "check_coverage",
    "get_global_registry",
    "register_global",
    "get_jbt_factors",
    "compare_registries",
    "check_factor_hash",
    "get_missing_factors",
    "generate_sync_report",
]
