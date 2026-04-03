# TASK-0003 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0003
- 执行 Agent：
  - 项目架构师（建档阶段 + 阶段一契约迁移）
  - 回测 Agent（阶段二 批次A/B/C + 阶段三看板）
- 对应提交 ID：
  - 建档提交（含草稿）：待完成后补填
  - 阶段一正式迁移提交：待完成后补填
  - 批次 A 提交：待完成后补填
  - 批次 B 提交：待完成后补填
  - 批次 C 提交：待完成后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 git revert（不得使用 git reset --hard）
- 回滚结果：N/A

## 影响文件（建档阶段，本批次）

- `docs/tasks/TASK-0003-backtest-全开发任务拆解与契约登记.md`
- `docs/reviews/TASK-0003-review.md`
- `docs/locks/TASK-0003-lock.md`
- `docs/rollback/TASK-0003-rollback.md`
- `docs/handoffs/TASK-0003-回测全开发阶段一预审与启动交接.md`
- `docs/prompts/公共项目提示词.md`
- `docs/prompts/agents/项目架构师提示词.md`
- `shared/contracts/drafts/backtest/backtest_job.md`
- `shared/contracts/drafts/backtest/backtest_result.md`
- `shared/contracts/drafts/backtest/performance_metrics.md`
- `shared/contracts/drafts/backtest/api.md`

## 影响文件（阶段一正式迁移，待补填）

- `shared/contracts/backtest/backtest_job.md`
- `shared/contracts/backtest/backtest_result.md`
- `shared/contracts/backtest/performance_metrics.md`
- `shared/contracts/backtest/api.md`

## 影响文件（阶段二，待补填）

- `services/backtest/src/`（批次 A/B 各文件）
- `services/backtest/configs/`（批次 C）
- `services/backtest/Dockerfile`、`requirements.txt`（批次 C）
- `docker-compose.dev.yml`（批次 C P0 修改）
- `services/backtest/README.md`（随批次 A 修正）
- `docs/prompts/agents/回测提示词.md`

## 回滚说明

- 各批次独立提交，回滚时优先对对应批次提交执行 `git revert <commit-id>`，不影响其他批次。
- `shared/contracts/backtest/` 回滚必须同步通知项目架构师执行终审取消与锁控更新。
- `docker-compose.dev.yml` 回滚需单独操作，不随批次 C 一起回滚，回滚前须 Jay.S 确认。
- 不得使用 `git reset --hard`，历史必须保留。
