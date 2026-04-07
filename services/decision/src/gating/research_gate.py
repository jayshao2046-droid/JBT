from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ResearchSnapshot:
    """内存研究快照，字段名对齐 shared/contracts/decision/research_snapshot.md"""

    research_snapshot_id: str       # 对应 session_id，全局唯一
    strategy_id: str
    factor_version_hash: str        # 因子版本哈希，用于资格门禁比对
    best_params: dict               # Optuna 最优参数
    metrics: dict                   # sharpe / drawdown / accuracy
    research_status: str            # completed / failed / expired
    shap_summary_path: str = ""     # SHAP 摘要 JSON 路径（占位）
    onnx_artifact_path: str = ""    # ONNX 模型文件路径（占位）
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ResearchGate:
    """验证策略是否已完成研究阶段（有 research_snapshot 且状态为 completed）。

    内存存储（dict），不依赖外部 DB。
    """

    def __init__(self) -> None:
        # strategy_id → ResearchSnapshot（每个策略保留最新一份）
        self._snapshots: dict[str, ResearchSnapshot] = {}

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def is_complete(self, strategy_id: str) -> bool:
        """返回策略是否已完成研究阶段。"""
        snap = self._snapshots.get(strategy_id)
        if snap is None:
            return False
        return snap.research_status == "completed"

    def register_snapshot(
        self,
        session_id: str,
        strategy_id: str,
        factor_hash: str,
        best_params: dict,
        metrics: dict,
        shap_summary_path: str = "",
        onnx_artifact_path: str = "",
    ) -> ResearchSnapshot:
        """注册（或覆盖）一份研究快照，状态固定为 completed。"""
        snap = ResearchSnapshot(
            research_snapshot_id=session_id,
            strategy_id=strategy_id,
            factor_version_hash=factor_hash,
            best_params=best_params,
            metrics=metrics,
            research_status="completed",
            shap_summary_path=shap_summary_path,
            onnx_artifact_path=onnx_artifact_path,
        )
        self._snapshots[strategy_id] = snap
        return snap

    def get_snapshot(self, strategy_id: str) -> Optional[ResearchSnapshot]:
        """获取策略最新研究快照。"""
        return self._snapshots.get(strategy_id)
