# backtest_job 契约

状态: ACTIVE
作者: 项目架构师
登记时间: 2026-04-03
来源草稿: `shared/contracts/drafts/backtest/backtest_job.md`

## 1. 用途

本契约定义 backtest 服务对外暴露的回测任务模型最小必要字段，用于：

1. 发起与查询单次回测任务。
2. 固化回测时间窗口、标的与生效配置快照。
3. 为结果查询与指标查询提供稳定关联键。

## 2. 当前执行口径

1. `strategy_id` 表示固定策略模板标识，不表示用户自定义 Python 策略代码上传。
2. 用户上传参数与风控参数统一放入同一个 YAML 文件；服务在执行前解析并校验该文件，再将生效值写回本契约中的公共字段快照。
3. 所有风控参数必须从该一体化 YAML 文件读取，禁止硬编码任何风控指标。
4. YAML 上传、挂载与存储属于 backtest 服务自身运行约束，本契约不单独展开上传接口实现。

## 3. 字段定义

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

## 4. 状态机

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

## 5. 明确排除字段

以下字段来自 legacy J_BotQuant `BacktestConfig`，明确不纳入本契约：

| 排除字段 | 排除原因 |
|---|---|
| `per_trade_risk_yuan` | 属于策略内部风控，由策略层持有，不作为回测任务公共字段 |
| `use_atr_trailing_stop`、`atr_trailing_stop_multiplier`、`atr_trailing_stop_period` | 属于策略参数，由策略层持有 |
| `take_profit_multiplier`、`min_profit_to_loss_ratio` | 同上 |
| `broker_id`、`investor_id` | 回测不涉及真实账户 |
| `tqsdk_session_id`、`auth_token` | TqSdk 内部凭证，不暴露于外部契约 |

## 6. 创建请求示例（POST /api/v1/jobs）

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

## 7. 响应示例

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