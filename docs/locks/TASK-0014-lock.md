# TASK-0014 Lock 记录

## Lock 信息

- 任务 ID：TASK-0014
- 阶段：sim-trading 风控通知链路预审
- 当前任务是否仍处于“预审未执行”状态：是
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 模拟交易 Agent（后续服务实现主体）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/sim-trading/src/**` / `services/sim-trading/tests/**`：后续 P1 Token
  - `services/sim-trading/.env.example`：后续 P0 Token
  - `shared/contracts/**` 若补通知事件契约：后续 P0 Token

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
2. `docs/reviews/TASK-0014-review.md`
3. `docs/locks/TASK-0014-lock.md`
4. `docs/rollback/TASK-0014-rollback.md`
5. `docs/handoffs/TASK-0014-风控通知链路预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/sim-trading/**`
2. `services/live-trading/**`
3. `shared/contracts/**`
4. `services/sim-trading/.env.example`
5. 其他全部非白名单文件

## 当前继续禁止修改的路径说明

1. 当前整个 `services/sim-trading/**` 仍未对本任务冻结文件级白名单，禁止写入。
2. 禁止复用 `services/live-trading/**` 或其他服务的默认 webhook、邮箱配置与通知模板。
3. 禁止在 `shared/contracts/**` 中先写通知事件契约后补审。
4. 禁止把真实 webhook、邮箱账号、邮箱密码或 SMTP Secret 写入仓库。

## 进入执行前需要的 Token / 授权

1. `TASK-0009`、`TASK-0013` 必须先闭环。
2. `TASK-0010` 必须先完成最小风险事件输出与风控钩子占位。
3. 需要先冻结 `services/sim-trading/**` 的文件级白名单，再由 Jay.S 签发对应 P1 / P0 Token。
4. Jay.S 还需确认通知渠道来源与运行时 Secret 注入方案。

## 当前状态

- 预审状态：已通过
- Token 状态：未申请代码 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**TASK-0014 当前仍处于“预审未执行”状态；通知链路相关服务文件、契约文件与 `.env.example` 继续锁定。**