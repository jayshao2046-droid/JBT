# TASK-0002 sim-trading Phase 1 任务拆解、契约初稿登记与骨架定义

## 任务信息

- 任务 ID：TASK-0002
- 任务名称：sim-trading Phase 1 任务拆解、契约初稿登记与骨架定义
- 所属服务：跨治理层（契约区 + sim-trading 服务）
- 执行 Agent：
  - 项目架构师（预审、契约初稿、任务派发）
  - 模拟交易 agent（骨架实现、服务目录写入）
- 前置依赖：
  - TASK-0001 已完全闭环：✅（提交 ID `c849c9ead692649e3d130c295619421332960a33`）
  - Git 仓库已初始化并完成本地初始提交：✅
  - lockctl bootstrap 已完成：✅
  - Jay.S 对 TASK-0002 方案审批：⏳ 等待中
- 允许修改文件白名单：
  - `docs/tasks/TASK-0002-*.md`（本文件）
  - `docs/reviews/TASK-0002-review.md`
  - `docs/locks/TASK-0002-lock.md`
  - `docs/rollback/TASK-0002-rollback.md`
  - `docs/prompts/公共项目提示词.md`
  - `docs/prompts/agents/项目架构师提示词.md`
  - `docs/prompts/agents/模拟交易提示词.md`
  - `shared/contracts/sim-trading/`（P0 区，**需要 Jay.S Token**，方案审批通过后方可写入）
  - `services/sim-trading/src/`（P1 区，**需要 Jay.S Token**，仅骨架目录与占位文件，由模拟交易 agent 执行）
  - `services/sim-trading/configs/`（P1 区，**需要 Jay.S Token**，配置文件骨架，由模拟交易 agent 执行）
- 是否需要 Token：
  - 协同账本区文件（`docs/`、`docs/prompts/`）：否
  - `shared/contracts/sim-trading/`：**是（P0 保护区，需 Jay.S 为项目架构师签发 Token）**
  - `services/sim-trading/src/`、`services/sim-trading/configs/`：**是（P1 保护区，需 Jay.S 为模拟交易 agent 签发 Token）**
- 计划验证方式：
  - 契约文件通过项目架构师预审与终审
  - sim-trading 骨架可在本地独立启动（有最小健康检查）
  - 无跨服务目录读写
  - 无旧系统代码直接复制
- 当前状态：待审核（等待 Jay.S 审批方案，未进入执行态）

## 任务目标

本任务分为两个执行阶段，本轮建档仅完成阶段一的预审准备；阶段二须等 Jay.S 审批后方可开始。

### 阶段一：契约初稿登记（项目架构师执行，需 P0 Token）

1. 在 `shared/contracts/sim-trading/` 建立以下初稿文件：
   - `order.md`：订单模型字段定义（最小必要字段）
   - `position.md`：持仓模型字段定义
   - `account.md`：账户与资金模型字段定义
   - `api.md`：sim-trading 对外暴露的 API 端点清单（供 decision、dashboard 调用）
2. 须对照旧系统（J_BotQuant）梳理字段，只提取最小必要字段，不搬运旧逻辑。

### 阶段二：sim-trading 服务骨架定义（模拟交易 agent 执行，需 P1 Token）

1. 在 `services/sim-trading/src/` 建立以下骨架（仅目录与占位文件，无业务逻辑）：
   - `main.py`：服务入口（仅启动框架与健康检查端点）
   - `api/`：API 层骨架
   - `execution/`：执行链骨架
   - `ledger/`：账本骨架
   - `risk/`：风控骨架
   - `gateway/`：SimNow 对接骨架
2. 在 `services/sim-trading/configs/` 建立配置骨架（对应 `.env.example` 字段注释）
3. 确认骨架可本地运行 `python3 -m services.sim-trading.src.main`（健康检查返回 200）

## 前置风险登记

### 风险 R1：shared/contracts 属于 P0 保护区

- 描述：对 `shared/contracts/sim-trading/` 的任何写入都必须先预审、后取 Token、再执行终审、最后锁回。
- 影响：若跳过审核流程直接写入，违反 WORKFLOW 硬性规则。
- 消除方案：项目架构师先提交契约初稿结构方案（本文件），等 Jay.S 签发 P0 Token 后方可写入。

### 风险 R2：契约定义不准确导致返工

- 描述：若契约初稿字段冗余或遗漏关键字段，后续模拟交易 agent 实现后需多次修改契约，造成工期延误。
- 影响：契约变更需走完整的 P0 审核流程，每次变更成本较高。
- 消除方案：
  1. 在写入 contracts 前，先在 task 文档中列出字段草稿，经架构师自校验后方可申请 Token。
  2. 只取"最小必要字段"，优先保持字段稳定，后续扩展走契约变更流程。

### 风险 R3：模拟交易 agent 越权写服务目录

- 描述：只有模拟交易 agent 可以写 `services/sim-trading/`，项目架构师不得代为写入。
- 影响：边界污染，违反 WORKFLOW 角色权限矩阵。
- 消除方案：项目架构师仅输出骨架结构定义文档（派发包），模拟交易 agent 负责实际文件创建。

### 风险 R4：旧系统代码混入

- 描述：直接从 J_BotQuant 复制业务逻辑到 `services/sim-trading/` 会引入边界污染与耦合。
- 影响：独立部署与独立回滚能力丧失。
- 消除方案：新服务全部重写；旧系统对接逻辑只允许在 `integrations/legacy-botquant/` 中存放。

### 风险 R5：TASK-0001 遗留未提交账本文件

- 描述：TASK-0001 的 6 个账本更新文件（lock、rollback、review、task、公共 prompt、私有 prompt）在初始提交后补写，尚未提交到 Git。
- 影响：当前仍处于工作树有改动但未记录到 Git 的状态。
- 消除方案：在 TASK-0002 建档提交中一并提交，使用提交信息 `docs: finalize TASK-0001 records and open TASK-0002`。

## 交付标准

1. ⏳ Jay.S 审批 TASK-0002 方案（前置条件）
2. ⏳ `shared/contracts/sim-trading/` 初稿登记（审批通过后，需 P0 Token）
3. ⏳ `services/sim-trading/` 服务骨架（需 P1 Token，由模拟交易 agent 执行）
4. ⏳ sim-trading 骨架本地可独立启动（健康检查 200）
5. ⏳ TASK-0002 终审与锁回完成

## 时间记录

- 任务建档时间：2026-04-03
- 当前状态：预审完成，等待 Jay.S 审批后进入执行态
