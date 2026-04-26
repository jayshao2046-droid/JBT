"""TASK-0018 批次 D — 系统级风控执行层

实现 max_drawdown 和 daily_loss_limit 两条最小风控规则，
产出符合 shared/contracts/backtest/api.md §6.2.2 的 risk_event 结构。

由 local_engine.py 在逐 bar 撮合中调用；不被 generic_strategy.py 或 runner.py 引用，
不引入任何对既有 tqsdk 路径的副作用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RiskParams:
    """风控参数。值 >= 1.0 表示对应规则禁用（不触发）。"""

    max_drawdown: float = field(default=1.0)
    """最大回撤上限（净值回撤比例）。0.05 = 5%；>= 1.0 表示不限制。"""

    daily_loss_limit: float = field(default=1.0)
    """日亏损上限（相对初始资金的比例）。0.05 = 5%；>= 1.0 表示不限制。"""


class RiskEngine:
    """
    系统级风控执行器。

    在 local_engine.py 的逐 bar 撮合循环中调用 check()：
      - 触发时：记录符合 api.md §6.2.2 的 risk_event、禁止新开仓，返回 risk_event。
      - 未触发时：返回 None。
      - 每条规则只触发一次，不重复记录。
    """

    def __init__(
        self,
        job_id: str,
        initial_capital: float,
        params: RiskParams,
        engine_type: str = "local",
    ) -> None:
        self._job_id = job_id
        self._initial_capital = initial_capital
        self._params = params
        self._engine_type = engine_type
        self._peak_equity: float = initial_capital
        self._open_allowed: bool = True
        self._event_counter: int = 0
        self._triggered_rules: set = set()
        self._risk_events: List[Dict[str, Any]] = []
        self._current_day: Optional[str] = None
        self._day_start_equity: float = initial_capital

    # ── public ────────────────────────────────────────────────────────────────

    @property
    def open_allowed(self) -> bool:
        """是否允许新开仓。风控触发后为 False。"""
        return self._open_allowed

    @property
    def risk_events(self) -> List[Dict[str, Any]]:
        """已触发的风控事件列表（符合 api.md §6.2.2）。"""
        return list(self._risk_events)

    def check(self, bar_time: datetime, current_equity: float) -> Optional[Dict[str, Any]]:
        """
        逐 bar 检查风控规则，在每根 bar 的收盘权益计算后调用。

        Returns:
            触发时返回 risk_event dict；未触发时返回 None。
        """
        # 日维度跟踪：每自然日首次出现时重置当日起始权益
        bar_date = bar_time.date().isoformat()
        if self._current_day is None:
            self._current_day = bar_date
            self._day_start_equity = current_equity
        elif bar_date != self._current_day:
            self._day_start_equity = current_equity
            self._current_day = bar_date
            # 日亏损限额每自然日重置：新的一天允许继续开仓（max_drawdown 是永久熔断，不重置）
            if "daily_loss_limit" in self._triggered_rules:
                self._triggered_rules.discard("daily_loss_limit")
                if "max_drawdown" not in self._triggered_rules:
                    self._open_allowed = True

        # 更新历史峰值净值
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity

        # 规则 1：max_drawdown
        if (
            "max_drawdown" not in self._triggered_rules
            and self._params.max_drawdown < 1.0
            and self._peak_equity > 0.0
        ):
            current_drawdown = (self._peak_equity - current_equity) / self._peak_equity
            if current_drawdown >= self._params.max_drawdown:
                event = self._emit_event(
                    bar_time=bar_time,
                    trigger_reason="max_drawdown_limit_breached",
                    threshold_name="max_drawdown",
                    threshold_value=self._params.max_drawdown,
                    observed_name="current_drawdown",
                    observed_value=current_drawdown,
                )
                self._triggered_rules.add("max_drawdown")
                self._open_allowed = False
                return event

        # 规则 2：daily_loss_limit
        if (
            "daily_loss_limit" not in self._triggered_rules
            and self._params.daily_loss_limit < 1.0
            and self._initial_capital > 0.0
        ):
            daily_loss = (self._day_start_equity - current_equity) / self._initial_capital
            if daily_loss >= self._params.daily_loss_limit:
                event = self._emit_event(
                    bar_time=bar_time,
                    trigger_reason="daily_loss_limit_breached",
                    threshold_name="daily_loss_limit",
                    threshold_value=self._params.daily_loss_limit,
                    observed_name="current_daily_loss",
                    observed_value=daily_loss,
                )
                self._triggered_rules.add("daily_loss_limit")
                self._open_allowed = False
                return event

        return None

    # ── private ───────────────────────────────────────────────────────────────

    def _emit_event(
        self,
        bar_time: datetime,
        trigger_reason: str,
        threshold_name: str,
        threshold_value: float,
        observed_name: str,
        observed_value: float,
    ) -> Dict[str, Any]:
        self._event_counter += 1
        event_id = f"evt-{bar_time.strftime('%Y%m%d')}-{self._event_counter:04d}"
        now_str = datetime.now(tz=timezone.utc).isoformat()
        event: Dict[str, Any] = {
            "event_id": event_id,
            "job_id": self._job_id,
            "engine_type": self._engine_type,
            "event_type": "system_risk",
            "trigger_reason": trigger_reason,
            "threshold": {
                "name": threshold_name,
                "operator": ">=",
                "value": round(threshold_value, 6),
                "unit": "ratio",
            },
            "observed": {
                "name": observed_name,
                "value": round(observed_value, 6),
                "unit": "ratio",
                "sample_time": bar_time.isoformat(),
            },
            "event_time": now_str,
            "action": {
                "decision": "stop_open",
                "status": "executed",
                "detail": "no_new_positions_allowed",
            },
        }
        self._risk_events.append(event)
        return event
