# sim-trading

## 角色

JBT 模拟交易服务，唯一目标是对接 SimNow 并完成模拟交易执行。

## 固定边界

1. 只负责 SimNow 模拟交易。
2. 不使用内存模拟交易。
3. 不使用 TqSim 作为模拟盘。
4. 自己维护订单、成交、持仓、资金和风控执行链。
5. 只通过 API 接收决策端或人工操作指令。

## 端口

- 8101

## 未来目录职责

- `src/`: API、交易执行、账本、风控
- `tests/`: 模拟交易服务测试
- `configs/`: SimNow、风控、通知配置

## 外部依赖

- 上游：decision
- 下游：dashboard
- 兼容层：legacy-botquant
