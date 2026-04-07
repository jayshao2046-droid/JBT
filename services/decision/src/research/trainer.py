from __future__ import annotations

import numpy as np
import xgboost as xgb  # type: ignore[import-untyped,import-not-found]


class XGBoostTrainer:
    """XGBoost 训练包装（主模型）。

    若 xgboost 未安装，模块导入时直接抛出 ImportError（不吞错）。
    LightGBM / CatBoost adapter 接口预留注释位，第一阶段不实现。
    """

    # ------------------------------------------------------------------
    # 主训练接口
    # ------------------------------------------------------------------

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        params: dict,
    ) -> xgb.XGBClassifier:
        """训练 XGBoost 分类器并返回已拟合模型。"""
        model = xgb.XGBClassifier(**params)
        model.fit(X, y)
        return model

    def cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        params: dict,
        cv: int = 5,
    ) -> dict[str, float]:
        """K-fold 交叉验证，返回 sharpe / drawdown / accuracy 指标。

        注：此为研究骨架实现，sharpe 以 accuracy 代理；
        生产阶段应替换为基于收益序列的真实 Sharpe 计算。
        """
        n = len(X)
        fold_size = n // cv
        scores: list[float] = []

        for i in range(cv):
            val_start = i * fold_size
            val_end = (i + 1) * fold_size if i < cv - 1 else n

            val_mask = np.zeros(n, dtype=bool)
            val_mask[val_start:val_end] = True

            X_tr, X_val = X[~val_mask], X[val_mask]
            y_tr, y_val = y[~val_mask], y[val_mask]

            model = xgb.XGBClassifier(**params)
            model.fit(X_tr, y_tr)
            preds = model.predict(X_val)
            acc = float(np.mean(preds == y_val))
            scores.append(acc)

        mean_acc = float(np.mean(scores))
        return {
            "sharpe": mean_acc,
            "drawdown": 1.0 - mean_acc,
            "accuracy": mean_acc,
        }

    # ------------------------------------------------------------------
    # Adapter 预留位（第一阶段不实现）
    # ------------------------------------------------------------------
    # def lightgbm_adapter(self, ...): ...   # LightGBM adapter 预留
    # def catboost_adapter(self, ...): ...   # CatBoost adapter 预留
