from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


class CertStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class BacktestCert:
    """内存回测证书，字段名对齐 shared/contracts/decision/backtest_certificate.md"""

    certificate_id: str
    strategy_id: str
    sharpe: float
    drawdown: float
    review_status: str  # pending / approved / rejected / expired
    expires_at: datetime
    registered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class BacktestGate:
    """验证策略是否持有有效 backtest_certificate。

    内存存储（dict），不依赖外部 DB。
    review_status 枚举对齐契约：pending / approved / rejected / expired。
    """

    def __init__(self) -> None:
        # strategy_id → BacktestCert（每个策略保留最新一张）
        self._certs: dict[str, BacktestCert] = {}

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _refresh_expiry(self, cert: BacktestCert) -> None:
        """若证书已过期且状态仍为 approved，将状态切换为 expired。"""
        if cert.review_status == CertStatus.APPROVED:
            if datetime.now(timezone.utc) > cert.expires_at:
                cert.review_status = CertStatus.EXPIRED

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def is_valid(self, strategy_id: str) -> bool:
        """返回该策略是否持有状态为 approved 且未过期的证书。"""
        cert = self._certs.get(strategy_id)
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
    ) -> BacktestCert:
        """注册（或覆盖）一张回测证书，初始状态为 approved。"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        cert = BacktestCert(
            certificate_id=cert_id,
            strategy_id=strategy_id,
            sharpe=sharpe,
            drawdown=drawdown,
            review_status=CertStatus.APPROVED,
            expires_at=expires_at,
        )
        self._certs[strategy_id] = cert
        return cert

    def invalidate(self, cert_id: str) -> None:
        """将指定 certificate_id 的证书状态切换为 rejected。"""
        for cert in self._certs.values():
            if cert.certificate_id == cert_id:
                cert.review_status = CertStatus.REJECTED
                return

    def get_cert(self, strategy_id: str) -> Optional[BacktestCert]:
        """获取策略当前证书（自动刷新过期状态后返回）。"""
        cert = self._certs.get(strategy_id)
        if cert is not None:
            self._refresh_expiry(cert)
        return cert
