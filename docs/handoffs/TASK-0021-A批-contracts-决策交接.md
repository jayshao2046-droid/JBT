# TASK-0021 A批 contracts 决策交接

## 文档信息

- 任务 ID：TASK-0021
- 批次：A contracts
- 提交 Agent：决策
- 提交时间：2026-04-07
- 批次目标：只在 A 批 active 白名单内完成 decision 正式契约最小落地，不触碰 `services/**`、`integrations/**` 或其他 `shared/contracts/**`

## 本批完成动作

1. 更新 `shared/contracts/README.md`，补登记 `decision/` 正式契约目录与文件索引。
2. 新增 `shared/contracts/decision/api.md`，冻结 decision 第一阶段正式 API 边界，并明确 decision 只负责因子、信号、审批与策略编排。
3. 新增 `strategy_package.md`、`research_snapshot.md`、`backtest_certificate.md`，把策略仓库动作、研究快照、回测合格证明与执行资格门禁拆成独立契约。
4. 新增 `decision_request.md` 与 `decision_result.md`，冻结请求/结果统一模型，明确“执行”只表示进入发布流程，不等于直接下单。
5. 新增 `model_boundary.md`，冻结本地与云端模型路线：`Qwen3 14B`、`DeepSeek-R1 14B`、`Qwen2.5`、`Qwen3.6-Plus`、`Qwen3-Max`、`DeepSeek-V3.2`、`DeepSeek-R1`；同时冻结研究主线 `XGBoost`，`LightGBM` 仅保留抽象位。
6. 新增 `notification_event.md` 与 `dashboard_projection.md`，为后续通知体系与 7 页决策看板提供最小稳定只读字段。
7. 同步更新决策 Agent 私有 prompt，当前状态切换为“待项目架构师终审”。

## 实际修改文件

- `shared/contracts/README.md`
- `shared/contracts/decision/api.md`
- `shared/contracts/decision/strategy_package.md`
- `shared/contracts/decision/research_snapshot.md`
- `shared/contracts/decision/backtest_certificate.md`
- `shared/contracts/decision/decision_request.md`
- `shared/contracts/decision/decision_result.md`
- `shared/contracts/decision/model_boundary.md`
- `shared/contracts/decision/notification_event.md`
- `shared/contracts/decision/dashboard_projection.md`
- `docs/prompts/agents/决策提示词.md`
- `docs/handoffs/TASK-0021-A批-contracts-决策交接.md`

## 关键冻结结论

1. decision 只负责因子、信号、审批、策略编排，不直接承接下单、成交、持仓或交易账本。
2. 策略仓库动作正式冻结为：导入、导出、预约、执行、下架。
3. 其中“执行”只表示进入发布流程，不等于直接下单，也不等于直接写交易服务内部目录。
4. 第一阶段发布目标只允许 `sim-trading`；`live-trading` 仅保留锁定可见语义，不能进入可执行状态。
5. 模型路线与研究边界正式冻结为：本地 `Qwen3 14B` / `DeepSeek-R1 14B` / `Qwen2.5`，云端 `Qwen3.6-Plus` / `Qwen3-Max` / `DeepSeek-V3.2` / `DeepSeek-R1`；研究主线为 `XGBoost`，`LightGBM` 仅保留抽象位。
6. `research_snapshot`、`backtest_certificate`、`notification_event`、`dashboard_projection` 均已保留后续总包实现所需的最小稳定字段。
7. 契约层明确排除了 API Key、prompt 原文、思维链、绝对路径、SQLite 行号与旧系统内部实现细节。

## 自校验结果

- 最小诊断校验：A 批 10 个契约文件诊断结果均为 `No errors found`。
- 关键词核对通过：已显式写入 `sim-trading` 第一阶段唯一发布目标、`live-trading` 锁定可见、策略仓库“执行不等于直接下单”、模型路线冻结、`XGBoost` 主线与 `LightGBM` 预留抽象位。
- 范围核对通过：未修改 `services/**`、`integrations/**`、其他 `shared/contracts/**` 业务文件。

## 待项目架构师终审项

1. 核验本批业务修改仍严格限制在 A 批 active 白名单 10 文件内。
2. 核验契约口径与 `TASK-0021` 冻结要求一致，未混入 `TASK-0012` 或 `TASK-0016` 字段语义。
3. 核验通知事件、看板投影、研究快照与回测证明字段已足够支撑后续总包批次，但未提前写入实现细节。
4. 若终审通过，请立即执行 A 批 contracts lockback。

## 向 Jay.S 汇报摘要

- `TASK-0021` 批次 A contracts 已完成最小正式落地，业务修改只发生在 A 批 10 个 active 契约文件内。
- decision 正式契约已冻结：API、策略仓库、研究快照、回测证明、请求/结果模型、模型边界、通知事件、看板只读聚合字段均已到位。
- 第一阶段发布目标已明确收口到 `sim-trading`，`live-trading` 仅锁定可见；策略仓库“执行”不等于直接下单。
- 最小自校验已完成：A 批 10 文件诊断均为 0，未发现白名单外业务改动。

## 下一步建议

1. 先提交项目架构师终审。
2. 终审通过后立即执行 A 批 lockback。
3. 锁回完成后，再由 Jay.S 按 Manifest 签发 B、C0、C、D、E0、E、F0、F、G。