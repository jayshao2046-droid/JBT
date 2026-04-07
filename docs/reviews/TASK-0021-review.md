# TASK-0021 Review

## Review 信息

- 任务 ID：TASK-0021
- 审核角色：项目架构师
- 审核阶段：旧决策域清洗升级迁移预审 + 批次 A 10 文件 P0 签发范围终审同步
- 审核时间：2026-04-07
- 审核结论：通过（预审结论继续有效；Jay.S 已明确要求批次 A 同时冻结通知事件与看板只读聚合字段，当前正式状态为“待 Jay.S 按 10 文件范围立即签发 P0 Token”，不是“已执行”）

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
2. 批次 A 10 文件正式签发范围虽已冻结，但 `shared/contracts/**` 仍未发生任何正式写入。
3. 当前尚未签发该 10 文件范围的实际 P0 Token。
4. 在 Jay.S 完成实际签发前，决策 Agent 仍不得进入 `shared/contracts/**`、`services/decision/**` 或 `services/dashboard/**` 代码实施。

## 六、预审风险点

1. 若把本任务并入 `TASK-0016`，会把正式接入与清洗迁移混为一体。
2. 若不把 `shared/contracts/**`、`integrations/**` 与 `services/**` 拆批，会造成跨服务边界失控。
3. 若在没有回测、因子同步和研究完成门禁的情况下直接开放执行，会让策略进入生产后失效或漂移。
4. 若把看板直接落到 decision 服务目录而不按 `services/dashboard/**` 拆批，会破坏服务隔离。

## 七、预审结论

1. **TASK-0021 预审通过。**
2. **当前轮次只完成立项与治理冻结，并把批次 A 正式签发范围升级并冻结到 10 文件，不进入代码执行。**
3. **后续进入实施前，仅待 Jay.S 对该 10 文件范围签发 P0 Token；在 Token 到位前继续禁止写入 `shared/contracts/**`。**

## 八、批次 A 草案终审结论

1. **Jay.S 已明确要求批次 A 同时冻结通知事件与看板只读聚合字段，因此批次 A 正式 P0 签发范围升级为 10 文件。**
2. 当前正式公共口径冻结为：**`TASK-0021` 批次 A 10 文件正式范围已完成架构终审同步，待 Jay.S 立即签发 P0 Token；当前仍未进入 `shared/contracts/**` 实施。**
3. `shared/contracts/README.md`
4. `shared/contracts/decision/api.md`
5. `shared/contracts/decision/strategy_package.md`
6. `shared/contracts/decision/research_snapshot.md`
7. `shared/contracts/decision/backtest_certificate.md`
8. `shared/contracts/decision/decision_request.md`
9. `shared/contracts/decision/decision_result.md`
10. `shared/contracts/decision/model_boundary.md`
11. `shared/contracts/decision/notification_event.md`
12. `shared/contracts/decision/dashboard_projection.md`
13. 原“A-Extension 仅条件范围 / 不自动合批”口径已失效，不再作为当前正式结论。
14. `services/**`、`integrations/legacy-botquant/**` 与 legacy 目录继续锁定；不得把 `TASK-0021` 与 `TASK-0016` 或 `TASK-0012` 混批。