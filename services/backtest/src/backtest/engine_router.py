"""TASK-0018 批次 C — 双引擎路由层

根据 engine_type 字段分发到对应执行引擎：
  - tqsdk：既有 OnlineBacktestRunner 路径（由 API 层直接调用，本模块只做类型校验）
  - local ：新增 LocalBacktestEngine 路径

不支持的值抛出 EngineTypeError，API 层捕获后转 HTTP 422。
"""
from __future__ import annotations

from typing import Any, Literal, Optional

try:
    from .local_engine import LocalBacktestEngine, LocalBacktestParams, LocalBacktestReport
except ImportError:
    from local_engine import LocalBacktestEngine, LocalBacktestParams, LocalBacktestReport

EngineType = Literal["tqsdk", "local"]

SUPPORTED_ENGINES: frozenset = frozenset({"tqsdk", "local"})


class EngineTypeError(ValueError):
    """不支持的引擎类型；API 层应将此异常转为 HTTP 422。"""


def resolve_engine_type(engine_type: Any) -> EngineType:
    """
    校验并标准化 engine_type 字段。

    - 未提供（None）时默认返回 "tqsdk"，保持既有路径兼容。
    - 不支持的值抛 EngineTypeError。
    """
    if engine_type is None:
        return "tqsdk"
    normalized = str(engine_type).strip().lower()
    if normalized not in SUPPORTED_ENGINES:
        raise EngineTypeError(
            f"Unsupported engine_type: '{engine_type}'. "
            f"Allowed values: {sorted(SUPPORTED_ENGINES)}"
        )
    return normalized  # type: ignore[return-value]


class EngineRouter:
    """
    统一引擎路由器。

    职责：
      1. 校验 engine_type 合法性（validate_engine_type）。
      2. 执行 local 引擎回测（route_local）。
      3. tqsdk 路径由调用方（jobs.py）直接调用既有 OnlineBacktestRunner，
         本路由器不介入 tqsdk 执行细节，仅负责类型校验。
    """

    def __init__(
        self,
        *,
        local_engine: Optional[LocalBacktestEngine] = None,
    ) -> None:
        self._local_engine = local_engine or LocalBacktestEngine()

    @staticmethod
    def validate_engine_type(engine_type: Any) -> EngineType:
        """
        校验 engine_type 字段，返回标准化后的值。
        不支持的值抛 EngineTypeError。
        """
        return resolve_engine_type(engine_type)

    def route_local(self, params: LocalBacktestParams) -> LocalBacktestReport:
        """
        执行 local 引擎回测，返回 LocalBacktestReport。
        不影响 tqsdk 路径任何逻辑。
        """
        return self._local_engine.run(params)
