"""
integrations.legacy_botquant.decision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Legacy BotQuant 决策域只读适配层。

对外公开接口：
  - LegacyDecisionAdapter: legacy dict → JBT DecisionRequest 转换
  - LegacyInputMapper:     字段名映射（strategy_fields / signal_fields）
  - LegacySignalCompat:    信号类型标准化与合法性验证

约束：
  - 只读：只负责字段转换，不调用任何交易 API
  - 隔离：不 import services/** 或 J_BotQuant/** 代码
"""

from .adapter import LegacyDecisionAdapter
from .input_mapper import LegacyInputMapper
from .signal_compat import LegacySignalCompat

__all__ = [
    "LegacyDecisionAdapter",
    "LegacyInputMapper",
    "LegacySignalCompat",
]
