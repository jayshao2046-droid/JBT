# TASK-0002 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0002
- 执行 Agent：
  - 项目架构师（建档阶段 + 阶段一契约初稿）
  - 模拟交易 agent（阶段二服务骨架）
- 对应提交 ID：
  - 建档提交：待完成后补填
  - 阶段一提交：待完成后补填
  - 阶段二提交：待完成后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 revert / 其他经批准方式
- 回滚结果：N/A

## 影响文件（建档阶段）

- `docs/tasks/TASK-0002-sim-trading-Phase1-任务拆解与契约登记.md`
- `docs/reviews/TASK-0002-review.md`
- `docs/locks/TASK-0002-lock.md`
- `docs/rollback/TASK-0002-rollback.md`
- `docs/prompts/公共项目提示词.md`
- `docs/prompts/agents/项目架构师提示词.md`

## 影响文件（阶段一，待补填）

- `shared/contracts/sim-trading/order.md`
- `shared/contracts/sim-trading/position.md`
- `shared/contracts/sim-trading/account.md`
- `shared/contracts/sim-trading/api.md`

## 影响文件（阶段二，待补填）

- `services/sim-trading/src/`（骨架各文件）
- `services/sim-trading/configs/`（骨架各文件）
- `docs/prompts/agents/模拟交易提示词.md`

## 回滚说明

1. **建档阶段**：仅账本与 prompt 文件，使用 `git revert <commit-id>` 定向撤销建档提交即可，无业务影响。
2. **阶段一（契约初稿）**：回滚契约文件需同步通知模拟交易 agent 暂停对应接口实现，防止契约与实现不一致。
3. **阶段二（服务骨架）**：仅骨架无业务逻辑，回滚风险极低；但需确认不影响后续已在骨架基础上的开发内容。
4. 每个阶段独立提交、独立可回滚，互不依赖。

## 后续动作

- 待每个阶段完成后，补充对应提交 ID。
- 如需回滚，回滚前必须告知 Jay.S 并经架构师评估影响范围。
