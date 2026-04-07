# TASK-0021 Lock 记录

## Lock 信息

- 任务 ID：TASK-0021
- 阶段：总包执行治理准备终审同步
- 当前执行组织：项目架构师 + 决策 agent
- 当前是否使用 Livis：否
- 当前总体状态：总包执行治理已就绪；**仅 A 批 Token 已 active**，其余批次待按 Manifest 一次性签发

## 本轮治理同步文件白名单

1. `docs/reviews/TASK-0021-review.md`
2. `docs/locks/TASK-0021-lock.md`
3. `docs/handoffs/TASK-0021-总包执行与Token清单.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

说明：本轮仍属于 P-LOG 治理留痕区，不构成业务目录解锁。

## 当前代码 Token 摘要

| 批次 | 范围摘要 | 保护级别 | 状态 | 说明 |
|---|---|---|---|---|
| A | `shared/contracts/README.md` + `shared/contracts/decision/*.md` 正式 10 文件范围 | P0 | active | 当前唯一可直接执行批次 |
| B | `integrations/legacy-botquant/**` 决策迁移只读适配层 | P0 | pending_manifest | 未签发前不得进入 legacy 适配实现 |
| C0 | `services/decision/.env.example` 与决策服务受保护模板配置 | P0 | pending_manifest | 必须独立 P0 |
| C | `services/decision/src/**`、`tests/**`、必要 `configs/**` | P1 | pending_manifest | 不得在 C0 前提前扩写受保护配置 |
| D | 决策研究中心与资格门禁联动实现 | P1 | pending_manifest | 不得提前进入研究编排实现 |
| E0 | `services/dashboard/.env.example` 与看板受保护模板配置 | P0 | pending_manifest | 必须独立 P0 |
| E | `services/dashboard/**` 决策看板实现范围 | P1 | pending_manifest | 不得提前写入看板业务文件 |
| F0 | compose / Dockerfile / deploy / 反代相关保护文件 | P0 | pending_manifest | 必须独立 P0 |
| F | 决策通知与日报实现范围 | P1 | pending_manifest | 不得提前进入通知链路实现 |
| G | 发布链路与迁移收口实现范围 | P1 | pending_manifest | 不得提前进入生产发布实现 |

## A 批 active 范围冻结

1. `shared/contracts/README.md`
2. `shared/contracts/decision/api.md`
3. `shared/contracts/decision/strategy_package.md`
4. `shared/contracts/decision/research_snapshot.md`
5. `shared/contracts/decision/backtest_certificate.md`
6. `shared/contracts/decision/decision_request.md`
7. `shared/contracts/decision/decision_result.md`
8. `shared/contracts/decision/model_boundary.md`
9. `shared/contracts/decision/notification_event.md`
10. `shared/contracts/decision/dashboard_projection.md`

说明：A 批当前可直接开工，但不得夹带新增文件，不得扩写到 B~G。

## 当前锁定范围

1. 除 A 批 active 范围外，`shared/contracts/**` 其余路径继续锁定。
2. `integrations/legacy-botquant/**` 当前继续锁定。
3. `services/decision/**` 当前除未来待签批次外整体继续锁定。
4. `services/dashboard/**` 当前继续锁定。
5. `services/backtest/**`、`services/data/**`、`services/sim-trading/**`、`services/live-trading/**` 继续锁定。
6. legacy `J_BotQuant/**` 继续锁定。
7. 其他全部非白名单文件继续锁定。

## 强制约束

1. 当前仅 A 批 Token 已 active，**其余批次一律不得提前执行**。
2. 其余批次必须以 `docs/handoffs/TASK-0021-总包执行与Token清单.md` 为 Manifest，由 Jay.S 一次性签发后方可进入执行态。
3. `C0`、`E0`、`F0` 为独立 P0，不得与 P1 批次混签、混提、混回滚。
4. 任何 `.env.example`、compose、Dockerfile、deploy 相关修改，都不得并入 C、E、F、G 等 P1 实施批次。
5. 不得以“A 已 active”为理由越权触碰 `integrations/**`、`services/**` 或其他未解锁契约文件。

## 当前状态

- 预审状态：已通过
- Token 状态：A=active；B/C0/C/D/E0/E/F0/F/G=pending_manifest
- 解锁时间：A 批已进入 active；其余批次待 Jay.S 按 Manifest 一次性签发
- 锁回时间：A 批执行完成后另行记录；其余批次当前未进入 lockback 阶段
- lockback 结果：当前仅治理准备完成，尚未产生本轮新 lockback

## 结论

**`TASK-0021` 当前正式处于“总包执行治理已就绪、执行组织固定为项目架构师 + 决策 agent、A 批 Token 已 active、其余批次待按 Manifest 一次性签发”的状态；除 A 批外，任何提前执行均视为越权。**