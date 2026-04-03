# TASK-0002 预审 Review

## Review 信息

- 任务 ID：TASK-0002
- 审核角色：项目架构师
- 审核阶段：阶段一正式迁移与最小自校验完成
- 审核时间：2026-04-03
- 审核结论：通过（四份正式契约已落地；与 drafts 一致；字段命名与 API 交叉引用无漂移；已准备进入终审与锁回）

## 核验内容

### 边界核验

- 本任务分为两个阶段：阶段一为契约登记（P0 保护区），阶段二为服务骨架（P1 保护区）。
- 项目架构师仅负责阶段一契约初稿的写入，以及阶段二的派发包输出，不进入 `services/sim-trading/` 目录写入任何文件。
- 模拟交易 agent 负责阶段二 `services/sim-trading/` 的所有文件创建，不越权写入其他服务目录。
- 本轮正式迁移仅写入 P0 Token 白名单中的四份正式契约文件，未新增任何额外 P0/P1 文件，未写入 `services/`，边界合规。

### 文件白名单核验

- `docs/tasks/TASK-0002-*.md`：P-LOG 区，项目架构师可写。✅
- `docs/reviews/TASK-0002-review.md`：P-LOG 区，项目架构师可写。✅
- `docs/locks/TASK-0002-lock.md`：P-LOG 区，项目架构师可写。✅
- `docs/rollback/TASK-0002-rollback.md`：P-LOG 区，项目架构师可写。✅
- `docs/prompts/公共项目提示词.md`：P-LOG 区，项目架构师可写。✅
- `docs/prompts/agents/项目架构师提示词.md`：P-LOG 区，项目架构师可写。✅
- `docs/prompts/agents/模拟交易提示词.md`：P-LOG 区，模拟交易 agent 独写；本轮建档阶段不写入。⏳
- `shared/contracts/sim-trading/`：P0 保护区，Jay.S 已为四份正式契约签发文件级 Token；本轮仅允许写入 `order.md`、`position.md`、`account.md`、`api.md`。✅
- `services/sim-trading/src/`：P1 保护区，需 Jay.S Token，由模拟交易 agent 执行，本轮不写入。⏳
- `services/sim-trading/configs/`：P1 保护区，需 Jay.S Token，由模拟交易 agent 执行，本轮不写入。⏳

### 契约一致性核验

- 本轮已将四份草稿迁入 `shared/contracts/sim-trading/` 正式目录：`order.md`、`position.md`、`account.md`、`api.md`。
- 四份正式契约的字段表、状态定义、排除项与示例口径均与 drafts 保持一致。
- `api.md` 中对 `order.md`、`position.md`、`account.md` 的交叉引用保持稳定，未出现路径或命名漂移。
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
- 四份正式契约已按草稿口径落地到 `shared/contracts/sim-trading/`，正文无字段漂移。✅
- `api.md` 仍只引用 `order.md`、`position.md`、`account.md` 三份正式契约，交叉引用稳定。✅
- 本轮未写入 `services/`，未扩展白名单，边界合规。✅

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

## P0 Token 执行态登记

- 签发时间：2026-04-03 17:49
- token_id：tok-e0a8639a-72b8-4e39-9768-62e6e2debd72
- 文件范围摘要：`shared/contracts/sim-trading/` 下四份正式契约文件（`order.md`、`position.md`、`account.md`、`api.md`）
- 当前状态：正式迁移与最小自校验已完成，待终审与锁回

## 阶段一正式迁移最小自校验

- `order.md`：订单字段、状态归一化定义、排除字段与示例均与 drafts 一致。
- `position.md`：持仓字段、`today_volume` / `yesterday_volume` 语义和 `account_id` 引用保持一致。
- `account.md`：资金字段命名保持 `unrealized_pnl` / `realized_pnl` 统一口径，无 legacy 命名回流。
- `api.md`：六个最小端点、创建订单请求字段以及 `order.md` / `position.md` / `account.md` 引用均保持一致。
- 本轮未复制 legacy 业务逻辑，正式目录仅包含字段定义与接口说明。

## 下一步

1. 向 Jay.S 汇报阶段一正式迁移结果，并申请确认进入终审与锁回收口。
2. 终审通过后，立即锁回本轮四份正式契约文件。
3. 阶段一锁回完成后，再决定是否启动 sim-trading 阶段二 P1 申请。

已锁回：2026-04-03，Atlas 已执行 lockback，结果为 `locked`。
