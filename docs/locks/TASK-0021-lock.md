# TASK-0021 Lock 记录

## Lock 信息

- 任务 ID：TASK-0021
- 阶段：A批 contracts 终审收口同步
- 当前执行组织：项目架构师 + 决策 agent
- 当前是否使用 Livis：否
- 当前总体状态：A 批 contracts 已完成实施并通过终审，当前**可进入 lockback**；B、C0、C、D、E0、E、F0、F、G 继续待按 Manifest 一次性签发

## 本轮治理同步文件白名单

1. `docs/reviews/TASK-0021-review.md`
2. `docs/locks/TASK-0021-lock.md`
3. `docs/prompts/公共项目提示词.md`
4. `docs/prompts/agents/项目架构师提示词.md`

说明：本轮仍属于 P-LOG 治理留痕区，不构成业务目录解锁。

## 当前代码 Token 摘要

| 批次 | 范围摘要 | 保护级别 | 状态 | token_id | 说明 |
|---|---|---|---|---|---|
| A | `shared/contracts/README.md` + `shared/contracts/decision/*.md` 正式 10 文件范围 | P0 | **locked** | tok-c5ce23fe | A 批 lockback 已执行，REVIEW-TASK-0021-A，approved，commit 3bea6fe |
| B | `integrations/legacy-botquant/**` 决策迁移只读适配层 | P0 | **active** | tok-746b5b6d | Jay.S 已签发，480min TTL，可立即执行 |
| C0 | `services/decision/.env.example` 与决策服务受保护模板配置 | P0 | **active** | tok-79cc37ff | Jay.S 已签发，独立 P0，480min TTL |
| C | `services/decision/src/**`、`tests/**`、`pyproject.toml`（23文件） | P1 | **active** | tok-763ac85c | Jay.S 已签发，480min TTL |
| D | 决策研究中心与资格门禁联动实现（11文件） | P1 | **active** | tok-17047062 | Jay.S 已签发，480min TTL |
| E0 | `services/dashboard/.env.example` 与看板受保护模板配置 | P0 | **active** | tok-3282b492 | Jay.S 已签发，独立 P0，480min TTL |
| E | `services/dashboard/**` 决策看板 7 页 Next.js（18文件） | P1 | **active** | tok-3af985b1 | Jay.S 已签发，480min TTL |
| F0 | `docker-compose.dev.yml` + 两份 Dockerfile（3文件） | P0 | **active** | tok-74510f58 | Jay.S 已签发，独立 P0，480min TTL |
| F | 决策通知与日报实现（9文件） | P1 | **active** | tok-02533342 | Jay.S 已签发，480min TTL |
| G | 发布链路与迁移收口（5文件） | P1 | **active** | tok-29b611b8 | Jay.S 已签发，480min TTL |

## A 批 contracts 范围冻结（当前待 lockback）

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

说明：A 批实施范围继续固定为上述 10 个契约文件；当前收口状态为“待 lockback”，不得夹带新增文件，不得扩写到 B~G。

## A 批收口说明

1. 决策 agent 已完成 A 批 10 个契约文件实施，并回交 `docs/handoffs/TASK-0021-A批-contracts-决策交接.md`。
2. 项目架构师终审确认：A 批业务写入未夹带 `services/**` 或 `integrations/**`。
3. 因此 A 批状态自 `active` 收口为 `pending_lockback`；当前仅表示“可进入 lockback”，不表示 lockback 已完成。

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

- 预审状态：已通过；A 批终审已通过
- Token 状态：A=pending_lockback；B/C0/C/D/E0/E/F0/F/G=pending_manifest
- 解锁时间：A 批 active 窗口已用于本轮实施；其余批次待 Jay.S 按 Manifest 一次性签发
- 锁回时间：A 批待执行 lockback；其余批次当前未进入 lockback 阶段
- lockback 结果：A 批当前仅形成“可进入 lockback”结论，尚未实际执行 lockback

## 结论

**`TASK-0021` 当前状态：A 批 locked（commit 3bea6fe）；B~G 全部 Token 已由 Jay.S 签发，均为 active 状态（TTL 480min），可按 B→C0→C→D→E0→E→F0→F→G 顺序连续派发执行。**