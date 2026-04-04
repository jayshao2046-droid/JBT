# TASK-0006 Lock 记录

## Lock 信息

- 任务 ID：TASK-0006
- review-id：REVIEW-TASK-0006
- 阶段：预审已完成，待 Token 签发；业务文件尚未执行
- 执行 Agent：
  - 项目架构师（P-LOG 治理文件）
  - 回测 Agent（P1 业务文件，待 Token 签发后执行）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/backtest/` P1 区 3 文件：待 Jay.S 签发 P1 Token
  - `shared/contracts/backtest/api.md` P0 区 1 文件：待 Jay.S 签发 P0 Token

## 当前状态

**待签发**（预审通过，白名单已冻结，等待 Jay.S 签发 Token）

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0006-backtest-Docker部署与契约更新.md`
2. `docs/reviews/TASK-0006-review.md`
3. `docs/locks/TASK-0006-lock.md`
4. `docs/rollback/TASK-0006-rollback.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 业务文件白名单（待 Token 签发后解锁）

### P1 Token 范围（3 文件，新建）

1. `services/backtest/Dockerfile`
2. `services/backtest/V0-backtext 看板/Dockerfile`
3. `services/backtest/docker-compose.yml`

### P0 Token 范围（1 文件，修改）

4. `shared/contracts/backtest/api.md`（仅"当前任务输入口径"节）

## 当前继续锁定的文件

- `docker-compose.dev.yml`（根目录 P0，本轮不动）
- `services/backtest/.env.example`（P0，本轮不动）
- `services/backtest/src/backtest/**`（TASK-0005 已锁回，本轮不动）
- `shared/contracts/backtest/backtest_job.md`（本轮不动）
- `shared/contracts/backtest/backtest_result.md`（本轮不动）
- `shared/contracts/backtest/performance_metrics.md`（本轮不动）

## Token 签发后追加记录（待填）

- P1 token_id：（待签发）
- P0 token_id：（待签发）
- 签发时间：（待签发）
- 有效期：（待签发）
- lockback review-id：（待执行）
- lockback 结果：（待执行）
- 当前状态：（待 lockback）
