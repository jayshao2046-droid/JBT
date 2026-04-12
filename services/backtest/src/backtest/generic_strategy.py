from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass
from datetime import datetime, time as time_of_day, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Set

try:
    from .factor_registry import factor_registry, normalize_bars  # noqa: F401 — resolve_factor_name via registry
    from .strategy_base import (
        GENERIC_FORMAL_TEMPLATE_ID,
        FactorConfig,
        IndicatorConfig,
        FixedTemplateStrategy,
        StrategyConfigError,
        StrategyDefinition,
        register_strategy_template,
    )
except ImportError:
    from factor_registry import factor_registry, normalize_bars
    from strategy_base import (
        GENERIC_FORMAL_TEMPLATE_ID,
        FactorConfig,
        IndicatorConfig,
        FixedTemplateStrategy,
        StrategyConfigError,
        StrategyDefinition,
        register_strategy_template,
    )


_ALLOWED_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "abs": abs,
    "all": all,
    "any": any,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "sum": sum,
}


@dataclass(frozen=True)
class GenericIndicatorSpec:
    name: str
    indicator_type: str
    params: Dict[str, Any]
    primary_output: str
    period_hint: int


@dataclass(frozen=True)
class GenericTemplateConfig:
    symbol: str
    timeframe_minutes: int
    indicators: List[GenericIndicatorSpec]
    factors: List[FactorConfig]
    market_filter_conditions: List[str]
    long_condition: Any
    short_condition: Any
    confirm_bars: int
    legacy_factor_mode: bool
    position_method: str
    position_ratio: float
    fixed_lots: Optional[int]
    contract_size: float
    price_tick: float
    slippage_per_unit: float
    commission_per_lot_round_turn: float
    stop_loss_atr: Optional[float]
    take_profit_atr: Optional[float]
    trailing_activate_at: Optional[float]
    trailing_distance: Optional[float]
    max_drawdown: Optional[float]
    daily_loss_limit: Optional[float]
    force_close_day: Optional[time_of_day]
    force_close_night: Optional[time_of_day]
    no_overnight: bool

    @classmethod
    def from_definition(
        cls,
        definition: StrategyDefinition,
        *,
        requested_symbol: str,
    ) -> "GenericTemplateConfig":
        if definition.template_id != GENERIC_FORMAL_TEMPLATE_ID:
            raise StrategyConfigError(
                f"generic strategy template_id must be {GENERIC_FORMAL_TEMPLATE_ID}"
            )

        if definition.timeframe_minutes is None or definition.timeframe_minutes <= 0:
            raise StrategyConfigError("generic strategy must declare timeframe_minutes/timeframe")

        if definition.symbols:
            requested_token = _normalize_symbol_token(requested_symbol)
            expected_tokens = [_normalize_symbol_token(s) for s in definition.symbols]
            if not any(_symbol_matches(exp, requested_token) for exp in expected_tokens):
                raise StrategyConfigError(
                    f"generic strategy requested symbol must match YAML symbols {definition.symbols}"
                )

        if not definition.factors:
            raise StrategyConfigError("generic strategy must declare factors")

        signal_config = dict(definition.signal)
        long_condition = signal_config.get("long_condition")
        if long_condition in {None, "", False}:
            raise StrategyConfigError("generic strategy must declare signal.long_condition")

        market_filter_config = dict(definition.market_filter)
        market_filter_conditions = []
        if market_filter_config.get("enabled"):
            market_filter_conditions = list(market_filter_config.get("conditions") or [])

        legacy_factor_mode = not definition.indicators or any(
            factor.formula is None for factor in definition.factors
        )
        indicators = [_build_indicator_spec(item) for item in definition.indicators]
        if legacy_factor_mode:
            indicators.extend(
                _infer_legacy_indicator_specs(
                    definition,
                    long_condition=long_condition,
                    short_condition=signal_config.get("short_condition"),
                    market_filter_conditions=market_filter_conditions,
                )
            )
            indicators = _dedupe_indicator_specs(indicators)

        # Auto-assign default formulas for legacy factors that have no formula
        resolved_factors = list(definition.factors)
        if legacy_factor_mode:
            resolved_factors = _assign_default_legacy_formulas(
                resolved_factors, indicators,
                long_condition=long_condition,
                short_condition=signal_config.get("short_condition"),
            )
        if not indicators:
            raise StrategyConfigError("generic strategy must declare indicators or legacy factors")

        if not legacy_factor_mode:
            for factor in resolved_factors:
                if not factor.formula:
                    raise StrategyConfigError(
                        f"generic factor {factor.factor_name} must declare formula"
                    )

        position_size = definition.params.get("position_size") or {}
        if position_size and not isinstance(position_size, Mapping):
            raise StrategyConfigError("position_size must be a mapping")

        position_method = str(position_size.get("method") or "fixed_ratio").strip().lower()
        position_ratio = _read_non_negative_float(
            position_size.get("ratio", definition.params.get("position_fraction", 0.0)),
            label="position_size.ratio",
        )
        fixed_lots = None
        if position_method == "fixed_lots":
            fixed_lots = _read_positive_int(position_size.get("lots"), label="position_size.lots")
        elif position_method != "fixed_ratio":
            raise StrategyConfigError(
                f"unsupported position_size.method {position_method}; expected fixed_ratio/fixed_lots"
            )

        contract_size = _read_positive_float(
            definition.capital_params.get("contract_size", 1),
            label="contract_size",
        )
        price_tick = _read_non_negative_float(
            definition.capital_params.get("price_tick", 0.0),
            label="price_tick",
        )

        risk_snapshot = definition.risk.as_snapshot()
        trailing_stop = risk_snapshot.get("trailing_stop") or {}
        if trailing_stop and not isinstance(trailing_stop, Mapping):
            raise StrategyConfigError("risk.trailing_stop must be a mapping")

        return cls(
            symbol=requested_symbol,
            timeframe_minutes=definition.timeframe_minutes,
            indicators=indicators,
            factors=resolved_factors,
            market_filter_conditions=market_filter_conditions,
            long_condition=long_condition,
            short_condition=signal_config.get("short_condition"),
            confirm_bars=max(1, _read_positive_int(signal_config.get("confirm_bars", 1), label="signal.confirm_bars")),
            legacy_factor_mode=legacy_factor_mode,
            position_method=position_method,
            position_ratio=position_ratio,
            fixed_lots=fixed_lots,
            contract_size=contract_size,
            price_tick=price_tick,
            slippage_per_unit=_read_non_negative_float(
                definition.transaction_costs.get("slippage_per_unit", definition.capital_params.get("slippage", 0.0)),
                label="transaction_costs.slippage_per_unit",
            ),
            commission_per_lot_round_turn=_read_non_negative_float(
                definition.transaction_costs.get(
                    "commission_per_lot_round_turn",
                    definition.capital_params.get("commission", 0.0),
                ),
                label="transaction_costs.commission_per_lot_round_turn",
            ),
            stop_loss_atr=_read_optional_positive_float(
                risk_snapshot.get("stop_loss_atr")
                or (risk_snapshot.get("stop_loss") or {}).get("atr_multiplier"),
                label="risk.stop_loss_atr",
            ),
            take_profit_atr=_read_optional_positive_float(
                risk_snapshot.get("take_profit_atr")
                or (risk_snapshot.get("take_profit") or {}).get("atr_multiplier"),
                label="risk.take_profit_atr",
            ),
            trailing_activate_at=_read_optional_positive_float(
                trailing_stop.get("activate_at"),
                label="risk.trailing_stop.activate_at",
            ),
            trailing_distance=_read_optional_positive_float(
                trailing_stop.get("distance"),
                label="risk.trailing_stop.distance",
            ),
            max_drawdown=_read_optional_fraction(
                risk_snapshot.get("max_drawdown", risk_snapshot.get("max_drawdown_pct")),
                label="risk.max_drawdown",
            ),
            daily_loss_limit=_read_optional_fraction(
                risk_snapshot.get("daily_loss_limit", risk_snapshot.get("daily_loss_limit_pct")),
                label="risk.daily_loss_limit",
            ),
            force_close_day=_read_optional_time(risk_snapshot.get("force_close_day"), label="risk.force_close_day"),
            force_close_night=_read_optional_time(risk_snapshot.get("force_close_night"), label="risk.force_close_night"),
            no_overnight=bool(risk_snapshot.get("no_overnight") or False),
        )


@register_strategy_template
class GenericStrategy(FixedTemplateStrategy):
    template_id = GENERIC_FORMAL_TEMPLATE_ID

    def run(self):
        config = GenericTemplateConfig.from_definition(
            self.strategy_config,
            requested_symbol=self.runtime_context.symbol,
        )
        if not self._supports_live_execution():
            return self._run_static_snapshot(config)

        backtest_finished_exception = _resolve_backtest_finished_exception()
        try:
            quote = self._get_quote()
            kline_serial = self._subscribe_bars(config)
            target_pos_task = self.build_target_pos_task(
                symbol=config.symbol,
                price=self._build_price_resolver(config, quote),
            )
        except backtest_finished_exception:
            self.append_note("backtest_finished_during_setup")
            return self._finish_with_backtest_guard(backtest_finished_exception)

        # Cache volume_multiple once at start (avoids get_quote in hot loop)
        _volume_multiple = 1.0
        try:
            vm = getattr(quote, "volume_multiple", None)
            if vm is not None and float(vm) > 0:
                _volume_multiple = float(vm)
        except Exception:
            pass
        self.append_note(f"volume_multiple={_volume_multiple}")

        seen_trade_ids = self._collect_trade_ids()
        last_observed_position = self._read_current_position()
        last_target_volume = last_observed_position
        last_signal_state: Optional[str] = None
        loop_entered = False
        signal_transitions = 0
        target_updates = 0
        observed_trade_records = 0
        market_filter_passes = 0
        total_bar_evals = 0
        current_side = _position_side_from_volume(last_target_volume)
        entry_price: Optional[float] = None
        highest_price: Optional[float] = None
        lowest_price: Optional[float] = None
        daily_anchor_date: Optional[Any] = None
        daily_anchor_equity = self.runtime_context.initial_capital
        risk_blocked = False
        global_max_drawdown_locked = False  # 全局回撤熔断：一旦触发永久锁定，不随日切重置
        risk_reason: Optional[str] = None

        self.append_note(f"template={self.template_id}")
        self.append_note("execution_loop=wait_update_target_pos")
        self.append_note(f"timeframe_minutes={config.timeframe_minutes}")
        self.append_note(
            "transaction_costs="
            f"slippage_per_unit={config.slippage_per_unit},"
            f"commission_per_lot_round_turn={config.commission_per_lot_round_turn}"
        )

        try:
            while True:
                self.session.api.wait_update()
                loop_entered = True

                latest_row = self._get_latest_kline_row(kline_serial)
                latest_timestamp = _coerce_timestamp(_extract_timestamp(latest_row))
                last_observed_position, observed_updates = self._record_execution_changes(
                    seen_trade_ids=seen_trade_ids,
                    last_observed_position=last_observed_position,
                    timestamp=latest_timestamp,
                    volume_multiple=_volume_multiple,
                    commission_per_lot=config.commission_per_lot_round_turn,
                )
                observed_trade_records += observed_updates

                if latest_row is None or not self._is_new_kline(latest_row):
                    continue

                bars = self._normalize_streaming_bars(kline_serial, config)
                if len(bars) < self._required_bar_count(config):
                    continue

                merged_rows = self._compute_signal_rows(bars, config)
                snapshot = self._select_signal_snapshot(merged_rows)
                signal_timestamp = _coerce_timestamp(_extract_timestamp(snapshot))
                reference_price = self._resolve_reference_price(snapshot, quote)
                total_bar_evals += 1
                if snapshot.get("market_filter_passed"):
                    market_filter_passes += 1

                if signal_timestamp is not None:
                    current_date = signal_timestamp.date()
                    if daily_anchor_date != current_date:
                        daily_anchor_date = current_date
                        daily_anchor_equity = self._read_current_equity()
                        # 全局回撤熔断永久锁定，不随日切重置；日内熔断每日重置
                        if not global_max_drawdown_locked:
                            risk_blocked = False
                            risk_reason = None

                current_equity = self._read_current_equity()
                drawdown_triggered = (
                    config.max_drawdown is not None
                    and current_equity <= self._peak_equity * max(0.0, 1.0 - config.max_drawdown)
                )
                daily_loss_triggered = (
                    config.daily_loss_limit is not None
                    and current_equity <= daily_anchor_equity * max(0.0, 1.0 - config.daily_loss_limit)
                )
                if drawdown_triggered:
                    if not global_max_drawdown_locked:
                        self.record_risk_violation(
                            rule_name="max_drawdown",
                            message=f"账户回撤超过阈值 {config.max_drawdown*100:.1f}%，触发全局止损，永久锁定",
                            actual_value=round((self._peak_equity - current_equity) / self._peak_equity, 4),
                            threshold_value=config.max_drawdown,
                            observed_at=signal_timestamp or latest_timestamp,
                        )
                        global_max_drawdown_locked = True
                    risk_blocked = True
                    risk_reason = "max_drawdown_triggered"
                if daily_loss_triggered:
                    if not risk_blocked:
                        self.record_risk_violation(
                            rule_name="daily_loss_limit",
                            message=f"当日亏损超过阈值 {config.daily_loss_limit*100:.1f}%，触发日内止损",
                            actual_value=round((daily_anchor_equity - current_equity) / daily_anchor_equity, 4),
                            threshold_value=config.daily_loss_limit,
                            observed_at=signal_timestamp or latest_timestamp,
                        )
                    risk_blocked = True
                    risk_reason = "daily_loss_limit_triggered"

                stop_triggered = False
                if current_side != "flat" and reference_price is not None:
                    highest_price = reference_price if highest_price is None else max(highest_price, reference_price)
                    lowest_price = reference_price if lowest_price is None else min(lowest_price, reference_price)
                    stop_triggered = self._position_should_flatten(
                        side=current_side,
                        reference_price=reference_price,
                        atr_value=_optional_float(snapshot.get("atr")),
                        entry_price=entry_price,
                        highest_price=highest_price,
                        lowest_price=lowest_price,
                        config=config,
                    )

                signal_state = self._resolve_signal_state(merged_rows, config)
                if risk_blocked or stop_triggered:
                    signal_state = "flat"
                if self._should_force_flat(signal_timestamp, config):
                    signal_state = "flat"

                if signal_state != last_signal_state:
                    signal_transitions += 1
                    last_signal_state = signal_state

                target_volume = self._resolve_target_volume(
                    signal_state=signal_state,
                    snapshot=snapshot,
                    quote=quote,
                    config=config,
                )
                if risk_blocked:
                    target_volume = 0

                if target_volume != last_target_volume:
                    target_pos_task.set_target_volume(target_volume)
                    target_updates += 1
                    if target_volume == 0:
                        current_side = "flat"
                        entry_price = None
                        highest_price = None
                        lowest_price = None
                    else:
                        current_side = _position_side_from_volume(target_volume)
                        entry_price = self._estimate_entry_price(reference_price, current_side, config)
                        highest_price = reference_price
                        lowest_price = reference_price
                    last_target_volume = target_volume

                try:
                    self.record_account_snapshot(timestamp=signal_timestamp or latest_timestamp)
                except Exception:
                    self.record_equity(
                        equity=current_equity,
                        position=last_observed_position,
                        timestamp=signal_timestamp or latest_timestamp,
                    )
        except backtest_finished_exception:
            pass

        self.append_note(f"execution_loop_entered={str(loop_entered).lower()}")
        self.append_note(f"signal_transitions={signal_transitions}")
        self.append_note(f"target_updates={target_updates}")
        self.append_note(f"observed_trade_records={observed_trade_records}")
        self.append_note(f"final_signal_state={last_signal_state or 'flat'}")
        if config.market_filter_conditions and total_bar_evals > 0:
            self.append_note(
                f"market_filter_pass_rate={market_filter_passes}/{total_bar_evals}"
                f"({round(market_filter_passes*100/total_bar_evals)}%)"
            )
        if risk_reason:
            self.append_note(f"risk_reason={risk_reason}")

        try:
            self.record_account_snapshot()
        except backtest_finished_exception:
            self.append_note("final_snapshot=backtest_finished")
            self.record_equity(
                equity=self._resolve_final_equity_fallback(self.runtime_context.initial_capital),
                position=last_observed_position,
            )
        except Exception:
            self.record_equity(
                equity=self._resolve_final_equity_fallback(self.runtime_context.initial_capital),
                position=last_observed_position,
            )

        return self._finish_with_backtest_guard(backtest_finished_exception)

    def _run_static_snapshot(self, config: GenericTemplateConfig):
        backtest_finished_exception = _resolve_backtest_finished_exception()
        bars = self._normalize_streaming_bars(self._subscribe_bars(config), config)
        if len(bars) < self._required_bar_count(config):
            raise StrategyConfigError("generic strategy requires sufficient K-line samples")

        merged_rows = self._compute_signal_rows(bars, config)
        snapshot = merged_rows[-1]
        signal_state = self._resolve_signal_state(merged_rows, config)
        target_volume = self._resolve_target_volume(
            signal_state=signal_state,
            snapshot=snapshot,
            quote=self._get_quote(),
            config=config,
        )

        self.append_note(f"template={self.template_id}")
        self.append_note("execution_loop=static_snapshot")
        self.append_note(f"signal_state={signal_state}")
        self.append_note(f"target_volume={target_volume}")
        self.append_note(
            "transaction_costs="
            f"slippage_per_unit={config.slippage_per_unit},"
            f"commission_per_lot_round_turn={config.commission_per_lot_round_turn}"
        )

        try:
            self.record_account_snapshot()
        except backtest_finished_exception:
            self.append_note("final_snapshot=backtest_finished")
            self.record_equity(equity=self.runtime_context.initial_capital, position=0)
        except Exception:
            self.record_equity(equity=self.runtime_context.initial_capital, position=0)
        return self._finish_with_backtest_guard(backtest_finished_exception)

    def _resolve_final_equity_fallback(self, default: float) -> float:
        if self._artifacts.equity_curve:
            return float(self._artifacts.equity_curve[-1].equity)
        return float(default)

    def _finish_with_backtest_guard(
        self,
        backtest_finished_exception: type[BaseException],
    ):
        try:
            return self.finish()
        except backtest_finished_exception:
            if self._artifacts.completed_at is None:
                self._artifacts.completed_at = datetime.now().astimezone()
            self.append_note("final_finish=backtest_finished")
            return self._artifacts

    def _supports_live_execution(self) -> bool:
        wait_update = getattr(self.session.api, "wait_update", None)
        is_changing = getattr(self.session.api, "is_changing", None)
        return callable(wait_update) and callable(is_changing)

    def _subscribe_bars(self, config: GenericTemplateConfig) -> Any:
        get_kline_serial = getattr(self.session.api, "get_kline_serial", None)
        if not callable(get_kline_serial):
            raise StrategyConfigError("generic strategy requires session.api.get_kline_serial")

        return get_kline_serial(
            config.symbol,
            config.timeframe_minutes * 60,
            data_length=self._required_bar_count(config),
        )

    def _normalize_streaming_bars(
        self,
        raw_bars: Any,
        config: GenericTemplateConfig,
    ) -> List[Dict[str, Any]]:
        bars = normalize_bars(raw_bars)
        if len(bars) < self._required_bar_count(config):
            return []
        return bars

    def _required_bar_count(self, config: GenericTemplateConfig) -> int:
        max_period = max((item.period_hint for item in config.indicators), default=10)
        return max(80, max_period * 4, config.confirm_bars + 10)

    def _compute_signal_rows(
        self,
        bars: List[Dict[str, Any]],
        config: GenericTemplateConfig,
    ) -> List[Dict[str, Any]]:
        merged_rows = [dict(row) for row in bars]
        for indicator in config.indicators:
            resolved_type = factor_registry.resolve_factor_name(indicator.indicator_type)
            result = factor_registry.calculate(resolved_type, bars, indicator.params)
            for row, indicator_row in zip(merged_rows, result.rows):
                primary_value = indicator_row.get(indicator.primary_output)
                row[indicator.name] = primary_value
                for key, value in indicator_row.items():
                    if key != "timestamp":
                        row[key] = value

        for row in merged_rows:
            factor_scores: List[float] = []
            weighted_factor_scores: List[float] = []
            factor_map: Dict[str, float] = {}
            environment = dict(row)
            for factor in config.factors:
                if not factor.formula:
                    continue
                value = _evaluate_factor_formula(factor, environment)
                factor_map[factor.factor_name] = value
                factor_scores.append(value)
                weighted_factor_scores.append(value * factor.weight)
                row[factor.factor_name] = value
                environment[factor.factor_name] = value
            row["factor_map"] = factor_map
            row["factor_scores"] = factor_scores
            row["weighted_factor_scores"] = weighted_factor_scores
            row["factor_total_score"] = sum(weighted_factor_scores)
            signal_environment = dict(environment)
            signal_environment["factor_map"] = factor_map
            signal_environment["factor_scores"] = factor_scores
            signal_environment["weighted_factor_scores"] = weighted_factor_scores
            signal_environment["factor_total_score"] = row["factor_total_score"]
            market_filter_passed = _evaluate_market_filter_conditions(
                config.market_filter_conditions,
                signal_environment,
            )
            row["market_filter_passed"] = market_filter_passed
            row["long_signal_candidate"] = _evaluate_signal_condition(
                config.long_condition,
                signal_environment,
            ) and market_filter_passed
            row["short_signal_candidate"] = _evaluate_signal_condition(
                config.short_condition,
                signal_environment,
            )
            row["short_signal_candidate"] = bool(row["short_signal_candidate"]) and market_filter_passed
        return merged_rows

    def _resolve_signal_state(
        self,
        merged_rows: List[Dict[str, Any]],
        config: GenericTemplateConfig,
    ) -> str:
        if not merged_rows:
            return "flat"
        recent_rows = merged_rows[-config.confirm_bars :]
        if len(recent_rows) < config.confirm_bars:
            return "flat"

        states = [_candidate_signal_state(row) for row in recent_rows]
        if states[-1] in {"long", "short"} and all(state == states[-1] for state in states):
            return states[-1]
        return "flat"

    def _get_quote(self) -> Any:
        get_quote = getattr(self.session.api, "get_quote", None)
        if not callable(get_quote):
            return None
        return get_quote(self.runtime_context.symbol)

    def _get_latest_kline_row(self, raw_bars: Any) -> Optional[Any]:
        iloc = getattr(raw_bars, "iloc", None)
        if iloc is not None:
            try:
                return iloc[-1]
            except Exception:
                pass
        bars = normalize_bars(raw_bars)
        if not bars:
            return None
        return bars[-1]

    def _select_signal_snapshot(self, merged_rows: List[Dict[str, Any]]) -> Mapping[str, Any]:
        if len(merged_rows) >= 2:
            return merged_rows[-2]
        return merged_rows[-1]

    def _is_new_kline(self, latest_row: Any) -> bool:
        return bool(self.session.api.is_changing(latest_row, "datetime"))

    def _record_execution_changes(
        self,
        *,
        seen_trade_ids: set[str],
        last_observed_position: int,
        timestamp: Optional[datetime],
        volume_multiple: float = 1.0,
        commission_per_lot: float = 0.0,
    ) -> tuple[int, int]:
        new_details = self._consume_new_trade_details(seen_trade_ids)
        trade_events = len(new_details)
        current_position = self._read_current_position()
        if trade_events == 0 and current_position != last_observed_position:
            trade_events = max(1, abs(current_position - last_observed_position))

        # Open-close pairing to compute per-trade PnL
        open_stack: list[dict] = getattr(self, "_pnl_open_stack", [])
        if not hasattr(self, "_pnl_open_stack"):
            self._pnl_open_stack: list[dict] = open_stack  # type: ignore[attr-defined]

        for detail in new_details:
            is_open = (detail.get("offset") or "").lower() == "open"
            is_buy = (detail.get("direction") or "").lower() == "buy"
            price = float(detail.get("price") or 0)
            vol = int(detail.get("volume") or 1)
            comm = round(commission_per_lot * vol, 2)
            detail["commission"] = comm

            if is_open:
                open_stack.append({"price": price, "volume": vol, "is_buy": is_buy, "commission": comm})
            else:
                pnl = 0.0
                if open_stack:
                    opener = open_stack.pop(0)
                    raw = (price - opener["price"]) if opener["is_buy"] else (opener["price"] - price)
                    pnl = round(raw * vol * volume_multiple - opener["commission"] - comm, 2)
                detail["profit"] = pnl
                self.record_trade_pnl(pnl)

            self.record_trade_detail(detail)

        if trade_events > len(new_details):
            for _ in range(trade_events - len(new_details)):
                self.record_trade_pnl(0.0)
        if trade_events > 0:
            try:
                self.record_account_snapshot(timestamp=timestamp)
            except Exception:
                pass
        return current_position, trade_events

    def _consume_new_trade_ids(self, seen_trade_ids: set[str]) -> List[str]:
        get_trade = getattr(self.session.api, "get_trade", None)
        if not callable(get_trade):
            return []
        try:
            trade_book = get_trade(account=self.session.account)
        except Exception:
            return []
        current_trade_ids = _collect_mapping_keys(trade_book)
        new_trade_ids = sorted(current_trade_ids - seen_trade_ids)
        seen_trade_ids.update(new_trade_ids)
        return new_trade_ids

    def _consume_new_trade_details(self, seen_trade_ids: set[str]) -> List[dict]:
        """从 TQSDK trade book 获取新成交明细（含方向、价格、手数）"""
        get_trade = getattr(self.session.api, "get_trade", None)
        if not callable(get_trade):
            return []
        try:
            trade_book = get_trade(account=self.session.account)
        except Exception:
            return []
        current_trade_ids = _collect_mapping_keys(trade_book)
        new_trade_ids = sorted(current_trade_ids - seen_trade_ids)
        seen_trade_ids.update(new_trade_ids)
        details: List[dict] = []
        for tid in new_trade_ids:
            try:
                entry = trade_book[tid]
                def _get(obj: Any, *keys: str, default: Any = None) -> Any:
                    for k in keys:
                        v = getattr(obj, k, None)
                        if v is None and hasattr(obj, "get"):
                            v = obj.get(k)
                        if v is not None:
                            return v
                    return default
                direction = str(_get(entry, "direction", default="") or "").upper()
                offset = str(_get(entry, "offset", default="") or "").upper()
                raw_dt = _get(entry, "trade_date_time", default="")
                if raw_dt and str(raw_dt).isdigit():
                    try:
                        from datetime import timezone
                        ts_sec = int(str(raw_dt)) / 1e9
                        raw_dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc).astimezone().isoformat()
                    except Exception:
                        raw_dt = str(raw_dt)
                details.append({
                    "trade_id": tid,
                    "symbol": str(_get(entry, "instrument_id", default=self.runtime_context.symbol) or ""),
                    "date": str(raw_dt or ""),
                    "direction": "buy" if direction == "BUY" else "sell",
                    "offset": "open" if offset == "OPEN" else "close",
                    "price": float(_get(entry, "price", default=0.0) or 0.0),
                    "volume": int(_get(entry, "volume", default=1) or 1),
                    "profit": None,
                    "commission": float(_get(entry, "commission", default=0.0) or 0.0),
                })
            except Exception:
                pass
        return details

    def _collect_trade_ids(self) -> set[str]:
        get_trade = getattr(self.session.api, "get_trade", None)
        if not callable(get_trade):
            return set()
        try:
            trade_book = get_trade(account=self.session.account)
        except Exception:
            return set()
        return _collect_mapping_keys(trade_book)

    def _read_current_position(self) -> int:
        get_position = getattr(self.session.api, "get_position", None)
        if not callable(get_position):
            return 0
        try:
            position_snapshot = get_position(self.runtime_context.symbol, account=self.session.account)
        except Exception:
            return 0
        return self._extract_position(position_snapshot)

    def _read_current_equity(self) -> float:
        get_account = getattr(self.session.api, "get_account", None)
        if not callable(get_account):
            return self.runtime_context.initial_capital
        try:
            account_snapshot = get_account(account=self.session.account)
        except Exception:
            return self.runtime_context.initial_capital
        return self._extract_number(
            account_snapshot,
            "balance",
            "equity",
            "static_balance",
            default=self.runtime_context.initial_capital,
        )

    def _resolve_target_volume(
        self,
        *,
        signal_state: str,
        snapshot: Mapping[str, Any],
        quote: Any,
        config: GenericTemplateConfig,
    ) -> int:
        if signal_state not in {"long", "short"}:
            return 0
        reference_price = self._resolve_reference_price(snapshot, quote)
        if reference_price is None or reference_price <= 0:
            return 0
        if config.position_method == "fixed_lots" and config.fixed_lots is not None:
            target_volume = config.fixed_lots
        else:
            raw_volume = (
                self.runtime_context.initial_capital
                * config.position_ratio
            ) / max(reference_price * config.contract_size, 1.0)
            target_volume = max(1, int(round(raw_volume)))

        # Respect exchange min_lot constraint (e.g. DCE.l2605 / DCE.v2605 = 8)
        min_lot = int(getattr(quote, "min_market_order_volume", 1) or 1)
        if min_lot < 1:
            min_lot = 1
        if target_volume < min_lot:
            target_volume = min_lot

        return target_volume if signal_state == "long" else -target_volume

    def _resolve_reference_price(
        self,
        snapshot: Mapping[str, Any],
        quote: Any,
    ) -> Optional[float]:
        if quote is not None:
            last_price = _optional_float(getattr(quote, "last_price", None))
            if last_price is not None and last_price > 0:
                return last_price
        return _optional_float(snapshot.get("close"))

    def _estimate_entry_price(
        self,
        reference_price: Optional[float],
        side: str,
        config: GenericTemplateConfig,
    ) -> Optional[float]:
        if reference_price is None:
            return None
        offset = config.slippage_per_unit
        if side == "long":
            return _round_to_tick(reference_price + offset, config.price_tick)
        if side == "short":
            return _round_to_tick(max(reference_price - offset, 0.0), config.price_tick)
        return reference_price

    def _build_price_resolver(
        self,
        config: GenericTemplateConfig,
        quote: Any,
    ) -> Callable[[str], float]:
        def _resolve(order_side: str) -> float:
            last_price = None
            ask_price = None
            bid_price = None
            if quote is not None:
                last_price = _optional_float(getattr(quote, "last_price", None))
                ask_price = _optional_float(getattr(quote, "ask_price1", None))
                bid_price = _optional_float(getattr(quote, "bid_price1", None))
            base_price = last_price or ask_price or bid_price or 0.0
            if str(order_side).upper().startswith("BUY"):
                return _round_to_tick((ask_price or base_price) + config.slippage_per_unit, config.price_tick)
            return _round_to_tick(max((bid_price or base_price) - config.slippage_per_unit, 0.0), config.price_tick)

        return _resolve

    def _position_should_flatten(
        self,
        *,
        side: str,
        reference_price: Optional[float],
        atr_value: Optional[float],
        entry_price: Optional[float],
        highest_price: Optional[float],
        lowest_price: Optional[float],
        config: GenericTemplateConfig,
    ) -> bool:
        if reference_price is None or atr_value is None or entry_price is None:
            return False

        if side == "long":
            if config.stop_loss_atr is not None and reference_price <= entry_price - atr_value * config.stop_loss_atr:
                return True
            if config.take_profit_atr is not None and reference_price >= entry_price + atr_value * config.take_profit_atr:
                return True
            if (
                config.trailing_activate_at is not None
                and config.trailing_distance is not None
                and highest_price is not None
                and highest_price >= entry_price + atr_value * config.trailing_activate_at
                and reference_price <= highest_price - atr_value * config.trailing_distance
            ):
                return True
            return False

        if config.stop_loss_atr is not None and reference_price >= entry_price + atr_value * config.stop_loss_atr:
            return True
        if config.take_profit_atr is not None and reference_price <= entry_price - atr_value * config.take_profit_atr:
            return True
        if (
            config.trailing_activate_at is not None
            and config.trailing_distance is not None
            and lowest_price is not None
            and lowest_price <= entry_price - atr_value * config.trailing_activate_at
            and reference_price >= lowest_price + atr_value * config.trailing_distance
        ):
            return True
        return False

    def _should_force_flat(
        self,
        timestamp: Optional[datetime],
        config: GenericTemplateConfig,
    ) -> bool:
        if timestamp is None:
            return False
        current_time = timestamp.timetz().replace(tzinfo=None)
        # 日盘强平（14:55）和夜盘强平（22:55）是死规则，与 no_overnight 无关
        if current_time.hour >= 20:
            cutoff = config.force_close_night
        else:
            cutoff = config.force_close_day
        return cutoff is not None and current_time >= cutoff


def _build_indicator_spec(config: IndicatorConfig) -> GenericIndicatorSpec:
    indicator_type = config.indicator_type.strip().upper()
    params = list(config.params)

    string_values = [value for value in params if isinstance(value, str)]
    numeric_values = [
        value
        for value in params
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    def source_or(default: str) -> str:
        return str(string_values[0]).strip().lower() if string_values else default

    def sources_or(*defaults: str) -> List[str]:
        resolved: List[str] = []
        for index, default in enumerate(defaults):
            if index < len(string_values):
                resolved.append(str(string_values[index]).strip().lower())
            else:
                resolved.append(default)
        return resolved

    if indicator_type in {
        "SMA",
        "EMA",
        "RSI",
        "VOLUMERATIO",
        "VOLUME_RATIO",
        "WMA",
        "HMA",
        "TEMA",
        "ROC",
        "MOM",
        "CMO",
        "DEMA",
        "HISTORICALVOL",
        "HISTVOL",
        "EMA_SLOPE",
        "STDEV",
        "ZSCORE",
        "DPO",
        "LINREG",
    }:
        if not numeric_values:
            raise StrategyConfigError(f"indicator {config.name} requires a positive period")
        normalized_type = {
            "VOLUMERATIO": "VolumeRatio",
            "VOLUME_RATIO": "VolumeRatio",
            "HISTORICALVOL": "HistoricalVol",
            "HISTVOL": "HistoricalVol",
            "EMA_SLOPE": "EMA_Slope",
            "STDEV": "Stdev",
            "ZSCORE": "ZScore",
            "LINREG": "LinReg",
        }.get(indicator_type, indicator_type)
        period = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.period")
        default_source = "volume" if normalized_type == "VolumeRatio" else "close"
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type=normalized_type,
            params={"source": source_or(default_source), "period": period},
            primary_output={
                "SMA": "sma",
                "EMA": "ema",
                "RSI": "rsi",
                "VolumeRatio": "volume_ratio",
                "WMA": "wma",
                "HMA": "hma",
                "TEMA": "tema",
                "ROC": "roc",
                "MOM": "mom",
                "CMO": "cmo",
                "DEMA": "dema",
                "HistoricalVol": "hist_vol",
                "EMA_Slope": "ema_slope",
                "Stdev": "stdev",
                "ZScore": "zscore",
                "DPO": "dpo",
                "LinReg": "linreg",
            }[normalized_type],
            period_hint=period,
        )

    if indicator_type in {"ATR", "ADX", "NTR", "BULLBEARPOWER"}:
        high, low, close = sources_or("high", "low", "close")
        default_period = 13 if indicator_type == "BULLBEARPOWER" else 14
        period = _read_positive_int(
            numeric_values[0] if numeric_values else default_period,
            label=f"indicator.{config.name}.period",
        )
        normalized_type = "BullBearPower" if indicator_type == "BULLBEARPOWER" else indicator_type
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type=normalized_type,
            params={"high": high, "low": low, "close": close, "period": period},
            primary_output={"ATR": "atr", "ADX": "adx", "NTR": "ntr", "BullBearPower": "bull_power"}[normalized_type],
            period_hint=period,
        )

    if indicator_type == "MACD":
        if len(numeric_values) < 3:
            raise StrategyConfigError(f"indicator {config.name} requires fast/slow/signal")
        fast = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.fast")
        slow = _read_positive_int(numeric_values[1], label=f"indicator.{config.name}.slow")
        signal = _read_positive_int(numeric_values[2], label=f"indicator.{config.name}.signal")
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type=indicator_type,
            params={"source": source_or("close"), "fast": fast, "slow": slow, "signal": signal},
            primary_output="macd_hist",
            period_hint=max(fast, slow, signal),
        )

    if indicator_type == "BOLLINGERBANDS":
        if not numeric_values:
            raise StrategyConfigError(f"indicator {config.name} requires period")
        period = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.period")
        std_dev = _read_positive_float(
            numeric_values[1] if len(numeric_values) > 1 else 2.0,
            label=f"indicator.{config.name}.std_dev",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="BollingerBands",
            params={"source": source_or("close"), "period": period, "std_dev": std_dev},
            primary_output="bb_position",
            period_hint=period,
        )

    if indicator_type == "DONCHIANBREAKOUT":
        high, low = sources_or("high", "low")[:2]
        if not numeric_values:
            raise StrategyConfigError(f"indicator {config.name} requires entry_period")
        entry_period = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.entry_period")
        exit_period = _read_positive_int(
            numeric_values[1] if len(numeric_values) > 1 else max(1, entry_period // 2),
            label=f"indicator.{config.name}.exit_period",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="DonchianBreakout",
            params={"high": high, "low": low, "entry_period": entry_period, "exit_period": exit_period},
            primary_output="donchian_high",
            period_hint=max(entry_period, exit_period),
        )

    if indicator_type in {"STOCHASTIC", "KDJ", "WILLIAMSR", "CCI"}:
        high, low, close = sources_or("high", "low", "close")
        if indicator_type == "STOCHASTIC":
            k_period = _read_positive_int(
                numeric_values[0] if numeric_values else 14,
                label=f"indicator.{config.name}.k_period",
            )
            d_period = _read_positive_int(
                numeric_values[1] if len(numeric_values) > 1 else 3,
                label=f"indicator.{config.name}.d_period",
            )
            smooth_k = _read_positive_int(
                numeric_values[2] if len(numeric_values) > 2 else 1,
                label=f"indicator.{config.name}.smooth_k",
            )
            return GenericIndicatorSpec(
                name=config.name,
                indicator_type="Stochastic",
                params={"high": high, "low": low, "close": close, "k_period": k_period, "d_period": d_period, "smooth_k": smooth_k},
                primary_output="stoch_k",
                period_hint=max(k_period, d_period, smooth_k),
            )
        if indicator_type == "KDJ":
            k_period = _read_positive_int(
                numeric_values[0] if numeric_values else 9,
                label=f"indicator.{config.name}.k_period",
            )
            d_period = _read_positive_int(
                numeric_values[1] if len(numeric_values) > 1 else 3,
                label=f"indicator.{config.name}.d_period",
            )
            j_smooth = _read_positive_int(
                numeric_values[2] if len(numeric_values) > 2 else 3,
                label=f"indicator.{config.name}.j_smooth",
            )
            return GenericIndicatorSpec(
                name=config.name,
                indicator_type="KDJ",
                params={"high": high, "low": low, "close": close, "k_period": k_period, "d_period": d_period, "j_smooth": j_smooth},
                primary_output="kdj_k",
                period_hint=max(k_period, d_period, j_smooth),
            )
        period = _read_positive_int(
            numeric_values[0] if numeric_values else (20 if indicator_type == "CCI" else 14),
            label=f"indicator.{config.name}.period",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="WilliamsR" if indicator_type == "WILLIAMSR" else "CCI",
            params={"high": high, "low": low, "close": close, "period": period},
            primary_output="williams_r" if indicator_type == "WILLIAMSR" else "cci",
            period_hint=period,
        )

    if indicator_type == "STOCHASTICRSI":
        if not numeric_values:
            raise StrategyConfigError(f"indicator {config.name} requires rsi_period")
        rsi_period = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.rsi_period")
        stoch_period = _read_positive_int(
            numeric_values[1] if len(numeric_values) > 1 else 14,
            label=f"indicator.{config.name}.stoch_period",
        )
        k_period = _read_positive_int(
            numeric_values[2] if len(numeric_values) > 2 else 3,
            label=f"indicator.{config.name}.k_period",
        )
        d_period = _read_positive_int(
            numeric_values[3] if len(numeric_values) > 3 else 3,
            label=f"indicator.{config.name}.d_period",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="StochasticRSI",
            params={"source": source_or("close"), "rsi_period": rsi_period, "stoch_period": stoch_period, "k_period": k_period, "d_period": d_period},
            primary_output="stochrsi_k",
            period_hint=max(rsi_period, stoch_period, k_period, d_period),
        )

    if indicator_type == "KELTNERCHANNEL":
        high, low, close = sources_or("high", "low", "close")
        ema_period = _read_positive_int(
            numeric_values[0] if numeric_values else 20,
            label=f"indicator.{config.name}.ema_period",
        )
        atr_period = _read_positive_int(
            numeric_values[1] if len(numeric_values) > 1 else ema_period,
            label=f"indicator.{config.name}.atr_period",
        )
        multiplier = _read_positive_float(
            numeric_values[2] if len(numeric_values) > 2 else 2.0,
            label=f"indicator.{config.name}.multiplier",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="KeltnerChannel",
            params={"high": high, "low": low, "close": close, "source": source_or(close), "ema_period": ema_period, "atr_period": atr_period, "multiplier": multiplier},
            primary_output="keltner_mid",
            period_hint=max(ema_period, atr_period),
        )

    if indicator_type == "AROON":
        high, low = sources_or("high", "low")[:2]
        period = _read_positive_int(
            numeric_values[0] if numeric_values else 25,
            label=f"indicator.{config.name}.period",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="Aroon",
            params={"high": high, "low": low, "period": period},
            primary_output="aroon_up",
            period_hint=period,
        )

    if indicator_type == "TRIX":
        if not numeric_values:
            raise StrategyConfigError(f"indicator {config.name} requires period")
        period = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.period")
        signal = _read_positive_int(
            numeric_values[1] if len(numeric_values) > 1 else 9,
            label=f"indicator.{config.name}.signal",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="TRIX",
            params={"source": source_or("close"), "period": period, "signal": signal},
            primary_output="trix",
            period_hint=max(period, signal),
        )

    if indicator_type in {"CHAIKINAD", "VWAP"}:
        high, low, close, volume = sources_or("high", "low", "close", "volume")
        normalized_type = "ChaikinAD" if indicator_type == "CHAIKINAD" else "VWAP"
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type=normalized_type,
            params={"high": high, "low": low, "close": close, "volume": volume},
            primary_output="chaikin_ad" if normalized_type == "ChaikinAD" else "vwap",
            period_hint=2,
        )

    if indicator_type in {"MFI", "CMF"}:
        high, low, close, volume = sources_or("high", "low", "close", "volume")
        period = _read_positive_int(
            numeric_values[0] if numeric_values else (14 if indicator_type == "MFI" else 20),
            label=f"indicator.{config.name}.period",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type=indicator_type,
            params={"high": high, "low": low, "close": close, "volume": volume, "period": period},
            primary_output="mfi" if indicator_type == "MFI" else "cmf",
            period_hint=period,
        )

    if indicator_type in {"OBV", "PVT"}:
        close, volume = sources_or("close", "volume")[:2]
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type=indicator_type,
            params={"close": close, "volume": volume},
            primary_output="obv" if indicator_type == "OBV" else "pvt",
            period_hint=2,
        )

    if indicator_type == "ATRTRAILINGSTOP":
        high, low, close = sources_or("high", "low", "close")
        period = _read_positive_int(
            numeric_values[0] if numeric_values else 14,
            label=f"indicator.{config.name}.period",
        )
        multiplier = _read_positive_float(
            numeric_values[1] if len(numeric_values) > 1 else 2.0,
            label=f"indicator.{config.name}.multiplier",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="ATRTrailingStop",
            params={"high": high, "low": low, "close": close, "period": period, "multiplier": multiplier},
            primary_output="atr_trail_stop",
            period_hint=period,
        )

    if indicator_type == "PARABOLICSAR":
        high, low, close = sources_or("high", "low", "close")
        af_start = _read_positive_float(
            numeric_values[0] if numeric_values else 0.02,
            label=f"indicator.{config.name}.af_start",
        )
        af_max = _read_positive_float(
            numeric_values[1] if len(numeric_values) > 1 else 0.2,
            label=f"indicator.{config.name}.af_max",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="ParabolicSAR",
            params={"high": high, "low": low, "close": close, "af_start": af_start, "af_max": af_max},
            primary_output="psar",
            period_hint=2,
        )

    if indicator_type == "SUPERTREND":
        high, low, close = sources_or("high", "low", "close")
        period = _read_positive_int(
            numeric_values[0] if numeric_values else 10,
            label=f"indicator.{config.name}.period",
        )
        multiplier = _read_positive_float(
            numeric_values[1] if len(numeric_values) > 1 else 3.0,
            label=f"indicator.{config.name}.multiplier",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="Supertrend",
            params={"high": high, "low": low, "close": close, "period": period, "multiplier": multiplier},
            primary_output="supertrend_stop",
            period_hint=period,
        )

    if indicator_type == "ICHIMOKU":
        high, low, close = sources_or("high", "low", "close")
        tenkan = _read_positive_int(
            numeric_values[0] if numeric_values else 9,
            label=f"indicator.{config.name}.tenkan",
        )
        kijun = _read_positive_int(
            numeric_values[1] if len(numeric_values) > 1 else 26,
            label=f"indicator.{config.name}.kijun",
        )
        senkou_b = _read_positive_int(
            numeric_values[2] if len(numeric_values) > 2 else 52,
            label=f"indicator.{config.name}.senkou_b",
        )
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="Ichimoku",
            params={"high": high, "low": low, "close": close, "tenkan": tenkan, "kijun": kijun, "senkou_b": senkou_b},
            primary_output="ichimoku_signal",
            period_hint=max(tenkan, kijun, senkou_b),
        )

    if indicator_type == "EMA_CROSS":
        if len(numeric_values) < 2:
            raise StrategyConfigError(f"indicator {config.name} requires fast_period/slow_period")
        fast = _read_positive_int(numeric_values[0], label=f"indicator.{config.name}.fast_period")
        slow = _read_positive_int(numeric_values[1], label=f"indicator.{config.name}.slow_period")
        return GenericIndicatorSpec(
            name=config.name,
            indicator_type="EMA_Cross",
            params={"source": source_or("close"), "fast_period": fast, "slow_period": slow},
            primary_output="ema_cross",
            period_hint=max(fast, slow),
        )

    raise StrategyConfigError(f"unsupported indicator type {config.indicator_type}")


def _evaluate_factor_formula(factor: FactorConfig, environment: Mapping[str, Any]) -> float:
    if not factor.formula:
        raise StrategyConfigError(f"factor {factor.factor_name} missing formula")
    if _expression_has_unresolved_inputs(factor.formula, environment):
        return 0.0
    result = _safe_eval_expression(factor.formula, environment)
    if isinstance(result, bool):
        return 1.0 if result else 0.0
    if isinstance(result, (int, float)) and not isinstance(result, bool):
        return float(result)
    raise StrategyConfigError(f"factor {factor.factor_name} formula must return numeric/bool")


def _evaluate_signal_condition(condition: Any, environment: Mapping[str, Any]) -> bool:
    if condition in {None, False, ""}:
        return False
    if condition is True:
        return True
    if not isinstance(condition, str):
        raise StrategyConfigError("signal condition must be a string or boolean")
    if _expression_has_unresolved_inputs(condition, environment):
        return False
    result = _safe_eval_expression(condition, environment)
    if isinstance(result, bool):
        return result
    if isinstance(result, (int, float)) and not isinstance(result, bool):
        return bool(result)
    raise StrategyConfigError("signal condition must return bool/numeric")


def _evaluate_market_filter_conditions(
    conditions: List[str],
    environment: Mapping[str, Any],
) -> bool:
    if not conditions:
        return True
    return all(_evaluate_signal_condition(condition, environment) for condition in conditions)


def _safe_eval_expression(expression: str, environment: Mapping[str, Any]) -> Any:
    prepared = _prepare_expression(expression)
    if len(prepared) > 1024:
        raise StrategyConfigError(f"expression too long ({len(prepared)} chars, max 1024)")
    try:
        tree = ast.parse(prepared, mode="eval")
        validator = _SafeExpressionValidator(set(environment) | set(_ALLOWED_FUNCTIONS))
        validator.visit(tree)
        if validator.node_count > 200:
            raise StrategyConfigError(f"expression too complex ({validator.node_count} nodes, max 200)")
        return eval(
            compile(tree, "<generic-strategy-expression>", "eval"),
            {"__builtins__": {}},
            {**_ALLOWED_FUNCTIONS, **dict(environment)},
        )
    except StrategyConfigError:
        raise
    except Exception as exc:
        raise StrategyConfigError(f"expression evaluation failed: {expression} ({exc})") from exc


def _prepare_expression(expression: str) -> str:
    normalized = expression.strip()
    if not normalized:
        raise StrategyConfigError("expression must be non-empty")
    normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace("&&", " and ").replace("||", " or ")
    normalized = _rewrite_legacy_expression_calls(normalized)
    return _convert_ternary_expression(normalized)


def _rewrite_legacy_expression_calls(expression: str) -> str:
    normalized = re.sub(
        r"\bsma\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d+)\s*\)",
        lambda match: f"sma_{match.group(1).lower()}_{match.group(2)}",
        expression,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\bema\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d+)\s*\)",
        lambda match: f"ema_{match.group(1).lower()}_{match.group(2)}",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"\bdonchian_high\s*\(\s*[^)]+\)", "donchian_high", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bdonchian_low\s*\(\s*[^)]+\)", "donchian_low", normalized, flags=re.IGNORECASE)
    normalized = re.sub(
        r"\badx\s*\(\s*period\s*=\s*(\d+)\s*\)",
        lambda match: f"adx_{match.group(1)}",
        normalized,
        flags=re.IGNORECASE,
    )
    return normalized


def _expression_has_unresolved_inputs(expression: str, environment: Mapping[str, Any]) -> bool:
    prepared = _prepare_expression(expression)
    try:
        tree = ast.parse(prepared, mode="eval")
    except SyntaxError as exc:
        raise StrategyConfigError(f"invalid expression syntax: {expression}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in _ALLOWED_FUNCTIONS:
            if environment.get(node.id) is None:
                return True
    return False


def _convert_ternary_expression(expression: str) -> str:
    question_index = _find_top_level_question(expression)
    if question_index < 0:
        return expression
    colon_index = _find_matching_colon(expression, question_index)
    condition = expression[:question_index].strip()
    true_expr = expression[question_index + 1 : colon_index].strip()
    false_expr = expression[colon_index + 1 :].strip()
    return (
        f"(({_convert_ternary_expression(true_expr)}) "
        f"if ({_convert_ternary_expression(condition)}) "
        f"else ({_convert_ternary_expression(false_expr)}))"
    )


def _find_top_level_question(expression: str) -> int:
    depth = 0
    for index, char in enumerate(expression):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "?" and depth == 0:
            return index
    return -1


def _find_matching_colon(expression: str, question_index: int) -> int:
    depth = 0
    nested_questions = 0
    for index in range(question_index + 1, len(expression)):
        char = expression[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "?" and depth == 0:
            nested_questions += 1
        elif char == ":" and depth == 0:
            if nested_questions == 0:
                return index
            nested_questions -= 1
    raise StrategyConfigError(f"invalid ternary expression: {expression}")


class _SafeExpressionValidator(ast.NodeVisitor):
    _allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.BinOp,
        ast.UnaryOp,
        ast.IfExp,
        ast.Compare,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.List,
        ast.Tuple,
    )

    _allowed_bin_ops = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)
    _allowed_unary_ops = (ast.UAdd, ast.USub, ast.Not)
    _allowed_bool_ops = (ast.And, ast.Or)
    _allowed_compare_ops = (ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE)

    _MAX_POW_EXPONENT = 100

    def __init__(self, allowed_names: Set[str]) -> None:
        self._allowed_names = allowed_names
        self.node_count = 0

    def generic_visit(self, node: ast.AST) -> None:
        self.node_count += 1
        if not isinstance(node, self._allowed_nodes):
            raise StrategyConfigError(f"unsupported expression node {type(node).__name__}")
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in self._allowed_names:
            raise StrategyConfigError(f"unsupported expression name {node.id}")

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
            raise StrategyConfigError("unsupported expression call")
        for argument in node.args:
            self.visit(argument)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if not isinstance(node.op, self._allowed_bool_ops):
            raise StrategyConfigError("unsupported boolean operator")
        for value in node.values:
            self.visit(value)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if not isinstance(node.op, self._allowed_bin_ops):
            raise StrategyConfigError("unsupported binary operator")
        if isinstance(node.op, ast.Pow):
            if not isinstance(node.right, ast.Constant) or not isinstance(
                getattr(node.right, "value", None), (int, float)
            ):
                raise StrategyConfigError(
                    "Pow exponent must be a numeric constant"
                )
            if node.right.value > self._MAX_POW_EXPONENT:
                raise StrategyConfigError(
                    f"exponent {node.right.value} exceeds max allowed ({self._MAX_POW_EXPONENT})"
                )
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if not isinstance(node.op, self._allowed_unary_ops):
            raise StrategyConfigError("unsupported unary operator")
        self.visit(node.operand)

    def visit_Compare(self, node: ast.Compare) -> None:
        for operator in node.ops:
            if not isinstance(operator, self._allowed_compare_ops):
                raise StrategyConfigError("unsupported comparison operator")
        self.visit(node.left)
        for comparator in node.comparators:
            self.visit(comparator)


def _candidate_signal_state(row: Mapping[str, Any]) -> str:
    long_candidate = bool(row.get("long_signal_candidate"))
    short_candidate = bool(row.get("short_signal_candidate"))
    if long_candidate and not short_candidate:
        return "long"
    if short_candidate and not long_candidate:
        return "short"
    return "flat"


def _position_side_from_volume(volume: int) -> str:
    if volume > 0:
        return "long"
    if volume < 0:
        return "short"
    return "flat"


def _normalize_symbol_token(symbol: str) -> str:
    return str(symbol).strip().split(".")[-1].lower()


def _get_variety_code(token: str) -> str:
    """Extract variety code: 'p2509'→'p', 'rb2510'→'rb', 'p_main'→'p'."""
    import re as _re
    t = str(token).lower().strip()
    t = _re.sub(r'_main$', '', t)       # strip _main suffix
    t = _re.sub(r'\d+$', '', t)         # strip trailing month digits
    return t


def _symbol_matches(expected_token: str, requested_token: str) -> bool:
    """Match allowing _main wildcard: 'p_main' matches 'p2509', 'p2611' etc."""
    if expected_token == requested_token:
        return True
    if '_main' in expected_token or expected_token.endswith('_main'):
        return _get_variety_code(expected_token) == _get_variety_code(requested_token)
    return False


def _dedupe_indicator_specs(indicators: List[GenericIndicatorSpec]) -> List[GenericIndicatorSpec]:
    deduped: List[GenericIndicatorSpec] = []
    seen: set[str] = set()
    for indicator in indicators:
        if indicator.name in seen:
            continue
        seen.add(indicator.name)
        deduped.append(indicator)
    return deduped


# ── Default legacy factor formulas ─────────────────────────────

_LEGACY_FACTOR_FORMULA: Dict[str, str] = {
    "sma": "1 if close > sma else (-1 if close < sma else 0)",
    "ema": "1 if close > ema else (-1 if close < ema else 0)",
    "macd": "1 if macd_hist > 0 else (-1 if macd_hist < 0 else 0)",
    "rsi": "1 if rsi > 55 else (-1 if rsi < 45 else 0)",
    "adx": "1 if adx > 25 else 0",
    "obv": "1 if obv > 0 else (-1 if obv < 0 else 0)",
    "volumeratio": "1 if volume_ratio > 1.2 else (-1 if volume_ratio < 0.8 else 0)",
    "bollingerbands": "1 if bb_position == 'lower_band' else (-1 if bb_position == 'upper_band' else 0)",
    "atr": "1 if atr > 0 else 0",
    "cci": "1 if cci > 100 else (-1 if cci < -100 else 0)",
    "kdj": "1 if kdj_k > 80 else (-1 if kdj_k < 20 else 0)",
    "williamsr": "1 if williams_r > -20 else (-1 if williams_r < -80 else 0)",
    "mfi": "1 if mfi > 60 else (-1 if mfi < 40 else 0)",
    "ema_cross": "1 if ema_cross > 0 else (-1 if ema_cross < 0 else 0)",
    "donchianbreakout": "1 if close > donchian_high else (-1 if close < donchian_low else 0)",
    "vwap": "1 if close > vwap else (-1 if close < vwap else 0)",
}


def _default_legacy_formula(factor_name: str, params: Dict[str, Any]) -> Optional[str]:
    """Return a default scoring formula for a legacy factor type."""
    normalized = factor_name.strip().lower()
    return _LEGACY_FACTOR_FORMULA.get(normalized)


def _assign_default_legacy_formulas(
    factors: List[FactorConfig],
    indicators: List[GenericIndicatorSpec],
    long_condition: Any,
    short_condition: Any,
) -> List[FactorConfig]:
    """Clone factors, filling in default formulas for those that lack one.

    Only applies when the signal conditions reference ``factor_total_score``,
    because that requires factor formulas to produce numeric scores.  If the
    signal conditions use raw indicator variables directly (e.g. ``rsi < 30``),
    we leave the factors as-is so they just contribute indicator calculations.
    """
    conditions_text = " ".join(str(c or "") for c in [long_condition, short_condition])
    if "factor_total_score" not in conditions_text:
        return list(factors)

    result: List[FactorConfig] = []
    for factor in factors:
        if factor.formula:
            result.append(factor)
            continue
        default_formula = _default_legacy_formula(factor.factor_name, factor.params)
        if default_formula is None:
            result.append(factor)
            continue
        patched = FactorConfig(
            factor_name=factor.factor_name,
            weight=factor.weight,
            params=factor.params,
            formula=default_formula,
            description=factor.description,
            factor_type=factor.factor_type,
        )
        result.append(patched)
    return result


def _infer_legacy_indicator_specs(
    definition: StrategyDefinition,
    *,
    long_condition: Any,
    short_condition: Any,
    market_filter_conditions: List[str],
) -> List[GenericIndicatorSpec]:
    specs: List[GenericIndicatorSpec] = []

    position_adjustment = definition.params.get("position_adjustment") or {}
    if not isinstance(position_adjustment, Mapping):
        position_adjustment = {}
    atr_period = _read_positive_int(position_adjustment.get("atr_period", 14), label="position_adjustment.atr_period")
    default_adx_period = 14

    def add(spec: GenericIndicatorSpec) -> None:
        specs.append(spec)

    for factor in definition.factors:
        normalized_name = factor.factor_name.strip().lower()
        params = dict(factor.params)
        alias_name = str(params.pop("_alias", "") or "").strip()
        if normalized_name == "macd":
            fast = _read_positive_int(params.get("fast", 12), label="MACD.fast")
            slow = _read_positive_int(params.get("slow", 26), label="MACD.slow")
            signal = _read_positive_int(params.get("signal", 9), label="MACD.signal")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "macd_hist",
                    indicator_type="MACD",
                    params={"source": "close", "fast": fast, "slow": slow, "signal": signal},
                    primary_output="macd_hist",
                    period_hint=max(fast, slow, signal),
                )
            )
        elif normalized_name == "rsi":
            period = _read_positive_int(params.get("period", 14), label="RSI.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "rsi",
                    indicator_type="RSI",
                    params={"source": "close", "period": period},
                    primary_output="rsi",
                    period_hint=period,
                )
            )
        elif normalized_name == "volumeratio":
            period = _read_positive_int(params.get("period", 10), label="VolumeRatio.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "volume_ratio",
                    indicator_type="VolumeRatio",
                    params={"source": "volume", "period": period},
                    primary_output="volume_ratio",
                    period_hint=period,
                )
            )
        elif normalized_name == "bollingerbands":
            period = _read_positive_int(params.get("period", 20), label="BollingerBands.period")
            std_dev = _read_positive_float(
                params.get("stddev", params.get("std_dev", params.get("multiplier", 2.0))),
                label="BollingerBands.stddev",
            )
            add(
                GenericIndicatorSpec(
                    name=alias_name or "bb_position",
                    indicator_type="BollingerBands",
                    params={"source": "close", "period": period, "std_dev": std_dev},
                    primary_output="bb_position",
                    period_hint=period,
                )
            )
        elif normalized_name == "donchianbreakout":
            entry_period = _read_positive_int(
                params.get("entry_period", params.get("period", 20)),
                label="DonchianBreakout.entry_period",
            )
            exit_period = _read_positive_int(
                params.get("exit_period", max(1, entry_period // 2)),
                label="DonchianBreakout.exit_period",
            )
            add(
                GenericIndicatorSpec(
                    name=alias_name or "donchian_high",
                    indicator_type="DonchianBreakout",
                    params={"high": "high", "low": "low", "entry_period": entry_period, "exit_period": exit_period},
                    primary_output="donchian_high",
                    period_hint=max(entry_period, exit_period),
                )
            )
        elif normalized_name == "atr":
            period = _read_positive_int(params.get("period", atr_period), label="ATR.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "atr",
                    indicator_type="ATR",
                    params={"high": "high", "low": "low", "close": "close", "period": period},
                    primary_output="atr",
                    period_hint=period,
                )
            )
        elif normalized_name == "atrtrailingstop":
            period = _read_positive_int(params.get("period", atr_period), label="ATRTrailingStop.period")
            multiplier = _read_positive_float(
                params.get("multiplier", params.get("atr_multiplier", 2.0)),
                label="ATRTrailingStop.multiplier",
            )
            add(
                GenericIndicatorSpec(
                    name=alias_name or "atr_trail_stop",
                    indicator_type="ATRTrailingStop",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "period": period,
                        "multiplier": multiplier,
                    },
                    primary_output="atr_trail_stop",
                    period_hint=period,
                )
            )
        elif normalized_name == "adx":
            period = _read_positive_int(params.get("period", default_adx_period), label="ADX.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "adx",
                    indicator_type="ADX",
                    params={"high": "high", "low": "low", "close": "close", "period": period},
                    primary_output="adx",
                    period_hint=period,
                )
            )
        elif normalized_name == "williamsr":
            period = _read_positive_int(params.get("period", 14), label="WilliamsR.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "williams_r",
                    indicator_type="WilliamsR",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "period": period,
                    },
                    primary_output="williams_r",
                    period_hint=period,
                )
            )
        elif normalized_name == "kdj":
            k_period = _read_positive_int(params.get("k_period", 9), label="KDJ.k_period")
            d_period = _read_positive_int(params.get("d_period", 3), label="KDJ.d_period")
            j_smooth = _read_positive_int(params.get("j_smooth", 3), label="KDJ.j_smooth")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "kdj_k",
                    indicator_type="KDJ",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "k_period": k_period,
                        "d_period": d_period,
                        "j_smooth": j_smooth,
                    },
                    primary_output="kdj_k",
                    period_hint=max(k_period, d_period, j_smooth),
                )
            )
        elif normalized_name == "cci":
            period = _read_positive_int(params.get("period", 20), label="CCI.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "cci",
                    indicator_type="CCI",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "period": period,
                    },
                    primary_output="cci",
                    period_hint=period,
                )
            )
        elif normalized_name == "obv":
            add(
                GenericIndicatorSpec(
                    name=alias_name or "obv",
                    indicator_type="OBV",
                    params={
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "volume": str(params.get("volume") or "volume").strip().lower() or "volume",
                    },
                    primary_output="obv",
                    period_hint=2,
                )
            )
        elif normalized_name == "vwap":
            add(
                GenericIndicatorSpec(
                    name=alias_name or "vwap",
                    indicator_type="VWAP",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "volume": str(params.get("volume") or "volume").strip().lower() or "volume",
                    },
                    primary_output="vwap",
                    period_hint=2,
                )
            )
        elif normalized_name == "mfi":
            period = _read_positive_int(params.get("period", 14), label="MFI.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "mfi",
                    indicator_type="MFI",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "volume": str(params.get("volume") or "volume").strip().lower() or "volume",
                        "period": period,
                    },
                    primary_output="mfi",
                    period_hint=period,
                )
            )
        elif normalized_name == "ema_cross":
            fast = _read_positive_int(params.get("fast_period", params.get("fast", 10)), label="EMA_Cross.fast_period")
            slow = _read_positive_int(params.get("slow_period", params.get("slow", 20)), label="EMA_Cross.slow_period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "ema_cross",
                    indicator_type="EMA_Cross",
                    params={
                        "source": str(params.get("source") or "close").strip().lower() or "close",
                        "fast_period": fast,
                        "slow_period": slow,
                    },
                    primary_output="ema_cross",
                    period_hint=max(fast, slow),
                )
            )
        elif normalized_name == "parabolicsar":
            af_start = _read_positive_float(params.get("af_start", 0.02), label="ParabolicSAR.af_start")
            af_max = _read_positive_float(params.get("af_max", 0.2), label="ParabolicSAR.af_max")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "psar",
                    indicator_type="ParabolicSAR",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "af_start": af_start,
                        "af_max": af_max,
                    },
                    primary_output="psar",
                    period_hint=2,
                )
            )
        elif normalized_name == "supertrend":
            period = _read_positive_int(params.get("period", 10), label="Supertrend.period")
            multiplier = _read_positive_float(params.get("multiplier", 3.0), label="Supertrend.multiplier")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "supertrend_stop",
                    indicator_type="Supertrend",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "period": period,
                        "multiplier": multiplier,
                    },
                    primary_output="supertrend_stop",
                    period_hint=period,
                )
            )
        elif normalized_name == "ichimoku":
            tenkan = _read_positive_int(params.get("tenkan", 9), label="Ichimoku.tenkan")
            kijun = _read_positive_int(params.get("kijun", 26), label="Ichimoku.kijun")
            senkou_b = _read_positive_int(params.get("senkou_b", 52), label="Ichimoku.senkou_b")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "ichimoku_signal",
                    indicator_type="Ichimoku",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "tenkan": tenkan,
                        "kijun": kijun,
                        "senkou_b": senkou_b,
                    },
                    primary_output="ichimoku_signal",
                    period_hint=max(tenkan, kijun, senkou_b),
                )
            )
        elif normalized_name in {
            "sma",
            "ema",
            "wma",
            "hma",
            "tema",
            "roc",
            "mom",
            "cmo",
            "dema",
            "historicalvol",
            "histvol",
            "ema_slope",
            "stdev",
            "zscore",
            "dpo",
            "linreg",
        }:
            indicator_type = {
                "histvol": "HistoricalVol",
                "historicalvol": "HistoricalVol",
                "ema_slope": "EMA_Slope",
                "stdev": "Stdev",
                "zscore": "ZScore",
                "linreg": "LinReg",
            }.get(normalized_name, normalized_name.upper() if len(normalized_name) <= 4 else normalized_name)
            if indicator_type == "Ema_slope":
                indicator_type = "EMA_Slope"
            period = _read_positive_int(params.get("period", 20), label=f"{factor.factor_name}.period")
            source = str(params.get("source") or "close").strip().lower() or "close"
            primary_output = {
                "SMA": "sma",
                "EMA": "ema",
                "WMA": "wma",
                "HMA": "hma",
                "TEMA": "tema",
                "ROC": "roc",
                "MOM": "mom",
                "CMO": "cmo",
                "DEMA": "dema",
                "HistoricalVol": "hist_vol",
                "EMA_Slope": "ema_slope",
                "Stdev": "stdev",
                "ZScore": "zscore",
                "DPO": "dpo",
                "LinReg": "linreg",
            }[indicator_type]
            add(
                GenericIndicatorSpec(
                    name=alias_name or primary_output,
                    indicator_type=indicator_type,
                    params={"source": source, "period": period},
                    primary_output=primary_output,
                    period_hint=period,
                )
            )
        elif normalized_name == "stochastic":
            k_period = _read_positive_int(params.get("k_period", params.get("period", 14)), label="Stochastic.k_period")
            d_period = _read_positive_int(params.get("d_period", 3), label="Stochastic.d_period")
            smooth_k = _read_positive_int(params.get("smooth_k", 1), label="Stochastic.smooth_k")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "stoch_k",
                    indicator_type="Stochastic",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "k_period": k_period,
                        "d_period": d_period,
                        "smooth_k": smooth_k,
                    },
                    primary_output="stoch_k",
                    period_hint=max(k_period, d_period, smooth_k),
                )
            )
        elif normalized_name == "stochasticrsi":
            rsi_period = _read_positive_int(params.get("rsi_period", 14), label="StochasticRSI.rsi_period")
            stoch_period = _read_positive_int(params.get("stoch_period", 14), label="StochasticRSI.stoch_period")
            k_period = _read_positive_int(params.get("k_period", 3), label="StochasticRSI.k_period")
            d_period = _read_positive_int(params.get("d_period", 3), label="StochasticRSI.d_period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "stochrsi_k",
                    indicator_type="StochasticRSI",
                    params={
                        "source": str(params.get("source") or "close").strip().lower() or "close",
                        "rsi_period": rsi_period,
                        "stoch_period": stoch_period,
                        "k_period": k_period,
                        "d_period": d_period,
                    },
                    primary_output="stochrsi_k",
                    period_hint=max(rsi_period, stoch_period, k_period, d_period),
                )
            )
        elif normalized_name == "keltnerchannel":
            ema_period = _read_positive_int(params.get("ema_period", params.get("period", 20)), label="KeltnerChannel.ema_period")
            atr_window = _read_positive_int(params.get("atr_period", ema_period), label="KeltnerChannel.atr_period")
            multiplier = _read_positive_float(params.get("multiplier", 2.0), label="KeltnerChannel.multiplier")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "keltner_mid",
                    indicator_type="KeltnerChannel",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "source": str(params.get("source") or params.get("close") or "close").strip().lower() or "close",
                        "ema_period": ema_period,
                        "atr_period": atr_window,
                        "multiplier": multiplier,
                    },
                    primary_output="keltner_mid",
                    period_hint=max(ema_period, atr_window),
                )
            )
        elif normalized_name == "ntr":
            period = _read_positive_int(params.get("period", 14), label="NTR.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "ntr",
                    indicator_type="NTR",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "period": period,
                    },
                    primary_output="ntr",
                    period_hint=period,
                )
            )
        elif normalized_name == "aroon":
            period = _read_positive_int(params.get("period", 25), label="Aroon.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "aroon_up",
                    indicator_type="Aroon",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "period": period,
                    },
                    primary_output="aroon_up",
                    period_hint=period,
                )
            )
        elif normalized_name == "trix":
            period = _read_positive_int(params.get("period", 15), label="TRIX.period")
            signal = _read_positive_int(params.get("signal", 9), label="TRIX.signal")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "trix",
                    indicator_type="TRIX",
                    params={
                        "source": str(params.get("source") or "close").strip().lower() or "close",
                        "period": period,
                        "signal": signal,
                    },
                    primary_output="trix",
                    period_hint=max(period, signal),
                )
            )
        elif normalized_name == "chaikinad":
            add(
                GenericIndicatorSpec(
                    name=alias_name or "chaikin_ad",
                    indicator_type="ChaikinAD",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "volume": str(params.get("volume") or "volume").strip().lower() or "volume",
                    },
                    primary_output="chaikin_ad",
                    period_hint=2,
                )
            )
        elif normalized_name == "cmf":
            period = _read_positive_int(params.get("period", 20), label="CMF.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "cmf",
                    indicator_type="CMF",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "volume": str(params.get("volume") or "volume").strip().lower() or "volume",
                        "period": period,
                    },
                    primary_output="cmf",
                    period_hint=period,
                )
            )
        elif normalized_name == "pvt":
            add(
                GenericIndicatorSpec(
                    name=alias_name or "pvt",
                    indicator_type="PVT",
                    params={
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "volume": str(params.get("volume") or "volume").strip().lower() or "volume",
                    },
                    primary_output="pvt",
                    period_hint=2,
                )
            )
        elif normalized_name == "bullbearpower":
            period = _read_positive_int(params.get("period", 13), label="BullBearPower.period")
            add(
                GenericIndicatorSpec(
                    name=alias_name or "bull_power",
                    indicator_type="BullBearPower",
                    params={
                        "high": str(params.get("high") or "high").strip().lower() or "high",
                        "low": str(params.get("low") or "low").strip().lower() or "low",
                        "close": str(params.get("close") or "close").strip().lower() or "close",
                        "period": period,
                    },
                    primary_output="bull_power",
                    period_hint=period,
                )
            )
        elif normalized_name == "spread":
            period = _read_positive_int(params.get("period", 20), label="Spread.period")
            col_a = str(params.get("col_a") or "close").strip().lower() or "close"
            col_b = str(params.get("col_b") or "close_ref").strip().lower() or "close_ref"
            add(
                GenericIndicatorSpec(
                    name=alias_name or "spread_zscore",
                    indicator_type="Spread",
                    params={"col_a": col_a, "col_b": col_b, "period": period},
                    primary_output="spread_zscore",
                    period_hint=period,
                )
            )
        elif normalized_name == "spread_rsi":
            period = _read_positive_int(params.get("period", 14), label="Spread_RSI.period")
            col_a = str(params.get("col_a") or "close").strip().lower() or "close"
            col_b = str(params.get("col_b") or "close_ref").strip().lower() or "close_ref"
            add(
                GenericIndicatorSpec(
                    name=alias_name or "spread_rsi",
                    indicator_type="Spread_RSI",
                    params={"col_a": col_a, "col_b": col_b, "period": period},
                    primary_output="spread_rsi",
                    period_hint=period,
                )
            )

    expression_texts: List[str] = []
    for value in [long_condition, short_condition, *market_filter_conditions]:
        if isinstance(value, str) and value.strip():
            expression_texts.append(value)

    combined_expression = "\n".join(expression_texts)
    if re.search(r"\batr\b", combined_expression):
        add(
            GenericIndicatorSpec(
                name="atr",
                indicator_type="ATR",
                params={"high": "high", "low": "low", "close": "close", "period": atr_period},
                primary_output="atr",
                period_hint=atr_period,
            )
        )
    for adx_period_text in re.findall(
        r"\badx\s*\(\s*period\s*=\s*(\d+)\s*\)",
        combined_expression,
        flags=re.IGNORECASE,
    ):
        adx_period = _read_positive_int(adx_period_text, label=f"adx(period={adx_period_text})")
        add(
            GenericIndicatorSpec(
                name=f"adx_{adx_period}",
                indicator_type="ADX",
                params={"high": "high", "low": "low", "close": "close", "period": adx_period},
                primary_output="adx",
                period_hint=adx_period,
            )
        )
    if re.search(r"\badx\b(?!\s*\()", combined_expression):
        add(
            GenericIndicatorSpec(
                name="adx",
                indicator_type="ADX",
                params={"high": "high", "low": "low", "close": "close", "period": default_adx_period},
                primary_output="adx",
                period_hint=default_adx_period,
            )
        )
    for source, period_text in re.findall(
        r"\bsma\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d+)\s*\)",
        combined_expression,
        flags=re.IGNORECASE,
    ):
        period = _read_positive_int(period_text, label=f"sma({source},{period_text})")
        add(
            GenericIndicatorSpec(
                name=f"sma_{source.lower()}_{period}",
                indicator_type="SMA",
                params={"source": source.lower(), "period": period},
                primary_output="sma",
                period_hint=period,
            )
        )
    for source, period_text in re.findall(
        r"\bema\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d+)\s*\)",
        combined_expression,
        flags=re.IGNORECASE,
    ):
        period = _read_positive_int(period_text, label=f"ema({source},{period_text})")
        add(
            GenericIndicatorSpec(
                name=f"ema_{source.lower()}_{period}",
                indicator_type="EMA",
                params={"source": source.lower(), "period": period},
                primary_output="ema",
                period_hint=period,
            )
        )

    return specs


def _read_positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be a positive integer")
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be a positive integer") from exc
    if not math.isfinite(float(coerced)) or float(coerced) != float(value) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be a positive integer")
    return coerced


def _read_positive_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be numeric")
    if isinstance(value, str):
        normalized = value.strip().replace("_", "")
        if not normalized:
            raise StrategyConfigError(f"{label} must be numeric")
        try:
            coerced = float(normalized[:-1].strip()) / 100.0 if normalized.endswith("%") else float(normalized)
        except ValueError as exc:
            raise StrategyConfigError(f"{label} must be numeric") from exc
        if not math.isfinite(coerced) or coerced <= 0:
            raise StrategyConfigError(f"{label} must be greater than zero")
        return coerced
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be numeric") from exc
    if not math.isfinite(coerced) or coerced <= 0:
        raise StrategyConfigError(f"{label} must be greater than zero")
    return coerced


def _read_non_negative_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise StrategyConfigError(f"{label} must be numeric")
    if isinstance(value, str):
        normalized = value.strip().replace("_", "")
        if not normalized:
            raise StrategyConfigError(f"{label} must be numeric")
        try:
            coerced = float(normalized[:-1].strip()) / 100.0 if normalized.endswith("%") else float(normalized)
        except ValueError as exc:
            raise StrategyConfigError(f"{label} must be numeric") from exc
        if not math.isfinite(coerced) or coerced < 0:
            raise StrategyConfigError(f"{label} must be greater than or equal to zero")
        return coerced
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise StrategyConfigError(f"{label} must be numeric") from exc
    if not math.isfinite(coerced) or coerced < 0:
        raise StrategyConfigError(f"{label} must be greater than or equal to zero")
    return coerced


def _read_optional_positive_float(value: Any, *, label: str) -> Optional[float]:
    if value in {None, ""}:
        return None
    return _read_positive_float(value, label=label)


def _read_optional_fraction(value: Any, *, label: str) -> Optional[float]:
    if value in {None, ""}:
        return None
    fraction = _read_non_negative_float(value, label=label)
    if fraction > 1:
        raise StrategyConfigError(f"{label} must be a ratio between 0 and 1")
    return fraction


def _optional_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        coerced = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(coerced):
        return None
    return coerced


def _read_optional_time(value: Any, *, label: str) -> Optional[time_of_day]:
    if value in {None, ""}:
        return None
    if not isinstance(value, str):
        raise StrategyConfigError(f"{label} must be an HH:MM string")
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError as exc:
        raise StrategyConfigError(f"{label} must be an HH:MM string") from exc


def _extract_timestamp(row: Any) -> Any:
    if isinstance(row, Mapping):
        if "timestamp" in row:
            return row["timestamp"]
        if "datetime" in row:
            return row["datetime"]
    return getattr(row, "timestamp", getattr(row, "datetime", None))


def _coerce_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=timezone.utc).astimezone()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            return None
        abs_value = abs(numeric_value)
        if abs_value >= 1e14:
            seconds = numeric_value / 1e9
        elif abs_value >= 1e11:
            seconds = numeric_value / 1e3
        else:
            seconds = numeric_value
        return datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()
    return None


def _collect_mapping_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        return {str(key) for key in value.keys()}
    keys = getattr(value, "keys", None)
    if callable(keys):
        try:
            return {str(key) for key in keys()}
        except Exception:
            return set()
    return set()


def _round_to_tick(price: float, tick: float) -> float:
    if tick <= 0:
        return float(price)
    return round(round(price / tick) * tick, 10)


def _resolve_backtest_finished_exception() -> type[BaseException]:
    try:
        from tqsdk import BacktestFinished
    except ImportError:
        return RuntimeError
    return BacktestFinished