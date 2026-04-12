"""因子双地同步工具 — 比对 decision 与 backtest 两端因子注册表。

TASK-0083 / Token: tok-e166b118
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def compare_registries(
    decision_factors: Dict[str, str],
    backtest_factors: Dict[str, str],
) -> Dict[str, any]:
    """比对 decision 与 backtest 两端因子注册表。

    Args:
        decision_factors: decision 端因子 {name: hash}
        backtest_factors: backtest 端因子 {name: hash}

    Returns:
        Dict 包含:
            - missing_in_decision: backtest 有但 decision 没有的因子
            - missing_in_backtest: decision 有但 backtest 没有的因子
            - hash_mismatch: 两端都有但 hash 不一致的因子
            - consistent: 两端一致的因子
    """
    decision_set = set(decision_factors.keys())
    backtest_set = set(backtest_factors.keys())

    missing_in_decision = list(backtest_set - decision_set)
    missing_in_backtest = list(decision_set - backtest_set)

    common = decision_set & backtest_set
    hash_mismatch = []
    consistent = []

    for name in common:
        if decision_factors[name] != backtest_factors[name]:
            hash_mismatch.append({
                "name": name,
                "decision_hash": decision_factors[name],
                "backtest_hash": backtest_factors[name],
            })
        else:
            consistent.append(name)

    result = {
        "missing_in_decision": missing_in_decision,
        "missing_in_backtest": missing_in_backtest,
        "hash_mismatch": hash_mismatch,
        "consistent": consistent,
    }

    # 输出警告日志
    if missing_in_decision:
        logger.warning(
            f"因子缺失（decision 端）: {', '.join(missing_in_decision)}"
        )
    if missing_in_backtest:
        logger.warning(
            f"因子缺失（backtest 端）: {', '.join(missing_in_backtest)}"
        )
    if hash_mismatch:
        logger.warning(
            f"因子版本不一致: {', '.join([m['name'] for m in hash_mismatch])}"
        )

    return result


def check_factor_hash(
    factor_name: str,
    decision_hash: Optional[str],
    backtest_hash: Optional[str],
) -> bool:
    """校验因子实现是否 bit-exact。

    Returns:
        True if hashes match, False otherwise
    """
    if decision_hash is None or backtest_hash is None:
        logger.warning(f"因子 {factor_name} 缺少 hash 信息")
        return False

    if decision_hash != backtest_hash:
        logger.warning(
            f"因子 {factor_name} hash 不一致: "
            f"decision={decision_hash}, backtest={backtest_hash}"
        )
        return False

    return True


def get_missing_factors(
    required_factors: List[str],
    available_factors: List[str],
) -> List[str]:
    """获取缺失因子列表。

    Args:
        required_factors: 所需因子列表
        available_factors: 可用因子列表

    Returns:
        缺失的因子列表
    """
    required_set = set(required_factors)
    available_set = set(available_factors)
    missing = list(required_set - available_set)

    if missing:
        logger.warning(f"缺失因子: {', '.join(missing)}")

    return missing
