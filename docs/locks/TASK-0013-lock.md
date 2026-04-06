# TASK-0013 Lock 记录

## Lock 信息

- 任务 ID：TASK-0013
- 阶段：统一风控核心与阶段预设治理预审
- 当前任务是否仍处于“预审未执行”状态：是
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 模拟交易 Agent / 实盘交易 Agent（后续按服务边界执行）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/python-common/**` 若承接统一核心：后续单独 P0 Token
  - `services/sim-trading/**` / `services/live-trading/**` 若承接 adapter：后续分别 P1 Token
  - `.env.example` 或 `shared/contracts/**` 若补 preset / 风险事件字段：后续 P0 Token

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0013-sim-live-统一风控核心与阶段预设治理预审.md`
2. `docs/reviews/TASK-0013-review.md`
3. `docs/locks/TASK-0013-lock.md`
4. `docs/rollback/TASK-0013-rollback.md`
5. `docs/handoffs/TASK-0013-统一风控核心与阶段预设预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/sim-trading/**`
2. `services/live-trading/**`
3. `shared/python-common/**`
4. `shared/contracts/**`
5. `services/sim-trading/.env.example`
6. `services/live-trading/.env.example`
7. 其他全部非白名单文件

## 当前继续禁止修改的路径说明

1. 禁止以“先做 SimNow”名义提前在 `services/sim-trading/**` 中写长期风控核心。
2. 禁止在 `services/live-trading/**` 中提前复制一套独立风控实现。
3. 禁止在 `shared/python-common/**` 中无 Token 写入统一核心代码。
4. 禁止在 `shared/contracts/**` 中先写 preset 或风险事件字段后补审。

## 进入执行前需要的 Token / 授权

1. `TASK-0009` 必须先闭环。
2. Jay.S 必须确认是否需要在 `shared/python-common/**` 落地统一核心，并按该结论签发对应 P0 / P1 Token。
3. 若进入服务侧 adapter 实现，必须先冻结各自文件级白名单。
4. 所有真实账户、鉴权与通知 Secret 仍只能运行时注入，不属于当前解锁范围。

## 当前状态

- 预审状态：已通过
- Token 状态：未申请代码 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**TASK-0013 当前仍处于“预审未执行”状态；治理账本已留痕，但所有业务与共享代码路径继续锁定。**