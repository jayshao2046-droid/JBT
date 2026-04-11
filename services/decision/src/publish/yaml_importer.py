"""
YAML 策略解析适配器 — TASK-0051 C0-3
解析 YAML 格式策略定义并校验必填字段。
"""
from __future__ import annotations

from typing import Any, Dict, List


def parse_yaml_strategy(yaml_content: str) -> Dict[str, Any]:
    """
    解析 YAML 格式策略定义为 dict。

    Raises:
        ImportError: yaml 库不可用时抛出。
        ValueError: YAML 内容解析失败时抛出。
    """
    try:
        import yaml  # noqa: F811
    except ImportError:
        raise ImportError("需要安装 PyYAML 库: pip install pyyaml")

    if not yaml_content or not yaml_content.strip():
        raise ValueError("YAML 内容不能为空")

    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML 解析失败: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("YAML 内容必须为字典结构")

    return data


def validate_yaml_schema(data: Dict[str, Any]) -> List[str]:
    """
    校验 YAML 数据必填字段。

    Returns:
        错误列表，空列表表示校验通过。
    """
    errors: List[str] = []
    for field_name in ("name", "symbol", "exchange"):
        value = data.get(field_name)
        if not value or not isinstance(value, str) or not value.strip():
            errors.append(f"缺少必填字段: {field_name}")
    return errors
