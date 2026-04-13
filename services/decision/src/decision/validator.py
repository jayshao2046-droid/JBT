"""
策略参数验证模块
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ParameterValidator:
    """策略参数验证器"""

    def __init__(self):
        self.errors: List[str] = []

    def validate_type(self, param_name: str, param_value: Any, expected_type: str) -> bool:
        """验证参数类型"""
        type_map = {
            "int": int,
            "float": (int, float),
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
        }

        if expected_type not in type_map:
            self.errors.append(f"未知的类型: {expected_type}")
            return False

        if not isinstance(param_value, type_map[expected_type]):
            self.errors.append(
                f"参数 '{param_name}' 类型错误: 期望 {expected_type}, 实际 {type(param_value).__name__}"
            )
            return False

        return True

    def validate_range(
        self, param_name: str, param_value: float, min_val: Optional[float] = None, max_val: Optional[float] = None
    ) -> bool:
        """验证参数范围"""
        if min_val is not None and param_value < min_val:
            self.errors.append(f"参数 '{param_name}' 小于最小值: {param_value} < {min_val}")
            return False

        if max_val is not None and param_value > max_val:
            self.errors.append(f"参数 '{param_name}' 大于最大值: {param_value} > {max_val}")
            return False

        return True

    def validate_dependencies(self, params: Dict[str, Any], rules: List[Dict]) -> bool:
        """验证参数依赖关系"""
        for rule in rules:
            param = rule.get("param")
            depends_on = rule.get("depends_on")
            condition = rule.get("condition")

            if param not in params:
                continue

            if depends_on not in params:
                self.errors.append(f"参数 '{param}' 依赖的参数 '{depends_on}' 不存在")
                return False

            # 简单条件检查
            if condition == "greater_than":
                if params[param] <= params[depends_on]:
                    self.errors.append(
                        f"参数 '{param}' 必须大于 '{depends_on}': {params[param]} <= {params[depends_on]}"
                    )
                    return False

            elif condition == "less_than":
                if params[param] >= params[depends_on]:
                    self.errors.append(
                        f"参数 '{param}' 必须小于 '{depends_on}': {params[param]} >= {params[depends_on]}"
                    )
                    return False

        return True

    def validate_all(self, params: Dict[str, Any], schema: Dict) -> Dict:
        """验证所有参数"""
        self.errors = []
        is_valid = True

        # 验证必填参数
        required = schema.get("required", [])
        for param_name in required:
            if param_name not in params:
                self.errors.append(f"缺少必填参数: {param_name}")
                is_valid = False

        # 验证参数类型和范围
        properties = schema.get("properties", {})
        for param_name, param_value in params.items():
            if param_name not in properties:
                continue

            prop = properties[param_name]

            # 类型验证
            if "type" in prop:
                if not self.validate_type(param_name, param_value, prop["type"]):
                    is_valid = False

            # 范围验证
            if "min" in prop or "max" in prop:
                if not self.validate_range(param_name, param_value, prop.get("min"), prop.get("max")):
                    is_valid = False

        # 依赖关系验证
        dependencies = schema.get("dependencies", [])
        if dependencies:
            if not self.validate_dependencies(params, dependencies):
                is_valid = False

        return {"valid": is_valid, "errors": self.errors}
