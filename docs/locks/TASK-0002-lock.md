# TASK-0002 Lock 记录

## Lock 信息

- 任务 ID：TASK-0002
- 执行 Agent：
  - 项目架构师（P-LOG 区账本 + P0 区契约，阶段一）
  - 模拟交易 agent（P1 区服务骨架，阶段二）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/contracts/sim-trading/`（P0 区）：**需要 Jay.S 为项目架构师签发 Token**，审批通过后补填
  - `services/sim-trading/src/`、`services/sim-trading/configs/`（P1 区）：**需要 Jay.S 为模拟交易 agent 签发 Token**，阶段一完成后补填
- 白名单文件（当前阶段：建档）：
  - `docs/tasks/TASK-0002-sim-trading-Phase1-任务拆解与契约登记.md`
  - `docs/reviews/TASK-0002-review.md`
  - `docs/locks/TASK-0002-lock.md`
  - `docs/rollback/TASK-0002-rollback.md`
  - `docs/prompts/公共项目提示词.md`
  - `docs/prompts/agents/项目架构师提示词.md`
- 白名单文件（阶段一：契约初稿，待审批后补填）：
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
- P0 Token 签发时间：待 Jay.S 审批后补填
- P1 Token 签发时间：待阶段一完成后补填
- 当前状态：建档阶段已解锁，执行阶段待 Jay.S 审批

## 说明

本任务分为两个执行阶段，分别对应不同的保护级别与 Token 签发需求：

1. **建档阶段（当前）**：仅写入 P-LOG 协同账本区，不需要 Token。已完成。
2. **阶段一（契约初稿）**：写入 P0 保护区 `shared/contracts/sim-trading/`，必须在 Jay.S 审批方案并签发 P0 Token 后方可执行。
3. **阶段二（服务骨架）**：写入 P1 保护区 `services/sim-trading/`，由模拟交易 agent 执行，需 Jay.S 为模拟交易 agent 签发 P1 Token。
