# SimNow ledger service — TASK-0019-B2: actual data tracking

from datetime import date, datetime
from threading import Lock
from typing import List, Tuple, Optional


class LedgerService:
    """SimNow ledger — tracks trades, account, and positions in memory."""

    def __init__(self):
        self._lock = Lock()
        self._trades: list = []
        self._account: dict = {}
        self._positions: list = []
        self._equity_history: List[Tuple[datetime, float]] = []  # P0-1: 权益历史

    def record_trade(self, trade: dict) -> None:
        """记录成交（委托到 add_trade，保持向后兼容）。"""
        self.add_trade(trade)

    def add_trade(self, trade_data: dict) -> None:
        """记录一笔成交到当日列表。"""
        with self._lock:
            self._trades.append(trade_data)

    def update_account(self, account_data: dict) -> None:
        """更新 CTP 账户资金快照。"""
        with self._lock:
            self._account = dict(account_data)

    def update_positions(self, positions: list) -> None:
        """更新持仓列表（全量替换）。"""
        with self._lock:
            self._positions = list(positions)

    def get_positions(self) -> list:
        """查询持仓。"""
        with self._lock:
            return list(self._positions)

    def get_trades(self) -> list:
        """查询当日成交列表。"""
        with self._lock:
            return list(self._trades)

    def get_account_summary(self) -> dict:
        """查询账户汇总。"""
        with self._lock:
            if not self._account and not self._trades:
                return {}

            trade_count = len(self._trades)
            win_count = sum(1 for t in self._trades if (t.get("pnl") or 0) > 0)

            if self._account.get("close_pnl") is not None:
                total_pnl = (self._account.get("close_pnl", 0) or 0) + \
                            (self._account.get("floating_pnl", 0) or 0)
            else:
                total_pnl = sum(t.get("pnl", 0) for t in self._trades)

            return {
                "total_pnl": total_pnl,
                "trade_count": trade_count,
                "win_count": win_count,
                "trades": list(self._trades),
            }

    def generate_daily_report(self) -> dict:
        """聚合当日交易数据，返回日报 dict。

        当前 ledger 无实际数据时返回合理默认值。
        """
        positions = self.get_positions()
        summary = self.get_account_summary()

        total_pnl = summary.get("total_pnl", 0.0)
        trade_count = summary.get("trade_count", 0)
        win_count = summary.get("win_count", 0)
        win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0.0

        return {
            "date": date.today().isoformat(),
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "trade_count": trade_count,
            "positions": positions,
            "trades": summary.get("trades", []),
        }

    def record_equity_snapshot(self, equity: float) -> None:
        """记录权益快照（P0-1）。"""
        with self._lock:
            self._equity_history.append((datetime.now(), equity))
            # 只保留最近 30 天数据（假设每分钟一个快照，30天约43200个点）
            if len(self._equity_history) > 50000:
                self._equity_history = self._equity_history[-43200:]

    def get_equity_history(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[dict]:
        """获取权益历史数据（P0-1）。"""
        with self._lock:
            if not self._equity_history:
                return []

            result = []
            for ts, equity in self._equity_history:
                if start_time and ts < start_time:
                    continue
                if end_time and ts > end_time:
                    continue
                result.append({"timestamp": ts.isoformat(), "equity": equity})

            return result


# Module-level singleton
_ledger_instance = None
_ledger_lock = Lock()


def get_ledger() -> "LedgerService":
    """获取全局 LedgerService 单例。"""
    global _ledger_instance
    if _ledger_instance is None:
        with _ledger_lock:
            if _ledger_instance is None:
                _ledger_instance = LedgerService()
    return _ledger_instance


def reset_ledger() -> None:
    """重置全局 LedgerService 单例（测试用）。"""
    global _ledger_instance
    with _ledger_lock:
        _ledger_instance = None
