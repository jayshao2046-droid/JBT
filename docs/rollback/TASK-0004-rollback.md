# TASK-0004 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0004
- 执行 Agent：
  - 项目架构师（预审治理）
  - 回测 Agent（建议执行主体；如 Jay.S 改指派，则以 Token 绑定主体为准）
- 对应提交 ID：待任务完成后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`（不得使用 `git reset --hard`）
- 回滚结果：N/A

## 影响文件（治理阶段）

1. `docs/tasks/TASK-0004-backtest-dashboard-Phase1-两页收敛.md`
2. `docs/reviews/TASK-0004-review.md`
3. `docs/locks/TASK-0004-lock.md`
4. `docs/rollback/TASK-0004-rollback.md`
5. `docs/handoffs/TASK-0004-看板预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 影响文件（开发阶段，待 Token 后）

1. `services/backtest/V0-backtext 看板/app/page.tsx`
2. `services/backtest/V0-backtext 看板/app/agent-network/page.tsx`
3. `services/backtest/V0-backtext 看板/app/operations/page.tsx`
4. 对应执行 Agent 的私有 prompt
5. 对应开发 handoff 文件

## 回滚原则

1. 治理文件与业务文件应随各自独立提交分别回滚，不得混用一次全局回退。
2. 若开发阶段仅涉及 3 个业务文件，则回滚也只允许针对该批次提交执行定向 revert。
3. 不得顺带恢复 `app/layout.tsx`、`package.json` 或本轮未纳入白名单的页面文件。
4. 若后续发生补充预审扩白名单，则必须在本文件追加新的影响文件与对应回滚边界。

## 当前结论

- 预审账本已建立。
- 开发阶段尚未开始，当前无业务提交需要回滚。