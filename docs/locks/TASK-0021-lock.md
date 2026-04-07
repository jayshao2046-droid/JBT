# TASK-0021 Lock 记录

## Lock 信息

- 任务 ID：TASK-0021
- 阶段：旧决策域清洗升级迁移预审 + 批次 A 10 文件 P0 签发范围终审同步
- 当前任务是否仍处于“预审未执行”状态：是；当前仅完成治理冻结与批次 A 10 文件正式签发范围同步，仍未进入代码执行
- 执行 Agent：
  - 项目架构师（当前预审）
  - Atlas（当前账本与调度留痕）
  - 决策 Agent（后续只读拆解 / 未来实施主体）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - 后续批次 A `shared/contracts/**`：P0（Jay.S 已明确要求按 10 文件正式范围签发；当前待立即签发）
  - 后续批次 B `integrations/legacy-botquant/**`：P0
  - 后续批次 C / D `services/decision/**`：P1
  - 后续批次 E `services/dashboard/**`：P1
  - 后续批次 F `services/decision/**` 通知体系：P1
  - 任意 `.env.example`：单独 P0

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0021-decision-旧决策域清洗升级迁移预审.md`
2. `docs/reviews/TASK-0021-review.md`
3. `docs/locks/TASK-0021-lock.md`
4. `docs/rollback/TASK-0021-rollback.md`
5. `docs/handoffs/TASK-0021-旧决策域清洗升级迁移预审交接单.md`
6. `docs/prompts/总项目经理调度提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`

## 当前锁定范围

1. `services/decision/**`
2. `services/dashboard/**`
3. `shared/contracts/**`
4. `integrations/legacy-botquant/**`
5. `services/backtest/**`
6. `services/data/**`
7. `services/sim-trading/**`
8. `services/live-trading/**`
9. legacy `J_BotQuant/**`
10. 其他全部非白名单文件

## 当前继续禁止修改的路径说明

1. 当前 `services/**` 仍未对本任务解锁，禁止写入。
2. 当前 `shared/contracts/**` 与 `integrations/legacy-botquant/**` 继续锁定。
3. 当前不得提前把看板原型目录、研究能力目录、通知链路目录列入代码白名单。
4. 当前不得把 `TASK-0021` 与 `TASK-0016` 或 `TASK-0012` 混批执行。
5. 当前不得以“先做一点试试”为名义写入任何业务文件。

## 进入执行前需要的 Token / 授权

1. `TASK-0021` 的治理账本闭环已完成本轮最小同步。
2. 公共项目提示词与项目架构师私有提示词已同步到批次 A 10 文件正式口径。
3. 批次 A 10 文件正式白名单已冻结。
4. 仍待 Jay.S 对对应 10 文件范围签发 P0 Token。
5. 若实施涉及其他服务目录，必须先拆成对应服务子任务，不得在本主任务内跨服务直接写入。

## 批次 A 10 文件正式签发范围冻结（2026-04-07）

1. 架构终审结论：通过；Jay.S 已明确要求批次 A 同时冻结通知事件与看板只读聚合字段，当前正式状态为“批次 A 10 文件正式范围待 Jay.S 立即签发 P0 Token”，不是“已执行”。
2. `shared/contracts/README.md`
3. `shared/contracts/decision/api.md`
4. `shared/contracts/decision/strategy_package.md`
5. `shared/contracts/decision/research_snapshot.md`
6. `shared/contracts/decision/backtest_certificate.md`
7. `shared/contracts/decision/decision_request.md`
8. `shared/contracts/decision/decision_result.md`
9. `shared/contracts/decision/model_boundary.md`
10. `shared/contracts/decision/notification_event.md`
11. `shared/contracts/decision/dashboard_projection.md`
12. 原“A-Extension 仅条件范围 / 不自动合批”口径已失效，不再作为当前正式冻结结论。
13. 本次终审不构成解锁；`services/**`、`integrations/legacy-botquant/**`、legacy `J_BotQuant/**` 与其他非白名单文件继续锁定。

## 当前状态

- 预审状态：已通过
- Token 状态：当前轮次未取得实际代码 Token；批次 A 10 文件正式范围已完成架构终审同步，待 Jay.S 立即签发 P0 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**`TASK-0021` 当前仍处于“批次 A 10 文件正式范围已冻结、待 Jay.S 签发 P0 Token、未进入执行”状态；继续锁定 `services/**`、`shared/contracts/**`、`integrations/**`、legacy 目录及其他全部非白名单文件。**