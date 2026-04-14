from __future__ import annotations

from typing import Optional

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

        TASK-0112-C: sharpe 改为基于真实收益序列计算（用 _calc_real_sharpe），
        不再以 accuracy 代理。
        """
        n = len(X)
        fold_size = n // cv
        sharpe_scores: list[float] = []
        acc_scores: list[float] = []

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
            sharpe_scores.append(self._calc_real_sharpe(preds, y_val))
            acc_scores.append(float(np.mean(preds == y_val)))

        mean_sharpe = float(np.mean(sharpe_scores))
        mean_acc = float(np.mean(acc_scores))
        return {
            "sharpe": mean_sharpe,
            "drawdown": max(0.0, 1.0 - mean_acc),
            "accuracy": mean_acc,
        }

    def train_for_symbol(
        self,
        symbol: str,
        regime: str,
        X: np.ndarray,
        y: np.ndarray,
        params: dict,
        existing_model: Optional[xgb.XGBClassifier] = None,
        val_ratio: float = 0.2,
    ) -> tuple[xgb.XGBClassifier, dict[str, float]]:
        """品种级训练（TASK-0112-C / TASK-0114）。

        支持方案B增量训练：传入 existing_model 时用 xgb_model 参数追加新树，
        保留已学习结构，不覆盖其他品种模型。
        增量训练安全检查：若 val Sharpe 低于原模型 5%，回滚到原模型。

        Args:
            symbol: 品种代码（如 'rb'）
            regime: 行情类型（'trend' / 'oscillation' / 'high_vol'）
            X: 特征矩阵
            y: 标签（+1/-1 或 0/1，代表方向）
            params: XGBoost 参数 dict
            existing_model: 现有模型（增量训练时传入）
            val_ratio: 验证集比例

        Returns:
            (trained_model, metrics)，metrics 含 sharpe / accuracy
        """
        split = max(1, int(len(X) * (1 - val_ratio)))
        X_tr, X_val = X[:split], X[split:]
        y_tr, y_val = y[:split], y[split:]

        model = xgb.XGBClassifier(early_stopping_rounds=50, **params)
        if existing_model is not None:
            model.fit(
                X_tr, y_tr,
                xgb_model=existing_model,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
        else:
            model.fit(
                X_tr, y_tr,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )

        preds = model.predict(X_val)
        new_sharpe = self._calc_real_sharpe(preds, y_val)
        acc = float(np.mean(preds == y_val)) if len(y_val) > 0 else 0.0

        # 增量训练安全检查：若 val Sharpe 下降 >5%，回滚
        if existing_model is not None:
            old_preds = existing_model.predict(X_val)
            old_sharpe = self._calc_real_sharpe(old_preds, y_val)
            if old_sharpe > 0 and new_sharpe < old_sharpe * 0.95:
                return existing_model, {"sharpe": old_sharpe, "accuracy": acc, "rolled_back": True}

        return model, {"sharpe": new_sharpe, "accuracy": acc, "symbol": symbol, "regime": regime}

    @staticmethod
    def _calc_real_sharpe(
        y_pred: np.ndarray,
        y_true: np.ndarray,
        risk_free: float = 0.0,
        annualize: int = 252,
    ) -> float:
        """用预测方向 × 真实标签构造日收益序列，计算年化 Sharpe。

        TASK-0112-C: 替换 cross_validate 中的 accuracy 代理。

        方向映射：preds 为 0/1 时，signal = 2*pred - 1（→ -1 或 +1）；
        y_true 同样做相同映射作为实际收益方向。
        returns_i = direction_pred_i × label_i（同向盈，反向亏）
        """
        if len(y_pred) == 0 or len(y_true) == 0:
            return 0.0
        # 规范化到 -1/+1 方向
        sign_pred = np.where(y_pred >= 0.5, 1.0, -1.0)
        sign_true = np.where(y_true >= 0.5, 1.0, -1.0)
        returns = sign_pred * sign_true  # +1 = 对, -1 = 错
        std = float(np.std(returns))
        if std < 1e-8:
            return 0.0
        sharpe = (float(np.mean(returns)) - risk_free) / std * (annualize ** 0.5)
        return float(sharpe)

    # ------------------------------------------------------------------
    # Adapter 预留位（第一阶段不实现）
    # ------------------------------------------------------------------
    # def lightgbm_adapter(self, ...): ...   # LightGBM adapter 预留
    # def catboost_adapter(self, ...): ...   # CatBoost adapter 预留
