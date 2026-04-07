# Shared Contracts

本目录用于存放跨服务共享的 API 契约、请求响应模型、字段定义和版本说明。

## 当前正式目录

| 目录 | 用途 | 当前文件 |
|---|---|---|
| `backtest/` | 回测任务、结果、指标与 API 边界 | `backtest_job.md`、`backtest_result.md`、`performance_metrics.md`、`api.md` |
| `sim-trading/` | 模拟交易订单、持仓、账户、桥接信号与 API 边界 | `order.md`、`position.md`、`account.md`、`api.md`、`bridge_signal.md` |
| `decision/` | 因子、信号、审批、策略编排、通知与只读看板投影 | `api.md`、`strategy_package.md`、`research_snapshot.md`、`backtest_certificate.md`、`decision_request.md`、`decision_result.md`、`model_boundary.md`、`notification_event.md`、`dashboard_projection.md` |

允许放入：

- 请求模型
- 响应模型
- OpenAPI 片段
- JSON Schema
- 跨服务字段映射说明

禁止放入：

- 任一服务的内部业务逻辑
- 交易账本实现
- 数据采集实现
