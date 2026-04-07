# TASK-0021 批次 A 契约白名单与 Token 草案

【签名】Atlas
【时间】2026-04-07
【设备】MacBook

## 目标

在不触碰 `services/**`、`integrations/**`、legacy 目录的前提下，为 `TASK-0021` 的首个正式实施批次准备最小 `shared/contracts/**` 文件级白名单与 P0 Token 草案。

## 本轮结论

1. `TASK-0021` 批次 A 继续只锁定在 `shared/contracts/**`，不得夹带任何 `services/**`、`integrations/legacy-botquant/**` 或 `.env.example`。
2. 为降低首批 P0 面积，建议先签发 **A-Core**，只冻结决策主链需要的 8 个契约文件。
3. 通知事件与看板只读聚合字段建议作为 **A-Extension** 补充冻结；若项目架构师坚持按 `TASK-0021` 的批次 A 全量口径一次完成，再并入同一批次签发。

## A-Core 建议白名单

| 文件路径 | 动作 | 保护级别 | 用途 |
|---|---|---|---|
| `shared/contracts/README.md` | MODIFY | P0 | 登记 decision 契约目录与索引 |
| `shared/contracts/decision/api.md` | CREATE | P0 | 决策服务正式 API 边界 |
| `shared/contracts/decision/strategy_package.md` | CREATE | P0 | 策略包元数据与版本快照 |
| `shared/contracts/decision/research_snapshot.md` | CREATE | P0 | 研究资格快照与有效期 |
| `shared/contracts/decision/backtest_certificate.md` | CREATE | P0 | 回测合格证明引用结构 |
| `shared/contracts/decision/decision_request.md` | CREATE | P0 | 决策请求统一入参 |
| `shared/contracts/decision/decision_result.md` | CREATE | P0 | 决策结果统一出参 |
| `shared/contracts/decision/model_boundary.md` | CREATE | P0 | 本地模型/云端模型/缓存边界 |

## A-Extension 建议白名单

| 文件路径 | 动作 | 保护级别 | 用途 |
|---|---|---|---|
| `shared/contracts/decision/notification_event.md` | CREATE | P0 | 决策通知事件标准载荷 |
| `shared/contracts/decision/dashboard_projection.md` | CREATE | P0 | 决策看板只读聚合字段 |

## 最小字段域冻结建议

### `shared/contracts/decision/api.md`

1. `GET /api/v1/health`：健康检查。
2. `POST /api/v1/decisions/analyze`：提交决策分析请求。
3. `GET /api/v1/decisions/{decision_id}`：查询单次决策结果。
4. `GET /api/v1/decisions`：按 `symbol`、`strategy_id`、`status` 分页查询。
5. `POST /api/v1/strategy-packages`：接收已通过回测审阅的策略包快照。

### `shared/contracts/decision/strategy_package.md`

1. `strategy_id`
2. `strategy_version`
3. `template_id`
4. `factor_version_hash`
5. `risk_profile_hash`
6. `config_snapshot_ref`
7. `allowed_targets`（第一阶段仅 `sim-trading`）
8. `created_at`

### `shared/contracts/decision/research_snapshot.md`

1. `strategy_id`
2. `research_status`
3. `model_family`
4. `feature_set_version`
5. `train_window`
6. `generated_at`
7. `valid_until`

### `shared/contracts/decision/backtest_certificate.md`

1. `strategy_id`
2. `result_id`
3. `metrics_ref`
4. `requested_symbol`
5. `executed_data_symbol`
6. `review_status`
7. `approved_at`
8. `expires_at`

### `shared/contracts/decision/decision_request.md`

1. `request_id`
2. `strategy_id`
3. `symbol`
4. `signal`（`-1/0/1`）
5. `signal_strength`
6. `factors`
7. `market_context`
8. `submitted_at`

### `shared/contracts/decision/decision_result.md`

1. `decision_id`
2. `request_id`
3. `action`（`approve/reject/hold/escalate`）
4. `confidence`
5. `layer`（只允许功能层级，不暴露内部参数）
6. `model_profile`
7. `reasoning_summary`
8. `generated_at`

### `shared/contracts/decision/model_boundary.md`

1. 仅 `decision` 服务可直接访问本地推理端点与云端模型 Secret。
2. 其他服务只能通过 decision 正式 API 获取决策结果。
3. SQLite 决策缓存、审计日志、prompt 模板、模型权重路径均归 `decision` 私有实现。

### `shared/contracts/decision/notification_event.md`

1. `event_id`
2. `service_name`
3. `category`
4. `risk_level_or_type`
5. `title`
6. `trace_id`
7. `emitted_at`

### `shared/contracts/decision/dashboard_projection.md`

1. `strategy_id`
2. `strategy_status`
3. `eligibility_status`
4. `latest_backtest_result_id`
5. `latest_decision_id`
6. `latest_notification_id`
7. `updated_at`

## 复用与禁止复用

### 直接复用

1. `shared/contracts/backtest/backtest_result.md` 与 `shared/contracts/backtest/performance_metrics.md` 作为 `backtest_certificate` 的上游引用来源。
2. `shared/contracts/sim-trading/bridge_signal.md` 的 `symbol`、`strategy_id`、`trace_id` 命名口径继续复用，不另造别名。
3. backtest 契约中已经冻结的 `requested_symbol` / `executed_data_symbol` 分离口径，直接下沉到 `backtest_certificate`。

### 明确禁止

1. 不把 `TASK-0012` 的桥接信号载荷直接当作 `decision_request` 契约。
2. 不把 `TASK-0016` 的正式接入链路字段回写到批次 A 契约，避免把接入与迁移混批。
3. 不在批次 A 内修改现有 `shared/contracts/backtest/*.md`、`shared/contracts/sim-trading/*.md` 的业务字段，只允许引用。

## 明确排除项

1. 本地模型路径、Ollama URL、云端 API Key。
2. prompt 模板名、prompt 版本、思考链文本、完整推理日志。
3. SQLite 行号、缓存命中标记、内部审计表结构。
4. legacy `.env` 路径、legacy 数据目录路径、legacy 运行态日志路径。
5. 任意 `services/**`、`integrations/**`、`.env.example`、`docker-compose.dev.yml`。

## Token 草案

### A-Core

1. 任务：`TASK-0021`
2. 执行 Agent：决策
3. 保护级别：P0
4. 建议 Token 范围：A-Core 表内 8 个文件
5. 当前状态：`draft_pending_arch_review`

### A-Extension

1. 任务：`TASK-0021`
2. 执行 Agent：决策
3. 保护级别：P0
4. 建议 Token 范围：A-Extension 表内 2 个文件
5. 当前状态：`draft_pending_arch_review`

## 风险清单

1. 若把批次 A 与 `TASK-0016` 混并，会把“正式接入”与“迁移清洗”混成同一回滚单元。
2. 若把批次 A 与 `TASK-0012` 混并，会把桥接兼容字段错误上升为 decision 正式契约。
3. 若批次 A 直接修改现有 backtest/sim-trading 正式契约，首批 P0 面积会无必要扩大。
4. 若在契约里写入模型、缓存、prompt、Secret、legacy 路径，后续实现会被内部细节反向绑死。

## 下一检查点

1. 由项目架构师审阅本草案，裁定 A-Core 与 A-Extension 是否合批。
2. 由项目架构师决定是否需要同步更新 `docs/reviews/TASK-0021-review.md` 与 `docs/locks/TASK-0021-lock.md` 的批次 A 冻结信息。
3. Jay.S 确认后，再进入 `shared/contracts/**` 的 P0 Token 签发。