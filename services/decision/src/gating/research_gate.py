from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ..persistence.state_store import MemoryStateStore, get_state_store


@dataclass
class ResearchSnapshot:
    """研究快照，字段名对齐 shared/contracts/decision/research_snapshot.md。"""

    research_snapshot_id: str       # 对应 session_id，全局唯一
    strategy_id: str
    factor_version_hash: str        # 因子版本哈希，用于资格门禁比对
    best_params: dict               # Optuna 最优参数
    metrics: dict                   # sharpe / drawdown / accuracy
    research_status: str            # completed / failed / expired
    shap_summary_path: str = ""     # SHAP 摘要 JSON 路径（占位）
    onnx_artifact_path: str = ""    # ONNX 模型文件路径（占位）
    valid_until: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSnapshot":
        return cls(
            research_snapshot_id=data["research_snapshot_id"],
            strategy_id=data["strategy_id"],
            factor_version_hash=data["factor_version_hash"],
            best_params=dict(data.get("best_params") or {}),
            metrics=dict(data.get("metrics") or {}),
            research_status=data["research_status"],
            shap_summary_path=data.get("shap_summary_path", ""),
            onnx_artifact_path=data.get("onnx_artifact_path", ""),
            valid_until=datetime.fromisoformat(data["valid_until"]),
            generated_at=datetime.fromisoformat(data["generated_at"]),
        )

    def to_dict(self) -> dict:
        return {
            "research_snapshot_id": self.research_snapshot_id,
            "strategy_id": self.strategy_id,
            "factor_version_hash": self.factor_version_hash,
            "best_params": dict(self.best_params),
            "metrics": dict(self.metrics),
            "research_status": self.research_status,
            "shap_summary_path": self.shap_summary_path,
            "onnx_artifact_path": self.onnx_artifact_path,
            "valid_until": self.valid_until.isoformat(),
            "generated_at": self.generated_at.isoformat(),
        }


class ResearchGate:
    """验证策略是否已完成研究阶段（有 research_snapshot 且状态为 completed）。"""

    def __init__(self, state_store=None) -> None:
        self._state_store = state_store or MemoryStateStore()

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def _refresh_expiry(self, snap: ResearchSnapshot) -> None:
        if snap.research_status == "completed":
            if datetime.now(timezone.utc) > snap.valid_until:
                snap.research_status = "expired"
                self._state_store.upsert_record(
                    "research_snapshots",
                    snap.strategy_id,
                    snap.to_dict(),
                )

    def _load_snapshot(self, strategy_id: str) -> Optional[ResearchSnapshot]:
        raw = self._state_store.get_record("research_snapshots", strategy_id)
        return ResearchSnapshot.from_dict(raw) if raw is not None else None

    def is_complete(self, strategy_id: str) -> bool:
        """返回策略是否已完成研究阶段。"""
        snap = self._load_snapshot(strategy_id)
        if snap is None:
            return False
        self._refresh_expiry(snap)
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
        valid_days: int = 30,
    ) -> ResearchSnapshot:
        """注册（或覆盖）一份研究快照，状态固定为 completed。"""
        generated_at = datetime.now(timezone.utc)
        snap = ResearchSnapshot(
            research_snapshot_id=session_id,
            strategy_id=strategy_id,
            factor_version_hash=factor_hash,
            best_params=best_params,
            metrics=metrics,
            research_status="completed",
            shap_summary_path=shap_summary_path,
            onnx_artifact_path=onnx_artifact_path,
            valid_until=generated_at + timedelta(days=valid_days),
            generated_at=generated_at,
        )
        self._state_store.upsert_record("research_snapshots", strategy_id, snap.to_dict())
        return snap

    def get_snapshot(self, strategy_id: str) -> Optional[ResearchSnapshot]:
        """获取策略最新研究快照。"""
        snap = self._load_snapshot(strategy_id)
        if snap is not None:
            self._refresh_expiry(snap)
        return snap


_research_gate: Optional[ResearchGate] = None
_research_gate_state_file: Optional[Path] = None


def get_research_gate() -> ResearchGate:
    global _research_gate, _research_gate_state_file

    state_store = get_state_store()
    if _research_gate is None or _research_gate_state_file != state_store.file_path:
        _research_gate = ResearchGate(state_store=state_store)
        _research_gate_state_file = state_store.file_path
    return _research_gate
