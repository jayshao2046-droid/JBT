# TASK-0016 Lock 记录

## Lock 信息

- 任务 ID：TASK-0016
- 阶段：J_BotQuant Studio 决策端 API 接入预审
- 当前任务是否仍处于“预审未执行”状态：是
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 模拟交易 Agent（后续服务侧批次）
  - Jay.S 指定的集成执行主体（后续 `integrations/**` 批次）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/contracts/**`：后续 P0 Token
  - `services/sim-trading/**`：后续 P1 Token
  - `integrations/legacy-botquant/**`：后续 P0 Token

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0016-J_BotQuant-Studio-决策端API接入预审.md`
2. `docs/reviews/TASK-0016-review.md`
3. `docs/locks/TASK-0016-lock.md`
4. `docs/rollback/TASK-0016-rollback.md`
5. `docs/handoffs/TASK-0016-Studio-正式接入预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `shared/contracts/**`
2. `services/sim-trading/**`
3. `integrations/legacy-botquant/**`
4. `services/sim-trading/.env.example`
5. 其他全部非白名单文件

## 当前继续禁止修改的路径说明

1. 禁止把本任务并入 `TASK-0012` 的兼容桥接实现。
2. 禁止在未冻结正式契约前直接修改 `services/sim-trading/**` 或 `integrations/legacy-botquant/**`。
3. `integrations/**` 当前一律按 P0 保护路径处理，禁止误按 P1 执行。
4. 禁止把上游 API URL、鉴权 key、签名密钥与回调凭证写入仓库。

## 进入执行前需要的 Token / 授权

1. `TASK-0009`、`TASK-0013`、`TASK-0010`、`TASK-0014`、`TASK-0015` 的前置条件必须先满足或被 Jay.S 书面豁免。
2. `TASK-0012` 的兼容桥接状态必须先明确。
3. 需要先冻结 contracts、服务侧与 integrations 的分批文件级白名单，再由 Jay.S 分别签发 P0 / P1 Token。
4. Jay.S 还需确认正式接入测试窗口、Secret 注入方式与 `integrations/**` 的执行主体。

## 当前状态

- 预审状态：已通过
- Token 状态：未申请代码 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**TASK-0016 当前仍处于“预审未执行”状态；contracts、sim-trading 与 integrations 路径继续锁定。**