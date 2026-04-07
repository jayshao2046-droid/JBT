# TASK-0021 Review

## Review 信息

- 任务 ID：TASK-0021
- 审核角色：项目架构师
- 审核阶段：旧决策域清洗升级迁移预审 + 批次 A 契约白名单与 Token 草案终审
- 审核时间：2026-04-07
- 审核结论：通过（预审结论继续有效；批次 A 草案已通过架构终审，当前正式状态为“待 Jay.S 签发 P0 Token”，不是“已执行”）

---

## 一、任务目标

1. 冻结旧 J_BotQuant 决策域清洗迁移的独立任务边界，明确其不等于 `TASK-0016` 和 `TASK-0012`。
2. 冻结干净独立的 decision 服务目标、研究能力主线、执行资格门禁与独立看板结构。
3. 冻结未来 contracts / integrations / decision / dashboard / notification 的最小拆批方案，避免跨服务混做。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0021-decision-旧决策域清洗升级迁移预审.md`
2. `docs/reviews/TASK-0021-review.md`
3. `docs/locks/TASK-0021-lock.md`
4. `docs/rollback/TASK-0021-rollback.md`
5. `docs/handoffs/TASK-0021-旧决策域清洗升级迁移预审交接单.md`
6. `docs/prompts/总项目经理调度提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`

## 三、当前轮次代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. 后续若修改 `shared/contracts/**`，需要 P0 Token。
3. 后续若修改 `integrations/legacy-botquant/**`，需要 P0 Token。
4. 后续若修改 `services/decision/**` 或 `services/dashboard/**`，需要对应 P1 Token；凡触及 `.env.example`，必须另拆 P0。

## 四、当前轮次通过标准

1. 已冻结 `TASK-0021` 与 `TASK-0016`、`TASK-0012` 的边界，明确三者不得复用白名单或 Token。
2. 已冻结清洗原则：旧通知、旧邮件、旧日志、旧策略、旧参数、旧设置不直接迁移；legacy 交易功能与外露回测功能关闭。
3. 已冻结模型矩阵、本地与在线模型路由、XGBoost 主线与 LightGBM 抽象预留位。
4. 已冻结因子/回测门禁：无回测、回测过期、因子版本变化一律失去执行资格。
5. 已冻结独立看板为 7 页结构，并冻结策略仓库动作与执行门禁。
6. 已冻结未来 contracts、integrations、decision、dashboard、notification 的拆批与保护级别。

## 五、当前轮次未进入代码执行的原因

1. 本任务当前轮次只做治理冻结，不做任何正式实现。
2. 当前尚未冻结首批代码文件级白名单。
3. 当前尚未签发任何 P0 / P1 Token。
4. 当前尚未完成面向决策 Agent 的只读迁移清单交接和公共项目提示词同步。

## 六、预审风险点

1. 若把本任务并入 `TASK-0016`，会把正式接入与清洗迁移混为一体。
2. 若不把 `shared/contracts/**`、`integrations/**` 与 `services/**` 拆批，会造成跨服务边界失控。
3. 若在没有回测、因子同步和研究完成门禁的情况下直接开放执行，会让策略进入生产后失效或漂移。
4. 若把看板直接落到 decision 服务目录而不按 `services/dashboard/**` 拆批，会破坏服务隔离。

## 七、预审结论

1. **TASK-0021 预审通过。**
2. **当前轮次只完成立项与治理冻结，不进入代码执行。**
3. **后续进入实施前，必须先补齐首批文件级白名单、对应 Token 与公共项目提示词同步。**

## 八、批次 A 草案终审结论

1. **A-Core / A-Extension 拆法通过。**
2. 当前正式公共口径冻结为：**`TASK-0021` 批次 A 草案已通过架构终审，待 Jay.S 签发 P0 Token；当前仍未进入 `shared/contracts/**` 实施。**
3. `A-Core` 建议文件范围冻结为：`shared/contracts/README.md`、`shared/contracts/decision/api.md`、`shared/contracts/decision/strategy_package.md`、`shared/contracts/decision/research_snapshot.md`、`shared/contracts/decision/backtest_certificate.md`、`shared/contracts/decision/decision_request.md`、`shared/contracts/decision/decision_result.md`、`shared/contracts/decision/model_boundary.md`。
4. `A-Extension` 条件范围冻结为：`shared/contracts/decision/notification_event.md`、`shared/contracts/decision/dashboard_projection.md`；仅在 Jay.S 明确要求批次 A 先冻结通知事件或看板只读聚合字段时，才进入后续 P0 签发。
5. 收紧说明：Atlas 草案中“A-Extension 可与 A-Core 合批签发”的表述，不进入当前正式口径。原因是首批 P0 需要继续维持最小面，通知事件与看板只读聚合字段目前不构成决策主链契约冻结前置。
6. `services/**`、`integrations/legacy-botquant/**` 与 legacy 目录继续锁定；不得把 `TASK-0021` 与 `TASK-0016` 或 `TASK-0012` 混批。