from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .trainer import XGBoostTrainer


class ResearchStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ResearchArtifacts:
    """研究产物路径占位对象。"""

    shap_path: str = ""
    onnx_path: str = ""


@dataclass
class ResearchSession:
    """研究会话，持有 XGBoost trainer + Optuna + SHAP + ONNX 资源。

    trainer 通过依赖注入传入，session.py 不在模块层 import trainer，
    避免 xgboost 未安装时拖累会话管理层。
    """

    strategy_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = field(default=ResearchStatus.PENDING)
    factor_hash: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None
    best_params: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    trainer: Any = None  # XGBoostTrainer（运行时注入）
    artifacts: ResearchArtifacts = field(default_factory=ResearchArtifacts)

    # ------------------------------------------------------------------
    # 状态流转
    # ------------------------------------------------------------------

    def start(self) -> None:
        """PENDING → RUNNING。"""
        if self.status != ResearchStatus.PENDING:
            raise ValueError(
                f"Cannot start session in status: {self.status!r}"
            )
        self.status = ResearchStatus.RUNNING

    def complete(self, best_params: dict, metrics: dict) -> None:
        """RUNNING → COMPLETED，记录最优参数与绩效指标。"""
        if self.status != ResearchStatus.RUNNING:
            raise ValueError(
                f"Cannot complete session in status: {self.status!r}"
            )
        self.best_params = best_params
        self.metrics = metrics
        self.status = ResearchStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, reason: str = "") -> None:
        """任意状态 → FAILED。"""
        self.status = ResearchStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
