# backtest API 契约

状态: ACTIVE
作者: 项目架构师
登记时间: 2026-04-03
来源草稿: `shared/contracts/drafts/backtest/api.md`

## 1. 用途

本契约定义 backtest 服务 MVP 阶段对外公开的 API 边界，用于：

1. 发起与查询回测任务。
2. 查询回测结果、绩效指标与精简版权益曲线。
3. 登记回测通过后策略推送的接口需求说明。

## 2. API 端点总览

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | /api/v1/health | 健康检查 | 否 |
| POST | /api/v1/jobs | 发起回测任务 | Bearer Token |
| GET | /api/v1/jobs/{job_id} | 查询任务状态 | Bearer Token |
| GET | /api/v1/jobs | 查询任务列表（分页） | Bearer Token |
| GET | /api/v1/results/{job_id} | 查询回测结果 | Bearer Token |
| GET | /api/v1/metrics/{job_id} | 查询绩效指标 | Bearer Token |
| GET | /api/v1/equity_curve/{job_id} | 查询权益曲线（精简版，前端用） | Bearer Token |

## 3. 当前任务输入口径

1. `POST /api/v1/jobs` 当前执行路径采用“固定模板 + 用户上传参数 + 一体化 YAML 风控文件”。
2. `strategy_id` 指向固定策略模板；用户上传的一体化 YAML 文件负责提供策略参数与风控参数。
3. YAML 上传、挂载与解析属于 backtest 服务自身运行约束，不在本契约中展开跨服务实现。

## 4. 端点详情

### GET /api/v1/health

响应 200：

```json
{
  "status": "ok",
  "service": "backtest",
  "version": "0.1.0"
}
```

### POST /api/v1/jobs

请求体：BacktestJob 创建字段（见 `backtest_job.md`）。当前执行口径下，`strategy_id` 指向固定策略模板；任务创建前应已有用户上传的一体化 YAML 文件，由 backtest 服务在运行目录中解析策略参数与风控参数。

响应 201：BacktestJob 对象（status = pending）

响应 422：字段校验错误

### GET /api/v1/jobs/{job_id}

路径参数：`job_id`（UUID）

响应 200：BacktestJob 对象（含最新 status 与 updated_at）

响应 404：任务不存在

### GET /api/v1/jobs

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| strategy_id | string | 否 | 按策略过滤 |
| symbol | string | 否 | 按合约过滤 |
| status | string | 否 | 按状态过滤（pending/running/completed/failed） |
| page | integer | 否 | 页码（默认 1） |
| limit | integer | 否 | 每页数量（默认 20，最大 100） |

响应 200：

```json
{
  "total": 87,
  "page": 1,
  "limit": 20,
  "items": [ /* BacktestJob[] */ ]
}
```

### GET /api/v1/results/{job_id}

路径参数：`job_id`（UUID）

响应 200：BacktestResult 对象（见 `backtest_result.md`）

响应 404：任务不存在或结果尚未生成（status 未达到 completed）

### GET /api/v1/metrics/{job_id}

路径参数：`job_id`（UUID）

响应 200：PerformanceMetrics 对象（见 `performance_metrics.md`）

响应 404：结果不存在或指标尚未计算完毕

### GET /api/v1/equity_curve/{job_id}

路径参数：`job_id`（UUID）

说明：返回精简版权益曲线 JSON，供前端看板绘图；完整数据通过 `BacktestResult.equity_curve_path` 指向的 Parquet 文件获取。

响应 200：

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "symbol": "SHFE.rb2405",
  "data": [
    {"timestamp": "2024-01-02T15:00:00", "equity": 1000000.0, "drawdown": 0.0},
    {"timestamp": "2024-01-03T15:00:00", "equity": 1012300.0, "drawdown": 0.0}
  ]
}
```

响应 404：结果不存在

## 5. 策略推送接口需求说明（需求登记，非本轮实现）

- 需求路径：`POST /api/v1/strategies/{strategy_id}/push`
- 需求用途：仅允许把已完成回测且通过审阅的策略推送给 decision 服务使用。
- 前置条件：对应回测任务已 `completed`，结果与绩效指标可查询，且已通过人工或治理审核。
- 最小载荷：`strategy_id`、`result_id`、策略配置快照引用、最新绩效摘要。
- 说明：该接口当前只登记 backtest 服务侧需求；decision 侧接收契约与跨服务实现细节后续单独建档，不在本契约展开。

## 6. 公共错误结构

```json
{
  "detail": "Job not found",
  "code": "NOT_FOUND"
}
```

## 7. 明确排除接口（MVP 阶段不纳入）

| 排除接口 | 排除原因 |
|---|---|
| POST /api/v1/jobs/batch / DELETE /api/v1/jobs | 批量操作，MVP 不需要 |
| POST /api/v1/param_scan | 参数网格扫描，属于进阶功能，后续单独任务 |
| GET /api/v1/walk_forward/{job_id} | Walk-forward 分析，进阶功能 |
| GET /api/v1/optimize | 超参数优化，进阶功能 |
| WebSocket /ws/jobs/{job_id} | 实时状态推送，MVP 用轮询替代 |
| POST /api/v1/strategies/upload | 策略代码上传，由 decision 服务管理 |
| GET /api/v1/admin/** | 运维管理接口，不属于跨服务公共契约 |