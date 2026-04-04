from __future__ import annotations

import ast
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

try:
    from .factor_registry import FactorResult, factor_registry, normalize_bars
    from .strategy_base import FixedTemplateStrategy, StrategyConfigError, register_strategy_template
except ImportError:
    from factor_registry import FactorResult, factor_registry, normalize_bars
    from strategy_base import FixedTemplateStrategy, StrategyConfigError, register_strategy_template

GENERIC_FACTOR_TEMPLATE_ID = "__generic_factor_strategy__"

_FACTOR_SCORE_KEYS: Dict[str, List[str]] = {
    "basisspread": ["basis_spread", "spread", "basis"],
    "bollingerbands": ["bollinger_zscore", "bollinger_position", "percent_b"],
    "cci": ["cci"],
    "cointresidual": ["coint_residual", "residual"],
    "dema": ["dema", "dema_diff"],
    "ema": ["ema", "ema_diff"],
    "historicalvol": ["historical_vol", "historical_volatility"],
    "ichimoku": ["tenkan_kijun_diff", "ichimoku_signal"],
    "impliedvolatility": ["implied_volatility", "iv"],
    "inventoryfactor": ["inventory_factor", "inventory_change", "inventory"],
    "macd": ["macd_hist", "macd", "macd_diff"],
    "mfi": ["mfi"],
    "newssentiment": ["news_sentiment", "sentiment"],
    "obv": ["obv_slope", "obv"],
    "openinterestfactor": ["open_interest_factor", "open_interest_change", "open_interest"],
    "parabolicsar": ["parabolic_sar", "sar_gap"],
    "rsi": ["rsi_slope", "rsi"],
    "sentimentfactor": ["sentiment_factor", "sentiment"],
    "sma": ["sma", "sma_diff"],
    "socialsentiment": ["social_sentiment", "sentiment"],
    "spreadcrosscommodity": ["spread_crosscommodity", "spread"],
    "spreadcrossperiod": ["spread_crossperiod", "spread"],
    "spreadratio": ["spread_ratio"],
    "supertrend": ["supertrend", "trend_signal"],
    "volatilityfactor": ["volatility_factor", "volatility"],
    "volumeratio": ["volume_ratio"],
    "vwap": ["vwap", "vwap_gap"],
    "warehousereceiptfactor": ["warehouse_receipt_factor", "warehouse_receipt_change", "warehouse_receipt"],
    "williamsr": ["williams_r"],
    "zscorespread": ["zscore_spread", "zscore"],
}
_NON_DIRECTIONAL_KEYS = {
    "adx",
    "atr",
    "garmanklass",
    "bollinger_lower",
    "bollinger_mid",
    "bollinger_upper",
    "conversion_line",
    "base_line",
    "leading_span_a",
    "leading_span_b",
}


@register_strategy_template
class GenericFactorStrategy(FixedTemplateStrategy):
    template_id = GENERIC_FACTOR_TEMPLATE_ID
    accepts_any_template_id = True

    def run(self):
        self._validate_runtime_inputs()
        self._append_common_notes()

        target_pos_task = self._build_live_target_pos_task()
        if target_pos_task is not None:
            return self._run_live_execution(target_pos_task)
        return self._run_static_snapshot()

    def _validate_runtime_inputs(self) -> None:
        if not self.factor_configs:
            raise StrategyConfigError("通用模板至少需要一个 factors 配置")
        if self.symbols and self.runtime_context.symbol not in self.symbols:
            raise StrategyConfigError(
                f"strategy symbol {self.runtime_context.symbol} is not listed in YAML symbols"
            )

    def _append_common_notes(self) -> None:
        self.append_note("template=generic_factor_fallback")
        self.append_note("generic_template_fallback=true")
        self.append_note(f"requested_template_id={self.strategy_config.template_id}")
        self.append_note(f"factor_count={len(self.factor_configs)}")
        self.append_note(
            "factor_names=" + ",".join(config.factor_name for config in self.factor_configs)
        )
        self.append_note(
            f"market_filter_config_present={str(bool(self.market_filter_config)).lower()}"
        )
        self.append_note(f"signal_config_present={str(bool(self.signal_config)).lower()}")

    def _run_static_snapshot(self):
        bars = self._load_bars()
        merged_rows, factor_snapshots = self._compute_merged_rows(bars)
        latest_row = merged_rows[-1]
        signal_state, market_filter_passed, signal_score = self._resolve_signal_state(
            merged_rows,
            exclude_last_bar=False,
        )

        self.append_note("execution_loop=static_snapshot")
        self.append_note(f"market_filter_passed={str(market_filter_passed).lower()}")
        self.append_note(f"signal_state={signal_state}")
        self.append_note(f"signal_score={signal_score:.6g}")
        self._append_factor_snapshot_notes(factor_snapshots)
        self._append_latest_keys_note(latest_row)

        try:
            self.record_account_snapshot()
        except Exception:
            self.record_equity(equity=self.runtime_context.initial_capital, position=0)
        return self.finish()

    def _run_live_execution(self, target_pos_task: Any):
        raw_bars = self._subscribe_bars()
        quote = self._get_quote()
        seen_trade_ids = self._collect_trade_ids()
        last_observed_position = self._read_current_position()
        last_target_volume = last_observed_position
        last_signal_state: Optional[str] = None
        last_signal_score = 0.0
        last_merged_rows: List[Dict[str, Any]] = []
        last_factor_snapshots: Dict[str, Mapping[str, Any]] = {}
        loop_entered = False
        signal_transitions = 0
        target_updates = 0
        observed_trade_records = 0

        self.append_note("execution_loop=wait_update_target_pos")
        self.append_note(f"position_fraction={self._read_position_fraction():.6g}")

        backtest_finished_exception = _resolve_backtest_finished_exception()
        try:
            while True:
                self.session.api.wait_update()
                loop_entered = True

                latest_row = self._get_latest_kline_row(raw_bars)
                latest_timestamp = _coerce_timestamp(_extract_timestamp(latest_row))
                (
                    last_observed_position,
                    observed_updates,
                ) = self._record_execution_changes(
                    seen_trade_ids=seen_trade_ids,
                    last_observed_position=last_observed_position,
                    timestamp=latest_timestamp,
                )
                observed_trade_records += observed_updates

                if latest_row is None or not self._is_new_kline(latest_row):
                    continue

                bars = normalize_bars(raw_bars)
                if len(bars) < self._estimate_required_bars():
                    continue

                merged_rows, factor_snapshots = self._compute_merged_rows(bars)
                signal_snapshot = self._select_signal_snapshot(merged_rows, exclude_last_bar=True)
                signal_timestamp = _coerce_timestamp(_extract_timestamp(signal_snapshot))
                signal_state, _, signal_score = self._resolve_signal_state(
                    merged_rows,
                    exclude_last_bar=True,
                )

                last_signal_score = signal_score
                last_merged_rows = merged_rows
                last_factor_snapshots = factor_snapshots

                if signal_state != last_signal_state:
                    signal_transitions += 1
                    last_signal_state = signal_state

                target_volume = self._resolve_target_volume(
                    signal_state=signal_state,
                    snapshot=signal_snapshot,
                    quote=quote,
                )
                if target_volume != last_target_volume:
                    target_pos_task.set_target_volume(target_volume)
                    last_target_volume = target_volume
                    target_updates += 1

                try:
                    self.record_account_snapshot(timestamp=signal_timestamp or latest_timestamp)
                except Exception:
                    self.record_equity(
                        equity=self.runtime_context.initial_capital,
                        position=last_observed_position,
                        timestamp=signal_timestamp or latest_timestamp,
                    )
        except backtest_finished_exception:
            pass

        if last_factor_snapshots:
            self._append_factor_snapshot_notes(last_factor_snapshots)
        if last_merged_rows:
            self._append_latest_keys_note(last_merged_rows[-1])

        self.append_note(f"execution_loop_entered={str(loop_entered).lower()}")
        self.append_note(f"signal_transitions={signal_transitions}")
        self.append_note(f"target_updates={target_updates}")
        self.append_note(f"observed_trade_records={observed_trade_records}")
        self.append_note(f"final_signal_state={last_signal_state or 'flat'}")
        self.append_note(f"final_signal_score={last_signal_score:.6g}")

        try:
            self.record_account_snapshot()
        except Exception:
            self.record_equity(
                equity=self.runtime_context.initial_capital,
                position=last_observed_position,
            )
        return self.finish()

    def _supports_live_execution(self) -> bool:
        wait_update = getattr(self.session.api, "wait_update", None)
        is_changing = getattr(self.session.api, "is_changing", None)
        return callable(wait_update) and callable(is_changing)

    def _build_live_target_pos_task(self) -> Optional[Any]:
        if not self._supports_live_execution():
            return None
        try:
            target_pos_task = self.build_target_pos_task()
        except Exception:
            return None
        if not callable(getattr(target_pos_task, "set_target_volume", None)):
            return None
        return target_pos_task

    def _load_bars(self) -> List[Dict[str, Any]]:
        raw_bars = self._subscribe_bars()
        bars = normalize_bars(raw_bars)
        if not bars:
            raise StrategyConfigError("通用模板未获取到 K 线数据")
        return bars

    def _subscribe_bars(self) -> Any:
        get_kline_serial = getattr(self.session.api, "get_kline_serial", None)
        if not callable(get_kline_serial):
            raise StrategyConfigError("通用模板需要 session.api.get_kline_serial")

        timeframe_minutes = self.timeframe_minutes or 5
        if timeframe_minutes <= 0:
            raise StrategyConfigError("timeframe_minutes must be greater than zero")

        return get_kline_serial(
            self.runtime_context.symbol,
            int(timeframe_minutes) * 60,
            data_length=self._estimate_required_bars(),
        )

    def _estimate_required_bars(self) -> int:
        required_bars = 64
        relevant_keys = (
            "period",
            "fast",
            "slow",
            "signal",
            "conversion_period",
            "base_period",
            "span_b_period",
        )
        for factor_config in self.factor_configs:
            for key in relevant_keys:
                raw_value = factor_config.params.get(key)
                if isinstance(raw_value, bool):
                    continue
                if isinstance(raw_value, (int, float)) and raw_value > 0:
                    required_bars = max(required_bars, int(raw_value) * 4)
        return required_bars

    def _compute_merged_rows(
        self,
        bars: List[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], Dict[str, Mapping[str, Any]]]:
        merged_rows = [dict(row) for row in bars]
        factor_snapshots: Dict[str, Mapping[str, Any]] = {}

        for factor_config in self.factor_configs:
            result = factor_registry.calculate(
                factor_config.factor_name,
                bars,
                factor_config.params,
            )
            self._merge_factor_result(merged_rows, result)
            factor_snapshots[factor_config.factor_name] = result.latest()

        return merged_rows, factor_snapshots

    def _merge_factor_result(
        self,
        merged_rows: List[Dict[str, Any]],
        factor_result: FactorResult,
    ) -> None:
        if len(merged_rows) != len(factor_result.rows):
            raise StrategyConfigError(
                f"factor result length mismatch for {factor_result.factor_name}"
            )
        for merged_row, factor_row in zip(merged_rows, factor_result.rows):
            for key, value in factor_row.items():
                if key == "timestamp":
                    continue
                merged_row[key] = value

    def _append_factor_snapshot_notes(
        self,
        factor_snapshots: Mapping[str, Mapping[str, Any]],
    ) -> None:
        for factor_config in self.factor_configs:
            snapshot = factor_snapshots.get(factor_config.factor_name, {})
            self.append_note(
                f"factor_snapshot.{factor_config.factor_name}={self._render_factor_snapshot(snapshot)}"
            )

    def _append_latest_keys_note(self, latest_row: Mapping[str, Any]) -> None:
        latest_keys = sorted(key for key in latest_row if key != "timestamp")
        if latest_keys:
            self.append_note("latest_factor_keys=" + ",".join(latest_keys[:12]))

    def _render_factor_snapshot(self, row: Mapping[str, Any]) -> str:
        parts: List[str] = []
        for key, value in row.items():
            if key == "timestamp" or value is None:
                continue
            if isinstance(value, float):
                parts.append(f"{key}={value:.6g}")
            else:
                parts.append(f"{key}={value}")
            if len(parts) == 3:
                break
        return ";".join(parts) if parts else "empty"

    def _select_signal_snapshot(
        self,
        merged_rows: List[Mapping[str, Any]],
        *,
        exclude_last_bar: bool,
    ) -> Mapping[str, Any]:
        if exclude_last_bar and len(merged_rows) >= 2:
            return merged_rows[-2]
        return merged_rows[-1]

    def _resolve_signal_state(
        self,
        merged_rows: List[Mapping[str, Any]],
        *,
        exclude_last_bar: bool,
    ) -> tuple[str, bool, float]:
        confirm_bars = self._read_confirm_bars()
        snapshots = list(merged_rows)
        if exclude_last_bar and len(snapshots) >= 2:
            snapshots = snapshots[:-1]
        if len(snapshots) < confirm_bars:
            return "flat", False, 0.0

        candidate_snapshots = snapshots[-confirm_bars:]
        states: List[str] = []
        market_filter_passed = False
        signal_score = 0.0

        for snapshot in candidate_snapshots:
            market_filter_passed = self._passes_market_filter(snapshot)
            signal_state, signal_score = self._resolve_raw_signal_state(
                snapshot,
                market_filter_passed=market_filter_passed,
            )
            states.append(signal_state)

        final_state = states[-1]
        if any(state != final_state for state in states):
            final_state = "flat"
        return final_state, market_filter_passed, signal_score

    def _passes_market_filter(self, snapshot: Mapping[str, Any]) -> bool:
        if not self.market_filter_config or not bool(self.market_filter_config.get("enabled")):
            return True

        conditions = self.market_filter_config.get("conditions") or []
        if not conditions:
            return True
        return all(self._evaluate_expression(expression, snapshot) for expression in conditions)

    def _resolve_raw_signal_state(
        self,
        snapshot: Mapping[str, Any],
        *,
        market_filter_passed: bool,
    ) -> tuple[str, float]:
        signal_score = self._resolve_signal_score(snapshot)
        if not market_filter_passed:
            return "blocked", signal_score

        long_condition = self.signal_config.get("long_condition")
        short_condition = self.signal_config.get("short_condition")
        if long_condition or short_condition:
            long_hit = self._evaluate_expression(long_condition, snapshot) if long_condition else False
            short_hit = self._evaluate_expression(short_condition, snapshot) if short_condition else False
            if long_hit and not short_hit:
                return "long", signal_score
            if short_hit and not long_hit:
                return "short", signal_score
            if long_hit and short_hit:
                if signal_score > 0:
                    return "long", signal_score
                if signal_score < 0:
                    return "short", signal_score
            return "flat", signal_score

        long_threshold = self._read_threshold("long_threshold")
        short_threshold = self._read_threshold("short_threshold")
        if signal_score > 0 and signal_score >= long_threshold:
            return "long", signal_score
        if signal_score < 0 and abs(signal_score) >= short_threshold:
            return "short", signal_score
        return "flat", signal_score

    def _resolve_signal_score(self, snapshot: Mapping[str, Any]) -> float:
        total_weight = 0.0
        weighted_score = 0.0

        for factor_config in self.factor_configs:
            try:
                weight = abs(float(factor_config.weight))
            except (TypeError, ValueError):
                continue
            if not math.isfinite(weight) or weight <= 0:
                continue

            contribution = self._resolve_factor_contribution(snapshot, factor_config.factor_name)
            if contribution is None:
                continue

            weighted_score += max(-1.0, min(1.0, contribution)) * weight
            total_weight += weight

        if total_weight == 0.0:
            return 0.0
        return weighted_score / total_weight

    def _resolve_factor_contribution(
        self,
        snapshot: Mapping[str, Any],
        factor_name: str,
    ) -> Optional[float]:
        normalized_name = _normalize_factor_name(factor_name)
        candidate_keys = list(_FACTOR_SCORE_KEYS.get(normalized_name, []))
        if normalized_name not in candidate_keys:
            candidate_keys.append(normalized_name)

        seen = set()
        for key in candidate_keys:
            if key in seen:
                continue
            seen.add(key)
            contribution = self._score_key(snapshot, key)
            if contribution is not None:
                return contribution

        for key in snapshot:
            normalized_key = _normalize_factor_name(str(key))
            if normalized_name and normalized_name in normalized_key:
                contribution = self._score_key(snapshot, str(key))
                if contribution is not None:
                    return contribution
        return None

    def _score_key(
        self,
        snapshot: Mapping[str, Any],
        key: str,
    ) -> Optional[float]:
        value = _optional_float(snapshot.get(key))
        if value is None:
            return None

        normalized_key = _normalize_factor_name(key)
        if normalized_key in _NON_DIRECTIONAL_KEYS:
            return None
        if normalized_key in {"rsi", "mfi"}:
            return _clamp_score((value - 50.0) / 50.0)
        if normalized_key == "williamsr":
            return _clamp_score((value + 50.0) / 50.0)
        if "ratio" in normalized_key or normalized_key.endswith("percentb"):
            return _clamp_score(value - 1.0)
        if normalized_key in {"ema", "sma", "dema", "vwap", "parabolicsar", "supertrend"}:
            close_value = _optional_float(snapshot.get("close"))
            if close_value is None or close_value == 0:
                return None
            return _clamp_score((close_value - value) / abs(close_value))
        if any(
            token in normalized_key
            for token in (
                "hist",
                "slope",
                "spread",
                "residual",
                "zscore",
                "sentiment",
                "signal",
                "factor",
                "diff",
            )
        ):
            return _clamp_score(value)
        if any(token in normalized_key for token in ("inventory", "warehouse")):
            return _clamp_score(-value)
        if any(token in normalized_key for token in ("volatility", "atr", "adx", "band")):
            return None
        return _clamp_score(value)

    def _evaluate_expression(self, expression: str, snapshot: Mapping[str, Any]) -> bool:
        context: Dict[str, Any] = {}
        for key, value in snapshot.items():
            normalized_key = _normalize_factor_name(str(key))
            if not normalized_key:
                continue
            context[normalized_key] = value

        try:
            tree = ast.parse(expression, mode="eval")
            value = _ExpressionEvaluator(context).visit(tree)
        except KeyError:
            return False
        except ZeroDivisionError:
            return False
        except SyntaxError as exc:
            raise StrategyConfigError(f"Unsupported expression syntax: {expression}") from exc
        except ValueError as exc:
            raise StrategyConfigError(f"Unsupported expression: {expression}") from exc
        return bool(value)

    def _read_confirm_bars(self) -> int:
        raw_value = self.signal_config.get("confirm_bars", 1)
        try:
            confirm_bars = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise StrategyConfigError("signal.confirm_bars must be an integer") from exc
        return max(1, confirm_bars)

    def _read_threshold(self, key: str) -> float:
        raw_value = self.signal_config.get(key)
        if raw_value is None:
            return 0.0
        if isinstance(raw_value, bool):
            raise StrategyConfigError(f"signal.{key} must be numeric")
        try:
            threshold = abs(float(raw_value))
        except (TypeError, ValueError) as exc:
            raise StrategyConfigError(f"signal.{key} must be numeric") from exc
        if not math.isfinite(threshold):
            raise StrategyConfigError(f"signal.{key} must be finite")
        return threshold

    def _resolve_target_volume(
        self,
        *,
        signal_state: str,
        snapshot: Mapping[str, Any],
        quote: Any,
    ) -> int:
        if signal_state not in {"long", "short"}:
            return 0

        reference_price = self._resolve_reference_price(snapshot, quote)
        if reference_price is None or reference_price <= 0:
            return 0

        volume_multiple = self._resolve_volume_multiple(quote)
        position_fraction = self._read_position_fraction()
        raw_volume = (
            self.runtime_context.initial_capital * position_fraction
        ) / max(reference_price * volume_multiple, 1.0)
        target_volume = max(1, int(round(raw_volume)))
        return target_volume if signal_state == "long" else -target_volume

    def _read_position_fraction(self) -> float:
        raw_value = self.params.get("position_fraction", 0.1)
        if isinstance(raw_value, bool):
            raise StrategyConfigError("position_fraction must be numeric")
        try:
            position_fraction = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise StrategyConfigError("position_fraction must be numeric") from exc
        if not math.isfinite(position_fraction) or position_fraction <= 0:
            raise StrategyConfigError("position_fraction must be greater than zero")
        return min(position_fraction, 1.0)

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

    def _resolve_volume_multiple(self, quote: Any) -> float:
        if quote is None:
            return 1.0
        volume_multiple = _optional_float(getattr(quote, "volume_multiple", None))
        if volume_multiple is None or volume_multiple <= 0:
            return 1.0
        return volume_multiple

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

    def _is_new_kline(self, latest_row: Any) -> bool:
        return bool(self.session.api.is_changing(latest_row, "datetime"))

    def _record_execution_changes(
        self,
        *,
        seen_trade_ids: set[str],
        last_observed_position: int,
        timestamp: Optional[datetime],
    ) -> tuple[int, int]:
        trade_events = len(self._consume_new_trade_ids(seen_trade_ids))
        current_position = self._read_current_position()
        if trade_events == 0 and current_position != last_observed_position:
            trade_events = max(1, abs(current_position - last_observed_position))

        for _ in range(trade_events):
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
            position_snapshot = get_position(
                self.runtime_context.symbol,
                account=self.session.account,
            )
        except Exception:
            return 0
        return self._extract_position(position_snapshot)


class _ExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, variables: Mapping[str, Any]) -> None:
        self._variables = dict(variables)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Name(self, node: ast.Name) -> Any:
        key = _normalize_factor_name(node.id)
        if key not in self._variables:
            raise KeyError(key)
        return self._variables[key]

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        values = [self.visit(value) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(bool(value) for value in values)
        if isinstance(node.op, ast.Or):
            return any(bool(value) for value in values)
        raise ValueError("Unsupported boolean operator")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not bool(operand)
        if isinstance(node.op, ast.USub):
            return -float(operand)
        if isinstance(node.op, ast.UAdd):
            return float(operand)
        raise ValueError("Unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return float(left) + float(right)
        if isinstance(node.op, ast.Sub):
            return float(left) - float(right)
        if isinstance(node.op, ast.Mult):
            return float(left) * float(right)
        if isinstance(node.op, ast.Div):
            return float(left) / float(right)
        if isinstance(node.op, ast.Mod):
            return float(left) % float(right)
        raise ValueError("Unsupported arithmetic operator")

    def visit_Compare(self, node: ast.Compare) -> Any:
        left = self.visit(node.left)
        for operator, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(operator, ast.Gt):
                matched = left > right
            elif isinstance(operator, ast.GtE):
                matched = left >= right
            elif isinstance(operator, ast.Lt):
                matched = left < right
            elif isinstance(operator, ast.LtE):
                matched = left <= right
            elif isinstance(operator, ast.Eq):
                matched = left == right
            elif isinstance(operator, ast.NotEq):
                matched = left != right
            else:
                raise ValueError("Unsupported comparison operator")
            if not matched:
                return False
            left = right
        return True

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def _normalize_factor_name(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(value.lower().split())


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


def _clamp_score(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return max(-1.0, min(1.0, float(value)))


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


def _resolve_backtest_finished_exception() -> type[BaseException]:
    try:
        from tqsdk import BacktestFinished
    except ImportError:
        return RuntimeError
    return BacktestFinished