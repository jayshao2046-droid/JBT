# TASK-0013 Review

## Review 信息

- 任务 ID：TASK-0013
- 审核角色：项目架构师
- 审核阶段：sim / live 统一风控核心与阶段预设治理预审
- 审核时间：2026-04-06
- 审核结论：通过（当前轮次只冻结统一风控核心、stage preset 与 sim / live 可迁移边界；本轮白名单仅限治理账本与 prompt，同步明确 shared/python-common 若承接统一核心必须另走 P0，当前不进入代码执行）

---

## 一、任务目标

1. 冻结“同一风控核心 + 不同执行端适配层”的正式治理口径。
2. 冻结至少 `sim` / `live` 两类阶段预设的正式要求。
3. 阻止后续在 `services/sim-trading/**` 与 `services/live-trading/**` 中先写出两套长期分叉的风控核心实现。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0013-sim-live-统一风控核心与阶段预设治理预审.md`
2. `docs/reviews/TASK-0013-review.md`
3. `docs/locks/TASK-0013-lock.md`
4. `docs/rollback/TASK-0013-rollback.md`
5. `docs/handoffs/TASK-0013-统一风控核心与阶段预设预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 三、当前轮次代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. 若后续把统一风控核心落到 `shared/python-common/**`，必须单独申请 P0 Token。
3. 若后续在 `services/sim-trading/**` 或 `services/live-trading/**` 分别实现 adapter，只能在统一核心治理冻结后按 P1 分批申请 Token。
4. 若后续需要补充 `.env.example` 或 `shared/contracts/**` 的 preset / 风险事件字段，仍需单独按 P0 申请 Token。

## 四、当前轮次通过标准

1. “同一风控核心 + 不同执行端适配层”已经冻结为正式治理结论。
2. `sim` / `live` 两类阶段预设已冻结为正式治理口径。
3. 已明确若存在共享核心代码，唯一允许落点只能是 `shared/python-common/**`，且必须另走 P0。
4. 已明确 `TASK-0010`、`TASK-0014`、`TASK-0016`、`TASK-0017` 不得绕过本任务先写长期 SimNow 专用风控实现。

## 五、当前轮次未进入代码执行的原因

1. 本任务当前轮次的目标是治理冻结，不是代码实施。
2. `TASK-0009` 负责部署前置门槛与验收，当前必须先完成其闭环，再进入风控核心的代码落点讨论。
3. `shared/python-common/**`、`services/sim-trading/**`、`services/live-trading/**` 当前都没有针对本任务签发的文件级 Token。
4. 若在当前阶段直接写代码，会绕过统一核心治理并导致 sim / live 风控长期分叉风险。

## 六、预审结论

1. **TASK-0013 预审通过。**
2. **当前轮次只完成治理冻结，不进入代码执行。**
3. **后续如需进入实现，必须先由 Jay.S 按 P0 / P1 保护级别签发对应文件级 Token。**