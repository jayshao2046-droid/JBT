# HANDOFF-U0-20260419-012 — backtest TqSdk 连续合约下单修复

【类型】U0 事后交接  
【日期】2026-04-19  
【执行人】Atlas  
【关联任务】TASK-U0-20260419-012

## 修复摘要

**根因**：TqSdk 连续主力合约（`KQ.m@CZCE.CF`）只能用于数据查询，不能用于 TqSim 下单。
`_ManualTargetPos` 直接用此符号调 `insert_order` 导致所有订单被拒绝（0 成交）。

**修复**：`_ManualTargetPos` 新增 `_resolve_trading_symbol()` 通过 `quote.underlying_symbol` 
解析真实可交易合约（如 `CZCE.CF405`），所有下单和查仓改用底层合约。

## 影响文件

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/generic_strategy.py`

## 验证记录

- 单元测试：3/3 trades（买入/平仓/做空）
- API 回测 task `4d0eea9a`：`observed_trade_records=8`，风控正常
- note: `target_pos=manual_order(KQ.m@CZCE.CF)->trading=CZCE.CF405`

## 部署状态

- ✅ 本地源码已更新
- ✅ Studio 容器 JBT-BACKTEST-8103 已部署并重启
- ✅ 用户确认修复通过
