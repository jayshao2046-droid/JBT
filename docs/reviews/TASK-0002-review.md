# TASK-0002 预审 Review

## Review 信息

- 任务 ID：TASK-0002
- 审核角色：项目架构师
- 审核阶段：阶段一草稿自校验完成
- 审核时间：2026-04-03
- 审核结论：通过（四份草稿已完成并通过自校验；P0 正式写入仍待实际 Token）

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

- 本轮仅在 `shared/contracts/drafts/sim-trading/` 草稿区完善字段与接口说明，未写入 P0 正式契约区。
- 已确认 `shared/contracts/` 目录规则：只允许放协议、模型、字段定义，禁止放业务逻辑。✅
- 已确认契约修改须走完整 P0 审核流程。✅

### 自校验结果核验

- TASK-0002 任务文档结构与 WORKFLOW.md 治理规则一致。✅
- 文件白名单分级（P-LOG / P0 / P1）标注清晰，与 WORKFLOW.md 保护级别一致。✅
- 风险矩阵覆盖服务边界、契约精度、越权操作、旧系统混入四个主要风险。✅
- 执行阶段拆分清晰，两个阶段分别标明执行方与所需 Token。✅
- 本轮阶段一草稿使用最小必要字段，且已去除 `internal_id`、网关原始状态、broker/investor 等实现绑定字段。✅
- 订单状态已做归一化，避免直接暴露 legacy/TqSdk 的 `ALIVE`、`FINISHED` 等内部口径。✅
- 持仓草稿保留期货场景所需的 `today_volume` / `yesterday_volume`，以支撑后续 `close_today` 语义。✅
- 账户草稿保留资金、保证金、盈亏与风险比率最小集合，未引入账本实现字段。✅
- API 草稿仅覆盖下单、撤单、查单、查持仓、查账户、健康检查六个最小端点，未引入管理或运维扩展接口。✅
- 本轮未写入 `shared/contracts/sim-trading/` 或 `services/`，边界合规。✅

### 风险说明

- R1（P0 Token 前置要求）：任何 contracts 写入必须先等 Jay.S 审批并签发 Token，不可绕过。
- R2（契约精度风险）：已要求在申请 Token 前先在任务文档中列字段草稿，经自校验后方可申请。
- R3（模拟交易 agent 执行边界）：项目架构师只输出骨架派发包，不代操 services 目录写入。
- R4（旧系统代码混入）：已明确旧系统对接只允许在 `integrations/legacy-botquant/` 中存放。
- R5（TASK-0001 遗留未提交账本）：已由提交 `6585b1d` 消除，不再构成当前阻塞。

## 阶段一草稿自校验

- `order.md`：已拆分 `side` 与 `offset`，保留跨服务必要的订单生命周期字段，不暴露网关内部订单 ID。
- `position.md`：已按 futures 场景定义方向、昨仓/今仓、可平量与浮动盈亏，避免把内部账本结构塞入契约。
- `account.md`：已统一资金字段命名，保留 `pre_balance` 用于日内损益口径，移除实现相关静态字段。
- `api.md`：已统一到 `/api/v1` 前缀，端点只引用三份模型草稿，不承载业务实现细节。

## P0 Token 申请清单

- `shared/contracts/sim-trading/order.md`
- `shared/contracts/sim-trading/position.md`
- `shared/contracts/sim-trading/account.md`
- `shared/contracts/sim-trading/api.md`

## 下一步

1. 继续留在草稿区，等待 Jay.S 提供以上四个 P0 目标文件的实际 Token。
2. 获得 P0 Token 后，再将草稿迁入 `shared/contracts/sim-trading/` 并执行阶段一终审与锁回。
3. 阶段一终审完成后，再向 Jay.S 申请 `services/sim-trading/src/` 的 P1 Token，派发给模拟交易 agent 执行阶段二骨架创建。
