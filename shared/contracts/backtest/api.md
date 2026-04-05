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
| GET | /api/v1/results/{job_id}/report | 下载正式回测报告 | Bearer Token |
| GET | /api/v1/metrics/{job_id} | 查询绩效指标 | Bearer Token |
| GET | /api/v1/equity_curve/{job_id} | 查询权益曲线（精简版，前端用） | Bearer Token |

## 3. 当前双层路由口径

1. 正式/规范层：`/api/v1/*` 是当前正式契约的标准命名空间，用于稳定 API 边界、后续实现并回与跨协作登记。
2. backtest_web 兼容层：当前仓内前端仍实际调用 `/api/backtest/*`、`/api/strategy/*`、`/api/strategies`、`/api/system/*`、`/api/market/*`。
3. 兼容层只表示 backtest 单服务内的兼容投影或包装，不新增跨服务边界，不暴露内部实现、legacy 路径或运行态部署路径。

## 4. 当前任务输入口径

1. `POST /api/v1/jobs` 当前执行路径采用“通用正式模板 + 用户上传一体化 YAML 严格填充”。
2. `strategy_id` / `strategy_template_id` 指向正式模板入口；默认以通用模板承接多策略 YAML，只有在出现全新因子类型、全新信号语义或全新执行语义时，才允许新增代码模板。
3. 用户上传的一体化 YAML 文件负责提供资金参数、策略参数、因子参数、信号参数与风控参数；服务端必须按 YAML 原值严格执行，不得静默改写任何数字或符号。
4. YAML 上传、挂载与解析属于 backtest 服务自身运行约束，不在本契约中展开跨服务实现。

## 5. backtest_web 兼容端点冻结与对齐关系

以下兼容端点按当前 backtest_web 实际调用面冻结，用于批次 B 正式并回时保持接口语义稳定。

### 5.1 回测任务与结果

| 兼容端点 | 与正式层的关系 | 当前归类 | 说明 |
|---|---|---|---|
| GET /api/backtest/summary | 无单一对等端点；语义上由 `/api/v1/jobs`、`/api/v1/results/{job_id}`、`/api/v1/metrics/{job_id}` 聚合形成 | 当前 backtest_web 兼容端点 | 面向看板摘要视图的聚合读取，限定在 backtest 单服务边界内 |
| GET /api/backtest/results | 无单一对等端点；语义上由 `/api/v1/jobs` 列表与 `/api/v1/results/{job_id}` 结果查询组合形成 | 当前 backtest_web 兼容端点 | 返回前端结果列表；正式层当前未单列“结果列表”端点 |
| POST /api/backtest/run | 对齐 `POST /api/v1/jobs` | 兼容投影或包装 | 发起回测任务；兼容层中的 `task_id` 命名与正式层 `job_id` 语义对齐 |
| GET /api/backtest/results/{task_id} | 对齐 `GET /api/v1/results/{job_id}` | 兼容投影或包装 | 查询单次回测结果；兼容层沿用前端当前的 `task_id` 路径命名 |
| GET /api/backtest/results/{task_id}/report | 对齐 `GET /api/v1/results/{job_id}/report` | 兼容投影或包装 | 下载单次回测的正式报告文件；兼容层沿用前端当前的 `task_id` 路径命名 |
| POST /api/backtest/adjust | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 表示基于既有任务参数重新调整并发起执行，限定在 backtest 单服务内 |
| GET /api/backtest/history/{strategy_id} | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 按策略查看历史回测记录，限定在 backtest 单服务内 |
| GET /api/backtest/results/{task_id}/equity | 对齐 `GET /api/v1/equity_curve/{job_id}` | 兼容投影或包装 | 查询单次结果的权益曲线 |
| GET /api/backtest/results/{task_id}/trades | 无单一对等端点；语义上属于 `GET /api/v1/results/{job_id}` 的结果明细切片 | 当前 backtest_web 兼容端点 | 查询交易明细，限定在 backtest 单服务内 |
| GET /api/backtest/progress/{task_id} | 对齐 `GET /api/v1/jobs/{job_id}` | 兼容投影或包装 | 供前端轮询任务进度与状态 |
| POST /api/backtest/cancel/{task_id} | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 取消任务，限定在 backtest 单服务内 |
| GET /api/backtest/equity-curve | 无单一对等端点；与 `GET /api/v1/equity_curve/{job_id}` 语义相近，但当前省略 `job_id` 选择 | 当前 backtest_web 兼容端点 | 当前看板使用的兼容查询，不替代正式层带 `job_id` 的标准查询路径 |
| DELETE /api/backtest/results/batch | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 批量删除回测结果；当前前端已实际使用，限定在 backtest 单服务内 |

### 5.2 策略管理

| 兼容端点 | 与正式层的关系 | 当前归类 | 说明 |
|---|---|---|---|
| GET /api/strategies | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 查询策略列表，限定在 backtest 单服务内 |
| POST /api/strategy/import | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 导入或覆盖策略内容，限定在 backtest 单服务内 |
| DELETE /api/strategy/{name} | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 删除策略，限定在 backtest 单服务内 |
| GET /api/strategy/export/{name} | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 导出策略文本内容，限定在 backtest 单服务内 |

### 5.3 系统与市场

| 兼容端点 | 与正式层的关系 | 当前归类 | 说明 |
|---|---|---|---|
| GET /api/system/status | 以 `GET /api/v1/health` 为底座的兼容投影 | 兼容投影或包装 | 在健康检查之上补充当前前端所需的 backtest 本地状态摘要 |
| GET /api/system/logs | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 读取系统日志摘要，限定在 backtest 单服务内 |
| GET /api/market/quotes | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 查询行情快照，限定在 backtest 单服务内 |
| GET /api/market/main-contracts | 当前无 `/api/v1` 对等端点 | 当前 backtest_web 兼容端点 | 查询主力合约列表，限定在 backtest 单服务内 |

### 5.4 当前延期接口

| 兼容端点 | 状态说明 |
|---|---|
| POST /api/strategy/approve | 当前不属于本批次活跃接口，继续延期；不得按当前已启用接口登记，也不纳入本批正式对齐范围 |

## 6. 对齐原则

1. 若已存在 `/api/v1` 对齐语义，则 `/api/*` 兼容路由视为同一 backtest 服务语义的兼容投影或包装，不单独扩张契约边界。
2. 若当前不存在 `/api/v1` 对等端点，则在本契约中明确标记为“当前 backtest_web 兼容端点”，并限定在 backtest 单服务边界内，由批次 B 正式并回实现。
3. 兼容层中的 `task_id` 仅表示前端当前兼容命名；正式契约继续保持 `job_id`、`result_id`、`strategy_id` 等稳定命名，不绑定内部实现。
4. 本契约只登记对外语义边界，不写入内部实现细节、legacy 目录路径、容器路径或运行态部署路径。

## 6.1 正式策略 YAML 执行约束

1. backtest 服务必须把策略输入统一拆分为五大类：资金参数、策略参数、因子参数、信号参数、风控参数。
2. 直接桥接到 TQSDK 会话层的参数仅限其公开会话与下单接口所接受的字段，例如认证、回测区间、初始资金、目标持仓相关参数。
3. 因子参数、信号参数以及 SDK 无直接 hook 的风控参数，必须由 backtest 服务本地正式引擎严格执行。
4. 本地正式引擎至少必须严格执行手续费、滑点、仓位规则、止损、止盈、移动止损、最大回撤、日亏损限制、强平时点与不隔夜等系统级参数，并在正式报告中保留可追溯性。
5. 用户未来导入的策略，不允许因“适配正式引擎”而被服务端自动改写 YAML 原值；如参数无法执行，应显式返回失败原因，而不是隐式修正。

## 7. 正式 /api/v1 端点详情

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

### GET /api/v1/results/{job_id}/report

路径参数：`job_id`（UUID）

说明：下载单次回测的正式报告文件。若当前结果来自兼容层预览、尚未形成正式报告，或报告文件不存在，应返回明确错误，不得伪造本地拼接报告替代。

响应 200：报告文件流

响应 404：结果不存在、结果不是正式回测、或正式报告文件不存在

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

## 8. 策略推送接口需求说明（需求登记，非本轮实现）

- 需求路径：`POST /api/v1/strategies/{strategy_id}/push`
- 需求用途：仅允许把已完成回测且通过审阅的策略推送给 decision 服务使用。
- 前置条件：对应回测任务已 `completed`，结果与绩效指标可查询，且已通过人工或治理审核。
- 最小载荷：`strategy_id`、`result_id`、策略配置快照引用、最新绩效摘要。
- 说明：该接口当前只登记 backtest 服务侧需求；decision 侧接收契约与跨服务实现细节后续单独建档，不在本契约展开。

## 9. 公共错误结构

```json
{
  "detail": "Job not found",
  "code": "NOT_FOUND"
}
```

## 10. 明确排除接口（MVP 阶段不纳入）

| 排除接口 | 排除原因 |
|---|---|
| POST /api/v1/jobs/batch / DELETE /api/v1/jobs | 正式层 `/api/v1` 批量任务接口仍不纳入；本排除项不影响当前兼容层已冻结的 `DELETE /api/backtest/results/batch` |
| POST /api/v1/param_scan | 参数网格扫描，属于进阶功能，后续单独任务 |
| GET /api/v1/walk_forward/{job_id} | Walk-forward 分析，进阶功能 |
| GET /api/v1/optimize | 超参数优化，进阶功能 |
| WebSocket /ws/jobs/{job_id} | 实时状态推送，MVP 用轮询替代 |
| POST /api/v1/strategies/upload | 策略代码上传，由 decision 服务管理 |
| POST /api/strategy/approve | 当前不属于本批次活跃接口，继续延期，不按已启用接口登记 |
| GET /api/v1/admin/** | 运维管理接口，不属于跨服务公共契约 |