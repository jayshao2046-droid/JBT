"""
Legacy BotQuant 决策域只读适配器。

职责：读取 legacy BotQuant 以 dict/JSON 形式输出的策略/信号数据，
      将其转换为 JBT decision_request 契约结构。

禁止：
  - 引入 legacy 的交易/回测/订单逻辑
  - 直接 import 任何 J_BotQuant/** 或 services/** 代码
  - 调用任何交易 API
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .input_mapper import LegacyInputMapper
from .signal_compat import LegacySignalCompat


class LegacyDecisionAdapter:
    """Legacy BotQuant → JBT DecisionRequest 转换适配器（只读）。"""

    def __init__(
        self,
        default_target: str = "sim-trading",
        default_trace_prefix: str = "legacy",
    ) -> None:
        """初始化适配器。

        Args:
            default_target: 默认发布目标，遵循契约约束（sim-trading / live-trading）。
            default_trace_prefix: trace_id 前缀，用于区分 legacy 来源链路。
        """
        self._default_target = default_target
        self._default_trace_prefix = default_trace_prefix
        self._mapper = LegacyInputMapper()
        self._signal_compat = LegacySignalCompat()

    def from_legacy_dict(self, raw: dict[str, Any]) -> dict[str, Any]:
        """将 legacy BotQuant 原始数据 dict 转换为 JBT DecisionRequest 标准字典。

        适配逻辑（纯转换，不调用任何外部 API）：
        1. 通过 LegacyInputMapper 进行字段名重映射。
        2. 通过 LegacySignalCompat 规范化信号类型，取得标准方向整数。
        3. 填充 request_id / trace_id / submitted_at 等元字段。
        4. 对缺失的门禁字段（factor_version_hash 等）填入占位值，
           由下游 decision 服务自行决定是否通过门禁校验。

        Args:
            raw: 来自 legacy BotQuant 的原始策略+信号字典。

        Returns:
            符合 JBT decision_request 契约的请求 dict。
        """
        # 1. 字段名重映射
        strategy_fields = self._mapper.map_strategy_fields(raw)
        signal_fields = self._mapper.map_signal_fields(raw)

        # 2. 信号规范化
        raw_signal_type: str = str(signal_fields.get("signal_type", "HOLD"))
        jbt_signal_type: str = self._signal_compat.normalize_signal_type(raw_signal_type)
        signal_direction: int = self._signal_compat.normalize_signal_direction(jbt_signal_type)

        # 3. 因子快照：优先取 signal_fields 的 factors，其次策略层
        raw_factors: Any = signal_fields.get("factors") or strategy_fields.get("factors")
        factors = self._normalize_factors(raw_factors)

        # 4. 构造标准请求字典
        now_iso = datetime.now(tz=timezone.utc).isoformat()
        request_id = f"legacy-{uuid.uuid4().hex[:12]}"
        trace_id = f"{self._default_trace_prefix}-{uuid.uuid4().hex[:8]}"

        decision_request: dict[str, Any] = {
            "request_id": request_id,
            "trace_id": trace_id,
            "strategy_id": strategy_fields.get("strategy_id") or raw.get("strategy_id", "unknown"),
            "strategy_version": strategy_fields.get("strategy_version") or raw.get("version", "legacy"),
            "symbol": strategy_fields.get("symbol") or raw.get("symbol", ""),
            "requested_target": raw.get("requested_target", self._default_target),
            "signal": signal_direction,
            "signal_strength": float(signal_fields.get("signal_strength") or raw.get("strength", 0.0)),
            "factors": factors,
            "factor_version_hash": raw.get("factor_version_hash", "legacy-unknown"),
            "market_context": self._normalize_market_context(raw.get("market_context")),
            "research_snapshot_id": raw.get("research_snapshot_id", "legacy-placeholder"),
            "backtest_certificate_id": raw.get("backtest_certificate_id", "legacy-placeholder"),
            "submitted_at": raw.get("submitted_at", now_iso),
            # 扩展元字段：标记本请求来源为 legacy 适配层
            "_legacy_source": True,
            "_legacy_signal_type": raw_signal_type,
        }

        return decision_request

    @staticmethod
    def _normalize_factors(raw_factors: Any) -> list[dict[str, Any]]:
        """将 legacy 因子数据规范化为 JBT factors 数组格式。

        支持三种 legacy 形式：
          - list[dict]: 已是数组，按字段补全
          - dict: 旧 {factor_name: value} 平铺格式，展开为数组
          - None / 其他: 返回空数组
        """
        if raw_factors is None:
            return []
        if isinstance(raw_factors, list):
            result: list[dict[str, Any]] = []
            for item in raw_factors:
                if isinstance(item, dict):
                    result.append({
                        "name": str(item.get("name", "unknown")),
                        "value": float(item.get("value", 0.0)),
                        "version": str(item.get("version", "legacy")),
                        "updated_at": str(item.get("updated_at", "")),
                    })
            return result
        if isinstance(raw_factors, dict):
            return [
                {
                    "name": str(k),
                    "value": float(v) if isinstance(v, (int, float)) else 0.0,
                    "version": "legacy",
                    "updated_at": "",
                }
                for k, v in raw_factors.items()
            ]
        return []

    @staticmethod
    def _normalize_market_context(raw_ctx: Optional[dict]) -> dict[str, str]:
        """将 legacy market_context 规范化为 JBT 市场上下文结构。

        若 raw_ctx 为 None 或类型不符，所有字段填入 "unknown"。
        """
        if not isinstance(raw_ctx, dict):
            return {
                "market_session": "unknown",
                "volatility_regime": "unknown",
                "liquidity_regime": "unknown",
                "headline_risk_level": "unknown",
            }
        return {
            "market_session": str(raw_ctx.get("market_session", "unknown")),
            "volatility_regime": str(raw_ctx.get("volatility_regime", "unknown")),
            "liquidity_regime": str(raw_ctx.get("liquidity_regime", "unknown")),
            "headline_risk_level": str(raw_ctx.get("headline_risk_level", "unknown")),
        }
