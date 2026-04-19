# TASK-U0-20260419-012 — backtest TqSdk 连续合约下单修复

【类型】U0 直修  
【服务】backtest（单服务）  
【执行人】Atlas  
【日期】2026-04-19  
【状态】✅ 用户确认通过

## 问题描述

TqSdk 回测中 `_ManualTargetPos` 使用 `KQ.m@CZCE.CF` 等连续主力合约符号调用 `api.insert_order()`，
TqSim 不支持此类合约下单（`exchange_id=KQ` 不是真实交易所），所有订单被静默拒绝：

```
order.last_msg = "不支持的合约类型，TqSim 目前不支持组合，股票，etf期权模拟交易"
```

结果：信号正常（237次切换）、`set_target_volume` 被调用 238 次，但 `observed_trade_records=0`。

## 根因

`KQ.m@CZCE.CF` 只能用于数据查询（行情、K线），不能用于下单。
真实可交易合约通过 `quote.underlying_symbol`（如 `CZCE.CF505`）获取。

## 修复文件

| 文件 | 修改内容 |
|------|---------|
| `services/backtest/src/backtest/strategy_base.py` | `_ManualTargetPos` 新增 `_resolve_trading_symbol()` 解析底层合约；`_sync_position()` 改用底层合约下单和查仓；`build_target_pos_task()` 暴露 `_position_symbol` |
| `services/backtest/src/backtest/generic_strategy.py` | `_read_current_position()` 优先使用 `_position_symbol` 查仓位 |

## 验证结果

1. **单元测试**：`_ManualTargetPos` 买入/平仓/做空 3/3 成交 ✅
2. **API 端到端回测** task `4d0eea9a`：
   - `status=completed`
   - `observed_trade_records=8`（修复前=0）
   - `signal_transitions=10, target_updates=10`
   - `target_pos=manual_order(KQ.m@CZCE.CF)->trading=CZCE.CF405`
   - 风控正常触发（`risk_reason=max_drawdown_triggered`）
3. 已部署到 Studio 容器 JBT-BACKTEST-8103
