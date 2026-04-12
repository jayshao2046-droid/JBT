"""统一因子注册表 — 记录 JBT 已有因子的名称、版本、hash。

TASK-0083 / Token: tok-e166b118
"""

import hashlib
import inspect
from typing import Any, Callable, Dict, List, Optional


class FactorRegistry:
    """因子注册表：因子名称 → 计算函数签名 → 版本号 → hash。"""

    def __init__(self) -> None:
        self._factors: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        calculator: Callable,
        version: str = "1.0.0",
        description: str = "",
    ) -> None:
        """注册因子到共享注册表。

        Args:
            name: 因子名称（如 "MA", "RSI", "MACD"）
            calculator: 因子计算函数
            version: 版本号（语义化版本）
            description: 因子描述
        """
        factor_hash = self._compute_hash(calculator)
        self._factors[name] = {
            "name": name,
            "calculator": calculator,
            "version": version,
            "hash": factor_hash,
            "description": description,
            "signature": str(inspect.signature(calculator)),
        }

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """获取因子信息。"""
        return self._factors.get(name)

    def list_all(self) -> List[str]:
        """列出所有已注册因子名称。"""
        return sorted(self._factors.keys())

    def get_hash(self, name: str) -> Optional[str]:
        """获取因子实现的 hash。"""
        factor = self._factors.get(name)
        return factor["hash"] if factor else None

    def check_coverage(self, required_factors: List[str]) -> Dict[str, bool]:
        """检查所需因子是否都已注册。

        Returns:
            Dict[因子名称, 是否已注册]
        """
        return {name: name in self._factors for name in required_factors}

    @staticmethod
    def _compute_hash(calculator: Callable) -> str:
        """计算因子函数的 SHA-256 hash（基于源码）。"""
        try:
            source = inspect.getsource(calculator)
            return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        except (OSError, TypeError):
            # 无法获取源码（如 built-in 函数），使用函数名作为 fallback
            return hashlib.sha256(calculator.__name__.encode("utf-8")).hexdigest()[:16]


# 全局共享注册表实例
_global_registry = FactorRegistry()


# JBT 已有因子列表（从 backtest/factor_registry.py 提取）
_JBT_FACTORS = [
    "SMA", "EMA", "MACD", "RSI", "VolumeRatio", "ATR", "ADX",
    "BollingerBands", "DonchianBreakout", "WilliamsR", "KDJ", "CCI",
    "OBV", "VWAP", "MFI", "ATRTrailingStop", "HistoricalVol",
    "EMA_Cross", "EMA_Slope", "DEMA", "ParabolicSAR", "Supertrend",
    "Ichimoku", "WMA", "HMA", "TEMA", "Stochastic", "StochasticRSI",
    "ROC", "MOM", "CMO", "KeltnerChannel", "NTR", "Aroon", "TRIX",
    "LinReg", "ChaikinAD", "CMF", "PVT", "Stdev", "ZScore",
    "BullBearPower", "DPO", "Spread", "Spread_RSI",
]


def get_factor_hash(name: str) -> Optional[str]:
    """获取因子实现的 hash。"""
    return _global_registry.get_hash(name)


def list_factors() -> List[str]:
    """列出所有已注册因子。"""
    return _global_registry.list_all()


def check_coverage(required_factors: List[str]) -> Dict[str, bool]:
    """检查所需因子是否都已注册。"""
    return _global_registry.check_coverage(required_factors)


def get_jbt_factors() -> List[str]:
    """返回 JBT 已有因子列表。"""
    return _JBT_FACTORS.copy()
