"""Decision 内聚的正式回测执行包。"""

# 导入模板模块以注册 formal strategy template。
from . import fc_224_strategy as _fc_224_strategy  # noqa: F401
from . import generic_strategy as _generic_strategy  # noqa: F401
from .local_engine import ApiDataProvider, LocalBacktestEngine, LocalBacktestParams
from .runner import BacktestExecutionError, BacktestJobInput, OnlineBacktestRunner

__all__ = [
    "ApiDataProvider",
    "BacktestExecutionError",
    "BacktestJobInput",
    "LocalBacktestEngine",
    "LocalBacktestParams",
    "OnlineBacktestRunner",
]