from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ..persistence.state_store import MemoryStateStore, get_state_store


class CertStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class BacktestCert:
    """回测证书，字段名对齐 shared/contracts/decision/backtest_certificate.md。"""

    certificate_id: str
    strategy_id: str
    sharpe: float
    drawdown: float
    review_status: str  # pending / approved / rejected / expired
    expires_at: datetime
    factor_version_hash: str = ""
    strategy_version: str = ""
    requested_symbol: str = ""
    executed_data_symbol: str = ""
    registered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    approved_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BacktestCert":
        approved_at_raw = data.get("approved_at")
        return cls(
            certificate_id=data["certificate_id"],
            strategy_id=data["strategy_id"],
            sharpe=float(data["sharpe"]),
            drawdown=float(data["drawdown"]),
            review_status=data["review_status"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            factor_version_hash=data.get("factor_version_hash", ""),
            strategy_version=data.get("strategy_version", ""),
            requested_symbol=data.get("requested_symbol", ""),
            executed_data_symbol=data.get("executed_data_symbol", ""),
            registered_at=datetime.fromisoformat(data["registered_at"]),
            approved_at=(
                datetime.fromisoformat(approved_at_raw)
                if isinstance(approved_at_raw, str) and approved_at_raw
                else None
            ),
        )

    def to_dict(self) -> dict:
        return {
            "certificate_id": self.certificate_id,
            "strategy_id": self.strategy_id,
            "sharpe": self.sharpe,
            "drawdown": self.drawdown,
            "review_status": self.review_status,
            "expires_at": self.expires_at.isoformat(),
            "factor_version_hash": self.factor_version_hash,
            "strategy_version": self.strategy_version,
            "requested_symbol": self.requested_symbol,
            "executed_data_symbol": self.executed_data_symbol,
            "registered_at": self.registered_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at is not None else None,
        }


class BacktestGate:
    """验证策略是否持有有效 backtest_certificate。"""

    def __init__(self, state_store=None) -> None:
        self._state_store = state_store or MemoryStateStore()

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _refresh_expiry(self, cert: BacktestCert) -> None:
        """若证书已过期且状态仍为 approved，将状态切换为 expired。"""
        if cert.review_status == CertStatus.APPROVED:
            if datetime.now(timezone.utc) > cert.expires_at:
                cert.review_status = CertStatus.EXPIRED
                self._state_store.upsert_record(
                    "backtest_certs",
                    cert.strategy_id,
                    cert.to_dict(),
                )

    def _load_cert(self, strategy_id: str) -> Optional[BacktestCert]:
        raw = self._state_store.get_record("backtest_certs", strategy_id)
        return BacktestCert.from_dict(raw) if raw is not None else None

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def is_valid(self, strategy_id: str) -> bool:
        """返回该策略是否持有状态为 approved 且未过期的证书。"""
        cert = self._load_cert(strategy_id)
        if cert is None:
            return False
        self._refresh_expiry(cert)
        return cert.review_status == CertStatus.APPROVED

    def register_cert(
        self,
        cert_id: str,
        strategy_id: str,
        sharpe: float,
        drawdown: float,
        expires_days: int = 90,
        factor_version_hash: str = "",
        strategy_version: str = "",
        requested_symbol: str = "",
        executed_data_symbol: str = "",
    ) -> BacktestCert:
        """注册（或覆盖）一张回测证书，初始状态为 approved。"""
        approved_at = datetime.now(timezone.utc)
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        cert = BacktestCert(
            certificate_id=cert_id,
            strategy_id=strategy_id,
            sharpe=sharpe,
            drawdown=drawdown,
            review_status=CertStatus.APPROVED,
            expires_at=expires_at,
            factor_version_hash=factor_version_hash,
            strategy_version=strategy_version,
            requested_symbol=requested_symbol,
            executed_data_symbol=executed_data_symbol,
            approved_at=approved_at,
        )
        self._state_store.upsert_record("backtest_certs", strategy_id, cert.to_dict())
        return cert

    def invalidate(self, cert_id: str) -> None:
        """将指定 certificate_id 的证书状态切换为 rejected。"""
        for raw in self._state_store.list_records("backtest_certs"):
            cert = BacktestCert.from_dict(raw)
            if cert.certificate_id == cert_id:
                cert.review_status = CertStatus.REJECTED
                self._state_store.upsert_record("backtest_certs", cert.strategy_id, cert.to_dict())
                return

    def get_cert(self, strategy_id: str) -> Optional[BacktestCert]:
        """获取策略当前证书（自动刷新过期状态后返回）。"""
        cert = self._load_cert(strategy_id)
        if cert is not None:
            self._refresh_expiry(cert)
        return cert


_backtest_gate: Optional[BacktestGate] = None
_backtest_gate_state_file: Optional[Path] = None


def get_backtest_gate() -> BacktestGate:
    global _backtest_gate, _backtest_gate_state_file

    state_store = get_state_store()
    if _backtest_gate is None or _backtest_gate_state_file != state_store.file_path:
        _backtest_gate = BacktestGate(state_store=state_store)
        _backtest_gate_state_file = state_store.file_path
    return _backtest_gate
