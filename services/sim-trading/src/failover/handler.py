from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HandoverPayload(BaseModel):
    orders: list[dict]
    positions: dict[str, float]
    capital: float
    source_engine: str
    handover_id: str


class HandoverResult(BaseModel):
    success: bool
    handover_id: str
    orders_received: int
    positions_merged: int
    capital_delta: float
    errors: list[str] = Field(default_factory=list)


class FailoverStatus(BaseModel):
    status: str
    last_handover_id: Optional[str] = None
    last_handover_time: Optional[str] = None
    orders_pending: int = 0


class FailoverHandler:
    def __init__(self):
        self._status = "idle"
        self._last_handover_id: Optional[str] = None
        self._last_handover_time: Optional[str] = None
        self._orders_pending = 0
        self._processed_handovers: set[str] = set()

    def receive_handover(self, data: HandoverPayload) -> HandoverResult:
        errors = []

        # Check duplicate handover_id
        if data.handover_id in self._processed_handovers:
            return HandoverResult(
                success=False,
                handover_id=data.handover_id,
                orders_received=0,
                positions_merged=0,
                capital_delta=0.0,
                errors=["Duplicate handover_id"]
            )

        # Validate data
        if data.capital < 0:
            errors.append("Negative capital")

        for symbol, qty in data.positions.items():
            if qty < 0:
                errors.append(f"Negative position quantity for {symbol}")

        if errors:
            return HandoverResult(
                success=False,
                handover_id=data.handover_id,
                orders_received=0,
                positions_merged=0,
                capital_delta=0.0,
                errors=errors
            )

        # Process handover
        self._status = "receiving"
        orders_count = len(data.orders)
        positions_count = len(data.positions)
        capital_delta = data.capital

        # Mark as processed
        self._processed_handovers.add(data.handover_id)
        self._last_handover_id = data.handover_id
        self._last_handover_time = datetime.utcnow().isoformat()
        self._orders_pending = orders_count
        self._status = "completed"

        return HandoverResult(
            success=True,
            handover_id=data.handover_id,
            orders_received=orders_count,
            positions_merged=positions_count,
            capital_delta=capital_delta,
            errors=[]
        )

    def get_status(self) -> FailoverStatus:
        return FailoverStatus(
            status=self._status,
            last_handover_id=self._last_handover_id,
            last_handover_time=self._last_handover_time,
            orders_pending=self._orders_pending
        )

    def confirm_handover(self, handover_id: str) -> bool:
        if handover_id not in self._processed_handovers:
            return False

        # Clear pending state
        self._orders_pending = 0
        self._status = "idle"
        return True
