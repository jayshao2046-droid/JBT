# TASK-0001 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0001
- 执行 Agent：项目架构师
- 对应提交 ID：待填写（Git 仓库初始化后补充）
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 revert / 其他经批准方式
- 回滚结果：N/A

## 影响文件

- `docs/tasks/TASK-0001-锁控器初始化.md`
- `docs/reviews/TASK-0001-review.md`
- `docs/locks/TASK-0001-lock.md`
- `docs/rollback/TASK-0001-rollback.md`
- `docs/prompts/公共项目提示词.md`（如已更新）
- `docs/prompts/agents/项目架构师提示词.md`（如已更新）
- `.jbt/lockctl/`（本地目录，不进入 Git，回滚后需手动删除）

## 回滚说明

1. TASK-0001 属于治理初始化，不涉及业务代码，回滚风险极低。
2. 如需回滚，使用 `git revert <commit-id>` 定向撤销本次提交。
3. `.jbt/lockctl/` 需手动删除后重新执行 bootstrap。
4. 在 Git 仓库初始化之前，本回滚方案理论上无法真正执行（**前置风险 #1 未消除**）。

## 后续动作

- 待 TASK-0001 完成并进入 Git 后，补充对应提交 ID。
