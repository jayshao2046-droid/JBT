from __future__ import annotations

import json
from typing import Any

import numpy as np
import shap


class ShapAuditor:
    """SHAP 离线解释（审计用）。

    若 shap 未安装，模块导入时直接抛出 ImportError（不吞错）。
    使用 shap.TreeExplainer 支持 XGBoost / LightGBM 等树模型。
    """

    def explain(self, model: Any, X: np.ndarray) -> dict[str, float]:
        """计算各特征的平均绝对 SHAP 值，返回 {feature_name: mean_abs_shap}。

        多分类场景下取各类 SHAP 值的绝对均值后再跨样本平均。
        """
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            # 多分类：各类 SHAP 值列表，取绝对值后按类平均
            abs_per_class = np.array([np.abs(sv) for sv in shap_values])
            abs_values = np.mean(abs_per_class, axis=0)
        else:
            abs_values = np.abs(shap_values)

        mean_abs: np.ndarray = np.mean(abs_values, axis=0)
        n_features = X.shape[1]
        return {f"feature_{i}": float(mean_abs[i]) for i in range(n_features)}

    def save_summary(self, values: dict[str, float], output_path: str) -> str:
        """将 feature importance dict 序列化为 JSON 文件，返回文件路径。"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(values, f, indent=2, ensure_ascii=False)
        return output_path
