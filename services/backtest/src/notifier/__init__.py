"""回测服务通知模块 — 回测完成/失败通知，路由到 INFO/ALERT 群。"""
from .dispatcher import notify_backtest_done, notify_backtest_failed

__all__ = ["notify_backtest_done", "notify_backtest_failed"]
