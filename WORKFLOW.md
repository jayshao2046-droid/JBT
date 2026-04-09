# JBT Workflow

【签名】Atlas
【时间】2026-04-03 13:05
【设备】MacBook

## 1. 总则

1. 从本文件生效起，所有新开发只允许在 `~/jbt/` 中进行。
2. `J_BotQuant` 从现在起视为 legacy 运行工程，不再承接任何新开发和新修补。
3. Atlas 作为总项目经理，默认拥有 JBT 全目录读取权，但对服务代码、共享代码、集成代码实行只读原则。
4. Atlas 仅可在 Jay.S 明确授权时修改治理文件，包括 `WORKFLOW.md`、`docs/**` 与 `.github/**` 中的治理类文件。
5. 所有子 agent，包括项目架构师，只能在自己的职责范围内工作，严禁越权修改其他目录的数据与代码。
6. 每个 agent 完成一个动作后，必须更新自己的 agent prompt。
7. 公共项目 prompt 允许所有 agent 读取，但只允许项目架构师写入。
8. 所有窗口在收到“开始工作”后，必须按统一读取顺序自动进入工作循环。
9. 总项目经理调度 prompt 允许所有 agent 读取，但只允许 Atlas 写入。
10. 每完成一个任务批次，必须先完成独立提交与上传，再决定是否进入下一任务。
11. 每完成一个任务后，必须先向 Jay.S 汇报并等待确认，未经确认不得进入下一任务。

## 2. 角色权限矩阵

| 角色 | 可读范围 | 可写范围 | 明确禁止 |
|---|---|---|---|
| Atlas | `~/jbt/` 全部 | `docs/prompts/总项目经理调度提示词.md`、`docs/prompts/agents/总项目经理提示词.md`、治理文件，且需 Jay.S 明确授权 | 修改任一服务业务代码、运行数据、账本、密钥文件 |
| 项目架构师 | `~/jbt/` 全部 | `docs/tasks/**`、`docs/reviews/**`、`docs/locks/**`、`docs/handoffs/**`、`docs/prompts/公共项目提示词.md`、`docs/prompts/agents/项目架构师提示词.md`、架构治理文档 | 直接修改任一服务业务代码 |
| 模拟交易 | `services/sim-trading/**`、必要治理文档、`shared/contracts/**`、`docs/prompts/公共项目提示词.md` | `services/sim-trading/**`、`docs/prompts/agents/模拟交易提示词.md`、自己提交的 handoff 文件 | 修改其他服务目录、运行数据、密钥文件、公共项目 prompt |
| 实盘交易 | `services/live-trading/**`、必要治理文档、`shared/contracts/**`、`docs/prompts/公共项目提示词.md` | `services/live-trading/**`、`docs/prompts/agents/实盘交易提示词.md`、自己提交的 handoff 文件 | 修改其他服务目录、运行数据、密钥文件、公共项目 prompt |
| 回测 | `services/backtest/**`、必要治理文档、`shared/contracts/**`、`docs/prompts/公共项目提示词.md` | `services/backtest/**`、`docs/prompts/agents/回测提示词.md`、自己提交的 handoff 文件 | 修改其他服务目录、运行数据、密钥文件、公共项目 prompt |
| 决策 | `services/decision/**`、必要治理文档、`shared/contracts/**`、`docs/prompts/公共项目提示词.md` | `services/decision/**`、`docs/prompts/agents/决策提示词.md`、自己提交的 handoff 文件 | 修改其他服务目录、运行数据、密钥文件、公共项目 prompt |
| 数据 | `services/data/**`、必要治理文档、`shared/contracts/**`、`docs/prompts/公共项目提示词.md` | `services/data/**`、`docs/prompts/agents/数据提示词.md`、自己提交的 handoff 文件 | 修改其他服务目录、运行数据、密钥文件、公共项目 prompt |
| 看板 | `services/dashboard/**`、必要治理文档、`shared/contracts/**`、`docs/prompts/公共项目提示词.md` | `services/dashboard/**`、`docs/prompts/agents/看板提示词.md`、自己提交的 handoff 文件 | 修改其他服务目录、运行数据、密钥文件、公共项目 prompt |

说明：

1. `shared/contracts/**` 为跨服务契约区，不属于任一服务私有目录。
2. `docs/prompts/总项目经理调度提示词.md` 为全员可读、Atlas 独写的总调度面板。
3. `docs/prompts/公共项目提示词.md` 为全员可读、项目架构师独写的公共协同面板。
4. `docs/prompts/agents/*.md` 为 agent 私有 prompt，默认只允许对应 agent 自己写。
5. 任何 agent 若需要修改 `shared/contracts/**`、`shared/python-common/**`、`integrations/**`、`.github/**`、`docker-compose.dev.yml`、`WORKFLOW.md`，都必须走 P0 保护流程。

## 3. 目录分级与保护级别

### P0 保护目录

- `WORKFLOW.md`
- `.github/**`
- `shared/contracts/**`
- `shared/python-common/**`
- `integrations/**`
- `docker-compose.dev.yml`
- 各服务 `.env.example`

规则：必须先由项目架构师预审，再由 Jay.S 生成文件级 Token，最后才能修改。

### P1 服务业务目录

- `services/*/src/**`
- `services/*/tests/**`
- `services/*/configs/**`

规则：仅服务 owner agent 可修改，且必须经过“一件事一审核一上锁”流程。

### P-LOG 协同账本目录

- `docs/tasks/**`
- `docs/reviews/**`
- `docs/locks/**`
- `docs/handoffs/**`
- `docs/prompts/总项目经理调度提示词.md`
- `docs/prompts/公共项目提示词.md`
- `docs/prompts/agents/**`

规则：

1. 该区域用于自动协同与项目留痕。
2. 该区域不使用代码 Token 锁控，而使用“角色归属写权限”。
3. Atlas 负责 `docs/prompts/总项目经理调度提示词.md` 与 `docs/prompts/agents/总项目经理提示词.md`。
4. 项目架构师负责 `docs/tasks/**`、`docs/reviews/**`、`docs/locks/**`、`docs/prompts/公共项目提示词.md`。
5. 每个子 agent 只允许写自己的 prompt 和自己提交的 handoff 文件。
6. 任何 agent 不得改写其他 agent 的私有 prompt。

### P2 永久禁改目录

- `services/*/runtime/**`
- `services/*/logs/**`
- `services/*/.env`
- 任意数据库、账本、真实凭证文件

规则：任何 agent 禁止直接修改；如确需处置，必须由 Jay.S 单独确认并走专门运维流程。

## 4. 标准开发流程

### Step 0. 开窗启动流程

任一 agent 在新窗口收到“开始工作”后，必须按以下顺序执行：

1. 读取 `WORKFLOW.md`。
2. 读取 `docs/prompts/总项目经理调度提示词.md`。
3. 读取 `docs/prompts/公共项目提示词.md`。
4. 读取自己的私有 prompt。
5. 读取与自己有关的最新任务、review、handoff。
6. 若公共项目 prompt 中存在自己的“已批准下一步”，则直接进入执行。
7. 若没有任务，则进入待命，不主动越权找事。

### Step 1. 建任务

1. 一次只允许处理一件明确任务。
2. 一个任务默认只允许落在一个服务目录内。
3. 若涉及多个服务，必须先拆成多个子任务，再分别审核。
4. 任务先由项目架构师记录到 `docs/tasks/`。

### Step 2. 项目架构师预审

1. 项目架构师只审边界、契约、风险、变更范围。
2. 项目架构师预审通过前，任何 agent 不得开始写文件。
3. 预审结果记录到 `docs/reviews/`。

### Step 3. 文件清单冻结

1. 先列出本次允许修改的文件白名单。
2. 白名单之外的文件视为锁定状态。
3. 若中途发现需要新增文件，必须重新提交预审。

### Step 4. Jay.S Token 解锁

1. Jay.S 使用密码生成 Token。
2. Token 必须绑定：任务 ID、执行 Agent、允许修改的文件列表、动作类型、过期时间。
3. Token 默认一次性、单 Agent、单任务、文件级生效。
4. Token 不得写入 Git，不得明文落盘。
5. Token 信息摘要与解锁结果记录到 `docs/locks/`。

### Step 5. 服务 Agent 修改

1. 只有拿到有效 Token 的指定 Agent 才能修改白名单文件。
2. 修改范围不得超出本服务目录，除非 Token 明确包含 `shared/contracts/**` 等保护文件。
3. 不允许借任务名义顺手改无关文件。
4. 每完成一个动作，必须立即更新自己的 agent prompt。

### Step 6. 自校验

1. 先做本服务范围内的导入检查、测试或最小运行验证。
2. 验证失败不得提交项目架构师终审。
3. 自校验结果追加到对应 review 记录。

### Step 6.5. 提交交接单

1. 服务 agent 完成当前批次后，必须写入 handoff 文件。
2. handoff 文件中必须包含：任务 ID、完成动作、修改文件、验证结果、待审问题、建议下一步。
3. 提交 handoff 后，服务 agent 将自己的私有 prompt 状态改为“待项目架构师审核”。
4. handoff 中必须包含一段“向 Jay.S 汇报摘要”和“一段下一步建议”。

### Step 7. 架构师终审

1. 项目架构师终审只做核验，不代写业务代码。
2. 终审必须确认：无越权修改、无跨服务污染、无契约漂移、无明显 bug。
3. 终审未通过，则本任务不算完成。
4. 终审通过后，项目架构师必须更新 `docs/prompts/公共项目提示词.md`，写入：
	- 本次核验结论
	- 对对应子 agent 的核验总结
	- 全局进度变化
	- 已批准的下一步执行项

### Step 8. 重新上锁

1. 终审通过后，所有本次白名单文件立即恢复锁定状态。
2. 后续再改同一文件，必须重新申请 Token。
3. 一次通过不代表永久解锁。
4. 锁回完成后，项目架构师更新公共项目 prompt，并通知下一个 agent 读取新状态继续工作。

### Step 9. 独立提交与上传

1. 每个任务批次必须形成独立提交，不允许多个 agent 的改动混在同一提交中。
2. 每个任务批次审核通过并锁回后，必须执行独立上传。
3. 提交信息必须绑定任务 ID、agent 名称和文件范围。
4. 后续回滚必须以该任务提交为单位执行，不允许全局回滚。
5. 任何回滚默认使用定向 revert，不允许用破坏性全局回退替代。

### Step 10. 向 Jay.S 汇报并等待确认

1. 每个任务完成后，服务 agent 必须把整个任务交代清楚。
2. 项目架构师必须把审核结论、风险、下一步建议同步给 Jay.S。
3. 未得到 Jay.S 对下一步的确认前，任何 agent 不得进入下一任务。
4. “自动推进”仅在单任务内部成立；跨任务推进必须经过 Jay.S 确认。

### 例外流程：极速维修 V2（标准流程之外的单服务 P1 极速通道）

1. `极速维修 V2` 不是通用开发流程，也不替代 Step 1~10；仅在**单服务 P1 热修 / 投诉 / 生产维修**场景下，作为标准流程之外的极速通道使用。
2. 报问题后必须先做只读检查：先确认问题、确认边界、确认归属，在确认完成前不得碰代码，不得提前扩白名单。
3. 最小维修单与预审前置必须压缩到 1 分钟内完成：项目架构师只记录最小必要信息、认证维修区域，并冻结最小必要文件白名单后，由 Jay.S 签发对应 Hotfix Token。
4. 在当前 `lockctl` 仍为文件级 Token 的前提下，“维修区域认证 + Hotfix Token”只表示问题范围和最小白名单已确认；实际解锁仍按文件级 Token 执行，不代表目录级通配授权，也不引入新的锁控命令。
5. 修复完成后，先做最小自校验，再由项目架构师快速验证，并先把结果交付给用户。
6. 用户未确认成功前，不补全后置 `task/review/lock/handoff/prompt` 材料，不执行锁回，不做独立提交；若验证失败，只允许在原任务内继续返工维修，不得扩展到新服务、新目录或新文件集。
7. 用户确认成功后，才允许一次性补齐 `task/review/lock/handoff/prompt`、完成锁回，并形成独立提交。
8. 只要涉及跨服务、`shared/contracts/**`、任一 P0 文件、目录变化、`shared/python-common/**`、`docker-compose.dev.yml`、任一 `.env.example`、`runtime/**`、`logs/**` 或任一真实 `.env`，必须立即退出 V2，回到标准流程。

### 例外流程：终极维护模式 U0（事后审计模式，仅 Jay.S 明确直修指令）

1. `终极维护模式 U0` 独立于 `极速维修 V2`，不是通用开发流程，也不是预审解锁模式；只有在 Jay.S 明确下达“直修”指令时，才允许作为单服务应急维修的事后审计模式使用。
2. `U0` 仅限单服务、已确认归属、且不触及任一 P0 / P2 区域的应急维修；报问题后仍必须先做最小只读确认，确认问题与服务边界后才能进入直修，不得把 `U0` 理解为“无任何限制”或“整端全解锁”。
3. 在满足上述前提时，`U0` 允许跳过前置建单、预审与 Token，直接进入单服务应急维修；该豁免只对当前直修成立，不产生目录级、整端级或跨任务解锁效果。
4. 用户未确认成功前，不补全 `task/review/lock/handoff/prompt` 材料，不锁回，不做独立提交；若修复失败，只能在原单服务范围内继续返工，不得扩展到新服务、新目录或新增共享 / 部署文件。
5. 用户确认成功后，才允许一次性补齐 `task/review/lock/handoff/prompt`，执行独立提交，并按事后审计口径完成收口。
6. 永久禁区在 `U0` 下继续保留，不得因直修放开：`shared/contracts/**`、`shared/python-common/**`、`WORKFLOW.md`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example`、`runtime/**`、`logs/**`、任一真实 `.env`。
7. 只要涉及跨服务、任一 P0 / P2 区域、目录变化、共享库或部署文件，必须立即退出 `U0`，回到标准流程；不得以“先修后说”为由继续扩范围。
8. `U0` 的正式定位是“事后审计模式”；后续留痕只能按最小审计事实补录，不得反向改写标准流程或 `V2` 的既有边界。

## 5. Token 规则

1. 默认只允许文件级 Token，不允许目录级通配解锁。
2. `极速维修 V2` 的 Hotfix Token 在当前工具能力下，仍必须落成最小文件白名单；“维修区域认证”只用于冻结问题范围，不等于目录级通配解锁。
3. Token 默认有效期 30 分钟，超时自动失效。
4. Token 绑定单一 Agent，不允许转交其他 agent 使用。
5. Token 一旦对应文件集变化，立即失效，必须重新申请。
6. 删除、重命名、移动文件必须申请专门的 delete/rename Token。
7. `终极维护模式 U0` 不属于 Token 解锁模式；仅在 Jay.S 明确直修指令且事项仍处于单服务、非 P0 / P2 应急维修时，允许跳过 Token；一旦范围外扩，立即回到标准 Token 流程。

## 6. 新增风控逻辑

1. 变更半径限制：单任务默认最多修改 5 个文件；超过 5 个文件必须拆任务。
2. 跨层限制：一个任务不得同时修改两个以上服务目录和一个共享目录。
3. 契约限制：凡是修改 `shared/contracts/**`，必须先确认受影响服务清单。
4. 公共库限制：`shared/python-common/**` 默认冻结，只有在确认“确实无服务归属”时才允许解锁。
5. 删除限制：删除任意文件前必须先登记备份点或恢复方案。
6. 密钥限制：任何 agent 不得创建、读取、改写真实密钥与真实 `.env`。
7. 运行态限制：任何 agent 不得改写 `runtime/`、`logs/`、账本、数据库快照。
8. 回滚限制：若审查失败，只处理本任务内变更，不得回滚无关文件。
9. 紧急冻结：Jay.S 任意时刻发出“冻结”指令后，所有写操作立即停止。
10. 完成门槛：未经过项目架构师终审与重新上锁的任务，一律视为未完成。
11. Prompt 强制同步：任何动作没有同步到私有 prompt，视为该动作不存在。
12. 公共进度唯一来源：只有项目架构师写入的公共项目 prompt 才能作为跨 agent 调度依据。
13. 独立回滚强制：每个 agent 的任务必须能独立 revert，不得依赖全局回退。
14. 上传强制：审核通过并锁回后的任务，必须形成独立提交并上传后才算真正归档。
15. 用户确认强制：没有 Jay.S 对下一步的确认，禁止自动跳转下一任务。

## 7. 留档规范

1. `docs/tasks/`：记录任务目标、服务归属、文件白名单。
2. `docs/reviews/`：记录项目架构师预审、终审和问题清单。
3. `docs/locks/`：记录 Token 摘要、解锁范围、锁回时间。
4. `docs/prompts/agents/`：记录每个 agent 的当前状态、动作日志、下一步。
5. `docs/prompts/公共项目提示词.md`：记录项目架构师核验后的公共状态与项目总进度。
6. `docs/handoffs/`：记录 agent 间任务交接与待审事项。
7. `docs/prompts/总项目经理调度提示词.md`：记录 Atlas 的跨 agent 派发与任务优先级。
8. `docs/rollback/`：记录任务级独立回滚方案与回滚结果。

## 8. 生效说明

1. 本文件优先级高于各服务 README 中的宽松描述。
2. 如其他文档与本文件冲突，以本文件为准。
3. 后续若要调整本流程，必须由 Jay.S 明确授权 Atlas 修改本文件。
