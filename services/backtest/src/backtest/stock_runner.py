"""A 股手动回测执行器 — TASK-0058 CG3

遵循 T+1、涨跌停（主板 10%/创业板 20%/科创板 20%/北交所 30%）、禁止做空。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class StockBacktestResult:
    """单次股票手动回测的完整记录。"""

    run_id: str
    strategy_id: str
    status: str  # pending / running / completed / failed
    start_time: str
    end_time: Optional[str] = None
    metrics: dict = field(default_factory=dict)
    approved: Optional[bool] = None  # None=未审核, True=通过, False=拒绝
    reviewer_note: str = ""
    asset_type: str = "stock"
    price_limit_hits: int = 0  # 触发涨跌停次数
    t1_violations: int = 0  # T+1 违规拦截次数

    def to_dict(self) -> dict:
        return asdict(self)


class StockRunner:
    """A 股手动回测管理器（内存存储）。"""

    def __init__(self, data_service_url: str = "http://localhost:8105") -> None:
        self._results: dict[str, StockBacktestResult] = {}
        self._data_service_url = data_service_url

    # ── 提交回测 ─────────────────────────────────────────────────────

    def submit(
        self,
        strategy_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        params: dict | None = None,
    ) -> StockBacktestResult:
        """创建并同步执行一次股票手动回测，返回结果。"""
        run_id = uuid.uuid4().hex[:16]
        now = datetime.now(timezone.utc).isoformat()

        result = StockBacktestResult(
            run_id=run_id,
            strategy_id=strategy_id,
            status="running",
            start_time=now,
        )
        self._results[run_id] = result

        try:
            bt = self._execute_stock_backtest(symbol, start_date, end_date, params)
            result.status = "completed"
            result.metrics = bt["metrics"]
            result.price_limit_hits = bt["price_limit_hits"]
            result.t1_violations = bt["t1_violations"]
        except Exception as exc:
            logger.warning("股票手动回测执行失败: %s", exc)
            result.status = "failed"
            result.metrics = {"error": str(exc)}

        result.end_time = datetime.now(timezone.utc).isoformat()
        return result

    # ── 查询 ──────────────────────────────────────────────────────────

    def get_result(self, run_id: str) -> StockBacktestResult | None:
        return self._results.get(run_id)

    def list_results(
        self, strategy_id: str | None = None
    ) -> list[StockBacktestResult]:
        items = list(self._results.values())
        if strategy_id:
            items = [r for r in items if r.strategy_id == strategy_id]
        return items

    # ── 审核确认 ──────────────────────────────────────────────────────

    def approve(
        self, run_id: str, approved: bool, note: str = ""
    ) -> StockBacktestResult:
        """对已完成的股票回测进行审核确认/拒绝。"""
        result = self._results.get(run_id)
        if result is None:
            raise KeyError(f"run_id not found: {run_id}")
        if result.status not in ("completed", "failed"):
            raise ValueError(f"只能审核已完成/失败的回测，当前状态: {result.status}")

        result.approved = approved
        result.reviewer_note = note

        self._notify_decision(run_id, result.strategy_id, approved)

        return result

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _price_limit_pct(self, symbol: str) -> float:
        """根据股票代码判断涨跌停幅度。

        - 30xxxx (创业板): 20%
        - 68xxxx (科创板): 20%
        - 8xxxxx (北交所): 30%
        - 其他 (主板):     10%
        """
        if symbol.startswith("30"):
            return 0.20
        if symbol.startswith("68"):
            return 0.20
        if symbol.startswith("8"):
            return 0.30
        return 0.10

    def _execute_stock_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        params: dict | None = None,
    ) -> dict:
        """从 data 服务拉取股票日线，MA 交叉策略模拟，实施 T+1 和涨跌停检查。"""
        short_window = (params or {}).get("short_window", 5)
        long_window = (params or {}).get("long_window", 20)
        limit_pct = self._price_limit_pct(symbol)

        bars = self._fetch_stock_bars(symbol, start_date, end_date)

        if len(bars) < long_window:
            return {
                "metrics": {
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "win_rate": 0.0,
                    "trades_count": 0,
                },
                "price_limit_hits": 0,
                "t1_violations": 0,
            }

        closes = [b.get("close", b.get("收盘价", 0.0)) for b in bars]

        trades: list[float] = []
        position = 0  # 0=空仓, 1=持仓
        entry_price = 0.0
        entry_day: int = -999  # 买入当日 index，用于 T+1 检查
        price_limit_hits = 0
        t1_violations = 0

        for i in range(long_window, len(closes)):
            short_ma = sum(closes[i - short_window : i]) / short_window
            long_ma = sum(closes[i - long_window : i]) / long_window

            # 涨跌停判断：当日涨跌幅超过限制则跳过交易
            if i > 0 and closes[i - 1] > 0:
                day_change = abs(closes[i] - closes[i - 1]) / closes[i - 1]
                if day_change >= limit_pct:
                    price_limit_hits += 1
                    continue

            # 买入信号（禁止做空，只有 position==0 时买入）
            if short_ma > long_ma and position == 0:
                position = 1
                entry_price = closes[i]
                entry_day = i

            # 卖出信号 — T+1 检查
            elif short_ma < long_ma and position == 1:
                if i - entry_day < 1:
                    # T+1 违规：买入当日不能卖出
                    t1_violations += 1
                    continue
                position = 0
                pnl = (closes[i] - entry_price) / entry_price
                trades.append(pnl)

        # 最后持仓平仓（必须满足 T+1）
        if position == 1 and closes:
            last_idx = len(closes) - 1
            if last_idx - entry_day >= 1:
                pnl = (closes[-1] - entry_price) / entry_price
                trades.append(pnl)

        total_return = sum(trades) if trades else 0.0
        win_count = sum(1 for t in trades if t > 0)
        win_rate = win_count / len(trades) if trades else 0.0

        # 最大回撤
        equity = [1.0]
        for t in trades:
            equity.append(equity[-1] * (1 + t))
        peak = equity[0]
        max_dd = 0.0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        # Sharpe ratio
        import statistics

        if len(trades) >= 2:
            avg = statistics.mean(trades)
            std = statistics.stdev(trades)
            sharpe = (avg / std) * (252 ** 0.5) if std > 0 else 0.0
        else:
            sharpe = 0.0

        return {
            "metrics": {
                "total_return": round(total_return, 4),
                "sharpe_ratio": round(sharpe, 4),
                "max_drawdown": round(max_dd, 4),
                "win_rate": round(win_rate, 4),
                "trades_count": len(trades),
            },
            "price_limit_hits": price_limit_hits,
            "t1_violations": t1_violations,
        }

    def _fetch_stock_bars(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[dict]:
        """从 data service 获取股票日线数据。"""
        url = f"{self._data_service_url}/api/v1/stocks/bars"
        try:
            resp = httpx.get(
                url,
                params={
                    "symbol": symbol,
                    "start": start_date,
                    "end": end_date,
                    "timeframe_minutes": 1,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("bars", data.get("data", []))
        except Exception as exc:
            logger.warning("从 data 服务获取股票 bars 失败: %s", exc)
            return []

    def _notify_decision(
        self, run_id: str, strategy_id: str, approved: bool
    ) -> None:
        """异步通知 decision 端审核结果（失败只打 warning 日志不抛异常）。"""
        try:
            httpx.post(
                "http://localhost:8103/api/v1/strategies/approval-callback",
                json={
                    "run_id": run_id,
                    "strategy_id": strategy_id,
                    "asset_type": "stock",
                    "approved": approved,
                },
                timeout=10.0,
            )
        except Exception as exc:
            logger.warning("通知 decision 端审核结果失败: %s", exc)
