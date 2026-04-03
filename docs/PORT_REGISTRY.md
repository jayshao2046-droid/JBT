# Port Registry

## 1. 服务端口分配

| 服务 | 端口 | 协议 | 说明 |
|---|---:|---|---|
| sim-trading | 8101 | HTTP API | SimNow 模拟交易 API |
| live-trading | 8102 | HTTP API | 实盘交易 API |
| backtest | 8103 | HTTP API | 回测任务与结果 API |
| decision | 8104 | HTTP API | 信号、审批、编排 API |
| data | 8105 | HTTP API | 数据供给 API |
| dashboard | 8106 | HTTP / Web | 看板与只读聚合 API |

## 2. 预留端口

| 用途 | 端口 |
|---|---:|
| metrics / observability gateway | 8190 |
| internal admin / health aggregate | 8191 |

## 3. 环境变量命名规范

| 服务 | URL 环境变量 |
|---|---|
| sim-trading | `JBT_SIM_TRADING_API_URL` |
| live-trading | `JBT_LIVE_TRADING_API_URL` |
| backtest | `JBT_BACKTEST_API_URL` |
| decision | `JBT_DECISION_API_URL` |
| data | `JBT_DATA_API_URL` |
| dashboard | `JBT_DASHBOARD_API_URL` |

## 4. 使用原则

1. 一个服务只拥有自己的监听端口。
2. 不允许两个服务共享同一个 API 端口。
3. 本地开发、Studio、Mini 都沿用同一端口语义，只变主机名。
4. 老系统对接由 `integrations/legacy-botquant` 做地址映射，不污染新服务目录。
