# TASK-0015 Lock 记录

## Lock 信息

- 任务 ID：TASK-0015
- 阶段：dashboard SimNow 临时 Next.js 看板预审
- 当前任务是否仍处于“预审未执行”状态：是
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 看板 Agent（后续前端实现主体）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/dashboard/**`：后续 P1 Token
  - `services/dashboard/.env.example`：后续 P0 Token
  - `shared/contracts/**` 若补只读契约：后续 P0 Token

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0015-dashboard-SimNow-临时Next.js看板预审.md`
2. `docs/reviews/TASK-0015-review.md`
3. `docs/locks/TASK-0015-lock.md`
4. `docs/rollback/TASK-0015-rollback.md`
5. `docs/handoffs/TASK-0015-SimNow-临时看板预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/dashboard/**`
2. `services/backtest/backtest_web/**`
3. `services/sim-trading/**`
4. `shared/contracts/**`
5. `services/dashboard/.env.example`
6. 其他全部非白名单文件

## 当前继续禁止修改的路径说明

1. 当前整个 `services/dashboard/**` 仍未对本任务冻结文件级白名单，禁止写入。
2. 禁止借本任务复用或改写 `services/backtest/backtest_web/**` 既有看板文件。
3. 禁止在前端页面中直接写入交易、清退、强平等执行逻辑。
4. 禁止先改 `shared/contracts/**` 或 `services/sim-trading/**` 再回补看板预审。

## 进入执行前需要的 Token / 授权

1. `TASK-0009`、`TASK-0013`、`TASK-0010`、`TASK-0014` 的前置口径必须先满足。
2. Jay.S 必须先提供前端材料或书面豁免，并确认是否需要 `.env.example` 占位。
3. 需要先冻结 `services/dashboard/**` 的文件级白名单，再由 Jay.S 签发 P1 / P0 Token。
4. 如需新增跨服务只读契约，必须先补 P0 契约预审。

## 当前状态

- 预审状态：已通过
- Token 状态：未申请代码 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**TASK-0015 当前仍处于“预审未执行”状态；dashboard 代码、前端环境模板与相关契约路径继续锁定。**