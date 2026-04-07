# decision API 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义 decision 服务第一阶段的最小正式 API 边界，用于：

1. 接收标准化决策请求并返回审批结果。
2. 管理策略仓库的导入、导出、预约、执行、下架动作。
3. 向后续看板与通知链路提供稳定的只读查询入口。

decision 服务只负责因子、信号、审批与策略编排，不直接承接下单、成交、持仓或交易账本实现。

## 2. API 端点总览

| 方法 | 路径 | 用途 | 请求模型 | 响应模型 |
|---|---|---|---|---|
| GET | `/api/v1/health` | 健康检查 | 无 | 服务状态对象 |
| POST | `/api/v1/decisions/analyze` | 提交单次决策分析请求 | `decision_request.md` | `decision_result.md` |
| GET | `/api/v1/decisions/{decision_id}` | 查询单次决策结果 | 路径参数 `decision_id` | `decision_result.md` |
| GET | `/api/v1/decisions` | 分页查询决策结果 | `strategy_id`、`symbol`、`action`、`page`、`limit` | `decision_result.md[]` |
| POST | `/api/v1/strategy-packages/import` | 导入策略包快照 | `strategy_package.md` | `strategy_package.md` |
| GET | `/api/v1/strategy-packages/{strategy_id}` | 查询单个策略包 | 路径参数 `strategy_id` | `strategy_package.md` |
| GET | `/api/v1/strategy-packages/{strategy_id}/export` | 导出当前策略包快照 | 路径参数 `strategy_id` | `strategy_package.md` |
| POST | `/api/v1/strategy-packages/{strategy_id}/reserve` | 预约进入发布窗口 | 路径参数 `strategy_id` + 时间窗口对象 | `strategy_package.md` |
| POST | `/api/v1/strategy-packages/{strategy_id}/execute` | 进入发布流程 | 路径参数 `strategy_id` + 目标服务对象 | `strategy_package.md` |
| POST | `/api/v1/strategy-packages/{strategy_id}/retire` | 下架策略包 | 路径参数 `strategy_id` | `strategy_package.md` |
| GET | `/api/v1/dashboard/projection` | 查询决策看板只读聚合投影 | `page`、`strategy_id`、`updated_since` | `dashboard_projection.md` |
| GET | `/api/v1/notification-events` | 查询通知事件流 | `category`、`risk_level_or_type`、`strategy_id`、`page`、`limit` | `notification_event.md[]` |

## 3. 关联契约

1. `POST /api/v1/decisions/analyze` 的输入输出分别对齐 `decision_request.md` 与 `decision_result.md`。
2. 策略仓库动作统一对齐 `strategy_package.md`，并引用 `research_snapshot.md` 与 `backtest_certificate.md` 作为执行资格前置证明。
3. `decision_result.md` 中的 `model_profile` 只允许引用 `model_boundary.md` 已登记的模型路线。
4. 看板只读聚合字段与通知事件字段分别对齐 `dashboard_projection.md` 与 `notification_event.md`。

## 4. 核心约束

1. decision 只负责因子、信号、审批与策略编排，不得把交易执行、副本账本或下单细节写进本契约。
2. 策略仓库动作冻结为：导入、导出、预约、执行、下架。
3. 其中“执行”只表示进入发布流程，不等于直接下单，也不等于写入 `sim-trading` 或 `live-trading` 内部目录。
4. 第一阶段发布目标只允许 `sim-trading`；`live-trading` 只能以锁定可见方式出现在响应中，不得进入可执行状态。
5. 若研究快照失效、回测证明过期或因子版本不一致，decision 必须返回 `hold`、`reject` 或 `escalate`，不得继续推进发布流程。

## 5. 端点详情

### GET /api/v1/health

响应 200：

```json
{
  "status": "ok",
  "service": "decision",
  "version": "0.1.0"
}
```

### POST /api/v1/decisions/analyze

请求体：`decision_request.md`

响应 201：`decision_result.md`

错误约束：

- 422：字段校验失败。
- 409：研究快照、回测证明或因子版本冲突。
- 423：目标为 `live-trading` 且当前阶段仅允许锁定可见。

### GET /api/v1/decisions/{decision_id}

路径参数：`decision_id`

响应 200：`decision_result.md`

响应 404：结果不存在。

### GET /api/v1/decisions

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| strategy_id | string | 否 | 按策略过滤 |
| symbol | string | 否 | 按标的过滤 |
| action | string | 否 | `approve` / `reject` / `hold` / `escalate` |
| page | integer | 否 | 页码，默认 1 |
| limit | integer | 否 | 每页条数，默认 20，最大 100 |

### POST /api/v1/strategy-packages/import

请求体最少包含：

1. `strategy_package.md` 主体字段。
2. `research_snapshot_id`。
3. `backtest_certificate_id`。

响应 201：返回导入后的 `strategy_package.md`，`lifecycle_status=imported`。

### GET /api/v1/strategy-packages/{strategy_id}/export

说明：返回当前生效的策略包快照，供只读导出、审阅或归档使用；不返回 prompt 原文、链路日志或绝对路径。

### POST /api/v1/strategy-packages/{strategy_id}/reserve

说明：登记预约发布窗口，返回更新后的 `strategy_package.md`，`lifecycle_status=reserved`。

### POST /api/v1/strategy-packages/{strategy_id}/execute

说明：把策略包推进到发布流程。

约束：

1. 请求中的 `publish_target` 第一阶段只允许 `sim-trading`。
2. 若请求目标为 `live-trading`，响应必须保留 `live_visibility_mode=locked_visible`，且不得进入发布执行态。
3. 返回对象中的状态只表示“进入发布流程”，不表示“已下单”或“已成交”。

### POST /api/v1/strategy-packages/{strategy_id}/retire

说明：下架策略包并停止后续发布编排；不删除历史决策、研究快照或回测证明引用。

### GET /api/v1/dashboard/projection

说明：返回 `dashboard_projection.md` 定义的只读聚合对象，供后续决策看板 7 页渲染使用。

### GET /api/v1/notification-events

说明：返回 `notification_event.md` 定义的标准事件对象，供通知中心、日报与审阅界面消费。

## 6. 明确排除项

以下内容不进入本契约：

- API Key、鉴权密钥、Webhook、SMTP 凭据
- prompt 原文、思维链、完整推理日志
- 绝对路径、容器路径、模型权重路径
- SQLite 行号、缓存命中行、内部审计表结构
- legacy 旧系统内部实现细节