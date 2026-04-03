# 回测任务模型草稿（BacktestJob）

【归属服务】services/backtest
【目标正式路径】shared/contracts/backtest/backtest_job.md
【草稿状态】已完成；等待 P0 Token 后迁入正式目录
【审核人】项目架构师
【最后更新】2026-04-03

---

## 字段定义

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| job_id | string (UUID) | 是 | 服务生成 | 回测任务唯一 ID |
| strategy_id | string | 是 | — | 策略标识，由 decision 服务管理 |
| symbol | string | 是 | — | 期货合约代码（如 `SHFE.rb2405`） |
| start_date | string (ISO8601 date) | 是 | — | 回测开始日期（如 `2024-01-01`） |
| end_date | string (ISO8601 date) | 是 | — | 回测结束日期（含当天） |
| initial_capital | float | 否 | 1000000.0 | 初始资金（CNY） |
| commission_rate | float | 否 | 0.0003 | 手续费率（双边） |
| slippage_rate | float | 否 | 0.0001 | 滑点率 |
| position_fraction | float | 否 | 0.1 | 单次建仓仓位比例（[0,1]） |
| daily_fuse_threshold | float | 否 | 0.05 | 日内熔断阈值；当日亏损超过此比例则停止开仓 |
| no_overnight | boolean | 否 | false | 是否强制收盘前平仓 |
| status | enum | 是 | pending | 任务状态（见状态机） |
| created_at | string (ISO8601 datetime) | 是 | 服务生成 | 创建时间 |
| updated_at | string (ISO8601 datetime) | 是 | 服务维护 | 最后更新时间 |

## 状态机

```
pending → running → completed
                 ↘ failed
```

| 状态 | 说明 |
|---|---|
| pending | 任务已创建，等待 TqSdk 会话启动 |
| running | TqSdk 在线回测会话已建立，回测正在执行 |
| completed | 回测完毕，结果已写入，可查询 BacktestResult |
| failed | TqSdk 异常、超时或参数错误，未产生有效结果 |

## 明确排除字段

以下字段来自 legacy J_BotQuant `BacktestConfig`，明确不纳入本契约：

| 排除字段 | 排除原因 |
|---|---|
| `per_trade_risk_yuan` | 属于策略内部风控，由策略层持有，不作为回测任务公共字段 |
| `use_atr_trailing_stop`、`atr_trailing_stop_multiplier`、`atr_trailing_stop_period` | 属于策略参数，由策略层持有 |
| `take_profit_multiplier`、`min_profit_to_loss_ratio` | 同上 |
| `broker_id`、`investor_id` | 回测不涉及真实账户 |
| `tqsdk_session_id`、`auth_token` | TqSdk 内部凭证，不暴露于外部契约 |

## 创建请求示例（POST /api/v1/jobs）

```json
{
  "strategy_id": "sma_cross_v1",
  "symbol": "SHFE.rb2405",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000.0,
  "commission_rate": 0.0003,
  "position_fraction": 0.1
}
```

## 响应示例

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "strategy_id": "sma_cross_v1",
  "symbol": "SHFE.rb2405",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000.0,
  "commission_rate": 0.0003,
  "slippage_rate": 0.0001,
  "position_fraction": 0.1,
  "daily_fuse_threshold": 0.05,
  "no_overnight": false,
  "status": "pending",
  "created_at": "2026-04-03T10:00:00+08:00",
  "updated_at": "2026-04-03T10:00:00+08:00"
}
```
