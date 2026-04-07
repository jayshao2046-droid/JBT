"""services/decision/src/research — 研究中心公开接口导出。

使用 __getattr__ 懒加载：允许在重型依赖（xgboost/optuna/shap/onnx）未安装时
正常导入轻量子模块（session / factor_loader），仅在实际访问对应类时才触发重型导入。
各子模块文件本身保留顶层 import，确保 ImportError 在使用点快速暴露。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .factor_loader import FactorLoader
    from .onnx_export import OnnxExporter
    from .optuna_search import OptunaSearch
    from .session import ResearchSession
    from .shap_audit import ShapAuditor
    from .trainer import XGBoostTrainer

__all__ = [
    "ResearchSession",
    "XGBoostTrainer",
    "OptunaSearch",
    "ShapAuditor",
    "OnnxExporter",
    "FactorLoader",
]


def __getattr__(name: str) -> object:
    if name == "ResearchSession":
        from .session import ResearchSession
        return ResearchSession
    if name == "XGBoostTrainer":
        from .trainer import XGBoostTrainer
        return XGBoostTrainer
    if name == "OptunaSearch":
        from .optuna_search import OptunaSearch
        return OptunaSearch
    if name == "ShapAuditor":
        from .shap_audit import ShapAuditor
        return ShapAuditor
    if name == "OnnxExporter":
        from .onnx_export import OnnxExporter
        return OnnxExporter
    if name == "FactorLoader":
        from .factor_loader import FactorLoader
        return FactorLoader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
