# TASK-0002 预审 Review

## Review 信息

- 任务 ID：TASK-0002
- 审核角色：项目架构师
 - 审核阶段：终审
 - 审核时间：2026-04-03
 - 审核结论：通过（Jay.S 已批准，进入执行态；草稿区准备中，P0 写入待 P0 Token）

## 核验内容

### 边界核验

- 本任务分为两个阶段：阶段一为契约登记（P0 保护区），阶段二为服务骨架（P1 保护区）。
- 项目架构师仅负责阶段一契约初稿的写入，以及阶段二的派发包输出，不进入 `services/sim-trading/` 目录写入任何文件。
- 模拟交易 agent 负责阶段二 `services/sim-trading/` 的所有文件创建，不越权写入其他服务目录。
- 本轮建档阶段**未发生任何 contracts 或 services 目录的代码写入**，边界合规。

### 文件白名单核验

- `docs/tasks/TASK-0002-*.md`：P-LOG 区，项目架构师可写。✅
- `docs/reviews/TASK-0002-review.md`：P-LOG 区，项目架构师可写。✅
- `docs/locks/TASK-0002-lock.md`：P-LOG 区，项目架构师可写。✅
- `docs/rollback/TASK-0002-rollback.md`：P-LOG 区，项目架构师可写。✅
- `docs/prompts/公共项目提示词.md`：P-LOG 区，项目架构师可写。✅
- `docs/prompts/agents/项目架构师提示词.md`：P-LOG 区，项目架构师可写。✅
- `docs/prompts/agents/模拟交易提示词.md`：P-LOG 区，模拟交易 agent 独写；本轮建档阶段不写入。⏳
- `shared/contracts/sim-trading/`：P0 保护区，需 Jay.S Token，本轮不写入。⏳
- `services/sim-trading/src/`：P1 保护区，需 Jay.S Token，由模拟交易 agent 执行，本轮不写入。⏳
- `services/sim-trading/configs/`：P1 保护区，需 Jay.S Token，由模拟交易 agent 执行，本轮不写入。⏳

### 契约一致性核验

- 本轮建档阶段尚未写入任何契约字段，契约一致性核验将在阶段一执行态中进行。
- 已确认 `shared/contracts/` 目录规则：只允许放协议、模型、字段定义，禁止放业务逻辑。✅
- 已确认契约修改须走完整 P0 审核流程。✅

### 自校验结果核验

- TASK-0002 任务文档结构与 WORKFLOW.md 治理规则一致。✅
- 文件白名单分级（P-LOG / P0 / P1）标注清晰，与 WORKFLOW.md 保护级别一致。✅
- 风险矩阵覆盖服务边界、契约精度、越权操作、旧系统混入四个主要风险。✅
- 执行阶段拆分清晰，两个阶段分别标明执行方与所需 Token。✅
- 本轮预审阶段未写入任何 contracts 或 services 目录，均为 P-LOG 账本写入。✅

### 风险说明

- R1（P0 Token 前置要求）：任何 contracts 写入必须先等 Jay.S 审批并签发 Token，不可绕过。
- R2（契约精度风险）：已要求在申请 Token 前先在任务文档中列字段草稿，经自校验后方可申请。
- R3（模拟交易 agent 执行边界）：项目架构师只输出骨架派发包，不代操 services 目录写入。
- R4（旧系统代码混入）：已明确旧系统对接只允许在 `integrations/legacy-botquant/` 中存放。
- R5（TASK-0001 遗留未提交账本）：建议随本次 TASK-0002 建档提交一并合批处理。

## 下一步

1. TASK-0002 已获 Jay.S 批准（终审通过），架构师进入阶段一草稿准备，请在 `shared/contracts/drafts/sim-trading/` 完成契约草稿并通知 Atlas。
2. 架构师草稿自校验完成后，向 Jay.S 申请并在 lockctl 中粘贴 P0 Token，方可将草稿迁入 `shared/contracts/sim-trading/`（P0 保护区）并完成锁回。
3. 阶段一终审完成后：向 Jay.S 申请 `services/sim-trading/src/` 的 P1 Token，派发给模拟交易 agent 执行阶段二骨架创建。
