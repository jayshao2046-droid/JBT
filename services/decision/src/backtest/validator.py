"""策略参数验证器"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ParameterValidator:
    """策略参数验证器"""

    def __init__(self) -> None:
        self.errors: List[str] = []

    def validate_type(self, param_name: str, value: Any, expected_type: type) -> bool:
        """验证参数类型"""
        if not isinstance(value, expected_type):
            self.errors.append(
                f"参数 {param_name} 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
            )
            return False
        return True

    def validate_range(
        self,
        param_name: str,
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> bool:
        """验证参数范围"""
        if min_value is not None and value < min_value:
            self.errors.append(f"参数 {param_name} 小于最小值 {min_value}: {value}")
            return False

        if max_value is not None and value > max_value:
            self.errors.append(f"参数 {param_name} 大于最大值 {max_value}: {value}")
            return False

        return True

    def validate_dependencies(
        self, params: Dict[str, Any], dependencies: Dict[str, List[str]]
    ) -> bool:
        """验证参数依赖关系"""
        for param, required_params in dependencies.items():
            if param in params:
                for required in required_params:
                    if required not in params:
                        self.errors.append(
                            f"参数 {param} 依赖参数 {required}，但 {required} 未提供"
                        )
                        return False
        return True

    def validate_strategy_params(
        self, strategy_id: str, params: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """验证策略参数"""
        self.errors = []

        # 通用参数验证
        if "initial_capital" in params:
            if not self.validate_type("initial_capital", params["initial_capital"], (int, float)):
                return False, self.errors
            if not self.validate_range("initial_capital", float(params["initial_capital"]), min_value=10000):
                return False, self.errors

        if "slippage_per_unit" in params:
            if not self.validate_type("slippage_per_unit", params["slippage_per_unit"], (int, float)):
                return False, self.errors
            if not self.validate_range("slippage_per_unit", float(params["slippage_per_unit"]), min_value=0):
                return False, self.errors

        if "commission_per_lot_round_turn" in params:
            if not self.validate_type(
                "commission_per_lot_round_turn", params["commission_per_lot_round_turn"], (int, float)
            ):
                return False, self.errors
            if not self.validate_range(
                "commission_per_lot_round_turn", float(params["commission_per_lot_round_turn"]), min_value=0
            ):
                return False, self.errors

        # 策略特定参数验证（可扩展）
        if strategy_id == "generic":
            # 通用策略参数验证
            if "timeframe_minutes" in params:
                if not self.validate_type("timeframe_minutes", params["timeframe_minutes"], int):
                    return False, self.errors
                if not self.validate_range(
                    "timeframe_minutes", float(params["timeframe_minutes"]), min_value=1, max_value=1440
                ):
                    return False, self.errors

        return len(self.errors) == 0, self.errors
