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
