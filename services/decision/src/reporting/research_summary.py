"""
ResearchSummaryBuilder — TASK-0021 F batch
研究会话完成后生成结构化摘要，供日报和通知使用。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


@dataclass
class ResearchSummary:
    session_id: str
    strategy_id: str
    model_id: str
    status: str                     # completed | failed
    started_at: str
    finished_at: str
    duration_seconds: float

    # 训练指标
    train_sharpe: Optional[float] = None
    train_accuracy: Optional[float] = None
    cv_mean_score: Optional[float] = None
    cv_std_score: Optional[float] = None

    # 最优参数（Optuna）
    best_params: Dict[str, Any] = field(default_factory=dict)
    best_value: Optional[float] = None
    n_trials: int = 0

    # SHAP 可解释
    top_features: List[str] = field(default_factory=list)
    shap_summary_path: Optional[str] = None

    # ONNX 导出
    onnx_path: Optional[str] = None
    onnx_verified: bool = False

    # 错误信息（仅 failed 状态）
    error_message: Optional[str] = None

    def to_notify_body(self) -> str:
        """生成飞书/邮件 Markdown 正文。"""
        lines = [
            f"**研究会话:** {self.session_id}",
            f"**策略:** {self.strategy_id}  |  **模型:** {self.model_id}",
            f"**状态:** {self.status}  |  **耗时:** {self.duration_seconds:.1f}s",
        ]
        if self.status == "completed":
            if self.train_sharpe is not None:
                lines.append(f"**训练Sharpe:** {self.train_sharpe:.4f}")
            if self.cv_mean_score is not None:
                cv_str = f"{self.cv_mean_score:.4f} ± {self.cv_std_score:.4f}" if self.cv_std_score is not None else f"{self.cv_mean_score:.4f}"
                lines.append(f"**CV得分:** {cv_str}")
            if self.best_value is not None:
                lines.append(f"**最优目标值:** {self.best_value:.4f}  |  **试验次数:** {self.n_trials}")
            if self.top_features:
                lines.append(f"**Top因子:** {', '.join(self.top_features[:5])}")
            if self.onnx_verified:
                lines.append(f"**ONNX导出:** ✅ 已验证")
        else:
            lines.append(f"**错误:** {self.error_message or '未知错误'}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "strategy_id": self.strategy_id,
            "model_id": self.model_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "train_sharpe": self.train_sharpe,
            "train_accuracy": self.train_accuracy,
            "cv_mean_score": self.cv_mean_score,
            "cv_std_score": self.cv_std_score,
            "best_params": self.best_params,
            "best_value": self.best_value,
            "n_trials": self.n_trials,
            "top_features": self.top_features,
            "shap_summary_path": self.shap_summary_path,
            "onnx_path": self.onnx_path,
            "onnx_verified": self.onnx_verified,
            "error_message": self.error_message,
        }


class ResearchSummaryBuilder:
    """将研究会话运行结果构建为 ResearchSummary。"""

    @staticmethod
    def from_session_result(session_id: str, result: Dict[str, Any]) -> ResearchSummary:
        """
        从研究会话执行结果字典构建摘要。
        result 预期来自 ResearchSession / XGBoostTrainer / OptunaSearch 的输出。
        """
        now_str = datetime.now(_TZ_CST).strftime("%Y-%m-%d %H:%M:%S")
        started_at = result.get("started_at", now_str)
        finished_at = result.get("finished_at", now_str)

        # 计算耗时
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            duration = (
                datetime.strptime(finished_at, fmt) - datetime.strptime(started_at, fmt)
            ).total_seconds()
        except (ValueError, TypeError):
            duration = 0.0

        top_features: List[str] = []
        shap_data = result.get("shap_summary", {})
        if isinstance(shap_data, dict):
            ranked = sorted(shap_data.items(), key=lambda x: abs(x[1]), reverse=True)
            top_features = [k for k, _ in ranked[:10]]

        return ResearchSummary(
            session_id=session_id,
            strategy_id=result.get("strategy_id", ""),
            model_id=result.get("model_id", "XGBoost"),
            status=result.get("status", "completed"),
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            train_sharpe=result.get("train_sharpe"),
            train_accuracy=result.get("train_accuracy"),
            cv_mean_score=result.get("cv_mean_score"),
            cv_std_score=result.get("cv_std_score"),
            best_params=result.get("best_params", {}),
            best_value=result.get("best_value"),
            n_trials=result.get("n_trials", 0),
            top_features=top_features,
            shap_summary_path=result.get("shap_summary_path"),
            onnx_path=result.get("onnx_path"),
            onnx_verified=bool(result.get("onnx_verified", False)),
            error_message=result.get("error_message"),
        )
