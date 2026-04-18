from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import optuna  # type: ignore[import-untyped,import-not-found]

if TYPE_CHECKING:
    from .trainer import XGBoostTrainer

optuna.logging.set_verbosity(optuna.logging.WARNING)


class OptunaSearch:
    """Optuna 参数搜索（夜间批量）。

    若 optuna 未安装，模块导入时直接抛出 ImportError（不吞错）。
    trainer 通过参数注入，OptunaSearch 不在模块层 import XGBoostTrainer，
    避免 xgboost → optuna 双重依赖在 TYPE_CHECKING 外暴露。
    """

    def run_search(
        self,
        trainer: Any,  # XGBoostTrainer（运行时注入）
        X: np.ndarray,
        y: np.ndarray,
        n_trials: int = 50,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """执行 Optuna 参数搜索，返回最优参数 dict。

        目标函数：最大化 sharpe（minimize -sharpe）。
        参数空间：n_estimators / max_depth / learning_rate / subsample。
        结果不写文件，直接返回 best_params dict。
        """

        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                "max_depth": trial.suggest_int("max_depth", 3, 8),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "eval_metric": "logloss",
                "use_label_encoder": False,
            }
            cv_result: dict[str, float] = trainer.cross_validate(X, y, params)
            return -cv_result["sharpe"]  # minimize -sharpe

        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials, timeout=timeout)
        return dict(study.best_params)

    def schedule_nightly(
        self,
        trainer: Any,
        X: np.ndarray,
        y: np.ndarray,
        symbol: str = "all",
        n_trials: int = 80,
        timeout: Optional[int] = 3600,
    ) -> dict[str, Any]:
        """夜间批量参数调优入口（TASK-0112-C）。

        由 qwen3:14b 在非交易时段触发，搜索最优 XGBoost 参数。
        返回 best_params + 调优摘要，不自动写入注册表（由调用方决定是否注册）。

        Args:
            trainer: XGBoostTrainer 实例
            X: 特征矩阵
            y: 标签
            symbol: 品种代码或 'all'
            n_trials: Optuna trials 数量
            timeout: 最大运行秒数（None = 不限）

        Returns:
            {"symbol": ..., "best_params": ..., "best_sharpe": ..., "n_trials": ...}
        """
        best_params = self.run_search(trainer, X, y, n_trials=n_trials, timeout=timeout)
        # 用最优参数做一次验证，获取 sharpe 估算
        cv_result = trainer.cross_validate(X, y, best_params)
        return {
            "symbol": symbol,
            "best_params": best_params,
            "best_sharpe": cv_result["sharpe"],
            "best_accuracy": cv_result["accuracy"],
            "n_trials": n_trials,
        }
