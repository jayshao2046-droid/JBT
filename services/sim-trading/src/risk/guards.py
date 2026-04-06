# Unified risk guard skeleton — TASK-0013 compliant
# Implements: reduce_only / disaster_stop / alert stubs
# Stage preset support: sim / live adapter injection pending


class RiskGuards:
    """风控守卫骨架。三类核心钩子占位，真实逻辑待 TASK-0013 统一补充。"""

    def check_reduce_only(self, order: dict, current_positions: list) -> bool:
        """
        只减仓模式检查。
        当账户处于 reduce_only 状态时，禁止新开仓。
        返回 True 表示该订单允许通过（减仓方向），False 表示拒绝（开仓方向）。
        # TODO: 实现 reduce_only 状态检测与方向判断
        """
        raise NotImplementedError("reduce_only hook not yet implemented")

    def check_disaster_stop(self, account_summary: dict) -> bool:
        """
        灾难止损检查。
        当净值回撤超过 RISK_NAV_DRAWDOWN_HALT 阈值时，触发全停。
        返回 True 表示系统可继续运行，False 表示触发熔断全停。
        # TODO: 实现净值回撤计算与熔断判定
        """
        raise NotImplementedError("disaster_stop hook not yet implemented")

    def emit_alert(self, level: str, message: str, context: dict = None) -> None:
        """
        风控告警通道。
        level: 'P0' | 'P1' | 'P2'
        # TODO: 接入 TASK-0014 风控通知链路
        """
        raise NotImplementedError("alert hook not yet implemented")
