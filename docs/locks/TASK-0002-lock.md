# TASK-0002 Lock 记录

## Lock 信息

- 任务 ID：TASK-0002
- 执行 Agent：
  - 项目架构师（P-LOG 区账本 + P0 区契约，阶段一）
  - 模拟交易 agent（P1 区服务骨架，阶段二）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/contracts/drafts/sim-trading/`（草稿区）：当前已获 Jay.S 批准，可继续写入草稿与说明，不迁入 P0 正式目录
  - `shared/contracts/sim-trading/`（P0 区）：**需要 Jay.S 为项目架构师签发 Token**，当前仅完成申请前准备
  - `services/sim-trading/src/`、`services/sim-trading/configs/`（P1 区）：**需要 Jay.S 为模拟交易 agent 签发 Token**，阶段一完成后补填
- 白名单文件（当前阶段：建档）：
  - `docs/tasks/TASK-0002-sim-trading-Phase1-任务拆解与契约登记.md`
  - `docs/reviews/TASK-0002-review.md`
  - `docs/locks/TASK-0002-lock.md`
  - `docs/rollback/TASK-0002-rollback.md`
  - `docs/prompts/公共项目提示词.md`
  - `docs/prompts/agents/项目架构师提示词.md`
- 白名单文件（当前阶段：草稿区与自校验）：
  - `shared/contracts/drafts/sim-trading/order.md`
  - `shared/contracts/drafts/sim-trading/position.md`
  - `shared/contracts/drafts/sim-trading/account.md`
  - `shared/contracts/drafts/sim-trading/api.md`
  - `docs/handoffs/TASK-0002-架构师阶段一继续执行.md`
- 白名单文件（阶段一正式迁移，待 P0 Token 后执行）：
  - `shared/contracts/sim-trading/order.md`
  - `shared/contracts/sim-trading/position.md`
  - `shared/contracts/sim-trading/account.md`
  - `shared/contracts/sim-trading/api.md`
- 白名单文件（阶段二：服务骨架，待阶段一完成后补填）：
  - `services/sim-trading/src/main.py`
  - `services/sim-trading/src/api/`（骨架）
  - `services/sim-trading/src/execution/`（骨架）
  - `services/sim-trading/src/ledger/`（骨架）
  - `services/sim-trading/src/risk/`（骨架）
  - `services/sim-trading/src/gateway/`（骨架）
  - `services/sim-trading/configs/`（骨架）
  - `docs/prompts/agents/模拟交易提示词.md`
- 解锁时间：2026-04-03（建档即解锁，P-LOG 区）
- 失效时间：TASK-0002 终审通过后锁回
- 锁回时间：待填写
- P0 Token 签发时间：待 Jay.S 提供实际 Token 后补填
- P1 Token 签发时间：待阶段一完成后补填
- 当前状态：阶段一草稿与自校验已完成，P0 正式写入待 Token

## 说明

本任务分为两个执行阶段，分别对应不同的保护级别与 Token 签发需求：

1. **建档阶段**：仅写入 P-LOG 协同账本区，不需要 Token。已完成。
2. **阶段一当前步骤**：允许在草稿区 `shared/contracts/drafts/sim-trading/` 完善草稿与自校验，不迁入 P0 正式目录。
3. **阶段一正式迁移**：写入 `shared/contracts/sim-trading/` 时，必须持有 Jay.S 提供的 P0 Token。
4. **阶段二（服务骨架）**：写入 P1 保护区 `services/sim-trading/`，由模拟交易 agent 执行，需 Jay.S 为模拟交易 agent 签发 P1 Token。

## 执行记录（变更）

- 2026-04-03：Jay.S 批准 TASK-0002 进入执行态（阶段一：契约草稿准备）。
- 2026-04-03：建档提交已落地，提交 ID：`6585b1d`。
- 当前 P0 Token 状态：Jay.S 已批准阶段一继续执行，但尚未提供四个正式目标文件的实际 Token。
- 当前执行状态：阶段一（草稿区）四份草稿与自校验已完成，等待 Jay.S 提供四个正式目标文件的 P0 Token。
